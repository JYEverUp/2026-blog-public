Dify 的语音自动播放开关已经打开，模型也配置好了，文字回答正常，却经常没有声音；有时手动点朗读又能播放。这类问题很容易先怀疑浏览器权限，但这次排查定位到了后端流式事件顺序和 TTS 等待时间两处问题。

本文根据本地 Dify **1.13.3 定制部署**的源码、2026-10-27 的事件顺序补丁和 2026-11-05 的等待时间修复包整理。涉及 Linux amd64 Docker 镜像，以及原有 3001 端口的 webapp2 页面。这里记录的是这套部署的修复方式，其他版本应先核对源码，不能直接套用镜像标签或断定同样存在问题。

## 一、先分清：没有生成音频，还是浏览器没有播放

自动朗读大致经过这条链路：

```text
发送消息 → 工作流输出文字 → TTS 插件合成音频
                                  ↓
浏览器播放 ← 前端接收音频块 ← API 通过 SSE 推送
```

手动朗读通常会重新发起语音请求，而自动朗读依赖当前回答流中的音频事件。因此，手动能读，只能说明模型和播放链路至少有一条路径可用，不能证明自动朗读的 SSE 数据完整。

排查时先打开浏览器开发者工具，在 Network 里找到这次对话的流式请求，检查事件和音频内容：

| 观察结果 | 优先检查 |
| --- | --- |
| 没有 `tts_message`，也没有有效音频数据 | 自动播放配置、TTS 插件、后端等待时间 |
| `workflow_finished` 先到，音频还没发送完 | 后端事件顺序，以及前端是否提前结束消费 |
| 有完整音频，控制台出现 `NotAllowedError` | 浏览器自动播放权限、用户交互、iframe 权限 |
| 有音频但格式不支持或解码失败 | 音频格式、MIME 类型、MediaSource 支持情况 |
| 能播放，但说话太慢 | 模型合成语速或播放器倍速 |

这次后端修复针对前两类。浏览器权限和模型语速是另外的处理点。

## 二、问题一：工作流结束事件发得太早

文字生成和语音合成不是同步完成的。文字回答结束时，TTS 可能还在处理最后一段内容。

原有包装逻辑在遍历工作流响应时直接 `yield response`，这会把 `workflow_finished` 提前送给客户端，之后才继续收集尾部音频。对于把这个事件视为本次请求终点的客户端，后面的音频就可能丢失。

```text
存在问题的顺序：文字 → workflow_finished → 尾部音频
修复后的顺序：文字 → 剩余 tts_message → tts_message_end → workflow_finished
```

音频可以与前面的文字事件交错发送；关键约束是：启用了自动朗读时，剩余音频和音频结束事件要在工作流结束事件之前送达。

### 修改哪些文件

这套源码中，两类应用各有一份包装逻辑：

- `api/core/app/apps/advanced_chat/generate_task_pipeline.py`
- `api/core/app/apps/workflow/generate_task_pipeline.py`

两处的 `_wrapper_process_stream_response()` 都需要处理。只修其中一个，另一类应用仍可能出现同样的问题。

### 修改思路：暂存结束事件，收完音频再发

下面是关键改动摘录，省略了已有的音频监听循环，不能直接当成完整函数覆盖：

```python
# 在已有的 task_entities 导入列表中补充 StreamEvent。
terminal_response: StreamResponse | None = None

# 遍历工作流响应时，保留原有的即时音频分发逻辑。
if tts_publisher and response.event == StreamEvent.WORKFLOW_FINISHED:
    terminal_response = response
else:
    yield response

# 原有的尾部音频监听循环放在这里，继续发送 MessageAudioStreamResponse。

if tts_publisher:
    yield MessageAudioEndStreamResponse(audio="", task_id=task_id)

if terminal_response is not None:
    yield terminal_response
```

`tts_publisher` 只在语音与自动播放均启用时创建。未启用自动朗读时，结束事件仍直接发送，避免普通文字回答也被拖延。

即使 TTS 报错或超时，也要让响应正常收尾，不能一直扣住 `workflow_finished`。此外，`tts_message_end` 代表音频传输结束，并不代表浏览器扬声器已经播完；播放状态仍应由播放器事件决定。

## 三、问题二：5 秒等待窗口容不下较慢的语音合成

修正事件顺序后，还有一种情况：文字已经出来，TTS 却迟迟没有返回首个音频块。原来的等待窗口只有 5 秒，云端模型较慢或插件刚启动时，可能在音频到来前就结束等待。

本次修改的是：

```text
api/constants/tts_auto_play_timeout.py
```

```diff
-TTS_AUTO_PLAY_TIMEOUT = 5
+TTS_AUTO_PLAY_TIMEOUT = 30
```

轮询让出 CPU 的时间保持原值：

```python
TTS_AUTO_PLAY_YIELD_CPU_TIME = 0.02
```

**30 秒是尾部音频监听阶段连续没有新音频的等待上限，不是整段语音时长限制，也不是从点击发送开始计算的总超时。** 源码在收到新的音频块后会重置计时；持续有数据的长语音可以超过 30 秒。

这是一处 Python 常量修改。只在 `.env` 里加同名变量不会自动生效，除非另行修改代码读取它。改完也需要重建或更新实际运行的镜像、重建对应容器，不能只改宿主机源码。

延长等待会让慢 TTS 有机会返回，也会让故障时的请求保持更久。30 秒仍然是有限等待；它不能解决插件启动失败、鉴权失败或服务不可达。若经常触发上限，应继续检查模型首包延迟和插件日志。

## 四、部署：先确认基础镜像已经包含事件顺序修复

本次有两层修改，不能混为一谈：

| 修改层次 | 本地对应镜像 | 内容 |
| --- | --- | --- |
| 事件顺序修复 | `local/dify-api:1.13.3-tts-autoplay-20261027` | 两类 pipeline 暂存工作流结束事件 |
| 等待时间修复 | `local/dify-api:1.13.3-tts-wait30-20261105` | 在上一层基础上将 5 秒改为 30 秒 |

这些是本地自建镜像标签，不能直接去公共镜像仓库拉取。11 月 5 日修复包里的 Dockerfile 只复制超时常量文件，因为它的基础镜像已经包含事件顺序修复。若从未修复的官方镜像起步，需要把两处 pipeline 修改和常量修改一起纳入自己的构建流程。

### 使用已经交付的离线修复包

修复包名为 `dify-tts-autoplay-20261105.zip`，内含完整镜像、Compose 覆盖文件、验收脚本及相关源码。本篇不把大型镜像上传到博客仓库；下面命令用于已经取得该修复包的环境。

解压后，在修复包目录导入镜像：

```bash
docker load -i image.tar
```

将 `compose.tts-autoplay.yaml` 复制到现有 Dify 的 Docker 部署目录。内容为：

```yaml
services:
  api:
    image: local/dify-api:1.13.3-tts-wait30-20261105
  worker:
    image: local/dify-api:1.13.3-tts-wait30-20261105
```

在部署目录执行：

```bash
docker compose -f docker-compose.yaml -f docker-compose.override.yaml -f compose.tts-autoplay.yaml up -d --no-deps api worker
```

没有 `docker-compose.override.yaml` 时，省略对应的 `-f` 参数。已有自定义覆盖文件则继续带上，保持原有配置，并核对最终合并结果。

本次统一更新 API 与 worker 的后端镜像；自动朗读响应的关键修复发生在 API。此次补丁不需要更新原有 3001 页面对应的 webapp2，也不涉及数据库迁移。

**后续执行 Compose 时，要继续追加语音覆盖文件，或者把新镜像版本合并进长期使用的 override。** 否则下一次操作可能重新切回旧镜像。

## 五、验收：不能只看开关，也不能只看结束事件

### 1. 确认运行容器加载了新常量

部署后先核对镜像与常量：

```bash
docker compose -f docker-compose.yaml -f docker-compose.override.yaml -f compose.tts-autoplay.yaml images api worker

docker compose exec -T api python -c "from constants.tts_auto_play_timeout import TTS_AUTO_PLAY_TIMEOUT; print(TTS_AUTO_PLAY_TIMEOUT)"
docker compose exec -T worker python -c "from constants.tts_auto_play_timeout import TTS_AUTO_PLAY_TIMEOUT; print(TTS_AUTO_PLAY_TIMEOUT)"
```

本部署没有变更 Compose 项目名或服务名，后两条命令可直接定位现有容器；使用自定义 `-p` 或其他项目配置时，请保持相同参数。两处常量应输出 `30`。这只能证明等待配置生效，不能单独证明事件顺序正确。

### 2. 检查 SSE 中存在有效音频

对一条新消息，至少检查：

- `tts_message` 中存在可以解码、总字节数大于零的音频。
- 音频块出现在 `tts_message_end` 之前。
- `tts_message_end` 出现在 `workflow_finished` 之前。

只有结束事件而没有有效音频，也可能是 TTS 超时或失败后的正常收尾，不能视为朗读成功。

修复包里的 `verify_tts.py` 会通过自定义 webapp 的代理接口发送一条测试消息，统计音频字节、音频事件数量、首包时间及事件顺序：

```bash
python verify_tts.py --url http://localhost:3001/difyapps --api-url http://api:5001/v1 --app-code APP_CODE
```

将 `APP_CODE` 替换成实际应用分享码。`--url` 要能从执行脚本的机器访问；`--api-url` 会传给 webapp 代理，因此需要从代理容器访问得通。示例中的 `api` 是 Docker 网络里的服务名，不是任意宿主机都能解析的地址。

这个脚本使用 `/api/passport`、`/api/chat-messages` 和该 webapp 的请求头约定，不能直接当作所有 Dify 部署的通用 API 脚本；存在必填应用输入时，也需调整脚本中的 `inputs`。

### 3. 在真实浏览器里听一次

流式脚本验证的是传输，最后还需要在实际页面发送新消息，确认可以听到声音、尾部没有截断，并测试连续多轮。全量重启 Docker 后，先等提供商插件加载完成再测。

已有回归测试覆盖了两类 pipeline 的正常音频、模拟 10 秒延迟音频、TTS 异常、超过 30 秒等待，以及关闭语音或自动播放的情况。它们验证事件顺序和退出行为；不能替代真实云端模型、网络和浏览器的验收。

## 六、音频到了仍然无声：再处理浏览器策略

如果 SSE 音频完整，而 `audio.play()` 返回的 Promise 被拒绝，应根据错误继续排查。`NotAllowedError` 可能表示当前环境不允许播放；设置 `autoplay = true` 不保证一定能够有声播放。详见 [MDN 的 play() 文档](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/play)。

播放器可以在明确的用户点击中恢复暂停的 `AudioContext`、调用 `play()`，并处理失败提示。使用跨域 iframe 时，还需核对嵌入方的自动播放权限；Chrome 的相关规则见 [官方自动播放策略说明](https://developer.chrome.com/blog/autoplay/)。

这些是前端排查方向，本次后端补丁没有实现新的点击解锁逻辑。只有确认音频已经到达，才应把重点转向播放权限、静音状态、音频格式和输出设备。

## 七、语速慢是另一个修改点

“等很久才开始说话”和“开始后说得慢”是两个指标：前者看合成首包延迟，后者看合成语速或播放倍速。延长超时不会让说话速度变快。

本地使用的 SiliconFlow `0.0.65` 定制插件另有语速修改：在提供商配置声明 `tts_speed`，在 `models/tts/tts.py` 读取并转成数字，默认值为 `1.0`，校验范围为 `0.25` 到 `4.0`，再将 `speed=speed` 传入语音合成请求。长文本分段和普通文本两个分支都需要传参。

这里的范围来自本地插件校验，具体模型是否支持该参数仍需实际确认。它不是 Dify 所有 TTS 提供商共有的配置，也没有包含在上述后端等待补丁中。若要迁移语速功能，应重新打包并安装对应插件，不要只修改运行目录后就认为下次重装仍会保留。

## 八、回滚与后续排查

修复包中的 `compose.rollback.yaml` 会把 API 和 worker 切回本机上一版镜像：

```yaml
services:
  api:
    image: local/dify-api:1.13.3-tts-autoplay-20261027
  worker:
    image: local/dify-api:1.13.3-tts-autoplay-20261027
```

保留旧镜像，在部署目录执行：

```bash
docker compose -f docker-compose.yaml -f docker-compose.override.yaml -f compose.rollback.yaml up -d --no-deps api worker
```

这次回滚只撤销 30 秒等待调整，仍保留此前的事件顺序修复。随后同步恢复长期使用的 override 配置，避免下一次操作再次切换版本。

后续再遇到自动朗读无声，可以按同样顺序定位：先确认应用启用了语音与自动播放，再查插件是否成功生成音频，接着查 SSE 是否把音频完整送到终点之前，最后检查浏览器是否允许播放。这样每一步都有可观察的数据，也能区分到底需要改配置、后端、插件，还是播放器。
