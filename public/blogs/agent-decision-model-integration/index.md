在我们公司的业务助手项目里，我关心的一个问题是：当业务查询、报表导出、知识检索和外部系统接口不断接进来以后，主模型是不是还应该每次都看到全部工具？

只有几个工具时，把目录直接交给主模型通常就能工作。但随着能力增加，每次都携带完整工具说明，可能带来额外的上下文开销，也增加了区分相似能力的难度。

我们可以在主模型前面增加一层决策：根据当前任务判断哪些能力值得保留，再让主模型决定具体怎么使用。这里的关键不只是多调用一次模型，而是明确评分、筛选和执行分别由谁负责，代码应该放在哪里，失败时又如何回退。

这篇文章以“查询昨天的发电量，并导出报表”为例，把公司项目里的接入思路抽成一套独立的 Python 示例。我们先看不使用决策模型时的调用方式，再逐步加入决策层，最后通过离线测试验证规则。文中不包含公司内部系统名称、接口地址或真实业务数据，评分和业务数值都用于演示。

> 本文中的“决策模型”指承担能力适用性判断的模型，不是泛指所有决策算法，也不预设某一种模型架构。示例只实现工具筛选；技能筛选、协作成员筛选放在最后讨论。所有评分与业务数值均为演示数据，不代表实测效果。

## 1. 没有决策模型时，Agent 怎么工作

先假设系统注册了五个工具：

| 工具 | 作用 |
| --- | --- |
| `current_time` | 查询当前日期和时间 |
| `query_generation` | 查询指定日期的发电量 |
| `query_profit` | 查询指定日期的利润 |
| `query_weather` | 查询指定日期的天气 |
| `export_report` | 将发电量导出为 CSV 报表 |

原来的链路非常直接。

![未加入决策模型时的工具调用循环](/blogs/agent-decision-model-integration/baseline.png)

[查看这张图的 Mermaid 源文件](/blogs/agent-decision-model-integration/baseline.mmd)

主模型看到工具名称、描述和参数结构，再结合对话决定调用。例如，它可能先调用 `current_time` 确认“昨天”的具体日期，再查询发电量，最后调用导出工具。

以 LangChain 为例，工具通过 `create_agent(..., tools=...)` 注册，由框架组织模型调用和工具执行循环。模型负责提出工具调用，执行器负责运行对应函数并回传结果。[工具机制说明](https://docs.langchain.com/oss/python/langchain/tools)

这套方式完全可以工作。工具不多、描述清晰、任务表现稳定时，没有必要为了增加一个模型而改变架构。

### 1.1 工具增加后，可能遇到什么问题

**第一，工具目录会占用输入上下文。**

工具的成本不只有名称。描述、参数说明、JSON Schema 都需要随模型请求传递。假设 80 个工具的序列化内容平均占 180 个 token，目录就约占 14,400 个 token。这个算式只是量级示例，实际消耗需要按所用模型和请求格式测量，还要区分缓存命中与未命中的计费。

**第二，相似工具会增加选择难度。**

例如，`query_generation` 查询发电量，`query_net_generation` 查询上网电量，`query_generation_plan` 查询计划电量。主模型需要在相近的名称和描述之间做正确区分。工具说明不够准确时，增加筛选模型也无法自动修复这些定义问题。

**第三，无关能力会占据本轮注意范围。**

用户只要求查询发电量，但主模型同时看到图片生成、邮件发送、设备检修和天气查询等能力。这些工具未必导致错误，却可能让每次模型调用都携带大量本轮用不到的信息。

**第四，定位选择错误时，缺少一个独立的观察点。**

当模型调用了不合适的工具，我们往往只能检查提示词、工具描述和完整对话。加入决策层后，可以另外观察候选集合、评分和保留集合。不过，系统也会多一个可能出错的环节，需要分别评估筛选错误和执行规划错误。

这些都是需要测量的工程问题，不能直接推导出“工具多就一定要使用决策模型”。

## 2. 决策模型到底负责什么

可以把一次工具决策写成：

```text
当前任务 + 必要的历史上下文 + 候选工具描述
                          ↓
                    决策模型评分
                          ↓
                 程序应用筛选和保留规则
                          ↓
                   本轮可用工具集合
```

对于“查询昨天发电量，并导出报表”，决策服务可能返回如下演示评分：

| 候选工具 | 适用性分数 | 示例判断 |
| --- | --- | --- |
| `query_generation` | 0.98 | 直接用于查询发电量 |
| `query_profit` | 0.06 | 当前任务没有要求查询利润 |
| `query_weather` | 0.12 | 当前任务没有要求分析天气 |
| `export_report` | 0.93 | 用于完成后续导出步骤 |

`current_time` 在本例中被配置为核心工具，始终保留，不参与评分。

如果阈值设为 `0.6`，程序可以保留 `query_generation` 和 `export_report`，再合并核心工具，交给主模型。

### 2.1 三个组件各自做什么

| 组件 | 输入 | 输出 | 职责 |
| --- | --- | --- | --- |
| 决策模型 | 任务上下文、候选能力描述 | 分数或结构化选择结果 | 判断能力与整个任务的相关性 |
| 筛选代码 | 模型结果、阈值、保留规则 | 工具名称集合 | 控制候选数量、处理缺分、合并核心工具 |
| 主模型 | 对话上下文、本轮可用工具 | 回答或工具调用及参数 | 安排行动顺序，生成参数，理解结果 |

例如，决策模型选中了 `query_generation`，不代表它已经查询了发电量。主模型还需要确定日期、生成参数，工具执行器才会访问真实数据源。

同样，`0.98` 在这里是模型输出的适用性分数。除非服务提供并验证了相应的概率校准，不能把它解释为“工具调用有 98% 的概率成功”。普通模型自报的分数尤其不能直接当作可靠概率。

### 2.2 接入决策能力，不等于从头训练模型

开发者可以选择不同实现：

| 方式 | 怎么做 | 需要权衡什么 |
| --- | --- | --- |
| 规则或关键词 | 用业务规则匹配候选工具 | 适合边界清晰的需求，复杂语义下需要维护规则 |
| 通用模型结构化输出 | 单独调用模型，要求返回工具 ID 或评分 | 容易验证思路，但多一次模型推理，输出仍需校验 |
| 专用决策服务 | 调用已部署或托管的适用性评分接口 | 需要适配服务协议，验证质量、延迟和费用 |

本文采用第三种方式，重点演示应用侧的接入。后面的 HTTP 协议是为示例约定的简化协议，不是通用行业标准；真实服务的字段不同，就在客户端中做转换。

## 3. 加入决策层后的整体架构

决策层适合放在主模型调用之前。业务工具继续负责查询和导出，主模型继续负责行动安排。

![决策模型、主模型与工具执行器的职责](/blogs/agent-decision-model-integration/architecture.png)

[查看这张图的 Mermaid 源文件](/blogs/agent-decision-model-integration/architecture.mmd)

图中的“当前工具集合”已经经过权限控制。评分失败后回退，也只能回退到这个集合，不能重新开放用户无权调用的能力。

本文基础版本在每次主模型调用前执行中间件。因此，工具结果返回后，再次调用主模型时也会经过决策层。这有利于结合新结果调整选择，但会增加评分次数。第 7 节再讨论如何在一轮任务内复用结果。

### 3.1 为什么用中间件接入

筛选逻辑如果散落在每个业务工具内部，往往已经太晚：主模型早就看到了完整目录，并生成了工具调用。

模型调用中间件可以在请求发送前统一调整工具集合。LangChain 提供 `wrap_model_call` 和 `awrap_model_call` 这类包装钩子，用于拦截模型调用。[自定义中间件说明](https://docs.langchain.com/oss/python/langchain/middleware/custom)

如果项目没有使用这类框架，也可以在自己封装的 `call_model()` 前执行同样的流程。关键是接入位置，而不是必须继承某个类。

### 3.2 一次完整请求的时序

![一次业务请求的完整调用时序](/blogs/agent-decision-model-integration/sequence.png)

[查看这张图的 Mermaid 源文件](/blogs/agent-decision-model-integration/sequence.mmd)

这是可能的调用顺序，不是模型行为保证。有完整日期时可以省去时间查询；模型也可能先追问缺失条件。

## 4. 代码放在哪里：先划清文件职责

为了把公司项目里的接入链路讲清楚，我把示例整理成一个独立的 `agent_demo` 目录，只保留配置、评分、筛选、中间件和业务工具这几个部分：

```text
agent_demo/
├── __init__.py
├── app.py                    # 读取环境变量，组装客户端和 Agent
├── tools.py                  # 业务工具与实际执行逻辑
├── decision/
│   ├── __init__.py
│   ├── config.py             # 决策配置
│   ├── client.py             # 调用评分服务并校验返回值
│   └── select.py             # 纯函数：评分 → 保留集合
└── middleware/
    ├── __init__.py
    └── decision.py           # 收集上下文，评分，调整模型请求
tests/
└── test_decision.py           # 不联网的筛选与客户端测试
```

各个 `__init__.py` 保持为空即可。

[下载完整示例代码与测试](/blogs/agent-decision-model-integration/decision-agent-demo.zip)。解压后在包含 `agent_demo/` 和 `tests/` 的目录运行文中的命令；离线测试不需要模型凭据。下面的代码块标明了文件名，可以按文件保存；命令在包含 `agent_demo/` 和 `tests/` 的父目录执行。

![项目代码的文件职责与依赖关系](/blogs/agent-decision-model-integration/modules.png)

[查看这张图的 Mermaid 源文件](/blogs/agent-decision-model-integration/modules.mmd)

这里不需要把阈值判断写进业务工具，也不需要让每个请求处理函数重复创建 Agent。配置和客户端在启动时组装，评分在运行时发生。

## 5. 按文件实现接入

示例使用 Python 3.12、LangChain 1.x、`httpx`。接口核对环境为 `langchain==1.4.3`、`langchain-core==1.6.6`、`httpx==0.28.1`。主模型示例使用 `langchain-openai` 的兼容客户端；如换其他模型供应商，可替换 `app.py` 中的模型构造部分。

安装依赖：

```bash
python -m pip install "langchain==1.4.3" "langchain-core==1.6.6" "httpx==0.28.1" "langchain-openai>=1.3.3,<2" pytest pytest-asyncio
```

> 后面的在线运行需要一个支持工具调用的主模型端点，以及一个实现本文约定协议的决策服务。本文没有训练或部署评分服务，也不会因为填写了一个 URL 就自动提供模型。没有服务时，可以先运行第 6 节的离线测试。

### 5.1 `decision/config.py`：声明策略参数

文件：`agent_demo/decision/config.py`（[下载此文件](/blogs/agent-decision-model-integration/code/agent_demo/decision/config.py)）

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionConfig:
    enabled: bool = True
    endpoint: str = ""
    threshold: float = 0.6
    max_selected: int = 3
    tool_min_count: int = 4
    timeout_s: float = 3.0
    always_keep: frozenset[str] = frozenset({"current_time"})

    def __post_init__(self) -> None:
        if not 0 < self.threshold < 1:
            raise ValueError("threshold must be between 0 and 1")
        if min(self.max_selected, self.tool_min_count) < 1:
            raise ValueError("tool counts must be positive")
        if self.timeout_s <= 0:
            raise ValueError("timeout_s must be positive")
        if self.enabled and not self.endpoint:
            raise ValueError("enabled decision requires an endpoint")
```

几个参数要区分开：

- `tool_min_count`：参与筛选的候选数量达到多少，才值得发起决策调用。
- `threshold`：模型评分达到什么水平，才进入高分候选集合。
- `max_selected`：最多保留多少个已评分的高分工具。
- `always_keep`：不参与评分、始终保留的核心工具。
- `timeout_s`：一次决策请求允许占用的时间预算。

`4`、`0.6`、`3` 都只是演示配置，不是行业最佳值。工具数量门槛还可以结合目录 token 体积和任务复杂度设置。

### 5.2 `decision/select.py`：用纯函数处理保留规则

文件：`agent_demo/decision/select.py`（[下载此文件](/blogs/agent-decision-model-integration/code/agent_demo/decision/select.py)）

```python
from __future__ import annotations

from dataclasses import dataclass

from .config import DecisionConfig


@dataclass(frozen=True)
class Candidate:
    id: str
    description: str


def select_tool_names(
    candidate_ids: list[str],
    asked_ids: set[str],
    scores: dict[str, float],
    config: DecisionConfig,
) -> set[str]:
    """Keep high scores, unknowns, and configured core tools."""
    available = set(candidate_ids)
    asked = asked_ids & available
    ranked = sorted(
        (name for name in asked if name in scores),
        key=lambda name: (-scores[name], name),
    )
    above_threshold = [name for name in ranked if scores[name] >= config.threshold]
    selected = set(above_threshold[: config.max_selected])
    unasked = available - asked
    missing = asked - scores.keys()
    core = config.always_keep & available
    return selected | unasked | missing | core
```

这个函数处理的是工具名称，不执行工具。规则是：

1. 对已询问且拿到分数的工具排序，按阈值和数量选取。
2. 没被询问的工具保留，因为没有依据认定它不相关。
3. 被询问但缺少有效分数的工具保留。
4. 合并当前实际存在的核心工具。

基础版为了方便跟踪数据，暂不加入“接近阈值也保留”的余量规则。实际项目可以用评测决定是否需要。

![高分、低分、缺分与核心工具的保留规则](/blogs/agent-decision-model-integration/selection.png)

[查看这张图的 Mermaid 源文件](/blogs/agent-decision-model-integration/selection.mmd)

因此，`max_selected` 不是最终工具总量上限。核心工具、未询问工具和缺分工具会额外保留。保守回退可能降低筛选收益，但能减少因服务缺分造成的能力丢失。

### 5.3 `decision/client.py`：适配评分服务

先约定服务接收如下 JSON，`candidates` 中只放当前候选项：

```json
{
  "instruction": "判断完成整个任务可能需要哪些工具，包括后续步骤依赖；只评分，不执行工具。",
  "state": "human: 查询昨天发电量，并导出报表",
  "candidates": [
    {"id": "query_generation", "description": "查询指定日期的发电量"},
    {"id": "query_profit", "description": "查询指定日期的利润"},
    {"id": "query_weather", "description": "查询指定日期的天气"},
    {"id": "export_report", "description": "将发电量导出为 CSV 报表"}
  ]
}
```

服务返回：

```json
{
  "scores": {
    "query_generation": 0.98,
    "query_profit": 0.06,
    "query_weather": 0.12,
    "export_report": 0.93
  }
}
```

这里发送的是上下文和工具说明，不是业务工具的执行参数。`query_generation` 的日期参数，要等主模型真正提出调用时才会生成。

文件：`agent_demo/decision/client.py`（[下载此文件](/blogs/agent-decision-model-integration/code/agent_demo/decision/client.py)）

```python
from __future__ import annotations

import asyncio
import math

import httpx

from .config import DecisionConfig
from .select import Candidate


class DecisionClient:
    def __init__(
        self,
        http: httpx.AsyncClient,
        config: DecisionConfig,
    ) -> None:
        self._http = http
        self._config = config

    async def score(
        self,
        state: str,
        candidates: list[Candidate],
    ) -> dict[str, float]:
        body = {
            "instruction": (
                "判断完成整个任务可能需要哪些工具，包括后续步骤依赖；只评分，不执行工具。"
            ),
            "state": state,
            "candidates": [{"id": item.id, "description": item.description} for item in candidates],
        }
        async with asyncio.timeout(self._config.timeout_s):
            response = await self._http.post(
                self._config.endpoint,
                json=body,
                timeout=self._config.timeout_s,
            )
            response.raise_for_status()
            payload = response.json()

        if not isinstance(payload, dict):
            raise ValueError("decision response must be an object")
        rows = payload.get("scores")
        if not isinstance(rows, dict):
            raise ValueError("decision response requires scores")

        asked = {item.id for item in candidates}
        scores: dict[str, float] = {}
        for name, value in rows.items():
            if name not in asked or isinstance(value, bool):
                continue
            if not isinstance(value, (int, float)):
                continue
            if math.isfinite(value) and 0 <= value <= 1:
                scores[name] = float(value)
        return scores
```

客户端只接受本次提交过的工具 ID，并丢弃布尔值、越界值、非有限数和其他无效分数。这些项目后续按“缺分”处理，不会因为解析失败被直接淘汰。

`httpx` 的超时控制与外层 `asyncio.timeout()` 配合，限制一次决策请求的等待。为了让基础示例容易理解，这里不加重试；真实项目若需要重试，重试和退避也要共享总时间预算，不能无限延长用户等待。

如果实际服务使用 `questions`、`answers` 或其他字段，应修改这个文件里的请求构造和响应解析，保持上层接收到的仍然是 `dict[str, float]`。

### 5.4 `middleware/decision.py`：连接评分与主模型

文件：`agent_demo/middleware/decision.py`（[下载此文件](/blogs/agent-decision-model-integration/code/agent_demo/middleware/decision.py)）

```python
from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import cast

import httpx
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.tools import BaseTool

from ..decision.client import DecisionClient
from ..decision.config import DecisionConfig
from ..decision.select import Candidate, select_tool_names

logger = logging.getLogger(__name__)


def build_state(request: ModelRequest) -> str:
    lines: list[str] = []
    for message in request.messages[-8:]:
        content = message.content
        if isinstance(content, str):
            text = content
        else:
            text = "\n".join(
                str(block.get("text", ""))
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            )
        lines.append(f"{message.type}: {text}")
    return "\n".join(lines)[-2400:]


class DecisionMiddleware(AgentMiddleware):
    def __init__(
        self,
        config: DecisionConfig,
        client: DecisionClient,
    ) -> None:
        super().__init__()
        self._config = config
        self._client = client

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        config = self._config
        if not config.enabled:
            return await handler(request)

        # 本示例仅注册 BaseTool；服务商原生工具字典需另行适配。
        tools = cast(list[BaseTool], request.tools)
        candidates = [
            Candidate(tool.name, tool.description)
            for tool in tools
            if tool.name not in config.always_keep
        ]
        if len(candidates) < config.tool_min_count:
            return await handler(request)

        try:
            scores = await self._client.score(build_state(request), candidates)
        except (httpx.HTTPError, TimeoutError, ValueError) as exc:
            logger.warning(
                "decision unavailable; keeping current catalog (%s)",
                type(exc).__name__,
            )
            return await handler(request)

        kept = select_tool_names(
            candidate_ids=[tool.name for tool in tools],
            asked_ids={item.id for item in candidates},
            scores=scores,
            config=config,
        )
        narrowed = request.override(
            tools=[tool for tool in tools if tool.name in kept],
        )
        return await handler(narrowed)
```

最关键的是最后几行：中间件构造一个工具集合更小的模型请求，再交给 `handler()` 调用主模型。它没有运行任何业务工具，也没有从注册表永久删除工具。

异常捕获只覆盖预期的请求与解析失败。取消信号和程序逻辑错误不应该一律吞掉，否则真实问题难以定位。

`build_state()` 采用最近 8 条消息和 2,400 个字符的简单预算，包括文本形式的工具结果，便于评分时知道已经发生了什么。这只是演示性的上下文构造：真实项目应保留原始任务、当前目标、关键结果和缺失条件，处理过长工具输出，并在发送到外部服务前执行必要的数据最小化。

### 5.5 `tools.py`：业务逻辑仍然放在业务模块

文件：`agent_demo/tools.py`（[下载此文件](/blogs/agent-decision-model-integration/code/agent_demo/tools.py)）

```python
from __future__ import annotations

import csv
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from langchain_core.tools import tool


@tool
def current_time() -> str:
    """查询北京时间，用于确定今天、昨天等相对日期。"""
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


@tool
def query_generation(day: str) -> dict[str, str | float]:
    """查询指定日期的发电量。day 格式为 YYYY-MM-DD，返回单位为 MWh。"""
    normalized = date.fromisoformat(day).isoformat()
    return {"day": normalized, "generation_mwh": 1250.0, "source": "demo"}


@tool
def query_profit(day: str) -> dict[str, str | float]:
    """查询指定日期的利润。day 格式为 YYYY-MM-DD，返回单位为元。"""
    normalized = date.fromisoformat(day).isoformat()
    return {"day": normalized, "profit_yuan": 80000.0, "source": "demo"}


@tool
def query_weather(day: str) -> dict[str, str]:
    """查询指定日期的天气。day 格式为 YYYY-MM-DD。"""
    normalized = date.fromisoformat(day).isoformat()
    return {"day": normalized, "weather": "晴", "source": "demo"}


@tool
def export_report(day: str, generation_mwh: float) -> str:
    """将查询到的日期和发电量导出为本地 CSV；返回文件绝对路径。"""
    normalized = date.fromisoformat(day).isoformat()
    folder = Path("reports")
    folder.mkdir(exist_ok=True)
    path = folder / f"generation-{normalized}.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["day", "generation_mwh"])
        writer.writerow([normalized, generation_mwh])
    return str(path.resolve())


TOOLS = [current_time, query_generation, query_profit, query_weather, export_report]
```

查询工具返回的是固定演示数据；接入公司的业务系统时，把函数体替换为数据库或业务 API 调用。报表工具会真实写入当前工作目录的 `reports/`，同一天重复导出会覆盖同名演示文件。它返回的是服务器本地文件路径，面向远程用户时还需由宿主应用提供下载或发送文件能力。

工具定义要描述业务能力和参数含义，决策策略不混进这些函数。查询工具不需要知道自己得了多少分，导出工具也不需要知道阈值是多少。

### 5.6 `app.py`：在启动入口完成装配

文件：`agent_demo/app.py`（[下载此文件](/blogs/agent-decision-model-integration/code/agent_demo/app.py)）

```python
from __future__ import annotations

import asyncio
import logging
import os

import httpx
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from .decision.client import DecisionClient
from .decision.config import DecisionConfig
from .middleware.decision import DecisionMiddleware
from .tools import TOOLS


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    config = DecisionConfig(
        enabled=os.getenv("DECISION_ENABLED", "1") == "1",
        endpoint=os.getenv("DECISION_ENDPOINT", ""),
    )
    key = os.getenv("DECISION_API_KEY", "")
    headers = {"Authorization": f"Bearer {key}"} if key else {}

    async with httpx.AsyncClient(headers=headers) as http:
        client = DecisionClient(http, config)
        middleware = [DecisionMiddleware(config, client)] if config.enabled else []
        model = ChatOpenAI(
            model=os.environ["CHAT_MODEL"],
            base_url=os.environ["CHAT_BASE_URL"],
            api_key=os.environ["CHAT_API_KEY"],
            temperature=0,
        )
        agent = create_agent(
            model=model,
            tools=TOOLS,
            middleware=middleware,
            system_prompt=(
                "你是业务助手。相对日期先通过工具确认具体日期。"
                "发电量必须来自查询工具，导出时使用实际查询结果。"
                "工具数据若标记 demo，回答中必须说明是演示数据。"
            ),
        )
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "查询昨天的发电量，并导出报表"}]}
        )
        print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
```

环境变量由运行环境提供，以下仅展示 PowerShell 的设置方式，请替换为真实可用的端点、模型 ID 和凭据：

```powershell
$env:CHAT_MODEL = "your-tool-capable-model"
$env:CHAT_BASE_URL = "https://chat.example.com/v1"
$env:CHAT_API_KEY = "sk-xxx"
$env:DECISION_ENDPOINT = "https://decision.example.com/score"
$env:DECISION_API_KEY = "sk-xxx"
$env:DECISION_ENABLED = "1"
python -m agent_demo.app
```

这些域名是占位地址，不能直接运行成功。`ChatOpenAI` 使用的主模型接口和本文简化的决策接口是两种协议，不能直接把普通聊天接口 URL 填到 `DECISION_ENDPOINT`。

如果没有专用服务，可以先用一个小模型实现服务端适配：接收 `state` 和候选描述，要求模型输出结构化评分，校验后转成 `scores`。也可以在进程内实现同样的 `score()` 接口，并通过一个简单的接口类型替换客户端依赖。两种方式都要单独评估评分质量。

本例只实现了异步模型调用钩子，因此通过 `ainvoke()` 运行。项目若使用同步 `invoke()`，应另外实现 `wrap_model_call()` 和对应的同步评分客户端，不能直接假定同步链路会执行这个异步钩子。

## 6. 把一次请求和所有变量对起来

这一节先手动代入，再通过不联网的测试验证规则。

### 6.1 数据如何传递

用户输入：

```text
查询昨天的发电量，并导出报表
```

中间件进入时，注册的工具有：

```text
current_time
query_generation
query_profit
query_weather
export_report
```

`current_time` 属于核心工具。其余四个成为 `candidates`，刚好达到 `tool_min_count=4`，因此提交评分。

| 变量 | 本例内容 | 意义 |
| --- | --- | --- |
| `candidate_ids` | 五个已注册工具的名称 | 筛选函数要处理的当前完整集合，含核心工具 |
| `candidates` | 四个非核心工具的 ID 和描述 | 发送到评分服务的候选项 |
| `asked_ids` | 四个非核心工具名称 | 本次确实提交评分的集合 |
| `scores` | 四个名称对应的有效分数 | 客户端解析后的评分 |
| `selected` | `query_generation`、`export_report` | 按评分选出的工具 |
| `kept` | 上述两个工具加 `current_time` | 本次交给主模型的工具名称集合 |

这里 `candidate_ids` 是筛选函数的完整输入，与服务端 `candidates` 的非核心候选范围不同。拆开命名是为了把“当前有哪些工具”和“本次给哪些工具评分”分别记录。

主模型收到这三个工具后，还要通过工具确认日期，生成类似下面的业务参数：

```json
{"day": "2026-11-13"}
```

这里假设北京时间为 2026 年 11 月 14 日。“昨天”的换算由运行时日期决定，不能把这个日期硬编码到业务逻辑里。

查询工具返回演示发电量 `1250.0 MWh` 后，主模型再生成导出参数：

```json
{"day": "2026-11-13", "generation_mwh": 1250.0}
```

决策层给出了可用能力范围；具体日期和导出内容来自主模型结合工具结果进行处理。

### 6.2 低分、缺分、未询问如何处理

| 情况 | 示例 | 本例处理 |
| --- | --- | --- |
| 已评分且高分 | 查询发电量 `0.98` | 达到阈值且在数量限制内则保留 |
| 已评分且低分 | 查询利润 `0.06` | 本次隐藏 |
| 已询问但缺分 | 服务没有返回天气工具分数 | 保留这个缺分工具 |
| 没有提交评分 | 核心时间工具，或将来因预算未询问的工具 | 保留 |
| 整个请求失败 | 超时、HTTP 错误、响应结构无效 | 使用进入中间件时的工具集合 |
| 所有非核心工具都有有效低分 | 四个工具全部低于阈值 | 仅保留核心工具 |

“全部有效低分”和“没有分数”表达的是不同情况。前者有明确的否定判断，后者缺少判断依据。

这里采用“缺谁保留谁”的策略。另一种更保守的实现是，只要有一个候选缺分，就让本次筛选整体回退。两者都可以，关键是通过测试固定语义，不要把缺分默认当作 `0` 分。

### 6.3 `tests/test_decision.py`：无需模型和网络的验证

文件：`tests/test_decision.py`（[下载此文件](/blogs/agent-decision-model-integration/code/tests/test_decision.py)）

```python
from __future__ import annotations

import json

import httpx
import pytest

from agent_demo.decision.client import DecisionClient
from agent_demo.decision.config import DecisionConfig
from agent_demo.decision.select import Candidate, select_tool_names


def make_config() -> DecisionConfig:
    return DecisionConfig(endpoint="https://decision.example.com/score")


def test_high_scores_and_core_are_kept() -> None:
    kept = select_tool_names(
        ["current_time", "query_generation", "query_profit", "export_report"],
        {"query_generation", "query_profit", "export_report"},
        {"query_generation": 0.98, "query_profit": 0.06, "export_report": 0.93},
        make_config(),
    )
    assert kept == {"current_time", "query_generation", "export_report"}


def test_missing_and_unasked_tools_are_kept() -> None:
    kept = select_tool_names(
        ["current_time", "query_generation", "query_profit", "export_report"],
        {"query_generation", "query_profit"},
        {"query_generation": 0.1},
        make_config(),
    )
    assert kept == {"current_time", "query_profit", "export_report"}


def test_fully_scored_low_scores_leave_only_core() -> None:
    kept = select_tool_names(
        ["current_time", "query_generation", "query_profit"],
        {"query_generation", "query_profit"},
        {"query_generation": 0.1, "query_profit": 0.2},
        make_config(),
    )
    assert kept == {"current_time"}


@pytest.mark.asyncio
async def test_client_filters_invalid_and_unknown_scores() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["state"] == "查询发电量"
        assert [item["id"] for item in body["candidates"]] == ["a", "b", "c"]
        return httpx.Response(
            200,
            json={"scores": {"a": 0.98, "b": True, "c": 1.2, "unknown": 0.99}},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as http:
        scores = await DecisionClient(http, make_config()).score(
            "查询发电量",
            [Candidate("a", "查询"), Candidate("b", "利润"), Candidate("c", "天气")],
        )
    assert scores == {"a": 0.98}
```

运行：

```bash
python -m pytest tests/test_decision.py -q
```

这些测试验证本地规则和协议解析，不会访问示例域名，也不能证明远程决策模型的相关性判断正确。下一阶段应另外验证：评分失败后主模型仍被调用、筛选结果确实传到模型请求、工具执行循环正常、相同 Agent 的并发请求不会混用选择结果。

## 7. 从演示走向实际项目，还需要考虑什么

### 7.1 核心工具要由业务决定

本例始终保留 `current_time`，是因为演示需要处理相对日期。其他系统可能需要保留文件读取、检索入口或人工确认工具。

“核心工具”表示系统认为它必须可用，不代表它永远安全、永远有权限，或者每个项目都应该保留。实际执行时仍要检查调用权限、资源范围和必要的审批条件。

### 7.2 不要遗漏任务后续需要的工具

如果只问决策模型“下一步马上用什么工具”，它可能只保留发电量查询，排除导出工具。

本文把评分问题定义为“完成整个任务可能需要什么”，包含后续步骤依赖。即使如此，也可能误删工具。可以用多步骤任务评测，必要时加入工具依赖规则，或者在任务阶段变化后重新评分。

### 7.3 决策次数要受控，缓存要按请求隔离

基础示例每次主模型调用前都评分，查询时间、查询数据、导出结果后都会再次经过决策环节。

一种改进方式是首次评分后，在同一轮任务内复用选择结果；当目标、关键结果或工具目录发生变化时再失效。缓存至少应绑定请求或会话轮次、候选目录版本和相关上下文，避免把一个用户的选择结果复用到另一个用户。

不能简单在中间件上放一个全局 `last_selected`：同一个 Agent 实例可能同时服务多个请求。

### 7.4 工具太多时，可以先缩小评分候选

假设系统有上千个工具，逐个提交给评分服务也会带来开销。可以先按工具类别、关键词或检索结果召回一个候选集合，再对召回结果评分。

![大规模工具目录的召回与评分流程](/blogs/agent-decision-model-integration/shortlist.png)

[查看这张图的 Mermaid 源文件](/blogs/agent-decision-model-integration/shortlist.mmd)

这会出现一个新的选择：未进入召回集合的工具怎么处理？本文基础规则保留所有未询问项，因而无法靠它直接压缩上千个工具。要获得收益，需要另行设计目录检索入口、按需扩展机制，或者验证可接受的召回淘汰策略，不能静默改变“未询问工具保留”的含义。

### 7.5 动态工具目录可能影响提示缓存

基础方案直接改变主模型请求中的 `tools`。实现简单，但可能改变服务商用于缓存匹配的请求前缀。是否影响缓存、影响多少，取决于模型服务的缓存机制，应以实际请求的缓存命中和计费数据为准。

更进一步，可以保持核心工具和一个固定的调度工具，把选中的长尾工具目录放到本轮上下文中。主模型通过调度工具指明目标和参数，运行时再转发到真实工具。

这种方式增加了参数验证、错误映射、可观测性和权限检查的复杂度；移动目录内容本身也不会自动减少 token。目录压缩、按需加载和缓存收益需要分别测量。基础版本稳定后，再决定是否引入。

### 7.6 失败回退和性能数据要看得到

至少记录以下指标即可开始排查：

| 指标 | 用途 |
| --- | --- |
| 候选数量、有效评分数量、最终保留数量 | 判断筛选是否真正发生，缺分是否太多 |
| 决策耗时、超时率、回退率 | 判断新增环节是否影响用户等待 |
| 必要工具保留率 | 判断是否误删完成任务所需能力 |
| 任务成功率、实际工具调用及错误率 | 判断筛选后业务表现是否改善 |
| 总输入输出 token、缓存命中、总费用 | 判断收益是否覆盖新增调用成本 |

日志默认记录数量、耗时和错误类别即可。是否记录工具名称和上下文，要根据业务数据敏感程度决定；不要把密钥和完整用户数据直接写入普通日志。

## 8. 怎么判断值不值得使用

评估时，不要只看“工具从 80 个减少到 8 个”，还要看必要工具是否被误删、最终任务是否成功。

可以准备一批真实任务，至少包括：单工具任务、多步骤任务、相似工具区分、不需要任何工具、包含省略指代的多轮追问，以及评分服务超时和缺分的情况。

对同一批任务，比较以下方案：

1. 直接向主模型提供当前完整工具集合。
2. 用规则或检索缩小目录。
3. 加入决策模型筛选。

主模型配置、工具定义和评测条件尽量保持一致，多次运行并报告波动。表格可以先留作实际测量记录：

| 指标 | 完整目录 | 规则或检索筛选 | 决策模型筛选 |
| --- | --- | --- | --- |
| 任务成功率 | 实测填入 | 实测填入 | 实测填入 |
| 必要工具保留率 | 基准目录包含情况 | 实测填入 | 实测填入 |
| 端到端耗时 P50 / P95 | 实测填入 | 实测填入 | 实测填入 |
| 平均模型与决策总费用 | 实测填入 | 实测填入 | 实测填入 |
| 错误工具调用次数 | 实测填入 | 实测填入 | 实测填入 |

一次请求的成本大致变成：

```text
接入后总费用
= 决策调用费用
+ 筛选后所有主模型调用费用
+ 工具与基础设施费用
```

端到端延迟则要累计关键路径上的实际调用。决策服务更快、目录更小，都不能单独保证总时间更短；增加评分次数、缓存命中下降或者错误重试，都可能抵消收益。

当工具目录规模较大，规则筛选维护困难，并且实际评测显示任务质量或总成本有所改善时，决策层有明确价值。工具少、调用稳定、延迟预算紧张，或误删工具的代价较高时，可以继续采用完整目录，或先用更简单的规则方案。

## 9. 同一套思路如何扩展到技能和协作 Agent

工具筛选跑通后，可以将候选项换成其他能力目录，但不同能力的应用方式要单独实现。

| 候选类型 | 评分对象 | 筛选结果作用于哪里 |
| --- | --- | --- |
| 工具 | 名称、用途、必要时的参数摘要 | 当前模型请求的可用工具集合 |
| 技能 | 技能简介、适用场景 | 本轮展示或加载的技能目录 |
| 协作 Agent | 成员能力、职责范围 | 本轮可推荐或派工的成员集合 |
| 结果充分性 | 任务目标与已有结果 | 是否提示主模型继续补充工作 |

例如，用户要求“分析发电量下降原因”，可以先筛选数据分析和设备诊断成员，再由主模型决定派工顺序。成员返回结果后，再判断信息是否足以支撑结论。

能力相关性评分不等于完整工作流编排，也不意味着可以把某个分数直接变成永久停止条件。是否继续执行、是否需要人工确认，以及什么算任务成功，仍应由明确的业务规则和运行时约束共同决定。

项目的第一步可以很小：保留业务工具，把评分请求封装到客户端，把保留规则写成纯函数，再通过模型调用中间件连接起来。等到实际评测表明这层筛选有价值，再逐步引入候选召回、轮内复用和延迟加载。

## 参考资料

- [LangChain：工具定义与动态工具选择](https://docs.langchain.com/oss/python/langchain/tools)
- [LangChain：自定义中间件与模型调用钩子](https://docs.langchain.com/oss/python/langchain/middleware/custom)
- [LangChain：Agent 的创建和模型工具循环](https://docs.langchain.com/oss/python/langchain/agents)
- [Mermaid：流程图语法](https://mermaid.js.org/syntax/flowchart.html)
- [Mermaid：时序图语法](https://mermaid.js.org/syntax/sequenceDiagram.html)
