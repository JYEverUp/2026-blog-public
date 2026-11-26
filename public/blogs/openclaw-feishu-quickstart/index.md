假设每天早上都要看一遍服务巡检结果，再把异常项发到飞书。可以先做一个小版本：把几行模拟巡检数据发给机器人，让它在原会话里回复异常摘要。跑通这一步之后，再考虑接入真实数据源。

搭 OpenClaw 时，我会在两个地方分别验收。先在本地 Dashboard 发一条消息，确认 Gateway 和模型能正常对话。再到飞书私聊里发同一条消息，确认飞书的收发链路也通了。这样做的好处是，飞书机器人沉默时，手里已经有一个能对照的入口。

## 一条飞书消息要经过哪些环节

```text
飞书私聊 → 飞书通道插件 → OpenClaw Gateway → Agent 调用模型
飞书私聊 ← 飞书通道插件 ← OpenClaw Gateway ← Agent 返回结果
```

Gateway 是运行在电脑或服务器上的常驻进程，负责承接会话和通道连接。飞书插件负责接收消息事件和发送回复。模型负责理解输入、生成输出。如果以后要读取监控数据，还需要给 Agent 配置相应工具，并明确它能访问哪些数据。

飞书使用 WebSocket 长连接时，由 OpenClaw 主动连到飞书，Gateway 可以继续绑定在本机回环地址。需要保持运行的是 Gateway，浏览器里的 Dashboard 可以关掉。[OpenClaw 飞书通道文档](https://docs.openclaw.ai/channels/feishu)

## 第一步：在 Dashboard 收到模型回复

下面以 Linux 上的官方 CLI 为例。准备一个普通系统账号和可用的模型凭据。已有 Node.js 时，可以先运行 `node --version`，再对照官方安装页确认兼容性。[OpenClaw 安装文档](https://docs.openclaw.ai/install)

```bash
curl -fsSL https://openclaw.ai/install.sh -o openclaw-install.sh
bash openclaw-install.sh
```

安装脚本会启动初始化向导。先配置模型供应商，让 Gateway 在后台运行。飞书可以留到下一步再配置。向导结束后运行：

```bash
openclaw --version
openclaw gateway status
openclaw dashboard
```

在 Dashboard 输入 `请只回复：本地对话已连通`。收到回复后，再接飞书。页面只要连得上 Gateway 就可能打开，因此还要实际发一条消息来确认模型可用。若日志出现模型鉴权、配额或网络错误，先处理对应的供应商配置。[OpenClaw 快速入门](https://docs.openclaw.ai/start/getting-started)

## 第二步：让飞书私聊也能收到回复

这里走企业自建应用的手动配置流程。先准备应用凭据，让 Gateway 建立长连接，再在飞书后台保存事件订阅。[OpenClaw 飞书配置向导](https://docs.openclaw.ai/channels/feishu/setup)

1. 在[飞书开放平台](https://open.feishu.cn/app)创建企业自建应用，启用机器人能力。在「凭证与基础信息」里找到 App ID 和 App Secret。测试期把应用可用范围限定为自己的账号或测试成员。
2. 运行 `openclaw channels login --channel feishu`，选手动配置，填入凭据并选择飞书域名。向导会按需安装官方 `@openclaw/feishu` 插件。只验收私聊时，可以把群聊策略设为 `disabled`。App Secret 留在受保护的配置里，别放进博客、截图或 Git 仓库。
3. 保持 Gateway 运行，回到飞书后台的「事件与回调」，选择「使用长连接接收事件」，订阅「接收消息」`im.message.receive_v1`。按平台提示开通接收机器人私聊和以应用身份回复所需的权限，保存后发布应用版本。若租户要求审批，需等该版本生效。首次测试只需要消息收发相关权限。[飞书接收消息事件](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1) · [飞书长连接配置](https://open.feishu.cn/document/ukTMukTMukTM/uYDNxYjL2QTM24iN0EjN/event-subscription-configure-)
4. 用 `openclaw channels status --probe` 检查通道，再到飞书客户端私聊机器人。如果使用默认的私聊配对策略，首次发消息会收到配对码。核对请求确实来自自己的测试账号，再在 Gateway 所在机器上批准。[飞书私聊访问控制](https://docs.openclaw.ai/channels/feishu/access-control)

```bash
openclaw pairing list feishu
openclaw pairing approve feishu YOUR_PAIRING_CODE
```

将 `YOUR_PAIRING_CODE` 换成刚收到的配对码。批准后重新发一条消息，等机器人回复。若手动设置了私聊白名单，则用白名单里的飞书账号直接测试。

## 用一条巡检摘要验收

在 Dashboard 和飞书私聊里各发一次下面的输入。任务只需要整理随消息发出的数据，可以在开通监控系统权限之前完成验收。

```text
以下是 09:00 的模拟巡检结果。请只列出状态为 WARN 或 FAIL 的服务，
每行保留服务名、状态和观测值，最后给出异常数量。不要补充数据中没有的故障原因。

api       OK    120 ms
queue     WARN  待处理 480 条
backup    FAIL  最后成功于昨天 02:00
```

两边的回复都应包含 `queue` 和 `backup`，异常总数应为 `2`。`api` 不应出现在异常列表里。通过这三个检查，可以同时确认消息往返和任务结果。接真实巡检数据时，我会先给 Agent 一个只读查询入口，保留查询时间和原始观测值。重启服务、修改配置等动作再单独设置权限和审批。[OpenClaw 安全指南](https://docs.openclaw.ai/gateway/security)

## 机器人没有回复，先查哪里

| 看到的现象 | 先查什么 |
| --- | --- |
| Dashboard 打不开 | 在运行 Gateway 的机器上执行 `openclaw gateway status`，确认服务正在运行。 |
| Dashboard 能打开，发消息时报错 | 看 `openclaw logs --follow` 里的模型请求错误，核对凭据、额度和网络。 |
| Dashboard 能回复，飞书无反应 | 先运行 `openclaw channels status --probe`，再核对飞书应用版本、可用范围、长连接及事件订阅。 |
| 飞书返回配对码 | 在 Gateway 上核对并批准自己的请求，再发一次消息。 |
| 日志收到消息，飞书仍没有回复 | 看日志区分模型处理失败与飞书发送失败。若发送返回权限错误，核对应用发送权限和生效版本。 |

如果同时排查多个环节，可以开着 `openclaw logs --follow`，再从飞书发一条带当前时间的测试消息，便于定位对应的日志。[OpenClaw 飞书排障文档](https://docs.openclaw.ai/channels/feishu/troubleshooting)

## 参考来源

- 本文的选题来自小傅哥的 OpenClaw 安装与飞书接入文章，流程按现行官方文档重新整理。[小傅哥《OpenClaw》](https://bugstack.cn/md/ai/openclaw.html)
