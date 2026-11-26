## 一、简要说明

Elastic Stack 技术栈，别是 `Elasticsearch`、`Logstash`、`Kibana` 组成，简称 ELK 是一套针对日志数据做解决方案的框架。它使您能够聚合来自所有系统和应用程序的日志，分析这些日志，并创建可视化来进行应用程序和基础设施监控、更快的故障排除、安全分析等。

- E = Elasticsearch：Elasticsearch 是在 Apache Lucene 上构建的分布式搜索和分析引擎。对各种语言、高性能和无架构 JSON 文档的支持使 Elasticsearch 成为各种日志分析和搜索使用案例的理想选择。
- L = Logstash：Logstash 是一个开源数据摄取工具，允许您从各种来源收集数据，转换数据，并将数据发送到您希望的目标。通过预构建的筛选器和对 200 多种插件的支持，Logstash 使用户能够轻松摄取数据，无论数据源或类型如何。
- K = Kibana：Kibana 是一种数据可视化和挖掘工具，可以用于日志和时间序列分析、应用程序监控和运营智能使用案例。它提供了强大且易用的功能，例如直方图、线形图、饼图、热图和内置的地理空间支持。此外，付费的 Kibana 还有 x-pack-jdbc 可以使用，让你就像使用 MyBatis 操作 MySQL 数据库一样操作 Elasticsearch 数据。

综上，3个组件的组合使用。由 Logstash 将摄取、转换数据并将其发送到 Elasticsearch 为摄取的数据编制索引，并且分析和搜索这些数据。最终 Kibana 会将分析结果可视化。也就是你可以在 Kibana 上实时看到系统的运行日志。

* 源码：https://github.com/18194085604/Elastic-Stack

## 二、环境配置

做了个工程案例，并配有对应的环境安装、日志上报，你只需要跟随接下来的文章说明，即可知道 ELK 如何配置和使用。

![img](/blogs/_archive-2024-assets/da728ea619bc825d26c4.webp)

- 环境；jdk 1.8、Maven 3.6.x、Docker
- 组件；ELK version 7.17.14 支持 ARM&AMD
- 代码；在 xfg-dev-tech-elk 测试工程中提供了测试代码和环境安装，绿色按钮点击即可安装【确保你已经本地安装了 Docker】

### 1. 环境配置

![img](/blogs/_archive-2024-assets/c38ff3f4382289447a52.webp)

- docker-compose.yml 运行时会加载下面的 kibana、logstash 配置信息。
- kibana.yml 设置了资源的基本信息，包括 ES 的连接，中文汉化。
- logstash.conf 设置了日志的格式，上报到 es:9200 的地址信息。这些都可以保持默认不用修改。

### 2. 安装环境

```java
version: '3'
# 执行脚本；docker-compose -f docker-compose.yml up -d
# 控制台；GET _cat/indices - 查看 springboot-logstash- 是否存在，上报后存在，则表示接入成功
services:
  elasticsearch:
    image: elasticsearch:7.17.14
    ports:
      - '9200:9200'
      - '9300:9300'
    container_name: elasticsearch
    restart: always
    environment:
      - 'cluster.name=elasticsearch' # 设置集群名称为elasticsearch
      - 'discovery.type=single-node' # 以单一节点模式启动
      - "cluster.name=docker-cluster" # 设置名称
      - 'ES_JAVA_OPTS=-Xms512m -Xmx512m' # 设置使用jvm内存大小
    networks:
      - elk

  logstash:
    image: logstash:7.17.14
    container_name: logstash
    restart: always
    volumes:
      - /etc/localtime:/etc/localtime
      - ./logstash/logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - '4560:4560'
      - '50000:50000/tcp'
      - '50000:50000/udp'
      - '9600:9600'
    environment:
      LS_JAVA_OPTS: -Xms1024m -Xmx1024m
      TZ: Asia/Shanghai
      MONITORING_ENABLED: false
    links:
      - elasticsearch:es # 可以用es这个域名访问elasticsearch服务
    networks:
      - elk
    depends_on:
      - elasticsearch # 依赖elasticsearch启动后在启动logstash

  kibana:
    image: kibana:7.17.14
    container_name: kibana
    restart: always
    volumes:
      - /etc/localtime:/etc/localtime
      - ./kibana/config/kibana.yml:/usr/share/kibana/config/kibana.yml
    ports:
      - '5601:5601'
    links:
      - elasticsearch:es #可以用es这个域名访问elasticsearch服务
    environment:
      - ELASTICSEARCH_URL=http://elasticsearch:9200 #设置访问elasticsearch的地址
      - 'elasticsearch.hosts=http://es:9200' #设置访问elasticsearch的地址
      - I18N_LOCALE=zh-CN
    networks:
      - elk
    depends_on:
      - elasticsearch

networks:
  elk:
    driver: bridge #网络
 
    
```



![img](/blogs/_archive-2024-assets/1fccf606a8d727f07938.webp)

![img](/blogs/_archive-2024-assets/185d65ed7e044e77c3ed.webp)

- 这是 docker compose 执行脚本，如果你本地已经安装了 Docker 可以直接执行 安装即可。
- 安装完成后，当你看到如上截图，则表示已经运行。注意 Quick Actions 下可以进入日志和控制台。如果启动失败，可以检查日志。

### 3. 日志配置

#### 3.1 引入POM - logstash

```text
<dependency>
    <groupId>net.logstash.logback</groupId>
    <artifactId>logstash-logback-encoder</artifactId>
    <version>7.3</version>
</dependency>
 
    
```

这个Jar是为了上报应用日志用的。工程的根目录下引入是定义版本，在 xfg-dev-tech-app 模块下引入是具体的引入。

#### 3.2 logback 采集

```yml
# logstash部署的服务器IP
logstash:
  host: 127.0.0.1
     
```

```xml
<springProperty name="LOG_STASH_HOST" scope="context" source="logstash.host" defaultValue="127.0.0.1"/>

<!--输出到logstash的appender-->
<appender name="LOGSTASH" class="net.logstash.logback.appender.LogstashTcpSocketAppender">
    <!--可以访问的logstash日志收集端口-->
    <destination>${LOG_STASH_HOST}:4560</destination>
    <encoder charset="UTF-8" class="net.logstash.logback.encoder.LogstashEncoder"/>
</appender>

<root level="info">
    <appender-ref ref="LOGSTASH"/>
</root>
 
    
```

- LOG_STASH_HOST 通过占位符可以使用 yml 配置，这样方便后期动态调整。

## 四、应用测试

### 1. 启动应用&检测上报

```java
public class Application {

    public static void main(String[] args) {
        SpringApplication.run(Application.class);
    }

    /**
     * curl http://localhost:8091/api/ratelimiter/login?fingerprint=uljpplllll01009&uId=1000&token=8790
     */
    @RequestMapping(value = "login", method = RequestMethod.GET)
    public String login(String fingerprint, String uId, String token) {
        log.info("模拟登录 login fingerprint:{}", fingerprint);
        return "模拟登录：登录成功 " + uId;
    }

}
 
    
```

![img](/blogs/_archive-2024-assets/79592e914ec29a208806.webp)

- 地址：[http://0.0.0.0:5601/app/dev_tools#/console(opens new window)](http://0.0.0.0:5601/app/dev_tools#/console)
- 命令：`GET _cat/indices` - 通过命令检测日志上报

### 2. 配置日志

地址：[http://0.0.0.0:5601/app/discover(opens new window)](http://0.0.0.0:5601/app/discover)

#### 2.1 创建索引

![img](/blogs/_archive-2024-assets/f5c6732dcbbbb7ccf571.webp)

![img](/blogs/_archive-2024-assets/c3786ebdcaef834fd703.webp)

- 当你的应用启动后，会上报数据。这个时候在点击 Discover 会提示你有可用的数据。
- 如图创建索引即可。

#### 2.2 回到监控

创建索引后，回到 Discover 即可查看监控日志。在这个阶段，你可以访问应用程序接口，查看上报日志信息；[http://localhost:8091/api/ratelimiter/login?fingerprint=uljpplllll01009&uId=1000&token=8790(opens new window)](http://localhost:8091/api/ratelimiter/login?fingerprint=uljpplllll01009&uId=1000&token=8790)

![img](/blogs/_archive-2024-assets/5ff87c994e5be932172d.webp)

- 当你不断的访问接口，就可以看到上报的日志数据信息了。
