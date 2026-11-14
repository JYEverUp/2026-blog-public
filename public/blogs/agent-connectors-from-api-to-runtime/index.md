给客户做 Agent 系统时，接入外部系统往往比“让模型回答一句话”更花时间。

客户希望助手能查 CRM、读知识库、创建工单。模型能理解这句话，却不知道客户公司的 CRM 地址，也没有员工的访问凭据。即便接口已经调通，还要继续回答：这次使用哪个账号？允许读取哪些数据？授权过期以后怎么办？

我会把这些问题集中到连接器这一层处理。下面沿着一个售后助手的需求，讲清这层设计怎么长出来，以及代码应该怎样组织。

> 文中的客户名称、账号、地址和业务数据均为示例。代码围绕“查询客户资料”跑通最小链路，工单和知识库用于讨论扩展边界；不涉及具体客户的真实配置。

## 从一句客户需求开始

假设用户对助手说：

> 查一下远山公司的客户信息，找找相关售后处理方案，需要的话帮我建一个工单。

这句话横跨三个系统：CRM 提供客户资料，知识库提供处理方案，工单系统接收后续任务。它们可能来自不同厂商，也可能全部是客户自建的。

此时，我会先画出业务步骤：查询客户，确认具体对象，检索用户有权访问的方案，再决定是否创建工单。遇到多个同名客户，先让用户选择；创建工单需要确认时，把内容展示出来再执行。

模型负责理解需求和提出工具调用。后端负责确定身份、检查授权，并调用外部系统。这两个责任分开以后，连接器的范围才容易说清楚。

## 没有统一连接器时，以前通常怎么做

最直接的方案，是给每个接口写一个工具函数。下面这段是一个单账号、只读查询的起点，需要安装 `httpx`，地址和环境变量由部署方配置：

```python
import os

import httpx


def search_customers(query: str) -> list[dict]:
    response = httpx.get(
        f"{os.environ['CRM_BASE_URL'].rstrip('/')}/api/customers",
        params={"keyword": query},
        headers={"Authorization": f"Bearer {os.environ['CRM_TOKEN']}"},
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json()["items"]
```

再把函数包装成模型能调用的工具，第一版就能工作。只有一个内部系统、一个固定服务账号时，这种方案完全可以继续用。

传统业务系统也一直在做类似的事：调用 SDK、封装 API 客户端、写定时同步任务，或者通过集成平台统一对接。连接器沿用了这些集成经验。Agent 带来的新要求，是要把可调用能力描述给模型，并在模型提出调用以后控制实际执行。

随着需求增加，直接写函数的代价会逐渐出现。

第二个客户换了一套 CRM，查询字段和返回结构不同。第三个客户仍然用同一款 CRM，却有两个独立账号。原本放在环境变量里的一个 Token，已经表达不了“本轮应该用谁的账号”。

接着，多个 Agent 都要查客户资料。如果每个 Agent 都保存一份鉴权和字段转换代码，一次接口升级就要修改多处。更麻烦的是，凭据刷新、权限检查和日志裁剪可能在各处表现不同。

这时值得抽取的，是**一套外部能力如何被配置、授权、调用和复用的规则**。请求最终仍然通过 API 或 SDK 发出去，只是调用前后的公共责任有了明确位置。

## 先把连接器、连接实例和工具分清楚

“接了一个 CRM”这句话可能指三件不同的事。

| 概念 | 解决的问题 | 例子 |
| --- | --- | --- |
| 连接器类型 | 这一类系统怎么接 | 某款 CRM 的鉴权、查询接口和字段转换规则 |
| 连接实例 | 这一次接的是哪个地址、哪个账号 | 客户 A 的销售 CRM、客户 A 的售后 CRM |
| Agent 工具 | 模型能提出什么操作 | `search_customers`、`get_customer` |
| 本轮选择 | 当前对话允许使用哪些连接 | 只启用销售 CRM，不启用售后 CRM |

同一种连接器可以创建多个实例，一个实例可以提供多个工具。用户在界面上选择连接实例以后，后端再检查这个用户是否有权使用它。

凭据也应该有独立生命周期。连接实例可以保存一个 `credential_ref`，指向凭据服务中的记录；真正的 Token 由后端在调用时取得。这样，配置对象、工具描述和模型上下文都不用携带秘密。

我会让连接实例保持简单：

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectionInstance:
    id: str
    tenant_id: str
    kind: str
    base_url: str
    credential_ref: str
    enabled: bool = True
```

这里的 `kind` 决定使用哪种适配器，`id` 标识一次具体连接。`tenant_id` 表示归属，但仅仅有这个字段还没有实现隔离，真正执行查询前必须检查它。

## 我会怎样划分这一层的职责

![Agent 连接器的职责边界](/blogs/agent-connectors-from-api-to-runtime/architecture.svg)

[查看大图](/blogs/agent-connectors-from-api-to-runtime/architecture.svg) · [下载 Mermaid 源文件](/blogs/agent-connectors-from-api-to-runtime/architecture.mmd)

图中是逻辑职责，可以先放在同一个进程里，不要求拆成多个服务。

**应用层**处理用户登录、连接配置、授权页面和本轮选择。它知道当前用户是谁，也决定哪些连接可以进入本轮请求。

**系统适配器**理解厂商接口。它负责把 `query` 转成厂商要求的字段，组织请求，并把结果裁剪成稳定的业务结构。协议分页、字段命名和厂商错误码留在这里。

**调用入口**检查业务参数、连接归属和操作权限，再取得有效凭据并调用适配器。权限检查需要发生在实际执行时，因为工具加载以后，授权仍可能被撤销。

**Agent 运行时**接收工具定义，把可用工具交给模型，执行模型提出的调用，再把结果送回模型继续组织回答。

这种分工让变化有了明确落点：更换 CRM，主要改适配器；更换 Agent 框架，主要改工具包装与运行时接缝；增加账号，主要新增连接实例。

也要保留系统差异。有些 CRM 支持全文搜索，有些只允许精确匹配。可以先暴露厂商原生能力，只有业务确实需要跨厂商替换时，再定义共同支持的 `search_customers` 契约。统一接口应该建立在共同语义上，否则就会出现大量无法兑现的参数。

## 代码的关键：把业务参数与执行身份分开

模型可以提供客户名称、分页大小等业务参数。租户、用户和连接实例，则由后端可信上下文确定。

```python
@dataclass(frozen=True)
class RequestContext:
    tenant_id: str
    user_id: str
    selected_connections: frozenset[str]
```

这里的上下文来自已经验证的登录态和已经检查过的本轮选择。不要把客户端传来的 `tenant_id` 原样封装进去，就认为它变可信了。

以最小示例为例，连接器服务在每次执行前检查四件事：连接仍然启用、连接属于当前租户、连接被本轮选中、用户仍有这个操作的授权。

```python
def authorize(self, ctx, connection_id, action):
    instance = self.connections[connection_id]
    grant = (ctx.tenant_id, ctx.user_id, connection_id, action)
    if (
        not instance.enabled
        or instance.tenant_id != ctx.tenant_id
        or connection_id not in ctx.selected_connections
        or grant not in self.grants
    ):
        raise PermissionError("Connection or operation is not allowed")
    return instance
```

这段是配套示例的核心逻辑。示例使用内存字典和授权集合，让边界容易观察；实际项目中，它们应替换为自己的配置仓库、权限服务和凭据服务。未知连接等内部异常，也应在对外入口统一转换成合适的错误响应。

还要继续向下检查数据范围：用户能够使用一个 CRM 连接，不代表可以读取该 CRM 中的全部客户。服务账号权限过大时，需要在业务层落实行级、部门级或对象级限制。上面的最小示例没有实现这些规则。

### 适配器只处理系统差异

对于前面的 REST 查询，我会把调用整理成下面的形状。这里仍是接口示意，实际字段需要按客户系统的文档确认：

```python
class CRMAdapter:
    def search(self, instance, token, query, limit):
        response = httpx.get(
            f"{instance.base_url.rstrip('/')}/api/customers",
            params={"keyword": query, "page_size": limit},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        response.raise_for_status()
        return [
            {
                "id": str(row["id"]),
                "name": row["name"],
                "status": row["status"],
            }
            for row in response.json()["items"][:limit]
        ]
```

返回结果采用字段白名单。模型只需要客户标识、名称和状态时，就不要顺带传入完整联系方式、内部备注或原始响应头。大结果还要限制条数与总体大小，避免一次查询占满上下文。

上面的 HTTP 片段没有实现分页遍历和厂商错误分类；它们应跟随真实接口补充。请求地址应来自受控配置，连接器支持用户自填地址时，还需要按部署环境验证可访问的主机范围、重定向和目标地址。

### 调用时取凭据，避免把 Token 固定在工具里

服务层把校验和适配器连接起来：

```python
def search(self, ctx, connection_id, query, limit=10):
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 100:
        raise ValueError("query must contain 1..100 non-blank characters")
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError("limit must be an integer in 1..20")

    instance = self.authorize(ctx, connection_id, "customers:read")
    token = self.secrets[instance.credential_ref]
    adapter = self.adapters[instance.kind]
    return adapter.search(instance, token, query.strip(), limit)
```

示例中的 `self.secrets` 是一份假凭据字典。实际项目的这一行应调用凭据服务，按需解密、检查有效期并刷新授权。业务工具本身不应实现完整 OAuth 流程。

每次调用读取当前凭据，有助于避免工具创建时捕获一个即将过期的 Token。并发刷新时，还要按凭据记录协调，避免多个请求同时刷新、覆盖新的刷新令牌。授权被撤销时，应该提示重新授权，并让相关缓存失效。

## 怎么把连接器变成 Agent 能调用的工具

我会先绑定当前请求的身份和连接，只把业务参数暴露出去：

```python
def bind_search(service, ctx, connection_id):
    service.authorize(ctx, connection_id, "customers:read")

    def search_customers(query: str, limit: int = 10) -> list[dict[str, str]]:
        """按客户名称查询当前已授权 CRM，最多返回 20 条客户摘要。"""
        return service.search(ctx, connection_id, query, limit)

    return search_customers
```

创建工具时检查一次，减少无效工具进入模型；执行时再检查一次，防止授权变化后继续调用。

这里用闭包绑定一次请求，要求上下文不可变，并且每轮重新构造绑定。不要把 `current_user` 或 `current_token` 写到共享 Agent 对象的可变字段上，否则两个并发请求可能覆盖彼此的身份。需要复用长期 Agent 时，可以使用框架提供的请求上下文注入机制；LangChain 的 [`ToolRuntime` 文档](https://docs.langchain.com/oss/python/langchain/tools#access-context)说明了这类上下文如何在执行时注入工具。

下面以 LangChain 工具包装为例，增加模型可见的参数约束。它接在配套示例的 `service`、`context` 和 `bind_search` 后面运行，需要额外安装 `langchain-core`、`pydantic`：

```python
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ConfigDict, Field


class CustomerSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    query: str = Field(min_length=1, max_length=100, description="客户名称关键词")
    limit: int = Field(default=10, ge=1, le=20, description="最多返回条数")


search_tool = StructuredTool.from_function(
    func=bind_search(service, context, "crm-a"),
    name="crm_a_search_customers",
    description="查询当前所选销售 CRM 中的客户摘要；需要完整客户名称时先向用户确认。",
    args_schema=CustomerSearchInput,
)

print(search_tool.invoke({"query": "远山", "limit": 5}))
```

工具的名字、描述和 Schema 是给模型看的使用说明；函数才是实际执行入口。[LangChain 工具文档](https://docs.langchain.com/oss/python/langchain/tools#create-tools)介绍了这几个部分的作用。

多账号同时可用时，工具名称要有稳定的实例区分，描述还要说明这是哪一套业务账号。仅用一个没有含义的实例 ID，模型仍然不知道应该选销售账号还是售后账号。

模型看见的参数只有 `query` 和 `limit`。它无法通过多传一个 `connection_id` 来切换账号，额外参数会被 Schema 拒绝；服务层仍然保留自己的检查，覆盖其他调用入口。

如果使用 LangChain 的 Agent 工厂，接入位置可以简化为下面这样。此段展示装配关系，`model` 需要由应用提前创建，运行时会实际调用模型服务：

```python
from langchain.agents import create_agent

agent = create_agent(model=model, tools=[search_tool])
result = agent.invoke({
    "messages": [{"role": "user", "content": "查询远山公司的客户信息"}]
})
```

这段闭包版本适用于当前请求独享的工具与 Agent 装配。生产环境如果复用执行图，应使用按请求注入的上下文，并在执行入口重新校验权限。模型生成的是调用意图，真正的授权决定始终由后端执行。

## 已经有 MCP，为什么还要连接器

如果外部系统已经提供 MCP 服务，可以由 MCP 客户端发现工具，并建立调用包装；自己掌握的 API，也可以直接包装成本地工具。两条路线可以并存。

![本地工具与 MCP 工具的接入路径](/blogs/agent-connectors-from-api-to-runtime/tool-paths.svg)

[查看大图](/blogs/agent-connectors-from-api-to-runtime/tool-paths.svg) · [下载 Mermaid 源文件](/blogs/agent-connectors-from-api-to-runtime/tool-paths.mmd)

[MCP 的架构文档](https://modelcontextprotocol.io/docs/learn/architecture)描述了客户端、服务端，以及工具发现和调用这些协议能力。[传输规范](https://modelcontextprotocol.io/specification/latest/basic/transports)则区分了 stdio 与 Streamable HTTP 等传输方式。

所以，“远程服务”“本地子进程”和“应用自己的内部 MCP 服务”主要说明连接目标与部署位置。内部 MCP 服务如果通过 HTTP 访问，仍然走 MCP 客户端；直接调用进程里的 Python 函数，则可以走本地工具包装。

这两条路径最后都要进入 Agent 的工具集合。不过，本地包装出来的函数不需要为了统一管理，再额外绕一遍 HTTP。

在应用产品里，连接器还需要回答：用户授权的是哪个账号、这一轮选择哪个实例、凭据何时刷新、哪些操作可以执行。MCP 为协议授权提供了机制，应用仍然需要实现自己的账号归属和业务权限规则。不能看到已经完成协议鉴权，就省略租户与对象权限检查。

我会根据实际条件选择：已有可靠 MCP 服务时复用它；客户系统只有普通 API 时先写适配器；同一套能力需要被多个 MCP 客户端使用时，再考虑在适配器外增加 MCP 服务入口。先保持内部业务调用独立，后面增加协议入口才容易复用。

## 工具装进去了，什么时候才可以使用

这里要区分三个状态。

**已经加载**表示系统知道这组工具，或者已经把工具包装放进运行时。**本轮开放**表示这些工具进入当前请求的模型可见列表。**允许执行**表示调用发生时，后端检查仍然通过。

有些工具在 Agent 创建时就能加载；有些需要等待用户选择连接、完成授权后再注入。工具集合发生变化时，某些运行时需要重新绑定模型工具，或者重新构建执行图。具体动作应由运行时负责，连接器管理层只提供工具或连接配置。

工具可见范围的过滤，能够帮助模型少选错工具，也能减少上下文体积。但它不能替代执行时校验：旧对话里的调用、缓存中的工具，以及其他内部入口，都可能绕过“这轮列表里有没有它”的判断。

权限变化时要更新运行时状态；最终调用入口还要拒绝已经失效的授权。对高权限操作，如果要求撤权后立即阻断正在执行的请求，还需要另行设计取消与外部系统侧的权限控制，单次调用前检查并不提供这种保证。

## 一次查询真正执行时，会经历什么

![从用户提问到 CRM 查询结果的调用时序](/blogs/agent-connectors-from-api-to-runtime/call-sequence.svg)

[查看大图](/blogs/agent-connectors-from-api-to-runtime/call-sequence.svg) · [下载 Mermaid 源文件](/blogs/agent-connectors-from-api-to-runtime/call-sequence.mmd)

这张图刻意把 Token 留在后端。模型收到的是客户信息和可理解的错误，不需要看到请求头、凭据引用的具体存储内容或厂商完整异常。

外部返回的文字也要作为业务数据处理。客户备注、知识库段落中即便出现“忽略之前的规则”之类内容，也不能据此扩大权限或更换连接。工具结果可以影响回答所依据的事实，授权判断依旧走后端规则。

记录调用日志时，我会优先保留请求关联 ID、工具名、连接实例标识、耗时和结果状态。正文和业务参数是否记录，要依据业务敏感程度决定；Token 和 Authorization 请求头应被排除。

如果用户说“查不到”，就可以沿着链路定位：连接没有选中，模型没有提出调用，后端拒绝授权，外部服务超时，还是查询成功但没有匹配结果。这些情况应该在系统中有不同状态，不能全部变成一个空列表。

## 从能演示走到能交付，还要补齐哪些细节

我会先把查询与写入分开处理。只读查询的重试，通常围绕超时、限流与服务端暂时失败；创建工单则必须考虑重复执行。

| 情况 | 处理思路 |
| --- | --- |
| 参数缺少或格式错误 | 返回明确校验结果，补齐参数后再调用 |
| Token 过期 | 由凭据服务尝试受控刷新；失败时提示重新授权 |
| 权限不足 | 拒绝执行，不能通过重试扩大权限 |
| 被外部系统限流 | 在整体时间预算内按厂商规则退避，必要时返回稍后重试 |
| 查询超时 | 按接口语义有限重试，保留取消与超时边界 |
| 创建工单后响应丢失 | 用稳定业务操作标识核对状态，避免直接重复创建 |

如果工单系统支持幂等键，可以把一次业务操作绑定到一个稳定键。同一次操作重试时复用该键，新工单才生成新键。外部系统不支持幂等时，单靠本地生成一个 UUID 并不能保证不会重复，需要查询核对、业务去重或补偿流程。

需要人工确认的写操作，还要把确认绑定到具体连接和操作内容。用户确认“给客户 A 创建这份工单”以后，模型如果改成客户 B 或换了正文，之前的确认就不应继续生效。

另一个常见问题是缓存。可以缓存工具元数据，但带有账号权限的工具列表、客户端或执行包装，必须考虑租户、用户、实例和凭据版本等实际隔离维度。不能因为两个连接属于同一种 CRM，就共享同一个已经绑定凭据的客户端。

第一版不一定需要复杂的插件市场或独立连接器服务。先在一个进程里把接口、身份和调用责任分清楚，再根据数量、部署和生命周期需求增加注册发现与独立部署，会更容易验证设计。

## 下载示例，先验证边界，再接真实系统

[下载完整 Python 示例](/blogs/agent-connectors-from-api-to-runtime/connector_demo.py)

这个文件使用 Python 3.12+ 标准库，提供两个虚构租户、两组假凭据和一个模拟 CRM 适配器。它不联网，也不调用模型服务。下载后运行：

```bash
python connector_demo.py
python connector_demo.py --test
```

第一条命令会沿着“配置实例—绑定本轮工具—校验授权—读取凭据—调用适配器”返回：

```json
[
  {
    "id": "crm-a-customer-1",
    "name": "远山公司",
    "status": "active"
  }
]
```

第二条命令检查 11 个行为，包括跨租户拒绝、其他用户拒绝、本轮未选择的连接不可用、绑定后撤销授权仍然有效、连接停用、调用时读取新凭据，以及两个请求的绑定不会互相覆盖。

这些检查只证明最小示例中的调用边界。它没有实现真实 OAuth、持久化配置、跨进程授权一致性、数据库行级权限，也没有证明模型一定会选对工具。接入真实 CRM 后，还要增加接口契约测试，并验证实际账号能读到的数据范围。

我会用第二个系统和第二个账号检验这套设计：新增系统时，变化是否集中在适配器和能力定义；新增账号时，是否主要新增连接实例；切换用户时，是否仍然通过当前请求的身份做授权。

如果每次新增客户都要复制一套 Agent，公共接入责任还没有收拢。如果每接一个系统都要修改所有公共模型，则要重新检查抽象是否承担了过多厂商细节。连接器是否有价值，最终可以通过这些具体变化来验证。
