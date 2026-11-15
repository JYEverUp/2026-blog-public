在公司做 Agent 项目时，看到代码里出现 `ProviderStore`、`ModelResolver`、`ChatModelFactory`，我会先提出一个质疑：DeepAgents 已经可以接入模型，为什么还要包这么多层？

如果只是把 `create_deep_agent(model=...)` 藏到另一个函数里，增加几个类名，却没有减少重复代码、明确配置归属或者隔离变化，这个质疑是成立的。

因此，讨论模型接入时，我更关心几个具体问题：原来十几行代码已经能跑，后来是哪项需求让它变得难维护？新增这一层以后，调用方到底少操心了什么？哪些能力框架已经提供，哪些责任应该留给平台？

这篇文章沿着一个设备运维助手的演进过程回答这些问题。我们先保留最简单的写法，再看需求变化如何推动代码分层，最后用完整 Python 示例验证这层设计是否真的有用。

## 先承认：只有一个模型时，直接用 DeepAgents 就够了

假设我们只需要一个助手，读取设备告警文本并给出分析建议。模型由开发者配置，所有人使用同一个部署账号，没有页面切换需求。

这时没有必要先设计“统一多模型平台”。一个正常的起点是：

```python
import asyncio
import os

from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model


async def main() -> None:
    model = init_chat_model(
        model=os.environ["DEEPSEEK_MODEL"],
        model_provider="deepseek",
        api_key=os.environ["DEEPSEEK_API_KEY"],
        api_base=os.environ["DEEPSEEK_BASE_URL"],
        timeout=30,
        max_retries=1,
    )
    agent = create_deep_agent(model=model)
    result = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": "设备温度连续升高，同时振动增大，请给出排查建议。",
        }]
    })
    print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
```

真实调用需要安装 `deepagents`、`langchain` 和 `langchain-deepseek`，配置有效凭证、服务地址和支持工具调用的模型，执行时会向模型服务发送请求。上面使用厂商专用集成，通过环境变量提供当前部署可用的模型名称，避免把模型目录写死在业务代码中。

DeepAgents 可以接收具备工具调用能力的 LangChain 聊天模型，也支持模型字符串。这说明“接入多个厂商”并不要求我们自行实现每家的 HTTP 协议。[DeepAgents 模型文档](https://docs.langchain.com/oss/python/deepagents/models)

如果需求一直停留在这个范围，我会保留这段代码。替换一次环境变量并重新启动，完全可以是合理的运维方式。

## 以前常见的写法，什么时候开始让人难受？

这里的“以前”指应用尚未抽出统一接入职责时的常见写法。为了方便对比，下面用简化代码说明方案如何演进，省略与模型接入无关的业务逻辑。

第一阶段只需要聊天。第二阶段增加交接班摘要。第三阶段增加每天自动生成日报的定时任务。每个功能都需要初始化模型，于是代码可能长成这样：

```python
import os

from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI


def create_chat_agent():
    model = ChatOpenAI(
        model=os.environ["CHAT_MODEL"],
        base_url=os.environ["MODEL_BASE_URL"],
        api_key=os.environ["MODEL_API_KEY"],
        use_responses_api=False,
        stream_usage=False,
        timeout=30,
    )
    return create_deep_agent(model=model)


def create_handover_agent():
    model = ChatOpenAI(
        model=os.environ["SUMMARY_MODEL"],
        base_url=os.environ["MODEL_BASE_URL"],
        api_key=os.environ["MODEL_API_KEY"],
        use_responses_api=False,
        timeout=30,
    )
    return create_deep_agent(model=model)


def create_daily_report_agent():
    model = ChatOpenAI(
        model=os.environ["REPORT_MODEL"],
        base_url=os.environ["MODEL_BASE_URL"],
        api_key=os.environ["MODEL_API_KEY"],
        use_responses_api=False,
        timeout=60,
    )
    return create_deep_agent(model=model)
```

这段代码假设服务支持所需的 OpenAI Chat Completions 行为。它确实有重复，但单纯为了少写几行，还不足以证明需要一个复杂的接入系统。真正推动分层的是下面几类变化。

**第一种变化：一个兼容参数要改三处。** 某个兼容服务不接受流式用量统计字段，聊天入口显式关闭了，后面新增的摘要入口却没有跟进。是否触发错误取决于 SDK 的默认行为与具体调用方式，问题可能直到流式调用时才暴露。类似的兼容选择应该跟着服务配置走，避免散落到每项业务中。

**第二种变化：同一个进程要同时服务不同账号。** Alice 使用自己的 DeepSeek 凭证，Bob 使用团队配置的另一家服务。进程级的 `MODEL_API_KEY` 无法表达这两个选择。更不能在处理一次请求时临时改全局环境变量，让并发中的另一次请求也读到新值。

**第三种变化：模型选择成了产品功能。** 用户希望通过页面为助手配置模型。修改配置需要检查所有权、供应商是否可用、模型是否在允许列表中。此时让每个路由自己读取配置、检查权限并初始化 SDK，重复的已经包括业务规则。

**第四种变化：只改地址不能覆盖所有能力。** 两个服务都提供兼容接口，也可能在推理字段、工具调用或用量统计上存在差异。能回答一句话，不能证明多轮工具执行也兼容。

例如，LangChain 的 `ChatOpenAI` 文档明确提示，它面向标准 OpenAI API，第三方扩展的推理响应字段不一定被保留；需要这些能力时，应优先评估对应厂商的专用集成。[ChatOpenAI 接口说明](https://reference.langchain.com/python/langchain-openai/ChatOpenAI)

![从固定模型脚本到多用户模型选择的演进](/blogs/deepagents-model-integration/evolution.svg)

[查看这张图的 Mermaid 源文件](/blogs/deepagents-model-integration/evolution.mmd)

## 要统一到什么程度？先把三个概念拆开

“模型供应商”经常混合表达三件不同的事：模型由谁提供、通过哪个账号访问、使用什么通信协议。

以一个企业模型网关为例，地址可能属于企业自己的服务，后面转发到不同厂商；两位用户也可能访问同一地址，但使用不同凭证和模型权限。因此，不能只拿域名当成供应商实例的身份。

在本文示例里，我用下面这些数据表达一次模型选择：

| 数据 | 示例 | 用途 |
| --- | --- | --- |
| 供应商实例 ID | `alice-deepseek` | 区分一份具体的接入配置 |
| 所有者 | `alice` 或平台共享 | 决定谁可以使用这份配置 |
| 适配方式 | `deepseek`、`openai-compatible` | 选择哪个 SDK 创建函数 |
| 接口地址 | 部署方提供的 URL | 确定请求发到哪里 |
| 凭据引用 | `ALICE_MODEL_KEY` | 后端按引用读取凭证 |
| 允许使用的模型 | 一组模型名称 | 限制本次选择范围 |
| Agent 默认模型 | 绑定到某个供应商实例 | 表达该助手的默认选择 |

注意，这里的 `deepseek`、`openai-compatible` 是示例程序的适配器键；公司项目中的供应商类型和内部运行时的通信协议可以有各自的取值与映射，不能直接把示例字段当作业务 API 的请求体。

“模型已经在列表里”还不等于“它适合所有任务”。对话、图片输入、工具调用、Embedding 的能力不同。本文只讨论聊天 Agent，生产环境还应根据任务检查所需能力，不能把 Embedding 模型塞给聊天 Agent。

## 拆出一条清楚的调用链

我会让平台层先确定用户有权使用的配置，再让模型工厂创建具体模型，最后把模型注入 Agent。

![模型管理、模型工厂、适配器和 Agent 的职责划分](/blogs/deepagents-model-integration/architecture.svg)

[查看架构图 Mermaid 源文件](/blogs/deepagents-model-integration/architecture.mmd)

这条链路有几个明确的边界：

- HTTP 入口从登录态取得用户身份，不能信任请求正文随便传来的 `user_id`。
- 配置解析器检查 Agent 归属和模型可用范围，返回选中的供应商与模型。
- 模型工厂根据适配方式选择创建函数，并在后端取得凭证。
- SDK 或运行时适配器负责具体的模型协议。
- Agent 接收模型对象，继续处理计划、工具调用和任务执行。

这里故意把“决定能用什么”放在“读取 Key、创建模型”之前。权限不通过，请求就不应该到达凭证和模型创建环节。

示例中的平台共享规则是 `owner_id=None` 表示所有平台用户可用。这只是本文选择的一种简化规则；实际项目也可以使用组织、角色或明确授权列表。

## 用完整代码验证：这层分工到底有没有作用？

下面是完整的 `model_demo.py`。使用 Python 3.12 或更高版本即可运行，不需要安装模型 SDK，不需要真实 Key，也不会发出模型请求。

为了只验证接入逻辑，示例注入了 `FakeModel` 和 `FakeAgent`。它们返回实际选中的模型引用，方便观察 Alice、Bob 和越权请求分别走到哪里。它们不会生成运维分析内容，也不能证明真实模型的协议兼容性。

[下载完整 model_demo.py](/blogs/deepagents-model-integration/model_demo.py)

```python
"""Python 3.12+; offline demo, no SDK, credentials, or model calls required."""
from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class Provider:
    id: str
    owner_id: str | None  # None means platform-shared in this example.
    adapter: str
    base_url: str
    secret_ref: str
    models: tuple[str, ...]
    enabled: bool = True
    stream_usage: bool = False


@dataclass(frozen=True)
class AgentConfig:
    id: str
    owner_id: str
    provider_id: str
    model: str


@dataclass(frozen=True)
class ModelSelection:
    provider: Provider
    model: str


class ModelResolver:
    def __init__(
        self,
        providers: Mapping[str, Provider],
        agents: Mapping[str, AgentConfig],
    ) -> None:
        self.providers = providers
        self.agents = agents

    def resolve(
        self, *, user_id: str, agent_id: str, model: str | None = None
    ) -> ModelSelection:
        agent = self.agents[agent_id]
        if agent.owner_id != user_id:
            raise PermissionError("agent is not owned by current user")

        provider = self.providers[agent.provider_id]
        if provider.owner_id not in (None, user_id):
            raise PermissionError("provider is not visible to current user")
        if not provider.enabled:
            raise ValueError("provider is disabled")

        selected = model if model is not None else agent.model
        if selected not in provider.models:
            raise ValueError("model is not enabled for this provider")
        return ModelSelection(provider=provider, model=selected)


ModelBuilder = Callable[[ModelSelection, str], Any]


class ModelFactory:
    def __init__(
        self,
        builders: Mapping[str, ModelBuilder],
        read_secret: Callable[[str], str],
    ) -> None:
        self.builders = builders
        self.read_secret = read_secret

    def create(self, selection: ModelSelection) -> Any:
        builder = self.builders[selection.provider.adapter]
        api_key = self.read_secret(selection.provider.secret_ref)
        return builder(selection, api_key)


class AgentRuntime(Protocol):
    async def ainvoke(self, state: dict[str, Any]) -> dict[str, Any]: ...


class ChatService:
    def __init__(
        self,
        resolver: ModelResolver,
        factory: ModelFactory,
        build_agent: Callable[[Any], AgentRuntime],
    ) -> None:
        self.resolver = resolver
        self.factory = factory
        self.build_agent = build_agent

    async def ask(self, *, user_id: str, agent_id: str, text: str) -> Any:
        selection = self.resolver.resolve(user_id=user_id, agent_id=agent_id)
        model = self.factory.create(selection)
        agent = self.build_agent(model)
        return await agent.ainvoke({
            "messages": [{"role": "user", "content": text}]
        })


@dataclass(frozen=True)
class FakeModel:
    provider_id: str
    model: str


class FakeAgent:
    def __init__(self, model: FakeModel) -> None:
        self.model = model

    async def ainvoke(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "selected": f"{self.model.provider_id}/{self.model.model}",
            "input": state["messages"][-1]["content"],
        }


async def main() -> None:
    # All addresses, model names, and secret values here are offline fixtures.
    providers = {
        "alice-deepseek": Provider(
            "alice-deepseek", "alice", "deepseek", "https://example.invalid/v1",
            "ALICE_MODEL_KEY", ("reasoning-model",),
        ),
        "team-qwen": Provider(
            "team-qwen", None, "openai-compatible", "https://example.invalid/v1",
            "TEAM_MODEL_KEY", ("chat-model",),
        ),
    }
    agents = {
        "alice-assistant": AgentConfig(
            "alice-assistant", "alice", "alice-deepseek", "reasoning-model"
        ),
        "bob-assistant": AgentConfig(
            "bob-assistant", "bob", "team-qwen", "chat-model"
        ),
        "bob-invalid-binding": AgentConfig(
            "bob-invalid-binding", "bob", "alice-deepseek", "reasoning-model"
        ),
    }
    secrets = {
        "ALICE_MODEL_KEY": "offline-placeholder-a",
        "TEAM_MODEL_KEY": "offline-placeholder-b",
    }
    created: list[str] = []

    def fake_builder(selection: ModelSelection, api_key: str) -> FakeModel:
        assert api_key.startswith("offline-placeholder-")
        created.append(selection.provider.id)
        return FakeModel(selection.provider.id, selection.model)

    resolver = ModelResolver(providers, agents)
    factory = ModelFactory(
        {"deepseek": fake_builder, "openai-compatible": fake_builder},
        secrets.__getitem__,
    )
    service = ChatService(resolver, factory, FakeAgent)

    alice = await service.ask(
        user_id="alice", agent_id="alice-assistant", text="分析设备告警"
    )
    bob = await service.ask(
        user_id="bob", agent_id="bob-assistant", text="整理交接班记录"
    )
    assert alice["selected"] == "alice-deepseek/reasoning-model"
    assert bob["selected"] == "team-qwen/chat-model"
    print("PASS: Alice and Bob resolve different configured models")

    for agent_id in ("alice-assistant", "bob-invalid-binding"):
        try:
            await service.ask(user_id="bob", agent_id=agent_id, text="hello")
        except PermissionError:
            pass
        else:
            raise AssertionError("unauthorized selection was accepted")
    assert len(created) == 2  # Denied requests never reach model construction.
    print("PASS: foreign agents and private providers are rejected before build")

    try:
        resolver.resolve(
            user_id="alice", agent_id="alice-assistant", model="not-enabled"
        )
    except ValueError:
        print("PASS: models outside the enabled list are rejected")
    else:
        raise AssertionError("unknown model was accepted")


if __name__ == "__main__":
    asyncio.run(main())
```

在文件所在目录执行：

```bash
python model_demo.py
```

预期输出：

```text
PASS: Alice and Bob resolve different configured models
PASS: foreign agents and private providers are rejected before build
PASS: models outside the enabled list are rejected
```

这几个验证对应具体的产品行为：Alice 的助手选择她自己的模型；Bob 的助手选择团队共享模型；Bob 不能使用 Alice 的助手，也不能通过错误绑定借用 Alice 的私有供应商；不在启用列表里的模型会被拒绝。

其中，`assert len(created) == 2` 检查的是：前两次合法请求创建了模型，后面的越权请求没有继续创建。检查权限的顺序因此有了可观察的结果。

示例用字典代替数据库，字典里的“Key”也是离线占位值。生产环境需要补齐配置 CRUD、记录不存在时的错误映射、审计和凭据存储，但这些部分不影响这里要展示的调用关系。HTTP 层应把预期异常映射成稳定的错误响应，不直接向用户返回堆栈或 SDK 中的凭据信息。

## 换成真实模型：替换创建函数，保留选择规则

离线示例的价值是验证职责边界，真正上线仍然需要 SDK。下面的 `live_builders.py` 沿用同一套 `ModelResolver` 和 `ChatService`，把两个模拟创建函数换成真实创建函数。

先安装对应依赖：

```bash
uv pip install deepagents langchain langchain-openai langchain-deepseek
```

[下载 live_builders.py](/blogs/deepagents-model-integration/live_builders.py)，与 `model_demo.py` 放在同一目录：

```python
"""Optional SDK wiring; importing this file does not send model requests."""
from __future__ import annotations

import os
from typing import Any

from model_demo import ChatService, ModelFactory, ModelResolver, ModelSelection


def build_deepseek(selection: ModelSelection, api_key: str) -> Any:
    from langchain.chat_models import init_chat_model

    return init_chat_model(
        model=selection.model,
        model_provider="deepseek",
        api_key=api_key,
        api_base=selection.provider.base_url,
        timeout=30,
        max_retries=1,
    )


def build_openai_compatible(selection: ModelSelection, api_key: str) -> Any:
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=selection.model,
        base_url=selection.provider.base_url,
        api_key=api_key,
        use_responses_api=False,
        stream_usage=selection.provider.stream_usage,
        timeout=30,
        max_retries=1,
    )


def build_service(resolver: ModelResolver) -> ChatService:
    from deepagents import create_deep_agent

    factory = ModelFactory(
        builders={
            "deepseek": build_deepseek,
            "openai-compatible": build_openai_compatible,
        },
        read_secret=os.environ.__getitem__,
    )
    return ChatService(
        resolver=resolver,
        factory=factory,
        build_agent=lambda model: create_deep_agent(model=model),
    )
```

使用时先根据自己的真实配置构造 `ModelResolver`，再调用 `build_service(resolver)`。`secret_ref` 在这个装配里对应环境变量名，由后端读取。数据库场景可以把 `read_secret` 替换为凭据服务提供的方法，不需要把 Key 交给前端。

这份示例中 `https://example.invalid/v1`、`reasoning-model` 和 `chat-model` 都是刻意使用的离线数据，真实调用前必须换成服务方当前支持的地址与模型标识；选中的模型还需要支持 Agent 使用的工具调用能力。

`openai-compatible` 创建函数明确选择 Chat Completions，并显式设置 `stream_usage`。它适合已经验证过标准消息和工具调用行为的兼容服务。若需要厂商专有推理字段或其他扩展能力，应增加专用创建函数，不能把这个通用分支当作所有厂商的完整适配。[DeepSeek 专用集成文档](https://docs.langchain.com/oss/python/integrations/chat/deepseek)

这段代码没有加入 Anthropic、Bedrock 等分支，因为当前演示不需要。新增时先复用对应集成，把创建函数登记进工厂；遇到现有接口无法表达的行为，再评估是否需要进一步抽象。

本文中的 `ChatService` 每次调用都新建 Agent，适合展示一次独立请求。带连续会话、检查点和长期运行实例的平台，应由运行时管理 Agent 生命周期，并按其机制绑定或切换模型；不要直接把示例当作完整聊天服务器。

## 这些代码到底属于什么设计模式？

看懂责任以后，再给模式命名会更准确。这里没有必要为了证明“架构先进”，给每个字典和函数都贴一个模式标签。

| 设计方式 | 对应代码 | 为什么放在这里 |
| --- | --- | --- |
| 简单工厂 | `ModelFactory.create()` | 集中完成选择创建函数、取得凭证、构造模型 |
| 创建函数注册表 | `builders` 字典 | 用适配器键找到具体创建函数 |
| 适配器模式 | LangChain 厂商集成及必要的运行时补充 | 把厂商协议转换成 Agent 可使用的模型接口 |
| 策略模式的思想 | 在统一接口下替换模型实现 | 让同一任务流程使用不同模型 |
| 依赖注入 | 构造器接收 `read_secret`、`build_agent` 等依赖 | 在真实运行与离线验证之间替换实现 |
| 配置驱动 | `Provider`、`AgentConfig` | 用配置表达实例、账号和模型选择 |

**简单工厂为什么有用？** 业务入口不再关心每家 SDK 的构造参数。以后修改兼容服务的初始化行为，优先修改对应创建函数；创建入口还能统一完成需要的装配。这里没有通过子类重写创建方法，因此不应称为经典的 Factory Method 模式，也没有创建一组相关产品的需求，不必套用抽象工厂。

**适配器为什么不能省？** 对外暴露同一接口，不代表底层协议天然相同。消息、工具调用和推理内容需要转换与保留。本文主要复用现有 SDK 适配，没有重新编写一套 HTTP 客户端。一个只负责调用 SDK 构造器的函数，也不应该被夸大成已经完成了全协议适配。

**策略为什么只是“思想”？** 模型实现可以替换，调用方依赖共同接口，这是策略设计的核心。示例没有为了形式再造一个 `Strategy` 基类；底层模型框架已经提供共同接口。这里展示的是创建时根据配置选择模型，也没有实现模型在任务中途自动切换。

**依赖注入解决了什么？** 如果工厂内部写死读某个数据库、服务内部写死创建真实 Agent，每次验证权限规则都可能要搭环境甚至消耗模型额度。把依赖从外部传入后，离线验证可以使用字典和模拟对象，真实装配再接 SDK。构造器传参已经足够，不需要先引入一个依赖注入框架。

**配置驱动能做到什么？** 使用已有适配器新增一份账号配置时，通常只需要增加配置；但遇到全新的协议或响应语义，仍可能需要修改和验证适配代码。因此，“接入一个新供应商永远不用改代码”不是这层设计能够保证的事。

## 再提出几个质疑：有了这层，就万事大吉了吗？

**为什么不只写一个 `create_model()` 函数？** 如果系统只有一个入口、没有用户隔离，把初始化代码抽成一个函数完全合理。本文分开解析器、工厂和服务，是因为三者分别处理权限选择、对象创建和任务执行。若没有这些独立变化，合在一起反而更简单。

**为什么不完全交给 DeepAgents？** 模型执行和平台授权是不同的职责。框架能够接收和切换模型，不会自动知道当前应用里谁拥有某个 Agent、某份配置属于哪个用户。平台应该把已经确定的配置交给运行时，复用框架能力，而不是重复实现 Agent 循环。

**为什么不全部通过一个模型网关？** 如果企业已经有成熟网关，可以让它处理上游协议、凭据和路由，平台只接网关，减少自身适配数量。平台通常仍需要把登录用户、Agent 绑定和使用范围映射到网关能力。网关承担了哪些职责，就避免在应用里重复建设哪些职责。

**多模型是不是天然更可靠？** 能手动选择另一家服务，不等于已有自动故障切换。自动切换还要定义触发条件、能力兼容、上下文转换、费用和工具副作用。工具已经执行后贸然重跑，可能造成重复操作。本文代码没有实现故障切换，也不应这样宣传。

**为什么示例没有模型对象缓存？** 先验证选择和隔离，缓存可以后加。生产环境复用模型对象时，缓存至少需要区分供应商实例、模型和影响行为的配置，并考虑凭据轮换后的失效和客户端资源释放。仅用 `base_url` 或模型名称作键，会让不同账号存在混用对象的风险。缓存设计应该由持有客户端生命周期的组件负责。

**换了模型，效果是不是一样？** 不会。统一接口只能减少调用方式上的差异，不能统一模型能力。至少要验证多轮工具调用、流式事件、推理内容回传、上下文长度与任务所需的多模态输入。离线模拟验证不能代替这些真实服务验证。

![合法请求与越权请求的不同调用路径](/blogs/deepagents-model-integration/sequence.svg)

[查看时序图 Mermaid 源文件](/blogs/deepagents-model-integration/sequence.mmd)

## 放到公司项目里：管理配置和实现模型协议分别放在哪里？

前面的代码是为了理解设计而写的独立示例。放到公司项目中，可以把平台侧的配置管理与内部 Agent 运行时分开：平台处理用户、配置和使用范围，运行时复用底层框架完成模型调用与任务执行。下面用通用名称说明这条链路。

平台侧的 `ProviderStore.build_runtime_configs()` 读取持久化供应商记录，筛选可用聊天模型，转换成内部运行时使用的 `ProviderConfig`。简化后的字段映射如下：

```python
ProviderConfig(
    id=row.name,
    base_url=row.base_url,
    api_key=row.api_key,
    protocol=protocol,
    name=row.name,
    models=models,
    headers=headers,
    session_header=session_header_for_provider(row.name, row.base_url),
    stream_usage=resolve_provider_stream_usage(
        provider_name=row.name,
        extra=extra,
    ),
)
```

这里可以看出，平台侧主要把业务配置翻译为运行时配置，避免在每个路由里直接创建模型客户端。`sync_providers_to_runtime()` 再把这些配置同步到内部运行时的管理器中。

运行时中的 `ChatModelFactory` 根据协议选择具体构建逻辑，并管理模型对象缓存；遇到推理内容回传等兼容问题，也集中在这一层补充处理。这样的协议行为由内部运行时维护，平台侧负责配置与装配。

凭据持久化也有自己的入口。例如，可以用 `SealedProviderRepo` 包装底层供应商仓储，在写入时加密 API Key、读取时解密。它更接近一个增加存储行为的装饰式包装；前面的离线字典并没有实现加密，需要在真实装配时接入凭据存储能力。

在公司项目中，可以按这些职责组织模块，不必把具体目录结构绑定到文章示例上：

- 供应商配置模块：将数据库记录转换为运行时配置。
- 运行时装配模块：同步供应商配置，并管理配置更新后的绑定关系。
- 模型参数模块：将页面上的推理选项映射为模型请求参数。
- 凭据存储模块：负责供应商密钥的加密保存与读取。
- 模型工厂与适配模块：负责模型创建、缓存和协议兼容。

这套划分说明的是公司项目中各部分应该承担的职责，不意味着本文示例已经包含完整的授权、路由和运行时实现。正式集成时还需要结合实际业务规则与所使用的库版本进行验证。

## 做不做这一层，用需求判断

如果应用只有开发者自己使用、模型固定、部署参数可控，直接把模型交给 DeepAgents，代码更少，也更容易维护。

当多个业务入口开始重复初始化，或者出现多用户配置、页面选择、模型权限和兼容差异时，可以把这些职责逐步集中起来。新增的代码应当换来具体收益：业务入口减少协议细节，模型配置有明确归属，越权请求在读取凭证前被拒绝，兼容规则有统一的修改位置。

下次再看到一个名叫 `ModelFactory` 的类，我会检查它隔离了什么变化，以及有没有对应的验证。只有名称、没有明确责任的封装可以删减；能让一次配置修改不再散落到聊天、摘要和定时任务中的边界，才值得保留。
