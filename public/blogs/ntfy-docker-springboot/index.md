我想给自己的小项目加一个手机通知：程序启动了告诉我一声，定时任务跑完了给个结果，磁盘快满了提醒我处理。平时不用一直盯着控制台，真有事情再打开电脑。

顺着这个需求，我整理了一套 ntfy 的用法。先用 Docker 把服务搭起来，再让安卓手机订阅，最后接到 Spring Boot 项目里。下面的域名、账号和主题都是示例，照着操作时换成自己的即可。

## 先弄明白：消息是怎么到手机上的

我把它理解成一个“自己搭的通知中转站”：

```text
我的 Spring Boot 项目 / 定时脚本
              │ 发送 HTTP 请求
              ▼
       自己部署的 ntfy 服务
              │ 分发到同名主题
              ▼
       手机上的 ntfy 客户端
```

这里的 `topic` 就是主题名。比如我用 `my-project-alerts` 放项目通知，手机也订阅这个名字。名字一致，服务器地址也一致，才能收到同一组消息。

ntfy 使用 HTTP 发布和订阅通知，也提供 Docker 部署方式；接口和安装细节可以查 [ntfy 发布文档](https://docs.ntfy.sh/publish/) 和 [安装文档](https://docs.ntfy.sh/install/)。对我来说，先把“发一条、收一条”跑通，再往项目里接就容易理解了。

## 一、用 Docker 搭一个自己的服务

下面按 **Linux 服务器已经安装 Docker 和 Compose 插件** 来写，使用的是 `docker compose` 命令。还没安装的话，可以先看 [Docker Engine 官方安装说明](https://docs.docker.com/engine/install/)。

我这里约定：

| 项目 | 示例值 |
| --- | --- |
| 对外访问地址 | `https://push.example.com` |
| 宿主机监听地址 | `127.0.0.1:8088` |
| 主题 | `my-project-alerts` |
| 手机账号 | `phone`，只读这个主题 |
| 项目账号 | `springboot`，只写这个主题 |

`push.example.com` 是占位域名，需要换成已经解析到自己服务器的域名。整个教程用同一个主题，避免部署时写一个、手机订阅另一个。

### 1. 准备目录和配置

```bash
mkdir -p ntfy/config ntfy/cache ntfy/data
cd ntfy
```

新建 `compose.yml`：

```yaml
services:
  ntfy:
    image: binwiederhier/ntfy:latest
    command: ["serve"]
    restart: unless-stopped
    environment:
      TZ: Asia/Shanghai
    ports:
      - "127.0.0.1:8088:80"
    volumes:
      - ./config:/etc/ntfy
      - ./cache:/var/cache/ntfy
      - ./data:/var/lib/ntfy
```

这里的 `latest` 方便第一次体验；长期使用时，我会在验证后固定镜像版本或 digest，升级前先备份配置和数据。挂载的三个目录分别存配置、消息缓存和账号数据，重建容器时也要保留它们。

新建 `config/server.yml`：

```yaml
base-url: "https://push.example.com"
listen-http: ":80"
cache-file: "/var/cache/ntfy/cache.db"
auth-file: "/var/lib/ntfy/auth.db"
auth-default-access: "deny-all"
behind-proxy: true
```

我从一开始就把匿名访问关掉，再给手机和项目各自分配权限。这样主题名只是分类名称，不用把它当密码。配置项和账号权限的说明见 [ntfy 服务端配置](https://docs.ntfy.sh/config/)。

启动并检查日志：

```bash
docker compose up -d
docker compose logs --tail=50 ntfy
curl -fsS http://127.0.0.1:8088/v1/health
```

健康接口应返回包含 `"healthy":true` 的 JSON。如果起不来，先看配置缩进、端口占用和挂载目录权限。

### 2. 创建两个账号

在 `ntfy` 目录执行，按提示分别设置密码：

```bash
docker compose exec ntfy ntfy user add phone
docker compose exec ntfy ntfy user add springboot
docker compose exec ntfy ntfy access phone my-project-alerts read-only
docker compose exec ntfy ntfy access springboot my-project-alerts write-only
docker compose exec ntfy ntfy token add springboot
```

最后一条会生成项目使用的访问令牌，后面放进环境变量 `NTFY_TOKEN`。它继承 `springboot` 账号的权限，只能往指定主题发消息。手机使用 `phone` 账号和密码订阅。

查看已有授权和令牌：

```bash
docker compose exec ntfy ntfy access
docker compose exec ntfy ntfy token list springboot
```

令牌不要写进 Git，也不要放进前端页面。需要替换时，可以重新生成并撤销旧令牌。

### 3. 用 HTTPS 域名访问

前面的端口只监听服务器本机，所以手机不能直接访问 `服务器IP:8088`。我用同一台宿主机上的 Nginx 接收 HTTPS 请求，再转发给 ntfy。

下面的配置放进现有 Nginx 的 `http` 配置上下文，证书路径也要替换。**证书需要先申请好**，这段配置本身不会申请证书。

```nginx
server {
    listen 443 ssl;
    server_name push.example.com;

    ssl_certificate /etc/letsencrypt/live/push.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/push.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8088;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 1d;
    }
}
```

`proxy_buffering off` 和较长的读取超时是为了让订阅连接正常保持。反向代理的完整说明可以对照 [ntfy 代理配置](https://docs.ntfy.sh/config/#behind-a-proxy-tls-etc)。

检查配置后再重载：

```bash
sudo nginx -t
sudo systemctl reload nginx
curl -fsS https://push.example.com/v1/health
```

服务器防火墙需要允许 HTTPS 的 443 端口。如果 Nginx 也跑在 Docker 里，容器中的 `127.0.0.1` 指向它自己，需要改用共享 Docker 网络和服务名，并调整端口暴露方式；这里的示例按宿主机 Nginx 编写。

## 二、让安卓手机收到第一条消息

我会从 [ntfy 手机端说明](https://docs.ntfy.sh/subscribe/phone/) 找客户端入口，然后进行下面几步：

1. 安装并打开 ntfy，允许系统通知权限。
2. 在应用设置的账号管理中，为 `https://push.example.com` 添加 `phone` 账号和密码。
3. 新建订阅，选择自定义服务器 `https://push.example.com`。
4. 主题填写 `my-project-alerts`，保存订阅。

手机里填的服务器地址不要带主题路径；主题单独填写。

下面的命令在服务器或电脑的 **Bash 终端**执行。先输入令牌，避免把明文直接留在命令历史中：

```bash
read -r -s -p "输入 ntfy 令牌: " NTFY_TOKEN
printf '\n'
export NTFY_TOKEN

curl --fail-with-body \
  -H "Authorization: Bearer ${NTFY_TOKEN}" \
  -H "Content-Type: application/json" \
  --data '{
    "topic": "my-project-alerts",
    "title": "我的第一条通知",
    "message": "手机能看到这条消息，说明发送和订阅都接通了。",
    "priority": 3,
    "tags": ["white_check_mark"]
  }' \
  https://push.example.com/
```

我优先使用 JSON 请求：中文标题放在请求体里，也方便后面在 Java 中序列化。**JSON 发布到服务器根路径 `/`，主题写在 `topic` 字段里。** 如果改用纯文本方式，才是把正文发送到 `/<主题名>`。字段定义见 [ntfy JSON 发布接口](https://docs.ntfy.sh/publish/#publish-as-json)。

常用的字段我先记住这几个：

| 字段 | 我怎么用 |
| --- | --- |
| `topic` | 区分项目或通知类型 |
| `title` | 一眼看清发生了什么 |
| `message` | 正文，写结果和必要线索 |
| `priority` | 1～5，普通结果用 3，需要处理的异常用 4 或 5 |
| `tags` | 如 `warning`、`white_check_mark`，帮助识别消息 |
| `click` | 可选，点击后打开自己的状态页 |

这些参数的实际表现也受手机客户端和系统通知设置影响，不能把“紧急优先级”理解成一定绕过静音。[ntfy 消息参数说明](https://docs.ntfy.sh/publish/)

安卓自建服务的订阅需要保持后台连接。如果亮屏能收到、锁屏就延迟，我会检查通知权限、后台运行、自启动和电池优化设置，再用移动网络锁屏测试一次。各客户端版本的即时投递行为可查 [手机端即时投递说明](https://docs.ntfy.sh/subscribe/phone/#instant-delivery)。

## 三、接进我的 Spring Boot 项目

这部分按 **Java 17、Spring Boot 3.x、`spring-boot-starter-web`** 编写。它使用 JDK 自带的 `HttpClient`，JSON 使用 Web starter 已经带入的 Jackson，不需要再加一个 ntfy SDK。

下面三个 Java 文件都放在 `com.example.notifydemo` 包里；接入已有项目时换成自己的包名，并确保位于 Spring Boot 的组件扫描范围内。

### 1. 先准备依赖和配置

已有 Spring Boot Web 项目可以跳过依赖这步。项目使用自己的 Spring Boot 3.x 父工程或 BOM 管理版本：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>
```

`application.yml` 增加：

```yaml
spring:
  application:
    name: my-blog-api

ntfy:
  enabled: ${NTFY_ENABLED:false}
  base-url: ${NTFY_BASE_URL:https://push.example.com}
  topic: ${NTFY_TOPIC:my-project-alerts}
  token: ${NTFY_TOKEN:}

demo:
  disk-path: ${NTFY_DISK_PATH:.}
  min-free-gb: ${NTFY_MIN_FREE_GB:1}
```

默认关闭推送，避免一启动开发环境就往手机发消息。需要发送时，在项目运行环境设置 `NTFY_ENABLED=true`、正确的 `NTFY_BASE_URL` 和 `NTFY_TOKEN`。

### 2. 封装一个发送服务

新建 `NtfyNotifier.java`：

```java
package com.example.notifydemo;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.Map;

@Service
public class NtfyNotifier {
    private final ObjectMapper mapper;
    private final boolean enabled;
    private final URI endpoint;
    private final String topic;
    private final String token;
    private final HttpClient client = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(3))
            .build();

    public NtfyNotifier(ObjectMapper mapper,
            @Value("${ntfy.enabled:false}") boolean enabled,
            @Value("${ntfy.base-url}") String baseUrl,
            @Value("${ntfy.topic}") String topic,
            @Value("${ntfy.token:}") String token) {
        this.mapper = mapper;
        this.enabled = enabled;
        this.endpoint = URI.create(baseUrl.replaceAll("/+$", "") + "/");
        this.topic = topic;
        this.token = token;
        if (enabled && (token.isBlank() || topic.isBlank())) {
            throw new IllegalArgumentException("开启 ntfy 时必须配置主题和令牌");
        }
    }

    public void send(String title, String message, int priority) {
        if (!enabled) {
            return;
        }
        if (priority < 1 || priority > 5) {
            throw new IllegalArgumentException("priority 必须在 1～5 之间");
        }
        try {
            Map<String, Object> payload = Map.of(
                    "topic", topic,
                    "title", title,
                    "message", message,
                    "priority", priority,
                    "tags", List.of(priority >= 4 ? "warning" : "white_check_mark")
            );
            HttpRequest request = HttpRequest.newBuilder(endpoint)
                    .timeout(Duration.ofSeconds(5))
                    .header("Authorization", "Bearer " + token)
                    .header("Content-Type", "application/json; charset=UTF-8")
                    .POST(HttpRequest.BodyPublishers.ofString(
                            mapper.writeValueAsString(payload), StandardCharsets.UTF_8))
                    .build();
            HttpResponse<Void> response = client.send(
                    request, HttpResponse.BodyHandlers.discarding());
            if (response.statusCode() < 200 || response.statusCode() >= 300) {
                throw new IllegalStateException("ntfy 返回 HTTP " + response.statusCode());
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("ntfy 发送被中断", e);
        } catch (IOException e) {
            throw new IllegalStateException("ntfy 发送失败", e);
        }
    }
}
```

这里不手工拼 JSON，中文、换行和双引号交给 Jackson 处理。连接超时设为 3 秒，单次请求超时设为 5 秒；HTTP 非 2xx 会抛出异常，调用方才能知道通知没有发出去。

`base-url` 请填写服务器的根地址，比如 `https://push.example.com`，不要带主题。发送成功表示 ntfy 已接受消息，手机是否显示仍取决于网络、订阅连接和通知权限。

### 3. 案例一：项目启动后提醒我

新建 `NotifyDemoApplication.java`。已有启动类的话，只需要加 `@EnableScheduling`，不用再建第二个启动类。

```java
package com.example.notifydemo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@EnableScheduling
@SpringBootApplication
public class NotifyDemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(NotifyDemoApplication.class, args);
    }
}
```

新建 `DemoNotifications.java`，把启动提醒和后面的磁盘检查放在一起：

```java
package com.example.notifydemo;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.annotation.Profile;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;

@Component
@Profile("ntfy-demo")
public class DemoNotifications {
    private static final Logger log = LoggerFactory.getLogger(DemoNotifications.class);
    private final NtfyNotifier notifier;
    private final String appName;
    private final Path diskPath;
    private final long minFreeBytes;
    private long lastAlertNanos;
    private boolean alerted;

    public DemoNotifications(NtfyNotifier notifier,
            @Value("${spring.application.name:my-app}") String appName,
            @Value("${demo.disk-path:.}") String diskPath,
            @Value("${demo.min-free-gb:1}") long minFreeGb) {
        this.notifier = notifier;
        this.appName = appName;
        this.diskPath = Path.of(diskPath);
        this.minFreeBytes = Math.multiplyExact(minFreeGb, 1024L * 1024 * 1024);
    }

    @EventListener(ApplicationReadyEvent.class)
    public void onReady() {
        notifySafely("项目已启动", appName + " 已完成启动，可以检查服务了。", 3);
    }

    @Scheduled(initialDelay = 60000, fixedDelay = 600000)
    public void checkDisk() {
        try {
            long free = Files.getFileStore(diskPath).getUsableSpace();
            if (free >= minFreeBytes) {
                alerted = false;
                return;
            }
            long now = System.nanoTime();
            if (alerted && now - lastAlertNanos < Duration.ofMinutes(30).toNanos()) {
                return;
            }
            boolean sent = notifySafely("磁盘空间不足",
                    appName + " 所在文件系统可用空间约 "
                            + free / (1024 * 1024) + " MiB，请检查。", 4);
            if (sent) {
                lastAlertNanos = System.nanoTime();
                alerted = true;
            }
        } catch (IOException e) {
            log.warn("读取磁盘空间失败", e);
        }
    }

    private boolean notifySafely(String title, String message, int priority) {
        try {
            notifier.send(title, message, priority);
            return true;
        } catch (RuntimeException e) {
            log.warn("通知发送失败，标题={}", title, e);
            return false;
        }
    }
}
```

我给演示组件加了 `ntfy-demo` profile，只有显式启用才会运行。启动通知使用 `ApplicationReadyEvent`；它能说明应用走到了就绪事件，不能代替数据库、第三方接口等完整健康检查。

### 4. 案例二：磁盘空间不足时通知我

上面的 `checkDisk()` 就是一个可以实际运行的检查：启动一分钟后第一次执行，每次结束十分钟后再检查。启用定时任务需要 `@EnableScheduling`，相关机制见 [Spring 定时任务文档](https://docs.spring.io/spring-framework/reference/integration/scheduling.html)。

默认检查当前工作目录所在的文件系统，可用空间不足 1 GiB 时发优先级 4 的通知；持续不足时，成功发出通知后至少隔 30 分钟再提醒。恢复正常后清除抑制状态，下次不足可以再次提醒。

这只是单实例的内存限频，重启后会重新计时。多副本部署时，每个实例都会检查；需要统一告警时，可以把限频状态放进 Redis 或交给专门的监控系统。在 Docker 里，它检查的是配置路径对应的文件系统，想看数据盘就把数据盘挂载进容器，并把 `NTFY_DISK_PATH` 指向挂载目录。

### 5. 真正启动测试

先确认电脑使用 Java 17。以下是 **Bash** 示例，令牌沿用前面安全输入得到的 `NTFY_TOKEN`：

```bash
export NTFY_ENABLED=true
export NTFY_BASE_URL=https://push.example.com
export NTFY_TOPIC=my-project-alerts
export SPRING_PROFILES_ACTIVE=ntfy-demo
mvn spring-boot:run
```

Windows PowerShell 中，可以在项目终端设置同名环境变量：

```powershell
$env:NTFY_ENABLED = 'true'
$env:NTFY_BASE_URL = 'https://push.example.com'
$env:NTFY_TOPIC = 'my-project-alerts'
$ntfySecret = Read-Host '输入 ntfy 令牌' -AsSecureString
$env:NTFY_TOKEN = [System.Net.NetworkCredential]::new('', $ntfySecret).Password
$env:SPRING_PROFILES_ACTIVE = 'ntfy-demo'
mvn spring-boot:run
```

预期现象是：项目启动后收到一条“项目已启动”。如果想测试磁盘告警，可在测试环境把 `NTFY_MIN_FREE_GB` 临时改成一个高于当前可用空间的值，重启后等待一分钟。测完恢复正常阈值。

别忘了移除测试终端里的令牌：Bash 用 `unset NTFY_TOKEN`，PowerShell 用 `Remove-Item Env:NTFY_TOKEN`。

### 6. 案例三：放到自己的业务任务里

接入现有的导出、备份或同步任务时，我会在原有业务逻辑之后调用 `notifier.send(...)`。下面是放在已有业务类方法中的示意片段，`runMyTask()` 代表自己的任务，`log` 是该类原有的日志对象：

```java
try {
    runMyTask();
} catch (Exception businessError) {
    try {
        notifier.send("任务执行失败", "数据同步失败，请查看服务端日志。", 4);
    } catch (RuntimeException notifyError) {
        log.warn("失败通知没有发出", notifyError);
    }
    throw businessError; // 保留原始业务异常，外层方法需声明或处理它
}

try {
    notifier.send("任务执行完成", "数据同步已完成，可以查看结果了。", 3);
} catch (RuntimeException notifyError) {
    log.warn("任务已经成功，但通知没有发出", notifyError);
}
```

我把成功通知放到业务 `try` 外面，是为了避免“任务做完了，只是推送失败，却被记录成业务失败”。失败提醒也不直接发送原始异常全文，手机上留个简短线索，具体错误回到服务端日志查看。

这个发送方法是同步的，网络不通时会占用当前线程直到失败或超时。定时任务里可以先这样用；如果放进下单、支付等响应敏感的流程，我会改成事务提交后由独立线程池或消息队列发送，并加有限次数重试。数据库事务里的通知应等提交成功后再发送，避免手机已收到“成功”，数据库却回滚。

## 四、收不到消息时，我会按这个顺序查

| 现象 | 先检查什么 |
| --- | --- |
| 服务器本机健康接口不通 | 容器状态、日志、配置缩进、目录权限 |
| 本机通，HTTPS 域名不通 | DNS、证书、Nginx 配置和 443 端口 |
| 发布返回 401 / 403 | 令牌、账号权限，以及主题是否拼错 |
| 发布成功，手机没显示 | 手机账号是否有读取权限、服务器地址和主题是否相同 |
| Wi-Fi 能收，移动网络不能收 | 域名是否只在内网可达，手机是否还在用内网地址 |
| 亮屏能收，锁屏延迟 | 后台连接、通知权限、电池优化和网络切换 |
| Spring Boot 没发启动通知 | `NTFY_ENABLED` 是否开启、`ntfy-demo` profile 是否生效 |

HTTP 发布成功和手机已经展示通知是两件事。排查时先把发送端、服务端和手机端分开看，比只盯着 Java 代码更容易定位。

## 我准备怎么用

对自己的小项目，我会先接三类消息：启动提醒、重要任务结果、需要处理的异常。普通运行日志继续留在服务端，手机只接收我看完能采取行动的内容。

先让通知数量保持可控，真正需要的时候才容易注意到。等任务多起来，再补去重、限频、重试和独立监控，逐步完善就行。
