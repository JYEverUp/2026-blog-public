想调整一个已有的博客首页时，可以先拿原页面做对照，保留文章列表和导航的主要行为，再做一份独立原型。真正耗时间的通常是验收：手机导航有没有被挤掉，长标题会不会撑破卡片，列表点进去能不能回到原位置？

Craft Anything 把观察、生成和比对放在同一个项目里。它先收集目标界面的证据，再调用本机的编程 Agent 生成项目，最后把结果放回对照流程。此前介绍的 REA 更适合追到程序的实现细节，这次关注的是怎样从可见行为做到可运行、可复验的原型。 [Craft Anything 项目仓库](https://github.com/storytold/craft-anything)

![Craft Anything 首次启动时的引导首页](/blogs/craft-anything-prototyping/onboarding-start.svg)

## 从观察到验收的四步

| 阶段 | 这一步要解决的问题 |
| --- | --- |
| Study | 记录目标页面的布局、状态和可复现的操作 |
| Build | 根据需求和已有证据，生成独立的项目文件 |
| Check | 在给定的屏幕宽度下对照结果，记录差异 |
| Ready | 打开产物，按验收条件操作一遍，决定继续迭代还是交付 |

默认的 Clean Room 模式围绕可见内容开展观察，例如截图、可见文字、间距和菜单展开后的状态。Deep 模式会开放读取代码或文件的工具，适合有授权的内部研究。两种设置约束的是工具可用范围，编程 Agent 的文件和命令权限仍取决于本机运行环境。 [官方模式说明](https://github.com/storytold/craft-anything#clean-room-or-deep)

![Craft Anything 从界面观察、生成原型到对照检查和继续迭代的流程](/blogs/craft-anything-prototyping/prototype-workflow.svg)

[Mermaid 源文件](/blogs/craft-anything-prototyping/prototype-workflow.mmd)

## 安装并连接编程 Agent

到 Releases 选择对应系统和 CPU 的安装包。Windows 按架构选 MSI 或便携包，macOS 选对应的 DMG，Linux 按发行版选软件包。下面的界面截图来自 Windows 版 0.5.0，下载时以当前发布页为准。 [Craft Anything Releases](https://github.com/storytold/craft-anything/releases)

先确认打算用的编程 Agent 已安装并完成登录，再在 Craft Anything 里选构建后端。Claude Code 是项目文档里优先支持的路径。其他后端的可用能力和验证状态可以查项目说明。安装了 CLI 时，可以先跑环境检查。 [编程 Agent 支持与命令行用法](https://github.com/storytold/craft-anything#get-started)

```bash
craft-anything-cli doctor
```

<details open>
<summary>Windows 首次配置截图</summary>

![首次配置时查看可用的模型提供商](/blogs/craft-anything-prototyping/provider-options.svg)

![提供商配置界面与启用状态](/blogs/craft-anything-prototyping/provider-configuration.svg)

![从本机可用的编程 Agent 中选择构建后端](/blogs/craft-anything-prototyping/coding-agent-selection.svg)

![首次启动流程中的用途选择](/blogs/craft-anything-prototyping/onboarding-purpose.svg)

![设置完成，准备打开工作区](/blogs/craft-anything-prototyping/onboarding-complete.svg)

</details>

## 给自有博客做一份可对照的原型

先限定范围。只做首页和文章列表，在 390px 和桌面宽度下都能打开导航、浏览列表和返回首页。给 Agent 指定项目技术和验收动作，减少它自行补功能的空间。

> 以我有权使用的博客页面为参考，用 React 和 Tailwind 做一个独立原型。只覆盖首页和文章列表。手机宽度下导航可展开，长标题可换行，页面没有水平滚动。请在输出里列出已验证的宽度、操作和剩余差异。

![简单模式中填写目标类型、网址和原型需求](/blogs/craft-anything-prototyping/simple-project-form.svg)

构建中可能出现审批卡。安装依赖或运行命令前，先看命令、工作目录和预期修改，再批准当前动作。对照结果可以从一个差异开始修，比如「390px 下菜单展开后遮住了列表，修完再用相同宽度复验」。 [官方构建与命令审批说明](https://github.com/storytold/craft-anything#get-started)

<details open>
<summary>研究、构建和检查过程</summary>

![项目界面显示对目标开展观察](/blogs/craft-anything-prototyping/study-progress.svg)

![进度区显示研究与构建过程中的说明](/blogs/craft-anything-prototyping/project-progress.svg)

![在项目界面并排查看观察对象和生成结果](/blogs/craft-anything-prototyping/comparison-preview.svg)

![检查结束后，查看结果与打开预览的入口](/blogs/craft-anything-prototyping/check-result.svg)

![审批卡和本次比对的结果记录](/blogs/craft-anything-prototyping/approval-and-score.svg)

</details>

截图里的博客尝试得到了较低的相似度，这是那一次输入和产物之间的比对结果。验收时可以回到更具体的问题，例如两边在同样宽度下导航是否可用、列表是否溢出、交互状态是否一致。

## 到项目目录里找结果

`app/` 是生成的应用目录。遇到偏差时，可以先对照 `capture/` 里工具观察到的界面，再看 `checks/` 里记录的差异。`craft.json` 保存项目请求、目标和历史，`investigation.cany/` 记录证据，`inbox/` 保存待回答的问题。 [项目文件结构](https://github.com/storytold/craft-anything#get-started)

![文件管理器展示生成项目的目录与日志](/blogs/craft-anything-prototyping/project-directory.svg)

<details open>
<summary>查看观察模式切换提示</summary>

![切换观察模式前的说明与确认界面](/blogs/craft-anything-prototyping/inspection-mode-switch.svg)

</details>

也可以从空项目开始，把「目标地址」换成 `-`，用明确目标跑一轮。例如先做一个自有的阅读清单，而后把检查项拆成新增、勾选和刷新后能否恢复。 [CLI 项目示例](https://github.com/storytold/craft-anything#get-started)

```bash
craft-anything-cli rebuild - "Build a personal reading list with a title, completed status and local storage" --rounds 1
```
