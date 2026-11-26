我想给自己搭一个飞书巡检助手。第一版只做一件事：我把几行巡检数据发给机器人，它在私聊里回一份异常摘要。这个范围够小，部署、消息收发和结果都能逐步核对。

我的顺序是先在 Dashboard 验证模型，再接飞书。两边用同一条测试消息。如果 Dashboard 能回、飞书没动静，我就先查飞书通道和权限。

## 我怎么理解这条消息链路

```text
我的飞书私聊 → 飞书通道插件 → OpenClaw Gateway → Agent 调用模型
我的飞书私聊 ← 飞书通道插件 ← OpenClaw Gateway ← Agent 返回结果
```

我把 Gateway 当作一直跑在电脑或服务器上的入口。飞书插件负责收发消息，Agent 接手后调用模型生成回复。以后要从监控系统读数据，我会再给 Agent 一个权限受限的查询工具。

我选飞书的 WebSocket 长连接。连接由 OpenClaw 主动发起，Gateway 可以继续监听本机回环地址。关掉 Dashboard 不影响已在后台运行的 Gateway。

![我使用的消息链路，覆盖飞书、Gateway、模型和工具](/blogs/openclaw-feishu-quickstart/source-images/message-flow.svg)

<details>
<summary>开篇动图</summary>

![两只小狗的动图](/blogs/openclaw-feishu-quickstart/source-images/road-map-openclaw-01.gif)

</details>

## 我先验收本地对话

我这里选 Linux 上的 CLI。开始前准备一个普通系统账号和模型凭据，已有 Node.js 时先运行 `node --version` 确认环境。

```bash
curl -fsSL https://openclaw.ai/install.sh -o openclaw-install.sh
bash openclaw-install.sh
```

安装向导里，我先选模型供应商，把 Gateway 设成后台运行，暂时跳过飞书。向导结束后，我用下面三条命令确认版本、检查服务和打开 Dashboard。

```bash
openclaw --version
openclaw gateway status
openclaw dashboard
```

我会发一条短消息，请模型只回复「本地对话已连通」。看到回复才继续接飞书。遇到模型鉴权、配额或网络错误，我先看对应的供应商配置。

<details>
<summary>部署流程和向导界面</summary>

向导的菜单和排列会随版本变化。我主要确认模型已配置、Gateway 能启动，并且对话有回复。

![我的 OpenClaw 部署和验收顺序](/blogs/openclaw-feishu-quickstart/source-images/setup-checkpoints.svg)

![向导的安全提示](/blogs/openclaw-feishu-quickstart/source-images/road-map-openclaw-09.png)

![向导选择快速开始或手动配置](/blogs/openclaw-feishu-quickstart/source-images/road-map-openclaw-10.png)

![向导的模型供应商列表](/blogs/openclaw-feishu-quickstart/source-images/road-map-openclaw-11.png)

![模型凭据设置示意](/blogs/openclaw-feishu-quickstart/source-images/model-credentials.svg)

![向导的技能配置与服务检查](/blogs/openclaw-feishu-quickstart/source-images/road-map-openclaw-16.png)

![向导提示安装完成](/blogs/openclaw-feishu-quickstart/source-images/road-map-openclaw-17.png)

![Gateway 启动日志](/blogs/openclaw-feishu-quickstart/source-images/road-map-openclaw-18.png)

</details>

## 我再接飞书私聊

这部分的飞书接入向导要求 OpenClaw 2026.5.29 或更高版本。我先用 `openclaw --version` 确认版本，再配置通道。

1. 我先在飞书开放平台建一个企业自建应用，启用机器人，把应用可见范围限定在测试账号。App ID 与 App Secret 在「凭证与基础信息」里取。
2. 我运行 `openclaw channels login --channel feishu`，选择手动配置，录入凭据并选择飞书域名。向导会按需安装飞书插件。我先验收私聊，把群聊策略设成 `disabled`。
3. Gateway 保持运行。我回到飞书后台，在「事件与回调」里选长连接，添加接收消息事件 `im.message.receive_v1`，开通私聊收发所需权限并发布。租户要求审批时，我等版本生效后再发消息。
4. 我用 `openclaw channels status --probe` 检查通道，然后在飞书客户端给机器人发一条消息。使用默认私聊策略时，如果收到配对码，我先核对请求来自自己的测试账号，再在 Gateway 所在机器上批准。

```bash
openclaw pairing list feishu
openclaw pairing approve feishu YOUR_PAIRING_CODE
```

我用刚收到的配对码替换 `YOUR_PAIRING_CODE`，批准后重新发一条消息。已经设置私聊白名单时，我直接用名单里的账号测试。

![飞书客户端首次私聊与配对提示](/blogs/openclaw-feishu-quickstart/source-images/feishu-first-chat-pairing-example.png)

<details>
<summary>飞书后台、通道配置与配对步骤</summary>

![我创建飞书企业自建应用的步骤](/blogs/openclaw-feishu-quickstart/source-images/feishu-app-creation.svg)

![我配置飞书机器人收发权限的步骤](/blogs/openclaw-feishu-quickstart/source-images/feishu-app-permissions.svg)

![飞书应用的创建版本和发布页面](/blogs/openclaw-feishu-quickstart/source-images/road-map-openclaw-06.png)

![飞书后台的事件与回调页面和长连接选项](/blogs/openclaw-feishu-quickstart/source-images/road-map-openclaw-07.png)

![向导选择飞书消息通道](/blogs/openclaw-feishu-quickstart/source-images/road-map-openclaw-13.png)

![向导安装飞书插件的界面](/blogs/openclaw-feishu-quickstart/source-images/road-map-openclaw-14.png)

![飞书通道凭据设置示意](/blogs/openclaw-feishu-quickstart/source-images/feishu-credentials.svg)

![飞书后台开通权限并添加接收消息事件](/blogs/openclaw-feishu-quickstart/source-images/road-map-openclaw-19.png)

![飞书应用修改事件订阅后创建新版本](/blogs/openclaw-feishu-quickstart/source-images/road-map-openclaw-20.png)

![我核对配对请求并验证飞书回复的步骤](/blogs/openclaw-feishu-quickstart/source-images/pairing-checkpoints.svg)

</details>

## 我用三行巡检数据验收

我在 Dashboard 和飞书私聊里各发一次下面的模拟输入。第一轮只整理消息自带的数据，暂时不用接监控系统。

```text
以下是 09:00 的模拟巡检结果。请只列出状态为 WARN 或 FAIL 的服务，
每行保留服务名、状态和观测值，最后给出异常数量。不要补充数据中没有的故障原因。

api       OK    120 ms
queue     WARN  待处理 480 条
backup    FAIL  最后成功于昨天 02:00
```

我会核对三件事：回复里有 `queue` 和 `backup`，异常总数是 `2`，`api` 没进入异常列表。接真实巡检数据时，我会先加只读查询，保留观测值和时间。重启服务和修改配置再单独设置执行权限和审批。

![飞书机器人回复系统概况和 Redis 状态的对话示意](/blogs/openclaw-feishu-quickstart/source-images/feishu-ops-bot-example.png)

## 机器人没回时我先查哪里

| 我看到的现象 | 我先做什么 |
| --- | --- |
| Dashboard 打不开 | 在 Gateway 所在机器上运行 `openclaw gateway status`，确认进程正在运行。 |
| Dashboard 打得开，发消息时报错 | 用 `openclaw logs --follow` 看模型请求错误，核对凭据、额度和网络。 |
| Dashboard 能回复，飞书没反应 | 运行 `openclaw channels status --probe`，核对飞书应用版本、可用范围、长连接和事件订阅。 |
| 飞书返回配对码 | 核对并批准自己的请求，然后重新发一条消息。 |
| 日志收到消息，飞书仍没有回复 | 从日志区分模型处理失败和飞书发送失败。发送若被拒绝，我会核对应用权限和生效版本。 |

排查时，我会开着 `openclaw logs --follow`，再从飞书发一条带当前时间的测试消息。这样能在日志里找到这一次请求，看到它停在哪一步。
