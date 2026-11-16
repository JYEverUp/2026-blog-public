在做电力 Agent 项目时，我关心的不只是模型能不能查出发电量、生成一份日报，还包括它准备覆盖文件、发布报表、提交工单时，程序能不能先停下来，让业务人员核对这次具体操作。

例如用户说：“查询昨天的发电量，重新生成日报，把旧版本处理掉，再发布出去。”这句话里同时包含查询、生成、清理和发布。查询通常可以自动进行，但“旧版本是哪份、是否覆盖正式报表、发布到哪里”，不能仅凭模型的一次理解就直接执行。

这篇文章沿着这个场景，解释为什么需要工具审核、为什么分成两种触发方式，以及程序如何暂停、等待决定、继续执行。代码整理成独立的 Python 示例，可以离线验证，不依赖某个业务平台的内部封装。

文中的厂站、日期、发电量和业务工具名称均用于演示；示例聚焦查询、报表与工单，不涉及设备控制。下文的“最简单方案”用于比较设计取舍，不代表某个生产系统的真实改造时间线。

## 1. 一开始，为什么可以不加人工审核

假设最简单的电力业务助手只有三个工具：

| 工具                | 作用                       |
| ------------------- | -------------------------- |
| `query_generation`  | 查询指定厂站、日期的发电量 |
| `query_unit_status` | 查询机组状态               |
| `export_report`     | 生成供用户下载的报表副本   |

用户提出问题，主模型选择工具、生成参数，执行器运行工具，再把结果交回模型。这条链路比较直接。

![基础版本中的工具调用循环](/blogs/power-agent-tool-approval/baseline.png)

[查看大图](/blogs/power-agent-tool-approval/baseline.svg) · [下载 Mermaid 源文件](/blogs/power-agent-tool-approval/baseline.mmd)

例如，一次查询可以表达为：

```python
# 工具调用示意，不是可直接运行的业务接口。
query_generation(plant_id="plant-demo", date="2026-11-14")
```

如果工具只读数据，或者只在隔离目录中生成新文件，自动执行通常能减少等待。每一次查询都要求点击确认，会把普通的数据分析变成繁琐的交互。

所以，增加审核的理由并不是“Agent 必须每一步都问人”，而是工具权限和动作影响范围发生了变化。

### 1.1 当工具开始写入业务系统，问题就不同了

随着项目扩展，可能接入这些能力：

| 新能力       | 可能产生的影响                     | 值得核对的内容                 |
| ------------ | ---------------------------------- | ------------------------------ |
| 覆盖已有日报 | 原来的人工修订可能丢失             | 厂站、日期、文件版本、是否覆盖 |
| 发布报表     | 其他用户可能开始使用这份数据       | 发布范围、报表版本、数据口径   |
| 提交检修工单 | 进入实际业务处理流程               | 设备标识、问题描述、提交目标   |
| 执行 Shell   | 同一个入口可以查看、移动或删除文件 | 命令参数、目标路径、风险原因   |

模型提出一个工具调用，只说明它认为这一步有助于完成任务。用户最初的自然语言指令，未必已经授权了模型最终生成的所有参数。

例如，“重新生成日报”可以是生成一个新副本，也可以是覆盖正式文件；“把旧版本处理掉”可以是归档，也可以是删除。这些差异发生在具体动作上。

如果程序直接执行，事后再提示“已覆盖”，业务人员就失去了最后核对的机会。

## 2. 为什么不是在提示词里写一句“危险操作先确认”

提示词可以引导模型先问，但它仍然依赖模型遵守约定。模型可能漏问，也可能把用户的一句“可以”理解成对后续所有操作的许可。

审核机制要把这件事放进必经的执行路径：模型先提出调用，程序按配置检查，需要确认时就暂停。即使模型没有主动提问，真实工具也不能越过这一步。

几种常见方案各有适用范围：

| 方案                     | 能解决什么                      | 局限                                   |
| ------------------------ | ------------------------------- | -------------------------------------- |
| 只靠提示词提醒           | 让模型更倾向于主动确认          | 缺少执行器层面的强制检查               |
| 执行后记录日志           | 便于追踪调用和结果              | 无法阻止已经发生的覆盖或发布           |
| 所有工具都人工确认       | 控制规则直观                    | 查询和中间步骤也会频繁打断用户         |
| 只扫描危险命令           | 细分同一个 Shell 工具的不同风险 | 无法自动理解发布报表等业务语义         |
| 工具名审核与参数检查结合 | 分别控制业务动作和命令风险      | 要明确两层职责，以及重复审核的处理方式 |

对电力 Agent 来说，更有用的划分是：业务工具按动作类别控制，通用执行入口按具体参数检查，另外保留独立的权限边界。

## 3. 整体设计：模型提出动作，程序决定是否进入审核

先把职责放在一张图里。

![电力 Agent 的工具审核与宿主职责](/blogs/power-agent-tool-approval/architecture.png)

[查看大图](/blogs/power-agent-tool-approval/architecture.svg) · [下载 Mermaid 源文件](/blogs/power-agent-tool-approval/architecture.mmd)

图中展示的是职责关系，不是要求所有框架必须按同一顺序装配中间件。

| 环节                  | 负责什么                                       |
| --------------------- | ---------------------------------------------- |
| 主模型                | 结合任务生成工具名与参数                       |
| 权限边界              | 判断当前用户能否访问厂站、工具、路径或业务对象 |
| 工具名审核            | 某类工具每次调用都需要人工确认                 |
| 命令风险检查          | 扫描适用工具的参数，决定放行、告警、阻止或审核 |
| 审核界面              | 展示具体动作、风险原因，收集用户决定           |
| 运行图与 checkpointer | 保存暂停状态，按会话恢复执行                   |
| 业务接口              | 再次落实对象权限、参数校验和写入约束           |

权限与审核需要分清。假设某用户没有 A 厂的数据发布权限，审核界面中的“批准”不能给他新增这项权限。审核表达的是对一个允许进入确认流程的具体动作作出决定。

同样，前一篇文章讨论的[决策模型筛选](/blog/agent-decision-model-integration)解决“本轮让模型看到哪些能力”；这里的审核解决“模型已经提出调用后，这个动作能否继续”。两个环节可以同时存在。

## 4. 第一种触发方式：按工具名称审核

### 4.1 哪些动作适合按名称审核

例如发布正式报表和提交工单，都可以通过专门的业务工具完成：

```python
# 工具调用示意，参数只用于说明审核内容。
publish_report(
    plant_id="plant-demo",
    report_date="2026-11-14",
    report_version="v3",
)
```

这类调用是否需要确认，可以由工具名直接决定。程序不必先尝试从参数字符串中猜测“发布”是什么意思。

一个简化的策略对象如下，完整版本包含在文末的离线代码文件中：

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ApprovalPolicy:
    enabled: bool = False
    tools: frozenset[str] = frozenset({
        "publish_report",
        "submit_maintenance_ticket",
    })

    def to_interrupt_on(self) -> dict[str, Any]:
        if not self.enabled:
            return {}
        return {
            name: {"allowed_decisions": ["approve", "reject"]}
            for name in sorted(self.tools)
        }
```

开启策略后，它会生成：

```python
{
    "publish_report": {"allowed_decisions": ["approve", "reject"]},
    "submit_maintenance_ticket": {"allowed_decisions": ["approve", "reject"]},
}
```

这里的名称是匹配条件，不会自动创建这些业务工具。工具要先注册，模型实际提出了对应调用，审核才可能发生。

### 4.2 使用 LangChain 时怎样装配

如果项目使用 LangChain 的 `create_agent()`，可以把生成的配置交给 `HumanInTheLoopMiddleware`：

```python
from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver


def build_agent(model: Any, business_tools: list[Any]):
    # model 和 business_tools 由宿主注入；这里不配置真实模型凭据。
    return create_agent(
        model=model,
        tools=business_tools,
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "publish_report": {
                        "allowed_decisions": ["approve", "reject"]
                    },
                    "submit_maintenance_ticket": {
                        "allowed_decisions": ["approve", "reject"]
                    },
                }
            )
        ],
        checkpointer=InMemorySaver(),
    )
```

这是装配函数，需要注入真实模型与已定义工具。中间件检查模型提出的工具调用，并在执行前请求外部决定。框架还支持 `edit`、`respond`，具体可用决定由每个工具的配置限制。[LangChain HITL 说明](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)

这个配置没有命令参数扫描；第二层检查需要另外接入。

### 4.3 这一层的粒度是什么

如果把 `execute` 放入审核名单，那么：

```python
execute(command="ls reports")
execute(command="rm reports/old.csv")
```

两条调用都会暂停。程序的依据是工具名，没有在这一层区分“查看目录”和“删除文件”。

因此，对明确的业务动作按名称审核比较直观；如果希望普通 Shell 查询自动通过，就需要更细的参数检查。

## 5. 第二种触发方式：参数命中风险规则才审核

### 5.1 工具名一样，具体操作可能完全不同

对于 `execute`、`bash` 这类通用入口，可以扫描 `command` 参数。例如，用一条规则表达删除命令：

```yaml
- id: remove_files
  tools: [bash, execute]
  params: [command]
  severity: HIGH
  patterns:
    - "\\b(rm|del|Remove-Item)\\b"
  description: '命令包含文件删除操作'
```

这是示例规则格式，不是某个框架自带的通用配置协议。使用它需要自己实现加载和匹配逻辑。文末代码为减少依赖，直接使用 Python 数据类保存两条规则。

风险发现至少应包含规则标识、等级、原因以及命中工具，供界面解释为什么暂停。不要只给业务人员一个没有上下文的“是否允许”。

### 5.2 命中规则之后，还要看运行模式

| 模式               | 本文示例的行为                  | 会不会出现人工审核 |
| ------------------ | ------------------------------- | ------------------ |
| `warn`             | 记录风险信息并继续              | 不会               |
| `block`            | HIGH、CRITICAL 直接阻止         | 不会               |
| `require_approval` | MEDIUM、HIGH、CRITICAL 等待决定 | 会                 |

这套等级阈值是本文示例的设计，可以按业务需要调整。规则说明文字不会自动改变模式，例如建议里写了“确认后删除”，程序仍然要有实际进入审核的分支。

两种触发方式合在一起，就是下面这条链路：

![工具名审核和命令参数审核的分支](/blogs/power-agent-tool-approval/triggers.png)

[查看大图](/blogs/power-agent-tool-approval/triggers.svg) · [下载 Mermaid 源文件](/blogs/power-agent-tool-approval/triggers.mmd)

注意这两个开关相互独立。工具名审核关闭，不代表风险命令就不会进入人工审核；命令检查使用 `warn`，也不代表发布工具能跳过自己的工具名审核。

### 5.3 真正暂停的位置

下面是完整示例中的审核函数，依赖同文件定义的 `Action` 和 `make_review()`：

```python
def ask_approval(action: Action, description: str) -> bool:
    response = interrupt(make_review(action, description))
    decision = response["decisions"][0]
    if decision["type"] not in {"approve", "reject"}:
        raise ValueError("此示例仅接受 approve 或 reject")
    return decision["type"] == "approve"
```

`interrupt()` 接收可以序列化的请求内容，暂停运行图并把请求交回调用方。恢复时，宿主提交的值才会成为这次 `interrupt()` 的返回值。这是 LangGraph 提供的动态中断机制。[中断与恢复说明](https://docs.langchain.com/oss/python/langgraph/interrupts)

参数检查节点据此作出分支选择：

```python
# 节选自 approval_demo.py 的 command_review()。
findings = scan_command(action)
risky = [rule for rule in findings if rule.severity in THRESHOLDS[mode]]

if mode == "block" and risky:
    return Command(update={"result": "风险规则直接阻止"}, goto=END)

if mode == "require_approval" and risky:
    description = "；".join(
        f"[{rule.severity}] {rule.description}" for rule in risky
    )
    if not ask_approval(action, description):
        return Command(update={"result": "用户拒绝风险命令"}, goto=END)
```

完整文件将工具名审核、参数审核和模拟执行分成独立节点。被拒绝的分支直接结束本次调用，不会进入实际执行节点。真实 Agent 可以把拒绝转换成工具错误结果，交回主模型解释或调整方案。

### 5.4 规则检查的边界

这里用的是正则匹配，没有再调用一个模型来理解命令的全部含义。合法的删除也可能命中；间接脚本或规则未覆盖的写法也可能漏报。

而且这类命令规则只作用于指定工具和参数，不能自动保护 `publish_report` 这样的业务接口。它适合补充风险提示，不能代替业务鉴权、路径限制和必要的运行隔离。

## 6. 触发以后，审核界面和后端怎样配合

### 6.1 把“问用户”变成一次可恢复的执行状态

如果只让模型回复“是否发布？”，后端仍然需要自己判断下一条消息是批准、补充需求还是另一个问题，也需要知道批准的是哪一份报表。

结构化暂停可以保留待执行动作和参数，把后续决定明确绑定到这个等待点。

![一次日报发布审核的交互时序](/blogs/power-agent-tool-approval/sequence.png)

[查看大图](/blogs/power-agent-tool-approval/sequence.svg) · [下载 Mermaid 源文件](/blogs/power-agent-tool-approval/sequence.mmd)

本文的请求结构沿用常见的动作审核形式：

```json
{
	"action_requests": [
		{
			"name": "publish_report",
			"args": {
				"plant_id": "plant-demo",
				"report_date": "2026-11-14",
				"report_version": "v3"
			},
			"description": "发布正式日报，需要核对厂站、日期与版本。"
		}
	],
	"review_configs": [
		{
			"action_name": "publish_report",
			"allowed_decisions": ["approve", "reject"]
		}
	]
}
```

`action_requests` 回答“准备做什么”；`review_configs` 回答“允许怎样处理”。界面可以把参数转换成中文字段，展示厂站、业务日期、版本和覆盖关系，而不是只显示一个工具名称。

### 6.2 `hitl_required` 从哪里来

`hitl_required` 可以作为宿主约定的事件名称，它不是 LangGraph 原始更新的固定名称。直接使用本示例的 `graph.invoke()` 时，中断在结果的 `__interrupt__` 中。

宿主可以对外转换成：

```python
# 事件投影示意：result 来自当前 graph.invoke() 的返回值。
for item in result.get("__interrupt__", ()):
    event = {"type": "hitl_required", "request": item.value}
    # 由宿主将 event 发往当前会话的界面。
```

采用流式接口时，也需要按所选协议转换内部中断，再交给前端消费。一次请求可能包含多个待审核动作，界面应逐项展示；本文的离线示例每次只处理一个动作。

### 6.3 批准与拒绝怎样恢复

在已经创建 `graph` 的宿主函数中，使用原会话配置恢复：

```python
from langgraph.types import Command

config = {"configurable": {"thread_id": "daily-report-session-demo"}}

result = graph.invoke(
    Command(resume={"decisions": [{"type": "approve"}]}),
    config=config,
)
```

拒绝则提交 `{"type": "reject"}`。本文示例只处理批准或拒绝，没有实现 `edit`、`respond`；使用支持这些决定的框架中间件时，也应以当前审核配置为准。

批准只放行当前等待的动作，不会永久信任这个工具。拒绝只表示当前调用不执行，也不自动等同于取消整个分析任务。

### 6.4 为什么必须保留相同的 `thread_id`

运行时需要知道恢复哪一个执行现场。checkpointer 保存会话运行状态，`thread_id` 用来定位对应会话。[LangGraph 持久化说明](https://docs.langchain.com/oss/python/langgraph/persistence)

![一次工具调用从计划到暂停、恢复和结束的状态](/blogs/power-agent-tool-approval/states.png)

[查看大图](/blogs/power-agent-tool-approval/states.svg) · [下载 Mermaid 源文件](/blogs/power-agent-tool-approval/states.mmd)

本文使用 `InMemorySaver` 做离线演示，进程退出后不会保留这些 checkpoint。生产环境需要选择合适的持久化实现，并由宿主保存审核者、会话归属、原用户身份和待审动作信息。

仅凭前端传了一个 `thread_id`，不能判断调用者有权恢复它。后端应先校验用户身份和权限，再恢复对应动作。

## 7. 为什么同一条操作可能弹出两次审核

假设同时配置：

```text
工具名审核：每次 execute 调用都需要确认
参数风险检查：require_approval
```

当模型提出删除历史报表的命令时，可能出现下面的流程：

![同一次删除调用依次触发两层审核](/blogs/power-agent-tool-approval/double-review.png)

[查看大图](/blogs/power-agent-tool-approval/double-review.svg) · [下载 Mermaid 源文件](/blogs/power-agent-tool-approval/double-review.mmd)

第一次批准通过工具类别关卡，第二次暂停来自具体命令风险。两个关卡没有共享“一次批准后全部放行”的隐含规则。

对本文的电力业务示例，可以采取这样的职责分配：

| 能力                     | 示例策略                             |
| ------------------------ | ------------------------------------ |
| 查询发电量、读取日报     | 在已有数据权限内自动执行             |
| 生成新报表副本           | 按目标目录和覆盖规则决定是否需要确认 |
| 发布正式报表、提交工单   | 按业务工具名审核                     |
| Shell 中的删除或覆盖动作 | 按参数规则进入审核或直接阻止         |

这只是示例分工，不是对所有电力业务的统一要求。若确实需要多层审核，界面应该分别解释两次暂停的原因；若要合并展示，则需要额外设计决定与检查结果的绑定，不能简单跳过后一层。

## 8. 代码怎样组织，才能避免到处写确认逻辑

业务工具内部不宜各自维护一套弹窗和等待流程。查询、发布、提交工单的业务函数可以保持清晰，审核统一由运行时与宿主协作完成。

建议按职责拆分：

```text
power_agent/
├── tools.py          # 业务查询、报表、工单工具
├── policy.py         # 工具名审核配置、模式与阈值
├── rules.yaml        # 参数规则及风险说明
├── guard.py          # 参数扫描与风险结果
├── bootstrap.py      # 装配模型、工具、中间件与 checkpointer
└── host.py           # 鉴权、事件交付、审核决定与恢复
```

这是建议目录，不表示读者必须采用相同的模块名称。本文的可运行示例把相关逻辑合在一个文件，便于先验证执行关系。

![审核代码的职责与依赖关系](/blogs/power-agent-tool-approval/modules.png)

[查看大图](/blogs/power-agent-tool-approval/modules.svg) · [下载 Mermaid 源文件](/blogs/power-agent-tool-approval/modules.mmd)

需要配置变化时，可以在装配阶段构造新的策略和运行图。已有审核等待时，应先明确策略版本与待审动作如何衔接，避免界面仍显示旧参数，恢复端却执行了新动作。

### 8.1 两种常用配置

只让高影响业务工具进入工具名审核：

```python
# ApprovalPolicy 来自随文的 approval_demo.py。
policy = ApprovalPolicy(
    enabled=True,
    tools=frozenset({"publish_report", "submit_maintenance_ticket"}),
)
mode = "warn"
```

只演示风险命令触发审核：

```python
policy = ApprovalPolicy(enabled=False)
mode = "require_approval"
```

第二段里关闭的只是工具名审核；参数规则仍然能暂停执行。本文示例默认关闭工具名审核，命令模式由 `build_graph(policy, mode)` 显式传入，不依赖隐藏的全局开关。

### 8.2 正常提问也可以使用中断，但含义不同

模型问“日报按自然日还是运行日统计”，是在收集缺失条件；询问“是否批准覆盖这份文件”，是在核对具体动作。

二者可以共用暂停技术，但界面和决定类型应区分。采用框架的 `respond` 决定时，通常表示由用户回答来代替工具结果，不应把它当成拒绝一个写入操作。

## 9. 一个真实容易踩到的点：恢复并不只是从下一行接着跑

调用 `interrupt()` 的节点在恢复时会重新进入，节点内中断之前的代码可能再次运行。因此，把真实业务写入放在中断前面，既可能先写后审，也可能产生重复副作用。

![审核节点恢复时重新进入与副作用边界](/blogs/power-agent-tool-approval/replay.png)

[查看大图](/blogs/power-agent-tool-approval/replay.svg) · [下载 Mermaid 源文件](/blogs/power-agent-tool-approval/replay.mmd)

下面这种写法会先提交工单，之后才请求审核：

```python
# 反例：教学伪代码，请勿按这个顺序接入业务写入。
ticket_id = submit_maintenance_ticket(args)
decision = interrupt({"ticket_id": ticket_id})
```

更合理的结构是先构造待审动作，取得决定，再进入执行节点：

```python
# 顺序示意，完整可运行版本见随文文件。
decision = interrupt(review_request)
if decision["decisions"][0]["type"] == "approve":
    result = execute_business_action(action)
```

“放在批准之后”也不能单独保证业务写入只发生一次。提交工单、发布报表这类接口仍应结合业务幂等标识和持久化结果，处理恢复、重试或网络异常导致的重复请求。

如果审核期间报表已经被他人修改，还要重新核对版本。用户批准的是某个版本的动作，不能在后台静默替换成另一份内容后继续执行。这是业务一致性问题，正则扫描和普通批准按钮都不会自动解决它。

### 9.1 文件硬拒绝与初始化豁免分别怎么处理

如果某条路径已经被权限配置明确禁止，就应直接返回拒绝，避免先展示一个批准后也无法执行的审核。文件工具的路径检查不能被当成对任意 Shell 命令中所有文件访问的完整检查。

初始化工作区时，自动写入模板可能不适合逐个打断用户。若项目需要豁免，应在装配阶段限定初始化工具、目标目录与生效范围；不要把“处于初始化”变成关闭全部检查的理由。本文的离线示例没有加入这项豁免。

## 10. 下载代码，先离线验证暂停和恢复

[下载完整 Python 示例](/blogs/power-agent-tool-approval/approval_demo.py)。文件使用 Python 3.12 和 LangGraph 1.x，只用模拟工具返回结果，不调用模型、不执行 Shell，也不连接业务系统。

代码核对环境为 Python 3.12、`langgraph==1.2.11`、`langchain==1.4.3`；离线示例只需要 LangGraph，装配 LangChain 中间件时才需要 LangChain。

保存文件后运行：

```bash
python -m pip install 'langgraph>=1.0,<2.0'
python approval_demo.py
```

示例使用一个预先构造的 `Action` 代替模型输出，把“模型是否选对工具”与“审核是否阻止执行”分开验证。真实接入时，用模型生成的工具调用进入对应检查位置即可。

其中一个完整的暂停与恢复片段如下，依赖该文件中的构建函数：

```python
from approval_demo import ApprovalPolicy, build_graph, resume, start

graph = build_graph(ApprovalPolicy(enabled=True), "warn")
action = {
    "name": "publish_report",
    "args": {"report_id": "daily-demo"},
}

paused = start(graph, action, "daily-demo-session")
assert paused["__interrupt__"]
assert paused["executed"] == []

finished = resume(graph, "daily-demo-session", "approve")
assert finished["executed"] == ["publish_report"]
```

代码内验证九个场景：

| 场景                 | 验证的可观察结果                       |
| -------------------- | -------------------------------------- |
| 普通业务查询         | 不暂停，查询工具进入执行记录           |
| 发布工具等待批准     | 暂停前执行记录为空，批准后才执行       |
| 拒绝发布             | 执行记录保持为空                       |
| 风险命令获批         | 命中规则后先暂停，批准后执行模拟工具   |
| `warn` 模式          | 有风险记录，但不暂停                   |
| `block` 模式         | 直接阻止，不产生人工审核等待           |
| 拒绝风险命令         | 模拟工具未执行                         |
| 同一调用经过两层审核 | 第一次批准后仍不执行，第二次批准后执行 |
| 两个会话分别等待     | 批准 A 不会执行 B；B 可以独立拒绝      |

通过后会输出：

```text
9 个离线审核场景通过；未执行 Shell、模型请求或真实业务写入。
```

这个示例验证的是审核控制流。真实接入还需要验证业务对象权限、版本校验、持久化、重试与幂等，不能把模拟函数返回“发布完成”当成对实际报表系统的验证。

## 11. 电力业务里，审核界面应该让人看见什么

一个有效的审核请求，需要让业务人员知道自己正在批准哪个动作。例如发布日报，可以展示：

| 展示项     | 示例内容                   |
| ---------- | -------------------------- |
| 操作       | 发布正式日报               |
| 厂站       | 演示厂站                   |
| 业务日期   | 2026-11-14                 |
| 当前版本   | v2                         |
| 待发布版本 | v3                         |
| 影响范围   | 业务平台中的指定报表       |
| 触发原因   | 发布工具按策略要求人工确认 |

删除报表则应突出目标清单和删除原因。提交工单则应展示设备标识、缺陷内容和接收范围。字段来自业务工具及宿主，不应让模型自由编造审核对象的身份或权限。

当用户拒绝时，保留具体原因，让模型能够说明下一步，例如先列出待清理文件、生成一个新副本，或者等待业务人员补充条件。这样，审核既能拦住不合适的动作，也能把任务带回可继续处理的状态。

### 参考资料

- [LangChain：Human-in-the-loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)
- [LangGraph：Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [LangGraph：Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)

本文的策略对象、命令规则、业务工具名称和离线运行图是为讲解整理的独立示例；框架接口与示例约定已在相应段落分别标明。
