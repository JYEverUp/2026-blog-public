在 Windows 计算器里输入 `200 + 10%`，结果是 `220`。这里的百分号用 `200` 作基数，所以 `10%` 先变成 `20`。如果只有安装好的程序，怎样找到处理百分号的分支，并验证这个解释适用于哪些运算？

REA（Reverse Engineer Anything）可以把应用检查接进编码 Agent。你指定应用和问题，Agent 通过 MCP 调用 REA，拿到模块、调用关系或反编译片段，再把结论和依据一起交回来。下面从接入开始，看看哪些结果值得相信，以及怎样补上验证。 [REA 官网](https://rea.tools/) · [项目仓库](https://github.com/morluto/rea)

![REA 官网演示对照：手工追踪百分号处理分支，与借助 Agent 核对 200 加 10% 的计算规则](/blogs/rea-mcp-software-analysis/calculator-comparison.svg)

## MCP 把问题和证据接起来

MCP 在这里负责把 Agent 的工具调用交给本机的 REA。以自有 Electron 应用的设置页为例，可以问「点下保存后，设置怎样从渲染进程传到主进程？」查看返回结果时，先定位按钮处理函数和消息通道，再核对主进程是否有对应接收方。证据里如果只有发送端，报告就应该把接收端标成待确认。

![REA 分析流程：提出问题、通过 MCP 检查应用、返回证据，再用实际行为核对](/blogs/rea-mcp-software-analysis/analysis-flow.svg)

[Mermaid 源文件](/blogs/rea-mcp-software-analysis/analysis-flow.mmd)

## 接入 Agent，也可以直接走命令行

先用 `node -v` 和 `npm -v` 检查本机环境，Node.js 的最低补丁版本以安装指南为准。在自己信任的目录运行下面的命令，选择要接入的客户端，检查配置计划并确认，随后重启客户端。PowerShell 如果限制执行 `npx` 的脚本入口，可以改用 `npx.cmd`。 [REA 安装指南](https://rea.tools/get-started/)

```bash
npx rea-agents@latest setup
```

![REA 安装向导列出检测到的客户端，可选择要配置的 Agent](/blogs/rea-mcp-software-analysis/setup-client-selection.svg)

![安装向导应用配置，并提示重启已接入的客户端](/blogs/rea-mcp-software-analysis/setup-complete.svg)

只想在命令行查看选项，可以全局安装 REA 后运行 `rea --help`。全局安装的版本可用 `rea update` 更新。通过 `npx` 接入的客户端，可以重新运行安装命令刷新配置。 [项目快速开始](https://github.com/morluto/rea#quick-start)

```bash
npm install --global rea-agents
rea --help
rea update
```

![终端里安装 REA 并查看帮助，截图中同时展示了正确的双连字符参数](/blogs/rea-mcp-software-analysis/cli-help.svg)

![rea update 回报已安装版本、最新版本与安装方式](/blogs/rea-mcp-software-analysis/cli-update.svg)

## 从自己打包的应用开始

如果手头有自己打包的 JavaScript 或 Electron 应用，可以先对解包目录做静态检查。把下面的示例路径换成本机实际路径。输出的 JSON 可以用来检索模块、导入关系和 Electron 进程边界，也可以回到对应文件核对。 [JavaScript 分析入口](https://rea.tools/get-started/#use-the-cli)

```bash
npx -y rea-agents@latest analyze-javascript-application "/path/to/my-electron-app" --json
```

静态 JavaScript 检查用不到原生反编译器。深入分析 Windows PE、macOS Mach-O 或 Linux ELF 时，要按目标文件格式和系统选分析后端。项目文档还列出了 Android APK、.NET、固件和抓包文件等入口，各自的前置工具可能不同。样本由 REA 在本机处理，工具输出会返回 Agent，后续是否发送给模型服务取决于客户端和模型配置。 [目标类型与工具要求](https://rea.tools/get-started/#other-targets-and-providers) · [项目常见问题](https://github.com/morluto/rea#faq)

## 原作者用 Android 计算器 Demo 看到了什么

孟郎郎用自己写的 Android 计算器做了示范。第一张截图里，Hermes 的 MCP 服务列表出现了 `rea (stdio)`。第二张是针对该 Demo 的功能分析请求，第三张是 Agent 返回的类、界面和计算逻辑说明。

![Hermes 的 MCP 服务列表中显示 rea 以 stdio 方式注册](/blogs/rea-mcp-software-analysis/hermes-mcp.svg)

![原作者让 Hermes 分析自己开发的 Android 计算器 APK](/blogs/rea-mcp-software-analysis/hermes-apk-request.svg)

![Hermes 给出的计算器分析报告，包含界面和部分 Java 逻辑](/blogs/rea-mcp-software-analysis/hermes-apk-report.svg)

这组截图可以用来对照接入过程。要验收报告，可以从加法、清空或非法输入中选一个场景，实际在 Demo 里操作，再对照自己保存的代码。报告中每一条影响结论的说法，最好都能点回对应类、方法或运行结果。

## 三种常见的核验办法

- **查调用链。** REA 的 Notion 案例跟踪了 Electron 剪贴板调用，串起渲染进程、preload、IPC 和主进程。用同样的思路看自己的应用时，可以逐个核对调用双方和消息名。
- **用输入输出做回归。** DX-Ball 案例用 3,205 组原程序用例校验了声道平衡计算，又比对了该函数的 63 个编译字节。日常排查一个业务函数，可以先用边界输入和常见输入覆盖关键分支。
- **比较编译结果。** TH04 案例从 PC-98 的 16 位指令中还原了角度计算，并与历史编译器的输出做比对。这种核验适合行为已经明确、还需要确认实现细节的场景。 [REA 官方案例](https://rea.tools/showcase/)

开始时选一个自己有权检查的小应用，提出一个能复现的问题。读完 Agent 的报告，回到样本再跑一遍并记录差异。反编译结果里的变量名、类型和控制结构都可能是推断，最终结论要能由文件位置、调用关系或实测结果支撑。
