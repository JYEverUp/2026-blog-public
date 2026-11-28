接手一个陌生仓库时，代码目录能告诉你文件放在哪里，但很难直接看出「请求从哪个入口进来、经过哪些模块、最后写到哪里」。一张能点回源码的图，比堆满文件名的目录树更适合交接。

Archify 把这个过程拆成两步。Agent 阅读描述或仓库，把组件、关系和证据整理成结构化 JSON。Archify 再按图类型校验和渲染，输出一份可在浏览器打开的 HTML，并提供检查结果供回看。 [Archify 项目仓库](https://github.com/tt-a1i/archify)

![Archify 的交互架构图及不同视觉样式展示](/blogs/archify-repository-architecture-map/archify-overview.svg)

## 让 Agent 整理事实，让程序检查结构

画图前先确定读者要回答的问题。要讲服务边界，就用 Architecture。要跟踪一次请求的先后，就用 Sequence。图里的节点、连线和证据都来自输入文件，所以能针对某一个节点修正信息并重新渲染。校验通过说明输入符合相应规则，仓库里的业务语义仍要回到源文件核对。 [Archify 编写指南](https://github.com/tt-a1i/archify/blob/main/docs/authoring-cookbook.md)

![Archify 从阅读仓库、生成 JSON 到校验、修正和交付 HTML 的流程](/blogs/archify-repository-architecture-map/diagram-workflow.svg)

[Mermaid 源文件](/blogs/archify-repository-architecture-map/diagram-workflow.mmd)

## 安装 Skill，先跑一份示例

Archify 的 CLI 需要 Node.js 18 或更高版本。用 Skills 安装器选择要用的 Archify 技能和 Agent，核对安装位置后确认。项目的快速开始也提供了面向不同 Agent 的安装命令。 [Archify 安装指引](https://github.com/tt-a1i/archify#quick-start)

```bash
npx skills add tt-a1i/archify -g
```

<details open>
<summary>终端安装与选择 Agent</summary>

![Skills 安装器打开并列出可选的 Archify 技能](/blogs/archify-repository-architecture-map/skills-command.svg)

![安装过程中选择可接收技能的本机 Agent](/blogs/archify-repository-architecture-map/agent-selection.svg)

![选择技能文件的安装方式](/blogs/archify-repository-architecture-map/installation-method.svg)

![核对技能的安装位置并确认](/blogs/archify-repository-architecture-map/installation-confirmation.svg)

![终端显示 Archify 技能已安装](/blogs/archify-repository-architecture-map/installation-finished.svg)

</details>

在已安装的 Archify 技能根目录运行下面两条命令。`doctor` 用来检查运行环境，`demo` 把可打开的示例写入指定目录。按终端输出的位置打开生成的 HTML。 [Archify CLI 编写指南](https://github.com/tt-a1i/archify/blob/main/docs/authoring-cookbook.md)

```bash
node bin/archify.mjs doctor
node bin/archify.mjs demo ./archify-demo
```

<details open>
<summary>环境检查与示例生成</summary>

![在技能目录运行 doctor 并核对运行环境](/blogs/archify-repository-architecture-map/doctor-result.svg)

![CLI 生成示例并输出 HTML 文件位置](/blogs/archify-repository-architecture-map/demo-command.svg)

</details>

![浏览器打开 Archify 自带的示例系统地图](/blogs/archify-repository-architecture-map/demo-map.svg)

## 让 Agent 画出一条可核对的主路径

在需要理解的仓库里开会话，先问一条真实存在的路径。例如「浏览器请求从入口经过哪一层，什么时候查缓存，缓存没命中后读什么存储」。提示词里明确要给哪些证据。

> 用 Archify 为这个仓库画一张运行架构图。只保留入口、核心处理模块、外部依赖和存储。标出一条请求主路径。每条关键连线给出调用方和被调用方的源码位置。无法确认的连线留在说明里。

<details open>
<summary>从 Agent 请求到结构化输入和交付结果</summary>

![在 CodeBuddy 中进入示例仓库并发起画图任务](/blogs/archify-repository-architecture-map/repository-prompt.svg)

![Agent 读取技能说明并检查示例仓库结构](/blogs/archify-repository-architecture-map/repository-inspection.svg)

![Agent 读取仓库说明以确认组件和入口](/blogs/archify-repository-architecture-map/source-file-reading.svg)

![生成架构图时编写的 JSON 节点和说明](/blogs/archify-repository-architecture-map/diagram-json.svg)

![Agent 汇报生成的架构图及关键组件](/blogs/archify-repository-architecture-map/delivery-report.svg)

</details>

打开结果后，从入口节点顺着连线走一遍，再抽查两处源码。最好先确认方向和触发条件，再看排版。下面是一个示例仓库生成后的运行架构图。 [Archify 的仓库证据示例](https://github.com/tt-a1i/archify)

![示例仓库的运行架构图在浏览器中展示](/blogs/archify-repository-architecture-map/repository-map.svg)

如果生成失败，先读 JSON 诊断里指出的规则和问题位置，修正对应的节点或连线再跑。需要手动验收时，可以用 CLI 先生成检查结果，再交付 HTML。下面沿用项目的 workflow 示例，命令从 Archify 技能根目录执行。 [校验与交付命令](https://github.com/tt-a1i/archify/blob/main/docs/authoring-cookbook.md)

```bash
node bin/archify.mjs validate workflow examples/agent-tool-call.workflow.json --json
node bin/archify.mjs deliver workflow examples/agent-tool-call.workflow.json ./workflow.html --json
```

## 选图时先选问题

| 图类型 | 适合回答 |
| --- | --- |
| Architecture | 系统由哪些组件组成，边界在哪里？ |
| Workflow | 一个流程经过哪些步骤、审批和决策分支？ |
| Sequence | 参与方以什么顺序交换请求和响应？ |
| Data Flow | 数据从哪里进来，经过什么处理，最后到哪里？ |
| Lifecycle | 一个对象怎样在排队、运行、失败和重试等状态间变化？ |

交接时可以把生成的 HTML 和输入 JSON 一起保存。HTML 提供浏览和分享入口，JSON 保留布局、语义与证据，有问题时可以在输入层改完再重新生成。
