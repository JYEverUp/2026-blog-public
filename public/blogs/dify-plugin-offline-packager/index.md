把 Dify 部署到内网以后，经常会遇到一个问题：插件文件明明已经下载好了，上传安装却一直转圈，最后报依赖下载失败。

原因是 `.difypkg` 文件里通常只有插件代码和依赖声明，安装时还需要创建 Python 环境、下载依赖。把插件从外网拷贝进来，只完成了第一步。

这篇文章用 `dify-plugin-offline-packager` 把依赖一起装进插件包，再带到内网安装。主流程采用 Docker，适合已经使用 Docker Compose 部署 Dify 的场景。命令根据项目源码和配置整理；目标环境能否使用，仍需要通过后面的断网冷安装与实际调用验收。

## 一、先弄明白：离线插件包解决什么问题

可以把流程理解成下面这样：

```text
联网机器
  原始 .difypkg + Python 依赖下载
                 │
                 ▼
  重新打包：插件代码 + wheels/ + 离线安装配置
                 │ 拷贝到内网
                 ▼
内网 Dify
  上传本地插件包 → 创建 Python 环境 → 从包内安装依赖
                 │
                 ▼
  配置模型地址或工具参数 → 执行一次真实调用
```

这里要分清两件事：

- **插件可以离线安装**：安装 Python 依赖时不需要访问外部软件源。
- **插件功能可以离线运行**：还要看插件调用的服务在哪里。对接公网模型、网页抓取或在线语音服务的插件，打成离线包后也仍然需要访问对应服务。

比如 OpenAI 兼容接口插件可以连接内网模型服务；把公网模型插件重新打包，并不会把模型权重和推理服务装进来。浏览器、字体、Pandoc 等系统组件也不一定属于 Python 依赖，需要单独准备。

## 二、准备与目标环境一致的打包环境

我会先在 **Dify 的部署目录** 执行：

```bash
docker compose images plugin_daemon
docker compose exec plugin_daemon python --version
docker compose exec plugin_daemon uname -m
```

记下 Plugin Daemon 镜像标签、Python 版本和 CPU 架构。假设目标镜像为 `langgenius/dify-plugin-daemon:0.5.3-local`，打包工具里的版本就填 `0.5.3`。

**这个版本是示例，不代表最新版本，也不是 Dify Web/API 的版本号。** 实际以自己的 `plugin_daemon` 镜像为准。Dify 的 Compose 配置会随版本变化，可对照[官方 Compose 源码](https://github.com/langgenius/dify/blob/main/docker/docker-compose.yaml)确认服务定义。

| 需要核对 | 为什么要核对 |
| --- | --- |
| 操作系统 | Windows 的原生扩展不能直接用于 Linux 容器 |
| CPU 架构 | `amd64/x86_64` 与 `arm64/aarch64` 的二进制依赖不能混用 |
| Python 版本 | 带 `cp312` 等标签的 wheel 有对应的解释器要求 |
| Daemon 镜像与系统库 | 下载到的二进制依赖可能依赖特定系统库 |
| 插件与 Dify 兼容要求 | 打包成功不会自动消除插件版本兼容问题 |

联网打包机器需要安装 Git、Docker 和 Docker Compose，并能访问插件来源、Python 软件源及 CLI 下载地址。使用 Windows 时，Docker Desktop 应运行 Linux 容器；宿主机是 Windows 不影响容器里下载 Linux 依赖。

下面优先使用和目标相同的镜像及架构。官方镜像能减少环境差异，但插件额外需要的系统库仍要检查。

## 三、下载工具并设置版本

在 **联网打包机器** 执行：

```bash
git clone https://github.com/kurokobo/dify-plugin-offline-packager.git
cd dify-plugin-offline-packager
```

Linux / macOS 复制配置：

```bash
cp .env.example .env
```

Windows PowerShell 使用：

```powershell
Copy-Item .env.example .env
```

编辑打包工具目录下的 `.env`。这份配置和 Dify 部署目录里的 `.env` 是两个文件：

```dotenv
# 示例：目标 Daemon 为 0.5.3-local 时，这里不带 -local
DIFY_PLUGIN_DAEMON_VERSION=0.5.3
MARKETPLACE_API_URL=https://marketplace.dify.ai
GITHUB_API_URL=https://github.com
PIP_INDEX_URL=https://pypi.org/simple
```

如果访问 PyPI 较慢，可以把 `PIP_INDEX_URL` 改为自己信任的软件源，例如 `https://mirrors.aliyun.com/pypi/simple`。它只调整 Python 依赖下载，不会代理 Docker 镜像、Marketplace 和 GitHub 请求。

检查配置并拉取镜像：

```bash
docker compose config --images
docker compose pull packager
```

这个项目直接使用官方 Daemon 镜像，不需要自己构建 Dockerfile。命令入口被替换为打包脚本，输出目录挂载在当前项目的 `difypkg/` 下。

## 四、三种插件来源，选择一种打包

### 1. 已有本地插件文件

这是最容易核对输入版本的方式。先从可信来源下载原始 `.difypkg`，放进工具目录的 `difypkg/` 文件夹。

假设文件名是 `my-plugin.difypkg`：

```bash
docker compose run --rm packager --local "difypkg/my-plugin.difypkg"
```

Windows 也可以直接运行这条单行命令。传给容器的路径使用 `difypkg/...`，不要写成宿主机上的 `D:\...`，因为容器里看到的是挂载后的目录。

### 2. 从 Marketplace 下载并打包

格式为 `作者/插件名:版本`。下面沿用项目文档中的固定版本示例，实际操作时替换为已经核实可下载的版本：

```bash
docker compose run --rm packager --marketplace "langgenius/openai:0.3.2"
```

这里填写的是插件标识，不是模型名称，也不是 Marketplace 页面的完整 URL。

### 3. 从 GitHub Release 下载并打包

格式为 `owner/repo:tag:附件文件名`，附件应当是 `.difypkg`，不要选择源码压缩包：

```bash
docker compose run --rm packager --github "junjiem/dify-plugin-agent-mcp_sse:0.2.4:agent-mcp_sse.difypkg"
```

Release 的 tag 是否带 `v`、附件叫什么，都要按发布页实际内容填写。这同样是项目文档中的版本示例，不代表当前最新插件。

### 4. 找到输出文件

本地输入示例的结果位于：

```text
difypkg/
  my-plugin.difypkg           原始插件包
  my-plugin-offline.difypkg   准备带到内网的包
```

打包完成会出现 `Success!` 和输出路径。离线包通常会变大，这是把依赖放进去的结果。先保留原始包，后续升级或排查时能确认输入来源。

## 五、不要只看文件名，检查依赖是否真的进了包

`-offline` 是输出命名规则，不是验收凭证。脚本主要做了这些事情：

1. 解压插件，优先识别 `pyproject.toml`，没有时再处理 `requirements.txt`。
2. 下载依赖到 `wheels/`；对于 `pyproject.toml`，先按当前系统与 Python 环境解析，再导出依赖。
3. 加入本地依赖查找配置，调整部分忽略规则，再调用 `dify-plugin` CLI 重新打包。

以下检查可以在联网机器上做，假设已经安装 Python 3，在 PowerShell 中执行：

```powershell
@'
from pathlib import Path
from zipfile import ZipFile

package = Path("difypkg/my-plugin-offline.difypkg")
with ZipFile(package) as archive:
    names = archive.namelist()
    dependencies = [name for name in names if name.startswith("wheels/")]
    print("依赖文件数:", len(dependencies))
    for name in dependencies[:12]:
        print(name)
    for name in ("requirements.txt", "pyproject.toml"):
        if name in names:
            print("\n配置文件:", name)
            print(archive.read(name).decode("utf-8"))
'@ | python -
```

输出的依赖配置应当指向包内目录。`requirements.txt` 路线会加入：

```text
--no-index --find-links=./wheels/
```

`pyproject.toml` 路线会加入类似配置：

```toml
[tool.uv]
no-index = true
find-links = ["./wheels/"]
```

注意这是**检查预期结果**，不要不看现有配置就重复粘贴一个 `[tool.uv]` 段落。具体处理逻辑可以查看[打包脚本源码](https://github.com/kurokobo/dify-plugin-offline-packager/blob/main/scripts/packager.py)。

还要检查 `wheels/` 里的文件类型。当前脚本使用 `pip download`，没有强制只下载二进制 wheel；某些依赖可能下载成 `.tar.gz` 源码包。源码包在目标机器安装时可能继续需要构建依赖、编译器或系统开发库。遇到这种情况，应在匹配的环境中先准备可用 wheel，再重新打包并验证。

如果插件根本没有这两种依赖文件，脚本可能跳过依赖下载。对于确实无依赖的插件这不一定有问题，但不能仅凭打包成功断言所有运行资源都已包含。

## 六、把包带入内网，调整 Dify 安装配置

### 1. 记录文件校验值

Windows 可以计算 SHA-256：

```powershell
Get-FileHash .\difypkg\my-plugin-offline.difypkg -Algorithm SHA256
```

Linux 使用：

```bash
sha256sum difypkg/my-plugin-offline.difypkg
```

把离线包和记录的校验值一起交付，在内网重新计算并比对，确认传输前后文件一致。同时记录插件版本、原始下载地址、Daemon 镜像、Python 版本和架构，方便日后复现。

### 2. 处理重新打包后的签名校验

重新打包会改变包内容，不能继续把原包的官方签名当作信任依据。对自行审查过的离线包，项目文档列出了可能需要调整的 Dify 配置：

```dotenv
FORCE_VERIFYING_SIGNATURE=false
ENFORCE_LANGGENIUS_PLUGIN_SIGNATURES=false
```

这会降低相应的签名校验要求，只应在接受该策略的受控环境中使用。已有组织签名机制时，应优先按组织流程签名和验签。不同 Dify 版本对这些变量的支持、映射和默认值可能不同，修改前核对所部署版本，而不是直接照搬最新分支配置。

### 3. 根据包大小调整上传限制

对于较大的插件包，可以在 **Dify 部署目录的配置中** 按需调整，例如允许约 500 MiB：

```dotenv
PLUGIN_MAX_PACKAGE_SIZE=524288000
NGINX_CLIENT_MAX_BODY_SIZE=500M
```

前者是插件包大小设置，后者是 Nginx 请求体限制。使用外层 Nginx、网关或其他代理时，还需要核对每一层的上传限制，不能只改 Dify 内部这一处。

变量位置和映射请对照部署版本的配置；可以参考 [Dify 1.10.1 环境变量示例](https://github.com/langgenius/dify/blob/1.10.1/docker/.env.example)。新版本也可能拆分配置文件，例如 [Plugin Daemon 默认配置](https://github.com/langgenius/dify/blob/main/docker/envs/core-services/plugin-daemon.defaults)。

### 4. 重新创建受影响的服务

环境变量变更通常需要重新创建容器。对于使用上述服务名的常见 Compose 部署，可以执行：

```bash
docker compose up -d --no-deps --force-recreate api worker plugin_daemon nginx
```

先核对自己的 Compose 服务定义；若版本使用其他 worker 或独立配置文件，也要让实际读取这些变量的服务更新。安排好维护窗口，并确保内网本地已有这些服务所需的镜像。仅执行 `docker compose restart` 不会把新的 Compose 环境变量写进已有容器。

## 七、上传安装，再做真正的离线验收

进入 Dify 的插件管理页面，找到“安装插件”中的本地文件入口，选择 `my-plugin-offline.difypkg`。不同版本的入口文字可能略有差异。

安装时在 Dify 部署目录查看日志：

```bash
docker compose logs -f --tail=100 plugin_daemon
```

我的验收标准是：

1. 在隔离测试环境中阻断公网出口，同时保留 Dify 内部服务之间的网络，以及插件需要访问的内网模型服务。
2. 使用未安装过该插件、没有相应依赖缓存的新环境进行安装，确认能够创建 Python 环境。
3. 日志没有因访问外部软件源、下载构建依赖或系统组件而失败。
4. 在插件管理中能看到安装结果，并完成一次最小真实调用。

**缓存环境里安装成功，不能证明一个包可以完整离线安装。** 已经下载过的依赖可能掩盖缺失项。需要冷安装测试时，使用独立测试实例或独立存储，不要为了清缓存去删除生产环境的插件目录。

如果是 OpenAI 兼容接口插件，还需要把服务地址配置为目标内网接口，例如 `http://model-server:8000/v1`。地址是否需要 `/v1` 以所用插件和模型服务文档为准。容器里的 `127.0.0.1` 指向容器自己，不能拿它直接代表另一台服务器。

## 八、遇到问题，按失败阶段排查

| 现象 | 优先检查 |
| --- | --- |
| 打包时插件下载失败 | 标识、版本、Release tag、附件名和下载源可达性 |
| Python 依赖下载失败 | 软件源、依赖版本、Python 版本和原生扩展是否有适配 wheel |
| CLI 下载失败 | GitHub Release 下载链路；更换 PyPI 镜像对此无效 |
| 上传出现 413 | Dify Nginx 与外层代理的请求体限制 |
| 提示插件包过大 | `PLUGIN_MAX_PACKAGE_SIZE` 是否传到了目标服务 |
| 签名校验失败 | 重打包后的信任策略及当前版本支持的签名配置 |
| 安装仍尝试访问软件源 | 是否选错原始包、离线配置是否生效、依赖是否含远程 URL 或构建依赖 |
| `No matching distribution` / 找不到候选包 | 包内依赖版本是否完整，平台、架构、Python 标签是否匹配 |
| 安装成功，导入时报系统库缺失 | Daemon 镜像中的动态库及插件所需的额外系统组件 |
| 插件能安装，调用超时 | 模型或工具服务的地址、路由、代理、认证及内网可达性 |

特别是文件转换、网页渲染一类插件，除了 Python 包，可能还需要字体、浏览器或外部可执行程序。把这些资源纳入镜像或独立离线交付流程，并测试实际转换，才能判断交付是否完整。

## 九、不使用 Docker 时怎么办

如果 Plugin Daemon 本来就是直接运行在宿主机上，可以安装 `uv`，在与目标匹配的系统、架构和 Python 环境里，从工具仓库根目录执行：

```bash
uv run scripts/packager.py --local "difypkg/my-plugin.difypkg"
```

直接运行脚本时，配置通过进程环境变量传入；它不会自动读取 Compose 使用的 `.env` 文件。例如 PowerShell：

```powershell
$env:DIFY_PLUGIN_DAEMON_VERSION = "0.5.3"
$env:PIP_INDEX_URL = "https://pypi.org/simple"
uv run scripts/packager.py --local "difypkg/my-plugin.difypkg"
```

这里的版本也要换成自己的目标版本。路径相对于当前工作目录，详细用法见[项目本地运行说明](https://github.com/kurokobo/dify-plugin-offline-packager/blob/main/docs/local-usage.md)。

如果目标仍然是 Linux 容器部署，我会继续使用 Docker 打包，减少宿主机系统、Python 与依赖二进制格式不同带来的问题。

以后给插件升级时，也重复这条交付链路：固定输入版本，在匹配环境里打包，检查包内容，记录校验值，再在无公网、无依赖缓存的测试环境里安装和调用。这样交付到内网的，才是经过验证的离线插件包。
