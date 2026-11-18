假设你对巡检助手说「帮我核对这份巡检表，把超过演示阈值的设备列出来」。主 Agent 可以把任务交给一个单独运行的程序。这个程序读取表格、算出结果，再把结果回给主 Agent，由主 Agent 整理成你能直接看的回复。ACP（Agent Client Protocol）约定了这两个程序怎么开会话、发任务、回进度和询问权限。

同一套协议也可以反着用。比如你从 Zed 编辑器发消息，由编辑器做 ACP 客户端，运行 Agent 的进程接单。要读懂代码，先问一句 **这次是谁在发任务，谁在接任务？**

| 场景 | ACP 客户端，负责发任务 | ACP Agent，负责接任务 |
| --- | --- | --- |
| 巡检助手把核表工作交给外部程序 | 主 Agent 的运行程序 | 巡检程序，或配置好的外部 Agent |
| 在 Zed 里使用我的 Agent | Zed | 包了一层 ACP 接口的 Agent |

示例用的是虚构设备、离线 CSV 和教学筛选规则。演示使用 Python 3.12、Deep Agents 0.7.21 和 ACP Python SDK 0.10.1。

## 1. 先看一张巡检表

在一个单独的演示目录里新建 UTF-8 文件 `readings.csv`。后面的 Python 示例文件也放在这个目录。

```csv
device,current_a,temp_c
馈线 F-07,442,67
箱变 T-03,318,81
馈线 F-12,389,62
```

这次只做两条演示筛选。电流 **严格大于 420 A**，或者温度 **严格大于 75 °C**，就把该行列入复核清单。于是 3 条记录里有 2 条命中。

| 设备 | 记录值 | 命中的演示规则 |
| --- | --- | --- |
| 馈线 F-07 | 442 A，67 °C | 442 A 大于 420 A |
| 箱变 T-03 | 318 A，81 °C | 81 °C 大于 75 °C |
| 馈线 F-12 | 389 A，62 °C | 两项均在演示阈值内 |

例子里，外部程序启动时会拿到一个工作目录（`cwd`），随后从该目录打开 `readings.csv`。任务正文只带文件名和筛选要求。外部程序自己读取 CSV 的内容。要把同一种接法用在另一个进程上，那个进程也要能访问该目录和文件。

## 2. 一次调用是怎么过去的

我的项目用的是 ACP 的 **stdio** 接法。Python 程序启动外部子进程，往它的标准输入写消息，同时读它的标准输出。两边通过这一对管道交换按行分隔的 JSON-RPC 消息。可以把 JSON-RPC 理解成带编号的请求单，`method` 写要办理的事项，`params` 是参数，回复用同一个 `id` 对应原请求。进度通知没有请求编号。外部程序的调试日志应写入标准错误，给标准输出留出专门的协议通道。参见 [ACP v1 传输规范](https://agentclientprotocol.com/protocol/v1/transports)。

![一次巡检委派的 ACP 时序图](/blogs/power-agent-acp/acp-turn.svg)

握手只需要在打开连接时做。新会话建好之后，下一条追问可以用同一个 `sessionId` 再发一次 `session/prompt`。下面是一轮里的三条消息，每行是一个 JSON 对象。前一条由客户端发出，后两条由外部程序发出。给客户端显示的正文在 `session/update` 里，最后的响应只报告本轮为何结束。参见 [ACP v1 会话设置](https://agentclientprotocol.com/protocol/v1/session-setup)与 [ACP v1 任务轮次](https://agentclientprotocol.com/protocol/v1/prompt-turn)。

```jsonl
{"jsonrpc":"2.0","id":3,"method":"session/prompt","params":{"sessionId":"inspection-001","prompt":[{"type":"text","text":"核对 readings.csv，列出超过演示阈值的设备"}]}}
{"jsonrpc":"2.0","method":"session/update","params":{"sessionId":"inspection-001","update":{"sessionUpdate":"agent_message_chunk","content":{"type":"text","text":"读到 3 条，2 条需要复核。"}}}}
{"jsonrpc":"2.0","id":3,"result":{"stopReason":"end_turn"}}
```

### 把握手和建会话也放进报文里

前面的三行是任务阶段。再往前看，客户端会先问协议版本和能力，再问外部进程要一个会话编号。以下是同一条调用链的前四行，目录和 ID 都是演示值。参见 [ACP v1 初始化](https://agentclientprotocol.com/protocol/v1/initialization)和 [ACP v1 会话设置](https://agentclientprotocol.com/protocol/v1/session-setup)。

```jsonl
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":1,"clientCapabilities":{},"clientInfo":{"name":"inspection-client","version":"1.0.0"}}}
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":1,"agentCapabilities":{"loadSession":false},"authMethods":[]}}
{"jsonrpc":"2.0","id":2,"method":"session/new","params":{"cwd":"/demo/inspection","mcpServers":[]}}
{"jsonrpc":"2.0","id":2,"result":{"sessionId":"inspection-001"}}
```

第一组的 `id=1` 只管这次握手，第二组的 `id=2` 只管这次建会话。它们收到回复以后就完成了。`inspection-001` 的寿命更长，后续几次 `session/prompt` 都用它。第 4 节代码里的 `conn.initialize()`、`conn.new_session()` 和 `conn.prompt()` 正是对这些请求的 Python 封装。ACP SDK 会处理消息编码、管道读写和请求匹配，业务代码只需要传参数和接回调。


## 3. 先做一个可运行的外部巡检程序

把下段保存为 `inspection_runner.py`。它用 ACP Python SDK 接请求，用普通 Python 算结果，因此外部这一侧可以在没有模型密钥的情况下运行。这里实现一个固定的核表任务，每次收到消息都会重新计算。它刻意保持简单，以便看清协议本身。真实外部 Agent 可以理解不同的追问、使用自己的工具，并在同一个会话里维护上下文。参见 [ACP Python SDK](https://agentclientprotocol.com/libraries/python)。

```python
# inspection_runner.py
import asyncio
import csv
from pathlib import Path
from uuid import uuid4

from acp import PROTOCOL_VERSION, run_agent, update_agent_message_text
from acp.schema import InitializeResponse, NewSessionResponse, PromptResponse


def summarize_readings(path: Path) -> str:
    with path.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    findings = []
    for row in rows:
        current = float(row["current_a"])
        temperature = float(row["temp_c"])
        reasons = []
        if current > 420:
            reasons.append(f"{current:g} A > 420 A")
        if temperature > 75:
            reasons.append(f"{temperature:g} °C > 75 °C")
        if reasons:
            findings.append(f"- {row['device']}（{'、'.join(reasons)}）")

    summary = f"读到 {len(rows)} 条，{len(findings)} 条需要复核。"
    return "\n".join([summary, *findings])


class InspectionRunner:
    def __init__(self):
        self.workdirs = {}

    def on_connect(self, conn):
        self.conn = conn

    async def initialize(self, protocol_version, **kwargs):
        return InitializeResponse(protocol_version=PROTOCOL_VERSION)

    async def new_session(self, cwd, **kwargs):
        session_id = uuid4().hex
        self.workdirs[session_id] = Path(cwd)
        return NewSessionResponse(session_id=session_id)

    async def prompt(self, prompt, session_id, **kwargs):
        summary = summarize_readings(self.workdirs[session_id] / "readings.csv")
        first_line, separator, details = summary.partition("\n")
        for text in (first_line, separator + details):
            if text:
                await self.conn.session_update(
                    session_id=session_id, update=update_agent_message_text(text)
                )
        return PromptResponse(stop_reason="end_turn")

    async def cancel(self, session_id, **kwargs):
        # 这个演示任务是一次很短的同步读表，没留可取消的后台任务。
        pass


if __name__ == "__main__":
    asyncio.run(run_agent(InspectionRunner()))
```

这个脚本由 ACP 客户端启动。手动执行后，它会在标准输入等客户端发消息。下文的客户端会启动它，并最终读到以下文本。

```text
读到 3 条，2 条需要复核。
- 馈线 F-07（442 A > 420 A）
- 箱变 T-03（81 °C > 75 °C）
```

## 4. 直接用 Deep Agents，怎么把任务发出去？

Deep Agents 本身会组织模型和工具的调用。要把任务交给上面的外部程序，可以自己写一个异步工具，工具里面用 ACP SDK 启动子进程、握手、开会话、发送任务。然后用 `create_deep_agent(tools=[...])` 把工具注册给主模型。这是出站调用。上游另有 `deepagents-acp`，它解决的是编辑器接入 Agent 的入站场景，第 7 节会用到。参见 [Deep Agents 工具文档](https://docs.langchain.com/oss/python/deepagents/tools)与 [Deep Agents ACP 文档](https://docs.langchain.com/oss/python/deepagents/acp)。

安装本节示例用到的依赖，保存代码为 `native_delegate.py`。若只想检查 ACP 连接，运行 `python native_delegate.py --check-acp`，该分支直接调用工具，不需要模型密钥。运行 `python native_delegate.py` 则走主模型的工具选择，先设置 `OPENAI_API_KEY` 和 `OPENAI_MODEL`，模型要支持工具调用。

```bash
python -m pip install "deepagents==0.7.21" "agent-client-protocol==0.10.1" langchain-openai
```

```python
# native_delegate.py
import asyncio
import os
import sys
from pathlib import Path

from acp import PROTOCOL_VERSION, spawn_agent_process, text_block
from acp.connection import StreamDirection
from acp.schema import AgentMessageChunk, DeniedOutcome, RequestPermissionResponse
from deepagents import create_deep_agent
from langchain_core.tools import tool

WORKSPACE = Path(__file__).resolve().parent
TASK = "核对 readings.csv，列出超过 420 A 或 75 °C 的设备和对应的记录值。"


class InspectionClient:
    def __init__(self):
        self.parts = []

    def on_connect(self, conn):
        pass

    def observe(self, event):
        message = event.message
        if event.direction != StreamDirection.INCOMING or message.get("method") != "session/update":
            return
        payload = message["params"]["update"]
        if payload.get("sessionUpdate") == "agent_message_chunk":
            update = AgentMessageChunk.model_validate(payload)
            if update.content.type == "text":
                self.parts.append(update.content.text)

    async def session_update(self, session_id, update, **kwargs):
        pass  # 正文由 observe 按收到报文的顺序记录。

    async def request_permission(self, options, session_id, tool_call, **kwargs):
        # 这个只读演示没有审批界面，统一取消外部权限请求。
        return RequestPermissionResponse(outcome=DeniedOutcome(outcome="cancelled"))


@tool
async def delegate_inspection(task: str) -> str:
    """让外部巡检程序读取演示数据并返回复核结果。"""
    client = InspectionClient()
    runner = WORKSPACE / "inspection_runner.py"
    async with asyncio.timeout(30):
        async with spawn_agent_process(
            client, sys.executable, str(runner), cwd=str(WORKSPACE), observers=[client.observe]
        ) as (conn, _process):
            init = await conn.initialize(protocol_version=PROTOCOL_VERSION)
            if init.protocol_version != PROTOCOL_VERSION:
                raise RuntimeError(f"ACP 版本不兼容：{init.protocol_version}")
            session = await conn.new_session(cwd=str(WORKSPACE))
            result = await conn.prompt(
                session_id=session.session_id, prompt=[text_block(task)]
            )
            if result.stop_reason != "end_turn":
                raise RuntimeError(f"巡检提前停止：{result.stop_reason}")
    return "".join(client.parts)


async def main():
    if "--check-acp" in sys.argv:
        print(await delegate_inspection.ainvoke({"task": TASK}))
        return

    agent = create_deep_agent(
        model=f"openai:{os.environ['OPENAI_MODEL']}",
        tools=[delegate_inspection],
        system_prompt="核对巡检表时使用 delegate_inspection 工具，并根据工具结果回答。",
    )
    result = await agent.ainvoke({"messages": [{"role": "user", "content": TASK}]})
    print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
```

这段代码每次调用工具都会启动一个新进程；离开 `async with` 就释放连接和进程。如果业务需要跟同一个外部 Agent 继续交流，客户端还要保存连接、子进程和 `session_id`，等追问时再用。Deep Agents 自带的 `subagents=[...]` 适合把任务交给其运行时里的子 Agent，常见入口是内置的 `task` 工具。连接一个会说 ACP 的独立进程，则用上面这样的客户端工具。参见 [Deep Agents 子 Agent 文档](https://docs.langchain.com/oss/python/deepagents/subagents)。

巡检结果来自 `session/update`。这个版本的 Python SDK 会把通知回调放进异步队列，结束回复可能先唤醒 `await conn.prompt(...)` 的调用方。演示把同步的 `observe()` 传给 `spawn_agent_process`，在收到每条报文时直接收集正文，再用结束回复划分轮次。这样第二轮清空缓冲时，第一轮的正文已经收齐。权限请求仍由异步 `request_permission()` 回答。参见 [ACP Python SDK](https://agentclientprotocol.com/libraries/python)。

### 原生 SDK 怎么接着问第二句

把下面保存为 `native_two_turns.py`，然后执行 `python native_two_turns.py`。它使用上文的 `InspectionClient`，直接展示客户端应该把哪些对象保留到第二轮。

```python
# native_two_turns.py
import asyncio
import sys

from acp import PROTOCOL_VERSION, spawn_agent_process, text_block

from native_delegate import InspectionClient, WORKSPACE


async def main():
    client = InspectionClient()
    runner_script = WORKSPACE / "inspection_runner.py"
    async with asyncio.timeout(30):
        async with spawn_agent_process(
            client, sys.executable, str(runner_script), cwd=str(WORKSPACE),
            observers=[client.observe],
        ) as (conn, process):
            handshake = await conn.initialize(protocol_version=PROTOCOL_VERSION)
            if handshake.protocol_version != PROTOCOL_VERSION:
                raise RuntimeError("ACP 协议版本不一致")
            session = await conn.new_session(cwd=str(WORKSPACE))

            for task in ("核对 readings.csv", "再核对一次设备名称"):
                client.parts.clear()
                response = await conn.prompt(
                    session_id=session.session_id, prompt=[text_block(task)]
                )
                print("进程", process.pid, "ACP 会话", session.session_id)
                print("结束原因", response.stop_reason)
                print("".join(client.parts))


if __name__ == "__main__":
    asyncio.run(main())
```

`conn` 是连到外部进程的通道，`session.session_id` 是通道另一端分配的会话编号。循环里发了两次 `prompt`，两次打印的进程 ID 和会话 ID 都会一致。`client.parts.clear()` 清的是客户端本轮要显示的文本，外部会话仍然存活。这个巡检程序会重新读表，所以两轮得到同一份摘要。真正支持上下文的外部 Agent 可以使用已有会话理解“刚才那两台”之类的追问。

## 5. 我的项目怎么把这套接法封装起来

我把它拆成三层。主模型看到的是一个叫 `acp_runner` 的工具，传进去的是动作、已配置的 runner 名称和任务正文。会话服务知道实际要启动哪个程序、当前进程是否还活着。ACP 客户端负责接收这个进程传回来的正文和权限请求。

| 一层 | 拿到什么 | 交出去什么 |
| --- | --- | --- |
| 主模型与工具 | 用户说“查一下这份巡检表” | `acp_runner(action="start", runner="inspection", message="核对 readings.csv")` |
| 会话服务 | 聊天编号、runner 名称、任务文本 | 一个实际的 ACP `session/prompt` 请求 |
| ACP 客户端 | `session/update` 或 `session/request_permission` | 工具结果，或一组需要用户选择的权限选项 |

这几个编号各有用处：

| 字段 | 例子 | 用在哪里 |
| --- | --- | --- |
| 聊天线程 `thread_id` | `inspection-demo` | 主 Agent 当前处理的对话，由应用放进 LangGraph 配置 |
| runner 名称 | `inspection` | 找到应用配置的启动命令，再与 `thread_id` 一起查会话 |
| 工具调用 `id` | `call-start` | 模型用它把本次 `ToolMessage` 和发出的工具调用对应起来 |
| ACP 会话 `session_id` | 例如 `a8ec4d…` | 外部进程分配；客户端用它向同一外部会话发下一条任务 |

### 5.1 把进程、连接和会话放在一起

第 4 节用 `async with spawn_agent_process(...)` 管住一次任务的连接。如果退出这个代码块，资源也随之释放。为了让第二次工具调用可以继续用那条连接，我在项目里把上下文交给 `AsyncExitStack` 管理，连同进程、ACP 会话 ID 和正在等待的任务一起保存。对应的会话记录以 `(thread_id, runner)` 为键。切换对话时，即便 runner 名称一样，也取到另一条记录。

下面是沿着这个设计整理的独立教学版。保存为 `delegation.py`，它使用第 4 节的依赖。代码按演示脚本的顺序处理同一会话的操作。实际项目还有运行超时、状态查看和环境配置等处理。

```python
# delegation.py
import asyncio
from contextlib import AsyncExitStack, suppress
from dataclasses import dataclass

from acp import PROTOCOL_VERSION, spawn_agent_process, text_block
from acp.client.connection import ClientSideConnection
from acp.schema import AllowedOutcome, RequestPermissionResponse
from langchain_core.tools import tool
from langgraph.config import get_config


from native_delegate import InspectionClient


class CallbackClient(InspectionClient):
    def __init__(self):
        super().__init__()
        self.options = []
        self.permission_ready = asyncio.Event()
        self.decision = None

    async def request_permission(self, options, session_id, tool_call, **kwargs):
        self.options = options
        self.decision = asyncio.get_running_loop().create_future()
        self.permission_ready.set()
        try:
            return await self.decision
        finally:
            self.options = []
            self.decision = None
            self.permission_ready.clear()


@dataclass
class LiveSession:
    stack: AsyncExitStack
    client: CallbackClient
    conn: ClientSideConnection
    process: asyncio.subprocess.Process
    session_id: str
    prompt_task: asyncio.Task | None = None


class DelegationService:
    def __init__(self, workspace, runners):
        self.workspace = workspace
        self.runners = runners
        self.sessions = {}

    async def start(self, key, message):
        _, runner = key
        if key in self.sessions:
            raise ValueError("会话已打开，请用 message 继续")

        command, *args = self.runners[runner]
        client = CallbackClient()
        stack = AsyncExitStack()
        try:
            conn, process = await stack.enter_async_context(
                spawn_agent_process(
                    client, command, *args, cwd=str(self.workspace),
                    observers=[client.observe],
                )
            )
            handshake = await conn.initialize(protocol_version=PROTOCOL_VERSION)
            if handshake.protocol_version != PROTOCOL_VERSION:
                raise RuntimeError("ACP 协议版本不一致")
            session = await conn.new_session(cwd=str(self.workspace))
        except BaseException:
            await stack.aclose()
            raise

        self.sessions[key] = LiveSession(stack, client, conn, process, session.session_id)
        return await self.message(key, message)

    async def message(self, key, message):
        session = self.sessions[key]
        if session.prompt_task is not None:
            raise ValueError("上一轮任务还在运行，请先处理权限请求")
        session.client.parts.clear()
        session.prompt_task = asyncio.create_task(
            session.conn.prompt(session_id=session.session_id, prompt=[text_block(message)])
        )
        return await self._wait_for_result(session)

    async def _wait_for_result(self, session):
        prompt = session.prompt_task
        permission = asyncio.create_task(session.client.permission_ready.wait())
        try:
            await asyncio.wait({prompt, permission}, return_when=asyncio.FIRST_COMPLETED)
            if prompt.done():
                response = await prompt
                if response.stop_reason != "end_turn":
                    raise RuntimeError(f"外部任务提前结束：{response.stop_reason}")
                return "".join(session.client.parts)

            choices = [f"- {item.name}（{item.option_id}）" for item in session.client.options]
            return "\n".join(["[permission_required]", *choices])
        finally:
            permission.cancel()
            with suppress(asyncio.CancelledError):
                await permission
            if prompt.done():
                session.prompt_task = None

    async def respond(self, key, option_id):
        session = self.sessions[key]
        client = session.client
        if client.decision is None or option_id not in {item.option_id for item in client.options}:
            raise ValueError("请传入当前权限请求里的选项 ID")
        client.permission_ready.clear()
        client.decision.set_result(
            RequestPermissionResponse(
                outcome=AllowedOutcome(outcome="selected", option_id=option_id)
            )
        )
        return await self._wait_for_result(session)

    async def close(self, key):
        session = self.sessions.pop(key, None)
        if session is None:
            return "没有打开的会话。"
        try:
            if session.prompt_task is not None:
                session.prompt_task.cancel()
                with suppress(asyncio.CancelledError):
                    await session.prompt_task
        finally:
            await session.stack.aclose()
        return "会话已关闭。"


def build_acp_tool(service):
    @tool
    async def acp_runner(action: str, runner: str, message: str = "") -> str:
        """委派给已配置的 ACP 程序。动作是 start、message、respond 或 close。"""
        thread_id = get_config()["configurable"]["thread_id"]
        key = (thread_id, runner)
        if action == "start":
            return await service.start(key, message)
        if action == "message":
            return await service.message(key, message)
        if action == "respond":
            return await service.respond(key, message)
        if action == "close":
            return await service.close(key)
        raise ValueError(f"未知动作：{action}")

    return acp_runner
```

这段代码可以顺着四个方法读。第一次 `start()` 打开子进程的输入输出，握手，拿到外部会话 ID。后续 `message()` 直接拿旧连接发送 `prompt`，每次只清空本轮要返回的文本。`respond()` 处理已经在等待的权限请求，下一节会用实际代码验证。`close()` 最后释放子进程和连接。

我的项目把工具放进 `create_deep_agent` 的工具列表，和原生 Deep Agents 的注册方式一样。区别集中在工具内部。它向会话服务要连接，具体的启动配置、会话生命周期和权限往返都由服务处理。以下是装配片段，`service` 用下面的演示脚本所示方式创建。

```python
agent = create_deep_agent(
    model=model,
    tools=[build_acp_tool(service)],
    system_prompt="核对巡检表时用 acp_runner。权限请求由用户决定。",
)
result = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "用巡检程序核对 readings.csv"}]},
    config={"configurable": {"thread_id": "inspection-demo"}},
)
```

### 5.2 在本地跑一遍工具调用

下面用 LangGraph 的 `ToolNode` 执行手工构造的工具调用，终端会显示实际返回的 `ToolMessage`。保存为 `delegation_demo.py` 后执行 `python delegation_demo.py`，即可离线跑通。真实对话由模型生成这条 `AIMessage`。这里把模型要填的几个字段写在脚本里，方便看清每一步。参见 [LangChain 工具执行文档](https://docs.langchain.com/oss/python/langchain/tools#tool-execution)。

```python
# delegation_demo.py
import argparse
import asyncio
import sys
from pathlib import Path

from langchain_core.messages import AIMessage
from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from delegation import DelegationService, build_acp_tool

WORKSPACE = Path(__file__).resolve().parent
RUNNER = "inspection"
THREAD_ID = "inspection-demo"


async def main(choice):
    runner_script = "permission_runner.py" if choice else "inspection_runner.py"
    service = DelegationService(WORKSPACE, {
        RUNNER: (sys.executable, str(WORKSPACE / runner_script)),
    })
    key = (THREAD_ID, RUNNER)

    graph = StateGraph(MessagesState)
    graph.add_node("tools", ToolNode([build_acp_tool(service)]))
    graph.add_edge(START, "tools")
    graph.add_edge("tools", END)
    app = graph.compile()

    async def call(action, message=""):
        call_id = f"call-{action}"
        ai_message = AIMessage(
            content="",
            tool_calls=[{
                "id": call_id,
                "name": "acp_runner",
                "args": {"action": action, "runner": RUNNER, "message": message},
            }],
        )
        state = await app.ainvoke(
            {"messages": [ai_message]},
            config={"configurable": {"thread_id": THREAD_ID}},
        )
        result = state["messages"][-1]
        assert result.tool_call_id == call_id
        print(result.tool_call_id, result.content, sep="\n")
        return result.content

    try:
        started = await call("start", "生成巡检简报" if choice else "核对 readings.csv")
        first = service.sessions[key]
        if choice:
            assert "[permission_required]" in started
            original_prompt = first.prompt_task
            assert original_prompt is not None and not original_prompt.done()
            await call("respond", {"allow": "allow-report", "reject": "reject-report"}[choice])
            assert original_prompt.done()
        else:
            print("第一轮", first.process.pid, first.session_id)
            await call("message", "再核对一次设备名称")
            second = service.sessions[key]
            print("第二轮", second.process.pid, second.session_id)
            assert second is first
        await call("close")
    finally:
        await service.close(key)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("choice", nargs="?", choices=["allow", "reject"])
    asyncio.run(main(parser.parse_args().choice))
```

`thread_id` 是运行图时传进去的，放在 `configurable` 里。工具用 `get_config()` 取到它。两次调用各有自己的工具 ID，脚本会打印 `call-start` 和 `call-message`；两次的聊天 ID 和 runner 一致，所以两行打印的进程 ID 和 ACP 会话 ID 相同。

示例是同一进程内保存外部连接。服务重启后，要重新建立连接和外部会话。主 Agent 是否能恢复聊天记录则由它自己的 checkpointer 决定。外部程序通过这个账号和工作目录在宿主机运行，`cwd` 只是起始目录。

### 5.3 把真实工具接回主 Agent，观察模型怎么走完两轮

第 5.2 节走到了 `ToolMessage`。接下来把同一个工具交给 `create_deep_agent`，让图完整走一次 **模型选工具 → 执行工具 → 模型读取结果**。把下面保存为 `agent_delegate.py`。默认运行 `python agent_delegate.py`，模型用本地替身，可以离线观察真实 LangGraph 和 ACP 子进程。运行 `python agent_delegate.py --live-model` 会使用之前配置的模型提供商，工具是否被选择取决于模型回复。

```python
# agent_delegate.py
import argparse
import asyncio
import os
import sys

from deepagents import create_deep_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.checkpoint.memory import InMemorySaver

from delegation import DelegationService, build_acp_tool
from delegation_demo import RUNNER, THREAD_ID, WORKSPACE


class ScriptedInspectionModel(BaseChatModel):
    @property
    def _llm_type(self):
        return "scripted-inspection"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        last = messages[-1]
        if isinstance(last, ToolMessage):
            reply = AIMessage(content=f"根据巡检程序返回的结果：\n{last.content}")
        else:
            continuing = any(isinstance(item, ToolMessage) for item in messages)
            action = "message" if continuing else "start"
            reply = AIMessage(content="", tool_calls=[{
                "id": f"call-{action}",
                "name": "acp_runner",
                "args": {"action": action, "runner": RUNNER, "message": last.content},
            }])
        return ChatResult(generations=[ChatGeneration(message=reply)])


async def main(live_model):
    service = DelegationService(WORKSPACE, {
        RUNNER: (sys.executable, str(WORKSPACE / "inspection_runner.py")),
    })
    model = f"openai:{os.environ['OPENAI_MODEL']}" if live_model else ScriptedInspectionModel()
    agent = create_deep_agent(
        model=model,
        tools=[build_acp_tool(service)],
        checkpointer=InMemorySaver(),
        system_prompt=(
            "使用 acp_runner 和 inspection 核对巡检表。"
            "第一次调用 start，后续调用 message。根据工具返回值回答。"
        ),
    )
    config = {"configurable": {"thread_id": THREAD_ID}}
    key = (THREAD_ID, RUNNER)
    printed = set()

    try:
        for task in ("核对 readings.csv", "再核对一次需要复核的设备"):
            state = await agent.ainvoke(
                {"messages": [{"role": "user", "content": task}]}, config=config
            )
            for message in state["messages"]:
                if isinstance(message, ToolMessage) and message.tool_call_id not in printed:
                    printed.add(message.tool_call_id)
                    print(f"工具结果 {message.tool_call_id}\n{message.content}")
            print(f"助理回复\n{state['messages'][-1].content}")
            if key in service.sessions:
                session = service.sessions[key]
                print("外部会话", session.process.pid, session.session_id)
    finally:
        await service.close(key)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-model", action="store_true")
    asyncio.run(main(parser.parse_args().live_model))
```

脚本默认会打印两个不同的工具调用编号 `call-start`、`call-message`，以及两次相同的外部进程 ID 和 ACP 会话 ID。替身模型第一次返回的 `AIMessage` 正文为空，因为它这一步只需要提出工具调用。等 `ToolMessage` 回来，它会把真实 CSV 结果整理成回复。所以你可以直接追出两条数据是谁算的、哪条消息把数据交给了主模型。

这里存了两种状态。图里的 `InMemorySaver` 保存主 Agent 的聊天消息，第二轮还能看到先前的工具结果。`DelegationService.sessions` 保存外部连接与子进程。前者里的历史可以用持久化 checkpointer 保存，后者还要求进程和连接本身活着。主聊天的历史仍然可见时，外部 Agent 的会话也可能需要重新建立。

### 5.4 我的项目怎样装配 runner 和工具

应用先读配置，再根据开关和 runner 清单决定要不要注册 `acp_runner`。下面是用通用字段写出来的配置示意。每个 runner 是部署时配置好的启动命令，模型发工具调用时只需要填 runner 名称。

```json
{
  "delegate_enabled": true,
  "runners": {
    "inspection": {
      "enabled": true,
      "command": "python",
      "args": ["inspection_runner.py"],
      "env": {"INSPECTION_MODE": "demo"}
    }
  }
}
```

接上实际应用时，最好像上面的脚本一样用 `sys.executable` 和脚本的绝对路径，便于确认用的是哪个 Python、从哪里加载代码。工具拿到 `runner="inspection"` 后查配置，再把 `command` 和逐个分开的 `args` 交给子进程启动函数。创建连接时，工作目录默认取 Agent 的宿主机工作区；有路径覆盖时，相对路径从这个工作区解析。下一轮用已有进程发消息，它的实际起始目录仍由当初启动时的参数决定。

在我的项目里，环境变量按 **宿主进程环境 → 工作目录的 `.env` → runner 专用环境** 合并，工作目录中的受保护键会跳过。这个顺序决定了同名变量最终用哪一份值，也让主模型和外部程序能各用各的认证配置。下面是只展示合并顺序的片段，`protected_keys` 由宿主定义。

```python
def build_child_env(process_env, workspace_env, runner_env, protected_keys):
    env = dict(process_env)
    env.update({key: value for key, value in workspace_env.items() if key not in protected_keys})
    env.update(runner_env)
    return env
```

实际项目还给工具提供了 `list` 和 `status`，方便知道下一步该做什么。独立教学版用四个动作走主流程，完整运行时里的动作边界可以用这张表核对。

| 动作 | 会对外部 Agent 做什么 | 当前聊天里的典型用法 |
| --- | --- | --- |
| `list` | 列出宿主配置并启用的 runner | 确认巡检程序是否可用 |
| `status` | 查询当前线程中该 runner 的记录 | 查看会话是否打开、是否在等权限 |
| `start` | 启动子进程、握手、开会话并交第一条任务 | 第一次让巡检程序核表 |
| `message` | 通过已有连接发下一条 `session/prompt` | “刚才那两台的读数各是多少？” |
| `respond` | 回答外部程序之前提出的权限请求 | 用户同意写入 `summary.md` |
| `close` | 移除会话记录并清理相关资源 | 本次巡检结束，退出外部会话 |

在真实交互里还有两类容易搞混的输出。外部 Agent 的工具进度和正文都可能从 `session/update` 过来。我的项目把中间事件转换成主模型能读的文本，整次工具调用结果仍以 `ToolMessage` 回给主模型。当前实现会优先返回格式化后的工具事件。事件文本为空时，才回退到累积正文。如果日志里看得到外部正文，主模型工具结果却只有进度，应该先查这一层的拼接逻辑。教学版只收集 `AgentMessageChunk`，所以终端里的巡检结果更容易看清。


## 6. 外部程序要权限时，怎么让原任务停在原处

现在换一个会保存简报的巡检程序。它读完表后想把摘要写到演示目录的 `summary.md`，先用 `session/request_permission` 问客户端。客户端给主 Agent 返回选项，主 Agent 等用户选择后再把选项 ID 交回去。参见 [ACP v1 工具调用和权限](https://agentclientprotocol.com/protocol/v1/tool-calls)。

![权限请求暂停与恢复时序图](/blogs/power-agent-acp/acp-permission.svg)

回到 `delegation.py` 看回调里等待权限的几行。

```python
async def request_permission(self, options, session_id, tool_call, **kwargs):
    self.decision = asyncio.get_running_loop().create_future()
    self.permission_ready.set()
    return await self.decision
```

`Event`（`permission_ready`）只承担通知的工作，告诉服务“现在需要问用户”。`Future`（`decision`）保存实际选择。服务用 `asyncio.wait(..., return_when=asyncio.FIRST_COMPLETED)` 同时等外部任务和权限信号，权限先来就让当前工具调用带着选项结束，原来的 `prompt_task` 继续等待。用户选了以后，`respond()` 给原 Future 填入答案，外部程序可以从 `await request_permission(...)` 后面继续运行。参见 [Python asyncio 等待机制](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.wait)。

把下面的代码保存成 `permission_runner.py`。它复用之前的 CSV 读取函数，固定向客户端请求一个写简报的选项。客户端回传的 `outcome="selected"` 只表示选中了某一项，还得看 `option_id` 才知道选的是允许还是拒绝。

```python
# permission_runner.py
import asyncio

from acp import run_agent, update_agent_message_text
from acp.schema import PermissionOption, PromptResponse, ToolCallUpdate

from inspection_runner import InspectionRunner, summarize_readings


class PermissionRunner(InspectionRunner):
    async def prompt(self, prompt, session_id, **kwargs):
        workspace = self.workdirs[session_id]
        report = summarize_readings(workspace / "readings.csv")
        decision = await self.conn.request_permission(
            session_id=session_id,
            tool_call=ToolCallUpdate(
                tool_call_id="save-inspection-report",
                title="保存巡检简报到 summary.md",
                kind="edit",
                raw_input={"path": "summary.md"},
            ),
            options=[
                PermissionOption(
                    option_id="allow-report", name="仅这次允许", kind="allow_once"
                ),
                PermissionOption(
                    option_id="reject-report", name="仅这次拒绝", kind="reject_once"
                ),
            ],
        )

        outcome = decision.outcome
        if outcome.outcome == "selected" and outcome.option_id == "allow-report":
            (workspace / "summary.md").write_text(report + "\n", encoding="utf-8")
            update = "已保存 summary.md。"
        else:
            update = "已跳过保存。"
        await self.conn.session_update(
            session_id=session_id, update=update_agent_message_text(update)
        )
        return PromptResponse(stop_reason="end_turn")


if __name__ == "__main__":
    asyncio.run(run_agent(PermissionRunner()))
```

先执行 `python delegation_demo.py reject`，会看到“已跳过保存”，演示目录原有内容保持不变。再执行 `python delegation_demo.py allow`，会看到“已保存 summary.md”，文件里是前面算出的两条复核记录。`respond` 执行后，脚本会检查原来的 `prompt_task` 已经结束。权限确认取决于外部程序主动提出请求，并按返回的选择执行。

### 看实际权限回复的两个编号

外部 Agent 在处理第 2 节的 `session/prompt` 时，可以从反方向发一个新的 JSON-RPC 请求。下面用 `id=91` 表示该请求。响应也带 `id=91`，SDK 据此唤醒外部 Agent 正在等待的那一次调用。`save-inspection-report` 则是外部程序的工具动作 ID，用来标记本次写简报。

```jsonl
{"jsonrpc":"2.0","id":91,"method":"session/request_permission","params":{"sessionId":"inspection-001","toolCall":{"toolCallId":"save-inspection-report","title":"保存巡检简报到 summary.md","kind":"edit","rawInput":{"path":"summary.md"}},"options":[{"optionId":"allow-report","name":"仅这次允许","kind":"allow_once"},{"optionId":"reject-report","name":"仅这次拒绝","kind":"reject_once"}]}}
{"jsonrpc":"2.0","id":91,"result":{"outcome":{"outcome":"selected","optionId":"reject-report"}}}
```

如果你在主 Agent 的日志里看到 `call-respond`，那是主模型发起另一次工具调用的编号。它会在同一个 `thread_id` 和 runner 下查到外部会话，再由 SDK 回答 `id=91`。所以这里会发生一次新的**主 Agent 工具调用**，外部程序继续的是同一个 **ACP prompt**。选择拒绝仍会返回 `selected`，它表示选择了一个选项，表示拒绝的是 `reject-report`。


## 7. 反过来，让编辑器调用我的 Agent

### 7.1 直接使用 Deep Agents 的 ACP 适配器

上面一直是主 Agent 发任务。编辑器接入时，角色刚好换过来，编辑器是 ACP 客户端，Agent 进程接收请求。Deep Agents 上游有独立的 `deepagents-acp` 适配器。用第 4 节的环境安装 `deepagents-acp==0.0.13`，并配置 `OPENAI_API_KEY`、`OPENAI_MODEL`。把以下保存为 `native_server.py`，ACP 客户端可用 Python 解释器启动它。参见 [Deep Agents ACP 适配器](https://docs.langchain.com/oss/python/deepagents/acp)。

```python
# native_server.py
import asyncio
import os
from pathlib import Path

from acp import run_agent
from deepagents import create_deep_agent
from deepagents_acp.server import AgentServerACP
from langgraph.checkpoint.memory import InMemorySaver

from inspection_runner import summarize_readings


def check_readings() -> str:
    """核对演示巡检表，返回需要复核的设备。"""
    return summarize_readings(Path(__file__).with_name("readings.csv"))


async def main():
    graph = create_deep_agent(
        model=f"openai:{os.environ['OPENAI_MODEL']}",
        tools=[check_readings],
        system_prompt="接到巡检问题时，调用 check_readings，然后根据结果回复。",
        checkpointer=InMemorySaver(),
    )
    await run_agent(AgentServerACP(graph))


if __name__ == "__main__":
    asyncio.run(main())
```

以 Zed 为例，在自定义 Agent 设置里填入虚拟环境的 Python 路径和脚本路径。Windows 虚拟环境通常用 `Scripts/python.exe`，模型环境变量要能被编辑器启动的进程读到。参见 [Zed 外部 Agent 配置](https://zed.dev/docs/ai/external-agents)。

```json
{
  "agent_servers": {
    "巡检助手": {
      "type": "custom",
      "command": "/absolute/path/to/venv/bin/python",
      "args": [
        "/absolute/path/to/demo/native_server.py"
      ]
    }
  }
}
```

我的项目也有同方向的适配器。核心是把客户端的 ACP 会话 ID 用作聊天线程 ID，收到 `session/prompt` 后拼接文本块，生成应用内部的请求。下面还原了这个请求的形状。

```python
request = {
    "messages": [{"role": "user", "content": "核对 readings.csv"}],
    "thread_id": session_id,
    "source": "acp",
}
```

另一半工作是把应用内部的流转成编辑器能拼接的消息。例如内部依次给出“读到 3 条”和“读到 3 条，2 条需要复核。”，第二条消息只需要补发后半句。下面是一个可独立验证文本增量的片段，实际适配器拿到片段后会通过 `session_update()` 发给客户端。

```python
from acp import update_agent_message_text

previous = ""
for current in ("读到 3 条", "读到 3 条，2 条需要复核。"):
    delta = current[len(previous):] if current.startswith(previous) else current
    previous = current
    if delta:
        update = update_agent_message_text(delta)
        print(update.model_dump_json(by_alias=True, exclude_none=True))
```

```jsonl
{"sessionUpdate":"agent_message_chunk","content":{"type":"text","text":"读到 3 条"}}
{"sessionUpdate":"agent_message_chunk","content":{"type":"text","text":"，2 条需要复核。"}}
```

### 7.2 我怎样把已有运行时接到 ACP 服务端

上游的 `AgentServerACP` 可以直接包住 LangGraph 图。如果应用已经有自己的聊天入口和流式事件，我会在 ACP 服务端接这个入口。适配器整理请求和输出，原来的模型选择、业务工具、聊天状态仍由应用处理。

![编辑器调用应用运行时的 ACP 时序图](/blogs/power-agent-acp/acp-editor.svg)

下面用两个小类还原这条接法。把代码保存成 `project_server.py`。`InspectionRuntime.stream()` 模拟应用已经提供的流接口，用第 3 节的读表逻辑产生两段累计正文。`ProjectACPAdapter` 负责建会话、在正确的线程里调用这个接口，以及把正文发给客户端。

```python
# project_server.py
import asyncio
from pathlib import Path
from uuid import uuid4

from acp import PROTOCOL_VERSION, run_agent, update_agent_message_text
from acp.schema import InitializeResponse, NewSessionResponse, PromptResponse
from acp.schema import TextContentBlock

from inspection_runner import summarize_readings


class InspectionRuntime:
    async def stream(self, request):
        summary = summarize_readings(request["workspace"] / "readings.csv")
        first_line = summary.splitlines()[0]
        yield {"type": "token", "content": first_line}
        await asyncio.sleep(0)
        yield {"type": "token", "content": summary}


class ProjectACPAdapter:
    def __init__(self, runtime):
        self.runtime = runtime
        self.workspaces = {}
        self.cancel_events = {}

    def on_connect(self, conn):
        self.conn = conn

    async def initialize(self, protocol_version, **kwargs):
        return InitializeResponse(protocol_version=PROTOCOL_VERSION)

    async def new_session(self, cwd, **kwargs):
        session_id = uuid4().hex
        self.workspaces[session_id] = Path(cwd)
        return NewSessionResponse(session_id=session_id)

    async def prompt(self, prompt, session_id, **kwargs):
        text = "\n".join(block.text for block in prompt if isinstance(block, TextContentBlock))
        if not text.strip():
            return PromptResponse(stop_reason="end_turn")

        request = {
            "messages": [{"role": "user", "content": text}],
            "thread_id": session_id,
            "source": "acp",
            "workspace": self.workspaces[session_id],
        }
        cancelled = self.cancel_events[session_id] = asyncio.Event()
        previous = ""
        try:
            async for chunk in self.runtime.stream(request):
                if cancelled.is_set():
                    return PromptResponse(stop_reason="cancelled")
                if chunk["type"] != "token":
                    continue
                current = chunk["content"]
                delta = current[len(previous):] if current.startswith(previous) else current
                previous = current
                if delta:
                    await self.conn.session_update(
                        session_id=session_id,
                        update=update_agent_message_text(delta),
                    )
            return PromptResponse(stop_reason="end_turn")
        finally:
            self.cancel_events.pop(session_id, None)

    async def cancel(self, session_id, **kwargs):
        event = self.cancel_events.get(session_id)
        if event is not None:
            event.set()


if __name__ == "__main__":
    asyncio.run(run_agent(ProjectACPAdapter(InspectionRuntime())))
```


1. **`new_session()` 负责发编号。** 客户端以后发请求时带回 `session_id`。适配器把这个 ID 原样放进应用请求的 `thread_id`，因此同一个编辑器会话会指向同一个应用线程。演示程序直接从客户端指定的目录找 CSV，实际应用的工作区由宿主配置管理。
2. **`prompt()` 是调用已有运行时的位置。** 真实应用可以继续发工具进度等事件。完整适配器会将应用侧的工具调用分片翻成 ACP 工具开始或进度，将工具结果翻成工具更新；这里的代码专门展示文本流。
3. **`previous` 按每轮初始化。** 它只用来算这一轮正文的差量。若下一轮问另一件事，适配器仍从空字符串开始算，聊天历史由运行时的 checkpointer 管理。我的项目对加载会话的处理包括登记已有会话 ID 和目录，历史能否继续使用取决于存储和会话配置；示例服务只实现新会话。

### 7.3 不开编辑器，也能验证服务端

把下面保存为 `check_editor_connection.py`。它扮演一个最简 ACP 客户端，通过真实的标准输入输出启动 `project_server.py`，然后在同一会话里发两次问题。默认运行 `python check_editor_connection.py` 是离线检查。也可以把上游适配器的脚本路径传给它，用 `python check_editor_connection.py native_server.py` 验证已配置模型的服务端。

```python
# check_editor_connection.py
import asyncio
import sys

from acp import PROTOCOL_VERSION, spawn_agent_process, text_block

from native_delegate import InspectionClient, WORKSPACE


async def main(script):
    client = InspectionClient()
    async with asyncio.timeout(45):
        async with spawn_agent_process(
            client, sys.executable, str(WORKSPACE / script), cwd=str(WORKSPACE),
            observers=[client.observe],
        ) as (conn, _process):
            handshake = await conn.initialize(protocol_version=PROTOCOL_VERSION)
            if handshake.protocol_version != PROTOCOL_VERSION:
                raise RuntimeError("ACP 协议版本不一致")
            session = await conn.new_session(cwd=str(WORKSPACE))
            for question in ("核对巡检表", "再核对一次"):
                client.parts.clear()
                response = await conn.prompt(
                    session_id=session.session_id, prompt=[text_block(question)]
                )
                print("编辑器会话", session.session_id, "结束原因", response.stop_reason)
                for number, part in enumerate(client.parts, start=1):
                    print(f"片段 {number}: {part!r}")
                print("拼接正文", "".join(client.parts))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "project_server.py"))
```

默认的服务端每轮都回两段正文。第二段从换行和设备列表开始，客户端直接把两段连接起来。两次打印的编辑器会话 ID 相同，说明它们走同一个服务端会话。示例的运行时每轮仍然独立核表，若接入带历史的应用，就能继续利用这个线程里的已保存消息。

## 8. 真接入时，出问题先看哪一层

把出错点和它前面最后一次成功的事件放在一起看，比只记录一条“调用失败”更容易定位问题。下面用前面的巡检例子列几个常见判断。

| 看到的现象 | 应该核对什么 |
| --- | --- |
| 主模型从头到尾没有调用 `acp_runner` | 检查委派开关、是否有已启用的 runner、工具是否进了模型的工具列表。用第 5.2 节的小图先验证工具本身。 |
| `initialize` 一直没回应 | 确认配置的命令能启动 ACP 服务，检查子进程标准错误。标准输出里应该是协议消息。 |
| 握手和建会话成功，第一轮却找不到 CSV | 对照启动子进程的 `cwd`、创建会话时传的 `cwd`，以及外部程序实际读表的目录。 |
| 第二次 `message` 找不到会话 | 核对两次的 `thread_id`、runner 名称和进程是否还活着。进程退出后要重新开会话。 |
| 执行到一半停住，但工具返回了权限选项 | 把选项交给用户，用同一个 runner 执行 `respond`，传请求里原样返回的选项 ID。 |
| 编辑器能连上，但正文重复 | 核对运行时产出的是累计文本还是增量。累计文本在转换层取差量，已有增量可以直接发送。 |

我的项目给一次工具等待设置了默认 300 秒的上限，超时后会尝试向外部程序发取消。收到取消通知后，外部 Agent 需要自行停止本轮工作，已发生的动作可能还在。超时、取消、关闭各管一件事。超时是宿主停止等待，取消是请求外部 Agent 停下当前轮次，关闭负责把连接和进程的资源收回来。参见 [ACP v1 取消机制](https://agentclientprotocol.com/protocol/v1/cancellation)。

要分辨两轮是否真的复用连接，可以记一行关联日志。下面是代码示意，实际运行用这次调用和会话的字段填进去。内容涉及业务数据或环境变量时，日志保留标识和状态就够定位。

```python
logger.info(
    "ACP action=%s thread=%s runner=%s tool_call=%s session=%s pid=%s",
    action, thread_id, runner_name, tool_call_id, session.session_id, session.process.pid,
)
```

第一轮可以看到 `start` 对应一次进程启动，第二轮是 `message`，两行的 `session` 和 `pid` 相同。权限场景再多记下请求出现和决定返回的时间，就能判断是在等外部程序还是在等用户。


回到最开始的三条巡检数据。两台设备触发复核规则，是外部 Python 程序根据 CSV 算出来的。ACP 负责把任务、进度、权限和结果送到该去的地方。原生 SDK 的例子用几次函数调用就能走完一轮；会话封装的价值，在于下一轮来了还能知道该找哪个进程，以及权限确认回来该唤醒哪个任务。
