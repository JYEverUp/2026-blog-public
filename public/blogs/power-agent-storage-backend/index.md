假设你让 Agent 做一件事：

> 帮我整理今天的工作，写成一份日报，再把文件发给我。

Agent 想好了日报内容，接下来还有一个实际问题：**这份文件存在哪？**

可以存在你的电脑上，可以存在腾讯云 COS、S3，也可以放进 Docker 容器，或者作为一条文件记录存进 Postgres。`backend` 就是负责把“读文件、写文件”这些动作真正办成的那一层。

这篇先从使用者能看到的现象讲起，再看开发者如何配置、代码怎么连起来。开发部分按这条线展开：**传统业务自己存文件 → 直接用 deepagents 接 backend → 再用 运行层 把接入和工作区处理封装起来。**

前五节先看“文件存哪、为什么统一”；第 6 节直接接 deepagents；第 7、8 节再看这里的配置和封装代码。这样能分清哪些是上游已经提供的能力，哪些是这层封装增加的。

> 说明：本文的“以前”指传统业务系统处理文件存储的几种写法，“现在”指这里采用的 backend 方案，不是本仓库的版本历史。传统写法与存储抽象至今都在使用，不能把它们看成所有系统都经历过的统一时间线。项目实现按 1.0.8 核对；教学代码和源码节选会分别标明。

## 1. 先理解 backend：Agent 说要存文件，它负责真的存进去

可以先把流程理解成这样：

![原文图示 1](/blogs/power-agent-storage-backend/file-flow.png)

[查看大图](/blogs/power-agent-storage-backend/file-flow.svg) · [下载 Mermaid 源文件](/blogs/power-agent-storage-backend/file-flow.mmd)

模型提出“写一份日报”，不代表磁盘上已经有文件了。程序还要调用文件工具，文件工具再通过 backend 执行写入。

如果 backend 是本地文件系统，日报就写到磁盘。如果 backend 是 COS，日报就交给 COS 的接口保存。之后读日报、修改日报、查看文件列表，也由选中的 backend 处理。

**对使用者来说，最直接的差别就是：文件最后在哪、换台机器还能不能拿到，以及 Agent 能不能执行命令。**

这里有个边界先记住：backend 主要管 Agent 使用的文件。聊天记录、长期记忆和运行日志还有各自的保存方式。把文件 backend 换成 COS，不等于把这三类数据也一起搬到了 COS。

## 2. 什么都不配置，会不会没地方存文件？

不会。项目已经准备了默认 backend。这里先讲 运行层 的默认值；直接调用上游 deepagents 的默认值不同，第 6.1 节会对照。

不填写 `backend`，也就是 `backend=None` 时，实际用的是下面这份配置：

```python
# 项目默认值，节选自 backends/__init__.py。
DEFAULT_BACKEND_SPEC = {
    "type": "local_shell",
    "root_dir": "/",
    "virtual_mode": True,
}
```

先不用逐个记参数，知道它的效果就行：**默认在宿主机上操作文件，也支持执行 Shell 命令。** 宿主机就是运行 Agent 的那台电脑或服务器。

`workspace_dir` 指定 Agent 平时应该在哪个工作目录干活。但是默认配置把文件根设为宿主根，所以“给了工作目录”并不意味着“Agent 就只能访问这个目录”。Windows 下的根按本机盘符和路径规则解释。

还有一个容易踩坑的区别：

| 你怎么配置 | 实际效果 |
|---|---|
| 不填，或写 `backend=None` | 用项目默认值，根目录已经明确设成宿主根 |
| 写 `backend="local_shell"` | 如果调用方传入了 `workspace_dir`，会用它作为根，因为这次没有明确指定根 |
| 写 `backend="filesystem"` | 同样可以用工作区作为根，但只提供文件操作，不提供 Shell 执行 |

所以，`None` 和 `"local_shell"` 看起来都选本地 Shell，根目录的来源却不同。

如果你只是没接 COS、S3 之类的远程存储，本地读写照常可用。代价也直观：文件留在这台机器上，换机器、共享文件和保留磁盘数据，需要宿主自己安排。

如果明确配了 COS，但凭证错了或网络不通，写入可能失败。**程序不会自动把这次失败的云端写入改成写本地。**

## 3. 为什么要支持这么多 backend？它们有什么实际区别？

还是拿日报来说，不同环境对“把文件存好”的要求不一样。

你在电脑上调试，存本地就方便；服务换机器部署，希望文件仍然能取到，就可以用外部存储；Agent 需要运行代码，又希望文件和命令在沙箱内处理，就会用到 Docker 或 OpenSandbox。

项目提供的选择可以这样看：

| 配置类型 | 用普通话解释 | 需要知道的区别 |
|---|---|---|
| `filesystem` | 文件存在运行程序的电脑上 | 能读写文件，不能执行 Shell |
| `local_shell` | 文件存在电脑上，还能执行命令 | 执行范围和隔离能力需要另外看配置与环境 |
| `s3` | 文件放在 S3，或 MinIO 等兼容服务里 | 通过 Python 连接工具 boto3 访问存储 |
| `cos` / `oss` / `obs` | 文件分别放在腾讯云、阿里云、华为云的对象存储里 | 使用各厂商提供的连接工具，也就是 SDK；配置字段有所不同 |
| `postgres` | 把文件路径和内容作为数据库记录保存 | 这里存的是“虚拟文件”，不是自动把聊天记录迁入数据库 |
| `docker` / `opensandbox` | 在容器或远程沙箱里处理文件和命令 | 文件能保留多久，取决于沙箱生命周期、卷等安排 |
| `state` | 把文件放进当前会话的运行数据里 | 文件跟着当前会话走，重启后能否恢复取决于会话状态是否被保存 |
| `store` | 借用 LangGraph 的 Store 保存文件 | 可按分组跨会话共享；是否真正写入磁盘，取决于所用的 Store |
| `composite` | 把几个 backend 接到同一个入口上 | 按文件路径决定用哪个 backend |

![后端存储与执行能力分类](/blogs/power-agent-storage-backend/backend-types.png)

[查看大图](/blogs/power-agent-storage-backend/backend-types.svg) · [下载 Mermaid 源文件](/blogs/power-agent-storage-backend/backend-types.mmd)

`state` 和 `store` 依赖对应的运行上下文或配置，不能都当作普通磁盘目录直接使用。

先不必记住全部类型。理解本地、云端、沙箱和组合后端这几类，就能看懂主要接入方式。

## 4. 同时接几个存储，Agent 怎么知道该写到哪个？

用 `composite`。它会看文件路径，再决定交给哪个 backend。

比如我们约定：

- 普通工作文件放本地。
- `/assets/` 开头的文件放 COS。
- `/archive/` 开头的文件放 S3。

那么写不同路径，就会去不同地方：

![原文图示 2](/blogs/power-agent-storage-backend/routing.png)

[查看大图](/blogs/power-agent-storage-backend/routing.svg) · [下载 Mermaid 源文件](/blogs/power-agent-storage-backend/routing.mmd)

这里的 `/assets/`、`/archive/` 就是路由前缀，相当于我们给程序定的分流规则。

假设 COS 还配置了存储前缀 `demo-assets`，那么一次写入会这样走：

```text
Agent 写：/assets/report.md
    → 组合后端看见 /assets/，选择 COS
    → 去掉路由前缀后，交给 COS 的路径是：/report.md
    → COS 最终保存的对象 key 是：demo-assets/report.md
```

对象 key 可以先理解成云存储里定位这份文件的名字。

注意，**路由前缀会被去掉**。如果你希望云端也有 `assets` 这一层，就要在 COS 自己的 `prefix` 里配置出来。

如果同时有 `/assets/` 和 `/assets/private/`，路径 `/assets/private/a.txt` 会选更具体、更长的那条规则。

还有两件事容易误会：

第一，一份文件按规则去对应存储，并不会同时写进本地和云端。因此，接了多个 backend 不代表自动多备份。

第二，默认后端只接收“没有匹配路由”的路径。COS 连接失败后，程序不会因为存在默认本地后端，就把那份文件悄悄存到本地。

## 5. “统一”到底统一了什么？

### 5.1 先看传统业务系统直接接存储的写法

传统系统完全可以由业务自己调用磁盘或云存储接口。例如，本地文件用 Python 的 `Path.write_text()`，S3 用 SDK 的 `put_object()`。这两种调用分别见 [Python 文件操作文档](https://docs.python.org/3.12/library/pathlib.html#pathlib.Path.write_text) 和 [boto3 写入对象文档](https://docs.aws.amazon.com/boto3/latest/reference/services/s3/client/put_object.html)。

把读写放在一个报表服务里，代码可能是下面这样。这是用于对照的传统业务示例，不是仓库源码；文件名由示例调用方提供，重复保存采用覆盖语义。

```python
from pathlib import Path
from typing import Any


class ReportService:
    def __init__(self, local_root: Path, s3_client: Any, bucket: str) -> None:
        self.local_root = local_root
        self.s3_client = s3_client  # 已经由外部创建好的 boto3 client
        self.bucket = bucket

    def save(self, destination: str, name: str, text: str) -> None:
        if destination == "local":
            target = self.local_root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        elif destination == "s3":
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=name,
                Body=text.encode("utf-8"),
            )
        else:
            raise ValueError(f"不支持的存储：{destination}")

    def load(self, destination: str, name: str) -> str:
        if destination == "local":
            return (self.local_root / name).read_text(encoding="utf-8")
        if destination == "s3":
            response = self.s3_client.get_object(Bucket=self.bucket, Key=name)
            return response["Body"].read().decode("utf-8")
        raise ValueError(f"不支持的存储：{destination}")
```

使用它的业务还要指定存储：

```python
# 接着上面的示例，s3_client 是宿主已经创建的连接。
reports = ReportService(Path("reports"), s3_client, bucket="demo-reports")
reports.save("local", "report.md", "今天的日报")
reports.save("s3", "report.md", "今天的日报")
```

这段代码可以解决实际问题。只有一个本地目录、只做上传下载时，它也很直接。

但如果再接 COS，就得在保存、读取等地方增加 COS 分支；再加删除、搜索、文字修改，也要决定每种存储怎么处理。如果这些判断散落到报表、附件、图片等多个业务里，改存储就会牵动多处代码。

### 5.2 外面的系统也早就会抽一层 Storage

另一类传统写法，是先定义一个 `Storage`，业务只调用 `storage.save()`，再分别实现本地和云端存储。这和 backend 的核心思路是相通的。

例如，[Django 的自定义存储文档](https://docs.djangoproject.com/en/4.2/howto/custom-file-storage/) 已经提供继承 `Storage`、实现 `_open()` / `_save()` 的扩展方式；[fsspec](https://filesystem-spec.readthedocs.io/en/latest/) 也为本地、远程等文件系统提供统一接口。因此，不能说传统系统都直接调用 SDK，也不能说这里第一次发明了存储抽象。

区别在于，这里接的是 Agent 的文件工具，还要统一文字编辑、目录搜索、工具结果和工作区路径。仅仅有一个“上传附件”的接口，覆盖不了这些动作。

### 5.3 这里让报表业务只认识 backend

接好 backend 后，同一个报表函数可以这样写：

```python
from deepagents.backends.protocol import BackendProtocol


def create_report(backend: BackendProtocol, text: str) -> str:
    result = backend.write("/report.md", text)
    if result.error is not None:
        raise OSError(result.error)
    return "/report.md"
```

`create_report()` 不需要问“现在是本地还是 S3”。传进来什么 backend，它就通过那个 backend 写文件。配置与连接放在组装阶段，报表函数集中做报表这件事。

同名文件怎么处理，仍要看具体实现：这里的远程公共基类会拒绝重复创建，而本地行为由 deepagents 的实现决定；本次核验环境中的 deepagents 0.7.21 文件系统后端允许覆盖。前面的教学 `save()` 也采用覆盖语义。所以，不能只换个方法名就假定行为完全一样，第 8.2 节会展开远程后端的创建规则。

上层遵守的是一份共同约定，代码里叫 `BackendProtocol`。`Protocol` 在这里可以理解成“每个后端都要提供这些方法、按约定返回结果”。

**统一的是使用方式，底层的区别仍然存在。** 比如云端有网络开销，本地没有；Shell backend 能执行命令，COS backend 没有这项能力；对象存储里的移动常常要先复制再删除，也不能当成本地的一次原子重命名。

## 6. 如果先不做这层封装，直接接 deepagents，怎么写？

前面说的是传统系统如何保存文件。换成 Agent 后，还有一步：让模型能调用文件工具，并把工具调用送到存储。

deepagents 已经提供这部分能力。你可以直接创建一个 backend 对象，交给 `create_deep_agent()`；框架会接上相应文件工具。[deepagents 快速入门](https://docs.langchain.com/oss/python/deepagents/quickstart) 展示了创建、调用 Agent 的基本入口，[backend 文档](https://docs.langchain.com/oss/python/deepagents/backends) 说明了文件后端及组合路由。

本节代码按本项目使用的 deepagents 0.7 接口核对，验证环境为 0.7.21。下面的 `model` 都表示宿主已经初始化好的、支持工具调用的模型，文件接入例子不重复展开模型凭证配置。

### 6.1 最开始，只创建一个原生 Agent

最小的原生调用外形是：

```python
from deepagents import create_deep_agent

# model 已经由宿主配置好。
native_agent = create_deep_agent(model=model)
```

这样已经能获得框架提供的文件能力，不过**原生不传 backend 时，文件默认放进会话状态，也就是 StateBackend**。不能因为模型说“保存了 report.md”，就认定电脑目录里已经出现这份文件。

这里尤其要和第 2 节区分：

| 调用方式 | 不配置 backend 时会怎样 |
|---|---|
| 原生 `create_deep_agent(model=model)` | 默认使用会话状态文件 |
| 本项目的 `AgentConfig(backend=None, ...)` | 运行层 先选择默认本地 Shell，再交给 deepagents |

后者改变了默认接法，这是封装层作出的选择。

### 6.2 想让日报真正落到磁盘，就明确传 FilesystemBackend

可以先写一个很小的原生构造函数：

```python
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend


def build_native_report_agent(model, workspace_dir: Path):
    root = workspace_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)

    backend = FilesystemBackend(
        root_dir=str(root),
        virtual_mode=True,
    )
    return create_deep_agent(
        model=model,
        backend=backend,
        system_prompt="根据用户提供的内容整理日报，并使用文件工具保存。",
    )
```

先构造 backend，再把对象传进 `create_deep_agent()`。这一步就把框架的文件工具和磁盘连接起来了。

使用已配置的真实模型时，调用外形如下：

```python
# 接着上面的函数，model 由宿主提供；invoke 会调用这个模型。
native_agent = build_native_report_agent(model, Path("./demo_workspace"))
result = native_agent.invoke({
    "messages": [{
        "role": "user",
        "content": "今天完成了登录接口。请把日报写到 /report.md。",
    }],
})
```

如果模型按要求调用 `write_file` 写入 `/report.md`，文件就会出现在 `demo_workspace/report.md`。用户消息只是提出任务，实际是否写入仍取决于工具是否被调用、调用结果是否成功。

这里的 `virtual_mode=True` 让示例中的 `/report.md` 按指定根目录映射到磁盘。它提供文件路径规则，不代表获得 Shell 能力；`FilesystemBackend` 本身不提供命令执行。

### 6.3 `write_file` 是谁提供的，怎么连到 backend.write？

不是上面的业务函数自己写的。deepagents 在创建图时会装入 `FilesystemMiddleware`。可以先把 Middleware 理解成框架给 Agent 接功能的一层代码，这一层负责提供文件工具、检查参数和处理结果。

当前安装源码中的组装关系，可以精简成：

```python
# deepagents.graph 内部的关系示意，省略其他中间件和参数。
filesystem_middleware = FilesystemMiddleware(backend=backend)
```

当模型提出 `write_file` 工具调用时，这层代码最终会执行类似下面的逻辑：

```python
# 简化自 deepagents 的文件工具实现。
# validated_path 是已经处理过的文件路径。
result = resolved_backend.write(validated_path, content)
if result.error:
    # 将错误作为工具结果返回给 Agent。
    return ToolMessage(
        content=result.error,
        name="write_file",
        tool_call_id=tool_call_id,
        status="error",
    )
return ToolMessage(
    content=f"Updated file {result.path}",
    name="write_file",
    tool_call_id=tool_call_id,
    status="success",
)
```

所以，模型看到的是 `write_file` 这类工具；存储实现收到的是 `backend.write()`。两者之间的连接和结果翻译，deepagents 已经做好。

![原文图示 3](/blogs/power-agent-storage-backend/architecture.png)

[查看大图](/blogs/power-agent-storage-backend/architecture.svg) · [下载 Mermaid 源文件](/blogs/power-agent-storage-backend/architecture.mmd)

### 6.4 多后端组合，deepagents 原生也支持

`CompositeBackend` 本身就来自 deepagents。为了先看清组装关系，下面用两个本地目录分别模拟工作区和归档区，不需要云端凭证：

```python
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend


def build_native_composite_agent(model, work_dir: Path, archive_dir: Path):
    work_dir = work_dir.resolve()
    archive_dir = archive_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    work_backend = FilesystemBackend(root_dir=str(work_dir), virtual_mode=True)
    archive_backend = FilesystemBackend(root_dir=str(archive_dir), virtual_mode=True)

    combined = CompositeBackend(
        default=work_backend,
        routes={"/archive/": archive_backend},
    )
    return create_deep_agent(model=model, backend=combined)
```

这个组合中，写 `/report.md` 会进入工作目录，写 `/archive/report.md` 会进入归档目录的 `report.md`。把归档子 backend 换成符合相同协议的云存储实现，就能沿用这套分流机制。

因此，这里后面出现的 `MountedCompositeBackend` 是基于上游组合类做补充，前缀路由本身沿用了上游能力。

### 6.5 那么已经能用，为什么还要封装？

如果只有一个示例 Agent，手动构造这些对象就够用了。要让同一套库反复创建不同工作区、连接不同存储，还会出现几件重复工作：

- 读取配置，决定实例化哪个 backend，再递归创建组合中的子 backend。
- 把 Agent 的工作目录、技能位置和系统文件路径安排到合适的存储地址。
- 补齐具体云服务的文件协议实现，让 SDK 结果符合 Agent 文件工具的要求。
- 确定默认值，并让宿主能通过统一配置创建 Agent。

这些就是本项目在上游能力外面增加的部分：

| deepagents 已经提供什么 | 运行层 在外面补什么 |
|---|---|
| `create_deep_agent()` 负责创建 Agent 图 | `AgentRuntime` 整理配置、模型、工具、中间件后调用它 |
| `BackendProtocol` 定义文件操作约定 | 远程适配类按这份约定连接 COS、S3、Postgres 等 |
| 原生文件和状态等后端 | 本地执行增强、额外后端和默认选择 |
| `CompositeBackend` 按前缀分流 | 工厂解析嵌套字典，`MountedCompositeBackend` 补默认后端的挂载信息 |
| 文件工具调用 backend | `BackendWorkspace` 统一 运行层 内部的工作区内容访问 |

这层封装仍然把实际 backend 交回 deepagents 使用，最终执行文件工具的链路没有另起一套。

另外，在本项目核验的 deepagents 0.7 接口里，应向原生 `backend=` 传已初始化的实例。第 7 节中的 `"filesystem"`、`{"type": "cos", ...}` 是 运行层 工厂接受的配置，先解析成对象后才传给上游。不要把字典配置或旧例子中的 backend 工厂函数直接当成当前原生接口的参数。

### 6.6 封装之后，调用方怎么变化？

前面直接使用上游时，是调用方自己创建 `FilesystemBackend` 和 Agent 图。使用 运行层 时，调用方可以把这部分交给配置和 manager：

```python
from pathlib import Path

from power_agent import AgentConfig


def register_report_agent(manager, providers, default_model: str, workspace_dir: Path):
    # manager 是宿主已经创建的 AgentManager。
    # providers 和 default_model 沿用宿主已有的模型配置。
    config = AgentConfig(
        name="report-agent",
        workspace_dir=workspace_dir.resolve(),
        providers=providers,
        default_model=default_model,
        backend={"type": "filesystem"},
    )
    return manager.create_agent(config)
```

manager 创建 `AgentRuntime`，后者把字典变成 backend 对象、建立工作区入口，再把对象传给 `create_deep_agent()`。正常聊天通过 manager 发起。这里先集中看文件接入，后面的第 7、8 节会把工厂和内部调用展开。

## 7. 开发者怎么接：先跑通本地，再换配置

下面开始看代码。只需要先记住两个入口：

- `resolve_backend()`：看配置，创建对应的 backend。
- `BackendWorkspace`：帮 运行层 内部处理工作区文件，把路径等细节集中起来。

### 7.1 最小的本地例子

这段不需要调用模型，可以直接运行：

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from power_agent.backends import BackendWorkspace, resolve_backend

with TemporaryDirectory(prefix="agent-backend-demo-") as directory:
    workspace_dir = Path(directory).resolve()
    backend = resolve_backend("filesystem", workspace_dir=workspace_dir)
    workspace = BackendWorkspace(backend, workspace_dir)

    workspace.write_text("report.md", "今天完成了 backend 文档。\n")
    print(workspace.read_text("report.md"))
```

这里的文件实际写进了临时目录。`workspace.write_text("report.md", ...)` 的意思就是“在这个工作区里保存 report.md”。

项目内部的初始化、技能文件、媒体内容等，都应该通过 `agent.workspace` 这样的入口处理。否则，内部代码如果自己用 `open()` 写磁盘，Agent 却在用 COS，就可能出现“程序写了一份，Agent 在另一个地方找”的问题。

`BackendWorkspace` 自己没有新建一套存储，它用的还是传进去的那个 backend。

### 7.2 接本地、COS 和 S3

先安装本例需要的 SDK：

```bash
pip install cos-python-sdk-v5 oss2 esdk-obs-python boto3
```

下面是连接配置示例。需要提前建好 bucket，并在环境变量中提供参数；不会自动创建云资源。

```python
import os

from power_agent.backends import resolve_backend

backend_spec = {
    "type": "composite",
    "default": {"type": "local_shell"},
    "routes": {
        "/assets/": {
            "type": "cos",
            "bucket": os.environ["COS_BUCKET"],
            "region": os.environ["COS_REGION"],
            "secret_id": os.environ["COS_SECRET_ID"],
            "secret_key": os.environ["COS_SECRET_KEY"],
            "prefix": "demo-assets",
        },
        "/archive/": {
            "type": "s3",
            "bucket": os.environ["S3_BUCKET"],
            "access_key_id": os.environ["S3_ACCESS_KEY_ID"],
            "secret_access_key": os.environ["S3_SECRET_ACCESS_KEY"],
            "region": os.environ["S3_REGION"],
            "prefix": "demo-archive",
        },
    },
}

backend = resolve_backend(
    backend_spec,
    workspace_dir=os.environ["AGENT_WORKSPACE"],  # 宿主上的绝对目录
)
```

这段会创建三个子后端，再把它们组合起来。默认本地配置没有指定 `root_dir`，因此这里会用传入的工作区作为本地根。

接入完整 Agent 时，把同一份 `backend_spec` 交给 `AgentConfig.backend` 即可。下面只展示配置位置，provider 和模型沿用你原来的设置：

```python
# 配置位置示意，不是独立运行的完整脚本。
config = AgentConfig(
    workspace_dir=workspace_dir,
    providers=providers,
    backend=backend_spec,
)
```

`AgentRuntime` 会自己调用工厂，再创建工作区入口。正常聊天仍然通过 `AgentManager` 发起，不需要在业务中手动重写文件工具。

工厂也接受已经创建好的 backend 实例。这样宿主可以接自定义实现，测试也可以传入假的存储，避免连接真实云服务。

### 7.3 COS 和 S3 都能存对象，为什么还要写两个 backend？

因为“能保存同一份文件”不代表“连接方法完全一样”。

当前 S3 backend 使用 boto3。COS、OSS、OBS 则分别使用厂商官方 SDK。它们的鉴权参数、分页方式和错误信息有差别，这些差别由各自的 backend 处理。

例如上面的 COS 用 `secret_id` / `secret_key`，S3 用 `access_key_id` / `secret_access_key`。所以“统一接口”不意味着配置字段也完全相同。

当前依赖声明中，COS、OSS、OBS 的聚合安装项是 `object-storage`，Postgres 用 `remote-backends`，S3 实现需要 boto3。相关 SDK 按需导入，没选那些 backend 时，不必装齐所有 SDK。

## 8. 再往代码里看：为什么不用给每家厂商重写一遍？

这一节按“约定方法 → 共用流程 → 连接厂商 → 创建对象 → 路由 → 接回 Agent”的顺序看。下面的源码节选帮助理解实现位置，不能每段单独复制运行；第 7 节才是完整接入示例。

### 8.1 第一步：约定每个 backend 要提供什么

先沿用上游的读写约定。`BackendProtocol` 来自 deepagents，运行层 没有再定义一套同名文件协议。下面只是把上游类的读写外形摘出来解释，省略其他方法和说明：

```python
from abc import ABC

from deepagents.backends.protocol import ReadResult, WriteResult


class BackendProtocol(ABC):
    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> ReadResult:
        raise NotImplementedError

    def write(self, file_path: str, content: str) -> WriteResult:
        raise NotImplementedError
```

这不是已经写好的存储功能，而是告诉实现者：读文件要返回 `ReadResult`，写文件要返回 `WriteResult`。其他代码便能按同一种方式检查 `result.error`。

名字叫 Protocol，但当前 deepagents 用的是抽象基类 `ABC` 来承载这份约定。这里只展示最小外形；真正的文件协议还有列目录、编辑、搜索和传输等方法。

### 8.2 第二步：把共用的“创建文件”流程写一次

项目把远程文件操作中相同的部分放进 `CloudStorageBackend`。它的 `write()` 逻辑如下，节选自 `src/power_agent/backends/cloud_storage_base.py:254`，缩短了重复文件的报错文字：

```python
# 这是 CloudStorageBackend 类里的方法。
def write(self, file_path: str, content: str) -> WriteResult:
    try:
        existing = self._get_file_data(file_path)
    except self._storage_error_types() as exc:
        return WriteResult(error=wrap_io_error("checking", file_path, exc), path=None)

    if existing is not None:
        return WriteResult(error=f"File already exists: {file_path}", path=None)

    try:
        self._put_file_data(file_path, create_file_data(content))
    except self._storage_error_types() as exc:
        return WriteResult(error=wrap_io_error("writing", file_path, exc), path=None)

    return WriteResult(error=None, path=file_path)
```

顺着读就是：先查有没有同名文件，有就拒绝；没有就包装内容、保存；最后返回成功或错误。

注意，它没有出现 COS、S3 或 SQL。具体怎么查、怎么存，分别交给 `_get_file_data()` 和 `_put_file_data()`。

这两个方法在公共基类中只作声明，要求子类实现：

```python
# CloudStorageBackend 中的接口节选。
from abc import abstractmethod

from deepagents.backends.protocol import FileData


@abstractmethod
def _get_file_data(self, path: str) -> FileData | None:
    """取回文件数据；没有这份文件时返回 None。"""


@abstractmethod
def _put_file_data(self, path: str, file_data: FileData) -> None:
    """把文件数据保存到具体存储。"""
```

所以新增一个同类存储时，不必把“检查同名文件、生成文件数据、返回统一结果”再抄一份。读取、编辑等共用流程也是类似的分工。

### 8.3 第三步：COS、S3、Postgres 各自实现真正的读写

COS 子类里，取文件、存文件的核心是 SDK 调用。下面简化自 `src/power_agent/backends/cos_backend.py:138`，省略了 404 和其他错误分支；正式实现会将对象不存在识别成 `None`。

```python
# 下面两个方法位于 CosBackend 类中。
def _get_file_data(self, path: str) -> FileData | None:
    response = self._client.get_object(
        Bucket=self._config.bucket,
        Key=self._key(path),
    )
    raw = response["Body"].get_raw_stream().read()
    return self._parse_body(raw)


def _put_file_data(self, path: str, file_data: FileData) -> None:
    self._client.put_object(
        Bucket=self._config.bucket,
        Key=self._key(path),
        Body=self._encode_file_data(file_data),
    )
```

这里的三个辅助方法各做一件事：`_key()` 计算云端对象名，`_encode_file_data()` 把文件数据转成 JSON 字节，`_parse_body()` 在读取时解析回来。

例如 `_key()` 的主要逻辑可以精简成：

```python
# 教学版，展示 prefix 和 backend 路径怎么拼成对象 key。
def object_key(prefix: str, path: str) -> str:
    prefix = prefix.strip("/")
    name = path.lstrip("/")
    if prefix:
        return f"{prefix}/{name}"
    return name


assert object_key("demo-assets", "/report.md") == "demo-assets/report.md"
```

真实代码还处理空路径等情况，位置是 `src/power_agent/backends/cloud_storage_base.py:122`。

S3 复用同一份公共 `write()`，其保存原语使用 boto3 client；当前 `_put_file_data()` 的调用外形和上面的 COS 保存方法相同，变化的是 client 的创建方式与兼容处理。

Postgres 也复用这套公共流程，但它实际保存的是数据库记录。下面节选自 `src/power_agent/backends/postgres.py:304`：

```python
# 位于 PostgresBackend 类中。
def _put_file_data(self, path: str, file_data: FileData) -> None:
    from psycopg.types.json import Jsonb

    key = self._key(path)
    with self._connect() as conn:
        conn.execute(
            f"""
            INSERT INTO {self._qualified} (path, content, created_at, modified_at)
            VALUES (%s, %s, NOW(), NOW())
            ON CONFLICT (path) DO UPDATE SET
                content = EXCLUDED.content,
                modified_at = NOW()
            """,
            (key, Jsonb(dict(file_data))),
        )
        conn.commit()
```

`path` 列保存名字，`content` 列保存文件数据。文件路径和内容作为参数传入 SQL；表名来自已经校验过的配置。

这里内部用的是 upsert，也就是“有则更新、无则插入”。它服务于创建、编辑等不同操作；对外的普通 `write()` 仍会先检查重复文件。这个先查再写并不等于数据库级的并发保护，两个客户端同时写仍需另行考虑。

### 8.4 第四步：用工厂把配置变成对象

现在有了几个实现，调用方还需要一个地方把 `{"type": "cos", ...}` 变成真正对象。这就是 `resolve_backend()`。

它的分派部分可以抽出下面这几行来理解，省略了类型校验、其他 backend 和额外参数：

```python
# resolve_backend() 内部逻辑的简化节选。
backend_type = spec["type"]
kwargs = {key: value for key, value in spec.items() if key != "type"}

if backend_type == "cos":
    return _build_cos(kwargs)
if backend_type == "s3":
    return _build_s3(kwargs)
if backend_type == "postgres":
    return _build_postgres(kwargs)
```

比如 S3 builder 再做配置转换和对象创建：

```python
# 简化自 backends/__init__.py 的 _build_s3()。
def _build_s3(kwargs):
    from power_agent.backends.s3_backend import S3Backend, S3Config

    config = S3Config.from_kwargs(**kwargs)
    return S3Backend(config)
```

这样，业务拿到的已经是可用的 backend 对象，不必关心它的配置类和构造细节。传入已构造实例时，工厂直接使用该实例。

### 8.5 第五步：多个 backend 先分别创建，再按路径分流

组合后端不是另一家云服务。它先创建默认后端和路由后端，再把这些对象放到一个组合对象里。

以下是 `_build_composite()` 的核心关系，省略了输入检查、系统目录和产物位置处理：

```python
# _build_composite() 内部的简化节选。
resolved_default = resolve_backend(
    default,
    workspace_dir=workspace_dir,
    _scope_host_artifacts=False,
)
resolved_routes = {
    prefix: resolve_backend(
        sub_spec,
        workspace_dir=workspace_dir,
        _scope_host_artifacts=False,
    )
    for prefix, sub_spec in routes.items()
}
return MountedCompositeBackend(
    default=resolved_default,
    routes=resolved_routes,
)
```

`_scope_host_artifacts=False` 是内部参数，目的是让子后端不要各自重复包装产物目录，组合层会统一安排。

真正收到文件路径时，deepagents 的组合类做前缀匹配。把它的选路逻辑单独写成一个教学函数，就比较容易看清：

```python
# 教学版：只展示选后端和剥离前缀，不包含列表汇总等完整功能。
def choose_backend(path, default, routes):
    # 更长的前缀排在前面，避免 /assets/ 抢先匹配 /assets/private/。
    ordered = sorted(routes.items(), key=lambda item: len(item[0]), reverse=True)

    for prefix, backend in ordered:
        root = prefix.rstrip("/")
        if path == root:
            return backend, "/"

        prefix = root + "/"
        if path.startswith(prefix):
            child_path = "/" + path[len(prefix):]
            return backend, child_path

    return default, path
```

选好之后，把同一个操作交给选中的后端：

```python
# 接着上面的教学函数，default 和 routes 是已经创建的 backend 对象。
selected, child_path = choose_backend("/assets/report.md", default, routes)
result = selected.write(child_path, "今天的日报")
```

假设 `/assets/` 对应 COS，这一步实际就是调用 COS 的 `write("/report.md", ...)`。它继承的公共 `write()` 又会调用 COS 子类的 `_get_file_data()` / `_put_file_data()`，整条调用链就接起来了。

![原文图示 4](/blogs/power-agent-storage-backend/routed-write.png)

[查看大图](/blogs/power-agent-storage-backend/routed-write.svg) · [下载 Mermaid 源文件](/blogs/power-agent-storage-backend/routed-write.mmd)

这个图展示成功创建文件的路径。报错时会沿结果返回；不会再选择本地后端重试保存。

### 8.6 第六步：给 运行层 内部接上工作区入口

Agent 组装时会先得到 backend，再把同一个对象交给 `BackendWorkspace`。下面精简自 `src/power_agent/agent.py:194` 和 `_build_backend()`：

```python
# AgentRuntime 内部的组装关系，省略其他初始化步骤。
self._backend = resolve_backend(
    self._config.backend,
    workspace_dir=self._workspace_path,
    system_files_path=self._config.system_files_path,
)
self._workspace = BackendWorkspace(
    self._backend,
    self._workspace_path,
    system_files_path=self._config.system_files_path,
)
```

创建 Agent 图时，运行层 再把这个 backend 交回上游。精简自 `src/power_agent/agent.py:1766` 的 `_build_graph()`，省略提示词、会话持久化和其他参数：

```python
# AgentRuntime._build_graph() 的组装关系节选。
kwargs = {
    "model": self._build_seed_model(),
    "tools": tools,
    "middleware": middleware,
    "backend": self._backend,
}
graph = deepagents.create_deep_agent(**kwargs)
```

这里的 `backend` 就是上一段创建的同一个对象。上游继续负责 `FilesystemMiddleware → 文件工具 → backend` 的调用链，运行层 的初始化模板、技能和媒体等内部逻辑则使用 workspace。后者先算工作区路径，再调用 backend。

比如 `write_text()` 中可以走 backend 的分支，核心是下面这些步骤，简化自 `src/power_agent/backends/workspace.py:748`：

```python
# 只展示 write_text() 中已经得到 backend key 的分支。
# 完整源码还处理不映射到 backend 挂载的本地工作区路径。
key = self._backend_storage_key(path)
if key is not None:
    if force:
        backend_write_force(self._backend, key, content)
    else:
        result = self._backend.write(key, content)
        if result.error is not None:
            raise OSError(result.error)
```

这也是为什么扩展 backend 时，上层可以继续写 `workspace.write_text("report.md", text)`，不用在每个业务里重新计算 COS key 或宿主路径。

### 8.7 设计模式的名字，现在再对上就容易了

| 代码做的事 | 通常叫什么 | 在这里解决什么问题 |
|---|---|---|
| 看 `type`，创建对应 backend | 简单工厂 | 让调用者不用自己判断该构造哪个类 |
| 上层方法不变，底层可选本地或云端 | 策略模式 | 更换文件存储方式时，少改业务代码 |
| 把 COS SDK、boto3、SQL 转成同一套文件方法 | 适配器模式 | 把不同服务的接口和结果翻译成统一约定 |
| 公共基类写流程，子类提供具体取数、存数操作 | 模板方法模式 | 共用读写逻辑，减少各后端行为不一致 |
| 多个 backend 由一个入口按路径分配 | 组合与路由 | 同一个 Agent 可以使用多个存储 |
| 内部工作区访问集中到 `BackendWorkspace` | 门面模式 | 集中处理路径、系统文件位置和读写细节 |
| 允许直接传入 backend 实例 | 依赖注入 | 宿主可扩展，测试可替换 |

这些名称是对当前结构的解释。实际阅读时，先看“这段代码替我省掉了什么重复工作”，比先记模式名字更有用。

## 9. 开发时最容易混淆的几个地方

### 9.1 `workspace_dir` 和 `root_dir` 是什么关系？

先用两个问题区分：

- `workspace_dir`：Agent 平时应该在哪个目录干活？
- `root_dir`：本地 backend 看到的虚拟 `/`，对应电脑上的哪个目录？

如果两者都设成 `/srv/demo`，事情就简单：工作区里的 `report.md`、backend 里的 `/report.md`，都能对应到 `/srv/demo/report.md`。

如果根是 `/srv`，工作区是 `/srv/demo`，就有区别了：

```text
workspace.write_text("report.md", ...)
    → /srv/demo/report.md

backend.write("/report.md", ...)
    → /srv/report.md
```

因此，不要看见路径前面有 `/`，就认为它一定是“工作区里的文件”。

云端则主要使用 bucket、`prefix` 或数据库表来定位文件，不靠本地的 `root_dir` 建立存储映射。`prefix` 可以先理解成云端存储名字前面统一加的一段目录。

### 9.2 直接写 backend，和通过工作区写，云端位置可能不同

假设纯 COS 后端配置了 `prefix="tenant-a"`，宿主工作区目录末级叫 `demo`：

```text
workspace.write_text("report.md", ...)
    → 云端 key：tenant-a/.agent/workspaces/demo/report.md

backend.write("/report.md", ...)
    → 云端 key：tenant-a/report.md
```

工作区入口会给相对路径加上远程工作区目录，直接调用 backend 不会自动加。

这样做是为了把不同工作区的文件分开。如果工作区已经使用 `/.agent/...` 形式，会保留该虚拟路径；普通宿主路径则按末级目录名生成远程工作区目录。

这也意味着，同一个存储前缀下，如果两个宿主工作区的末级名字都叫 `demo`，仍可能撞到一起。宿主需要分配不同工作区名字或存储前缀。

这个例子说的是纯远程工作区。第 4 节 composite 中显式访问 `/assets/...` 的规则，是先去掉路由前缀，再交给子 backend，不能把两种路径处理混在一起。

### 9.3 云端“文件”可能带着一层包装

这些远程 backend 正常写入时，会把内容和编码、时间等信息一起保存，结构类似：

```json
{
  "content": "今天完成了日报。",
  "encoding": "utf-8",
  "created_at": "2026-11-16T00:00:00+00:00",
  "modified_at": "2026-11-16T00:00:00+00:00"
}
```

对象存储保存这份 JSON，Postgres 保存相应的 JSONB 数据。二进制文件会使用 Base64 包装，下载接口再还原为原来的字节。

所以，不要默认把 bucket 中的对象链接直接当作原始 PDF 或图片链接发出去。通过下载接口取回内容，或通过文件交付能力处理，才符合这套存储格式。

公共读取逻辑也兼容部分已有原始文本和二进制对象，并非只能读取自己的 JSON 包装。

### 9.4 文件路由不会把云存储挂进 Shell

下面两种操作看起来都在读同一个路径，实际走法不同：

```text
read_file("/assets/a.txt")
    → 文件工具按路由去 COS 读

execute("cat /assets/a.txt")
    → 在默认 backend 的 Shell 里运行命令
```

Shell 不会查询 composite 的路由表，所以不会自动到 COS 下载这个文件。要交给本地程序处理，应先明确下载文件。

组合 backend 的 `execute` 始终交给 `default`。只在某条路由中放一个 Shell backend，不能让整个组合自动具备执行能力。

同样，当前也没有通用的“一次 move 就把 COS 文件迁去 S3”的功能。跨存储搬文件，需要安排下载、上传、核对结果和删除源文件。

### 9.5 文件写入和命令隔离，也有几个细节

这里的远程公共 `write()` 是创建文件，同名文件已存在时返回错误；本地 backend 的行为要看所用的 deepagents 实现，本次核验的 0.7.21 文件系统后端会覆盖。运行层 明确需要覆盖时，可使用 `workspace.write_text(..., force=True)`，其辅助逻辑必要时会先读原文再编辑。它没有因此获得统一的并发锁或事务保证。

云端目录移动可能要逐个复制、删除，搜索可能要取回文件内容再匹配。接口相同，不代表成本和原子性相同。

另外，`local_shell` 设置了一个较小的文件根，不总等于 Shell 已被关进这个目录。只有满足 Linux、非宿主根、虚拟模式且可用 bwrap 等条件时，才会选用相应目录 jail；否则仍是在宿主上执行并做路径转换。

## 10. 把传统系统的写法和这里的 backend 放在一起看

把前面的代码连起来，可以看到四种做法：业务直接接存储、业务使用通用 Storage、直接接 deepagents，以及使用 运行层 封装。它们都能解决问题，处理重复工作的层次不同。

| 你遇到的问题 | 业务直接接磁盘 / SDK | 通用 Storage | 直接用 deepagents | 使用这里的 运行层 |
|---|---|---|---|---|
| 保存一份报表 | 业务选磁盘或 SDK 方法 | 调用 `storage.save` 等方法 | 文件工具调用 backend | 沿用上游文件工具和 backend |
| 再接一种云存储 | 增加 SDK 调用 | 增加 Storage 实现 | 提供符合文件协议的 backend | 提供适配实现；同类远程逻辑复用公共基类 |
| 文件按路径去不同存储 | 业务判断 | 取决于框架 | 手动构造 `CompositeBackend` | 字典描述路由，工厂递归创建组合 |
| 让模型编辑和搜索文件 | 另接 Agent 工具 | 取决于现有功能 | 上游已经提供文件工具 | 继续使用这些工具，增加路径等配套处理 |
| 创建不同工作区的 Agent | 业务安排 | 看宿主怎么组织 | 宿主组织模型、后端和图创建 | 配置、manager 与 `AgentRuntime` 组织创建 |
| 运行层 自己读取技能等内容 | 业务安排 | 看路径约定 | 宿主自行处理 | 通过 `BackendWorkspace` 集中处理 |

### 10.1 什么时候直接调用 SDK 也够用？

如果一个服务只往固定 bucket 上传附件，再把地址交给调用方，直接调用 SDK 就可能足够清楚。已经使用 Django Storage 或其他文件抽象的应用，也可以继续沿用现有方案。

这里面对的是另一组需求：Agent 会自己决定下一步要读、写、编辑、列目录还是搜索；同一套工具还可能在本地、云端和沙箱中工作。因此，把这些动作组织成统一 backend，能让工具层和存储实现分开变化。

### 10.2 对开发者来说，代码主要从哪搬到了哪？

用第 5、6、8 节的例子对照：

```text
直接接 SDK 时：
    报表业务 → 判断 local / s3 / cos → 调对应存储

直接接 deepagents 时：
    宿主创建 backend → create_deep_agent(backend=对象)
    Agent → 上游文件工具 → backend → 存储

使用 运行层 后：
    配置 → manager / AgentRuntime → 工厂创建 backend
    AgentRuntime → create_deep_agent(backend=对象)
    Agent → 上游文件工具 → backend → 存储
    运行层 内部内容 → BackendWorkspace → backend

多个存储的文件调用：
    文件工具 → composite 选路 → 子 backend → 存储
```

SDK 调用被放进了各自的 backend。选择实现的判断主要集中在创建阶段的工厂和调用阶段的路由中。`create_deep_agent()` 仍然处在封装后的链路里，它负责的图和文件工具能力继续由上游提供。

收益是：报表业务不用随着存储种类增加而反复加判断；接新存储时，可以集中修改适配部分。代价是要维护文件协议、配置转换、路径规则和各后端一致性，代码总量未必比只接一种存储更少。

### 10.3 也有一些事，统一 backend 之后仍然要自己安排

自动备份、跨云同步、失败改写到备用存储、跨存储事务，以及把聊天记忆和日志一起迁走，都不能只靠配置一个 composite 获得。

换现有系统的存储时，也要区分“以后读写走哪里”和“原来的文件有没有搬过去”。改配置只解决前一个问题，历史文件迁移需要另行处理。
