假设要修一个报表页。手机上筛选区把表格挤出了屏幕，你想比较「筛选折叠」和「筛选横向滚动」两种改法。把任务都交给同一个目录里的两个 Agent，它们很可能改到同一份组件。等两个结果回来，你还得分辨哪一段改动属于哪套方案。

Orca 把并行任务放到各自的 Git worktree 里。每份工作区有独立的文件、分支和 Agent 终端，也可以打开各自的预览。两个 Agent 可以从同一个提交开始，你最后再逐个看 diff、跑测试，决定合并哪一份。 [Orca 项目仓库](https://github.com/stablyai/orca) · [工作区文档](https://api.onorca.dev/docs/model/worktrees)

## 先理解 worktree 隔离了什么

普通的切分支是在一个目录里换出不同版本。用 worktree，可以为同一仓库挂出多个目录，每个目录各有自己的工作文件和暂存区，底层共享 Git 对象和提交历史。只要两个任务在各自的路径里执行，A 保存一个文件时，B 目录里的同名文件就不会随之改变。 [Git worktree 文档](https://git-scm.com/docs/git-worktree)

在一个已经有提交的仓库根目录，可以用下面的命令看到这个结构。两条新分支都从当前的 `HEAD` 开始。

```bash
git worktree add -b report-collapse ../report-collapse HEAD
git worktree add -b report-scroll ../report-scroll HEAD
git worktree list
```

![同一个 Git 提交开出两个独立 worktree，Agent 分别完成任务，再经过差异审查和测试选择合并](/blogs/orca-parallel-agents-worktree/parallel-worktrees.svg)

[Mermaid 源文件](/blogs/orca-parallel-agents-worktree/parallel-worktrees.mmd)

新目录只拿到 Git 检出的文件。依赖、被忽略的本地配置和开发服务端口，要在项目的工作区设置或启动脚本里单独处理。要比较两个开发预览，可以给两个工作区分别分配端口。 [Orca 的共享路径与工作区配置](https://api.onorca.dev/docs/model/worktrees)

## 安装 Orca 并添加项目

Orca 有 Windows、macOS 和 Linux 桌面版。打开 Orca 之前，先确认打算使用的 Agent CLI 能在终端启动，并按对应客户端完成登录。Orca 负责组织这些客户端的会话，使用量由各自的账号和模型方案计算。 [Orca 安装指南](https://api.onorca.dev/docs/install) · [软件下载](https://www.onorca.dev/download)

```bash
git --version
codex --version
claude --version
```

按实际使用的客户端检查即可。首次启动时选择默认 Agent，后续在某个工作区里仍然可以选择另一个客户端。用到 GitHub 任务和 PR 功能时，再检查 `gh` 能否在同一个环境中运行。Windows 的默认 Shell 可以按项目习惯选择 PowerShell、CMD 或 WSL。 [Orca 终端文档](https://api.onorca.dev/docs/terminal) · [GitHub CLI 配置](https://api.onorca.dev/docs/github-errors)

![首次启动时选择默认 Agent，图中选的是 Hermes](/blogs/orca-parallel-agents-worktree/setup-default-agent.svg)

<details open>
<summary>Windows 首次配置截图</summary>

![设置应用主题，深色、浅色和跟随系统任选](/blogs/orca-parallel-agents-worktree/setup-theme.svg)

![为 GitHub 任务功能配置 GitHub CLI](/blogs/orca-parallel-agents-worktree/setup-github.svg)

![GitHub CLI 下载页面展示 Windows 的 WinGet 安装命令](/blogs/orca-parallel-agents-worktree/github-cli-download.svg)

![Windows 命令提示符显示 GitHub CLI 已安装成功](/blogs/orca-parallel-agents-worktree/github-cli-installed.svg)

![Orca 中选择 Windows 终端的默认 Shell](/blogs/orca-parallel-agents-worktree/setup-windows-shell.svg)

![Orca 首次配置中的通知提示音设置](/blogs/orca-parallel-agents-worktree/setup-notifications.svg)

</details>

首次配置结束后，添加已有 Git 仓库，或先建一个项目练手。要做并行对照，先保证两份工作区都从同一个基线分支或提交开始。 [Orca 的首个并行会话](https://api.onorca.dev/docs/first-session)

![添加项目后的 Orca 主界面和项目终端](/blogs/orca-parallel-agents-worktree/project-workspace.svg)

<details open>
<summary>添加项目与检查终端的截图</summary>

![添加项目时可登记已有目录、克隆仓库或创建项目](/blogs/orca-parallel-agents-worktree/add-project.svg)

![在本地选择项目名和保存目录](/blogs/orca-parallel-agents-worktree/create-project.svg)

![Orca 内置终端返回运行状态 JSON](/blogs/orca-parallel-agents-worktree/runtime-status.svg)

![Hermes 在 Orca 的项目终端里启动](/blogs/orca-parallel-agents-worktree/agent-terminal.svg)

![项目侧栏显示已有仓库和工作区入口](/blogs/orca-parallel-agents-worktree/project-repository.svg)

</details>

## 跑两个工作区，再选择要合并的方案

在同一个仓库中创建两个工作区。给它们起能看懂的名字，例如 `report-collapse` 和 `report-scroll`。分别打开各自的 Agent，给出同一组验收条件，再指明要尝试的方案。

> 修复报表页在 390px 宽度下的横向溢出。保留日期筛选和查询按钮。完成后说明改了哪些文件、实际跑过哪些检查，以及桌面布局有没有变化。

![为同一个仓库创建新工作区，填写任务名并选择起始分支](/blogs/orca-parallel-agents-worktree/create-worktree.svg)

<details open>
<summary>第二份工作区与两份执行结果</summary>

![第一份 worktree 在侧栏中出现，并打开自己的 Agent 终端](/blogs/orca-parallel-agents-worktree/first-worktree.svg)

![为同一项目创建第二份 worktree，并选择另一个 Agent](/blogs/orca-parallel-agents-worktree/second-worktree.svg)

![第一个工作区返回实现说明和验证信息](/blogs/orca-parallel-agents-worktree/first-agent-result.svg)

![第二个工作区返回独立的实现结果](/blogs/orca-parallel-agents-worktree/second-agent-result.svg)

</details>

如果想比较两个 Agent 本身的表现，可以给它们相同的提示词、起始提交和验证条件。并行会让多个会话各自消耗额度，实际完成时间取决于运行较慢的任务和最后的审查。第一次对照时，两份可对比的结果就够用了。 [Orca 并行工作流](https://api.onorca.dev/docs/first-session)

## 把反馈落到 diff 或页面元素上

两个工作区跑完后，打开各自的 diff。先检查修改范围和测试记录，再逐行看关键改动。比如某个方案通过隐藏整个筛选区来消除溢出，就在对应改动上留一条批注，说明要保留哪些控件，再发回该工作区的 Agent。 [Orca 工作区审查](https://api.onorca.dev/docs/model/worktrees)

![在 Orca 的差异视图中审查第一份工作区的代码](/blogs/orca-parallel-agents-worktree/review-first-diff.svg)

<details open>
<summary>另一份差异与会话交接截图</summary>

![切到第二份工作区查看另一套修改](/blogs/orca-parallel-agents-worktree/review-second-diff.svg)

![工作区的会话操作区域提供移交入口](/blogs/orca-parallel-agents-worktree/session-handoff-entry.svg)

![选择接手当前任务的另一个 Agent](/blogs/orca-parallel-agents-worktree/session-handoff-picker.svg)

</details>

做前端时，还可以在 Orca 的内置浏览器用 Design Mode 选中具体元素。Agent 可以随任务收到元素的 HTML、计算后的 CSS 和局部截图。改完后重新打开对应 worktree 的页面，按同样的视口宽度复验。需要换人继续时，交接前可以记下当前分支、已通过的检查和剩下的问题。 [Orca Design Mode](https://orca.dev/docs/browser/design-mode)

选定要合并的工作区后，在这份结果上跑最终检查，再提交或开 PR。清理其余工作区前，先确认里面还有没有要保留的实验。普通的 `git worktree remove` 会拒绝删除含有未提交修改或未跟踪文件的工作区。 [Git worktree 的清理规则](https://git-scm.com/docs/git-worktree#Documentation/git-worktree.txt-remove)

## 用 CLI 看任务跑在哪

在 Orca 中注册其自带 CLI 后，可以从终端检查运行状态，再列出工作区和当前工作区的终端。这几条命令适合先确认脚本要操作的对象。Linux 桌面版使用的命令名可能显示为 `orca-ide`，按对应安装说明执行。 [Orca CLI 概览](https://orca.dev/docs/cli/overview) · [平台说明](https://api.onorca.dev/docs/install)

```bash
orca status --json
orca worktree ps --json
orca terminal list --worktree active --json
```

回到报表页的例子，最后比较的是两份可验证的改动。哪一份在手机宽度下保持筛选可用，桌面布局也正常，且 diff 易于审查，就把那一份合并进去。
