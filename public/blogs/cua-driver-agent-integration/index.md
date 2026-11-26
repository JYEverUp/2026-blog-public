想象一个常见的报表流程。Agent 可以用脚本把数据算好，但旧客户端里的「生成报表」只提供桌面按钮。流程跑到这里，人得接过鼠标，选日期、点生成，再回到对话里告诉 Agent 结果。如果这是每天都要做的工作，这个按钮就成了整个流程的人工交接点。

Cua Driver 解决的是这段交接。现有 Agent 继续用 API、命令行和文件工具处理数据。遇到只能在界面里完成的步骤，它通过 Cua Driver 读取目标窗口、操作控件，再检查应用里的结果。模型和任务流程由 Agent 管，桌面观察和操作由 Driver 管。 [Cua Driver 工作原理](https://cua.ai/docs/cua-driver/concepts/how-cua-driver-works)

## 接入前的三个痛点

- **流程卡在 GUI。** API、脚本和浏览器自动化各自能覆盖一部分工作，但桌面窗口里的菜单、弹窗或导出按钮经常要另写脚本，或者交给人补上。
- **坐标容易失效。** 只靠全屏截图和固定坐标的脚本，遇到窗口移动、缩放变化或弹窗就容易点错。用全局鼠标和键盘执行时，还会占用人正在用的输入设备。
- **点击成功和任务成功是两回事。** 点击事件可以正常送达，但应用可能在校验输入、等待生成，或弹出了确认框。验收应该看应用状态，比如报表是否生成、日期范围是否正确。 [Cua Driver 的动作验证](https://cua.ai/docs/cua-driver/concepts/how-cua-driver-works#the-action-ladder)

## 怎么接入现有 Agent

有 MCP 客户端的 Agent 可以把 `cua-driver mcp` 注册成工具服务。只支持 Shell 的 Agent 可以调用 `cua-driver call <tool>`，自研应用也可以通过 Python 或 TypeScript SDK 调用。下面以 Windows 上的 MCP 接入为例。 [Agent 接入指南](https://cua.ai/docs/cua-driver/guides/connect-your-agent) · [SDK 指南](https://cua.ai/docs/cua-driver/guides/use-the-sdk)

![现有 Agent 通过 MCP 调用 Cua Driver 操作目标应用的链路](/blogs/cua-driver-agent-integration/architecture.svg)

[Mermaid 源文件](/blogs/cua-driver-agent-integration/architecture.mmd)

### 安装并检查 Cua Driver

在需要操作的 Windows 桌面会话中安装 Cua Driver。启用登录启动后，可以用 `cua-driver autostart kick` 立即启动，再用 `doctor` 和 `list_apps` 检查 Driver 能否看到桌面。 [安装与诊断](https://cua.ai/docs/cua-driver/quickstart)

```powershell
irm https://cua.ai/driver/install.ps1 | iex
cua-driver autostart kick
cua-driver doctor
cua-driver call list_apps
```

如果登录启动任务没有注册成功，可以在当前桌面会话的终端运行 `cua-driver serve` 并保持终端打开，再用另一个终端做检查。 [Windows 安装步骤](https://cua.ai/docs/cua-driver/quickstart#1-install-and-start-cua-driver)

### 注册 MCP 连接器

在支持本地 MCP 的客户端里添加一个 `stdio` 连接器。服务器 ID 填 `cua-driver`，Command 填本机 `cua-driver.exe` 的完整路径，Args 填 `mcp`。启用连接器后，就可以在会话里选择 Cua Driver。 [Agent 接入指南](https://cua.ai/docs/cua-driver/guides/connect-your-agent)

![Windows 客户端的 Cua Driver 自定义连接器，使用 stdio 和 mcp 参数](/blogs/cua-driver-agent-integration/windows-stdio-connector.png)

_Windows 上的 Cua Driver 连接器配置。Command 使用本机的安装路径。_

使用 Codex 时，用 `codex mcp list` 检查安装器是否已经注册 `cua-driver`。需要手动注册时，运行下面的命令，再执行它打印出来的注册命令，最后重新打开 Codex 会话。 [Codex 接入文档](https://cua.ai/docs/cua-driver/guides/codex)

```powershell
cua-driver mcp-config --client codex
```

### 用计算器验证接入

让 Agent 用 `cua-driver` MCP 打开系统计算器，实际按键完成 `6 × 7`，再从新的窗口快照读取显示值。预期是计算器显示 `42`，Agent 能从窗口里读到这个值。 [计算器快速入门](https://cua.ai/docs/cua-driver/quickstart#4-ask-your-agent)

![Agent 操作计算器并重新读取显示值的时序图](/blogs/cua-driver-agent-integration/calculator-sequence.svg)

[Mermaid 源文件](/blogs/cua-driver-agent-integration/calculator-sequence.mmd)

在实际任务里，Agent 先用 `list_windows` 找到目标窗口，再用 `get_window_state` 读取截图和无障碍树。按钮或输入框在树里有对应元素时，优先按元素操作。界面只暴露像素时，可以用同一次窗口截图里的坐标。支持的浏览器页面还可以走页面工具。某些应用必须在前台接收输入，Agent 可以显式选择前台操作。动作效果无法确认时，重新观察窗口，再决定是否需要重试。 [目标定位与动作验证](https://cua.ai/docs/cua-driver/concepts/how-cua-driver-works#the-action-ladder)

## 用 Windows 计算器和记事本制作消费报告

接入后，可以让 Agent 在两个桌面应用之间完成一次交接。这次给它六笔模拟支出和 300 元预算，要求它用系统计算器求出总额、平均每笔、最高单笔和预算余额，每次计算后读取窗口里的显示值。随后把六笔明细和四项结果写进记事本，再回读核对。

![会话里的消费报告任务指令和已完成的三项任务进度](/blogs/cua-driver-agent-integration/expense-report-prompt.png)

_任务把计算、写入和核对都交给 Agent。_

记事本里的《今日消费报告》列出了六笔支出。汇总结果是总额 **215.60 元**、平均每笔 **35.93 元**、最高单笔 **64.50 元（午餐）**，预算还剩 **84.40 元**。

![Windows 记事本中的今日消费报告，包含六笔消费明细和四项计算结果](/blogs/cua-driver-agent-integration/expense-report-notepad.png)

_记事本窗口里的报告正文。_

Agent 在最终回复中报告，标题、六笔明细和四项结果共 11 项核对一致，报告以未保存草稿的形式留在记事本窗口里。

![Agent 汇报四项计算结果和记事本报告的核对结果](/blogs/cua-driver-agent-integration/expense-report-result.png)

_会话里返回的金额和核对结果。_

## 接入后能做到什么

最直接的变化是，原本需要人工接手的桌面步骤可以纳入同一条任务流程。以开头的报表为例，Agent 可以用脚本准备参数，在旧客户端中选择日期并生成报表，最后检查文件是否存在、内容是否覆盖所选日期。Cua 的公开演示用了类似的路径，让 Agent 在没有 API 的 Windows 邮务客户端里填写寄件信息并打印回执。 [旧版邮务客户端演示](https://cua.ai/docs/cua-driver/quickstart)

目标应用和系统支持后台操作时，Agent 可以操作指定窗口，同时让人继续使用前台窗口。这项能力需要按应用验收。比如 macOS 需要辅助功能和屏幕录制权限，Windows 的交互依赖可访问的桌面会话，Wayland 下被遮挡窗口的原始输入通常受合成器限制。 [平台支持说明](https://cua.ai/docs/cua-driver/concepts/platform-support)

公开的 Cua Driver Bench 将后台通过定义为三个条件同时满足。应用状态证明任务完成，全程仅使用 GUI，前台用户也没有受到干扰。在这组测试里，Cua Driver 在 macOS 上完整通过 23/40 轮，在 Windows 11 上通过 11/40 轮，在 Ubuntu 24.04 + XFCE 上通过 5/40 轮。macOS 和 Linux 的结果来自 Scale AI，Windows 结果来自 Cua。这些数字对应报告中的任务、环境和 Driver 版本。 [Cua Driver Bench 原始报告](https://github.com/trycua/cua/blob/main/blog/cua-driver-bench.md#2-results)

回到报表流程，接入是否成功可以用两个具体问题来验收。应用是否生成了日期正确的报表？如果要求后台执行，人的前台窗口、键盘焦点和鼠标指针是否保持原样？把这两件事一起测，才能判断那个原本必须人工接手的按钮，能不能真正交给 Agent。
