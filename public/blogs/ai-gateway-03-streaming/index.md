系列导航：[第一篇 · 职责与架构](/blog/ai-gateway-01-architecture) / [第二篇 · 消息调度](/blog/ai-gateway-02-concurrency) / **第三篇 · 回复与等待** / [第四篇 · 群聊上下文](/blog/ai-gateway-04-group-context) / [第五篇 · 图片与文件](/blog/ai-gateway-05-media)

> 本系列以面向中国华能集团的企业知识助手为设计场景，业务对话均为示例。代码节选与结构示意用于说明设计原因、作用和取舍，省略了无关细节。

## 沉默十秒，用户已经开始怀疑了

员工问：“帮我整理这几份培训材料的差异。”

处理器可能要读取文件、检索资料、组织回答。对程序来说，这是正常工作；对聊天窗口前的人来说，只能看到自己刚发出的那句话。

用户很容易再问一次：“收到没有？”然后系统又多了一次请求。

所以，“让模型更快”之外，还有一个独立的问题：**等待期间，用户能否知道系统仍在工作？** 我会把它作为交付链路的设计内容，而不是最后补的一条文案。

## 先分清三种反馈

| 反馈方式 | 用户看见什么 | 适合表达什么 |
| --- | --- | --- |
| typing 状态 | 对方正在输入 | 系统仍然活跃 |
| 占位回复 | “正在整理资料，请稍等” | 已接收任务，暂时没有结果 |
| 正文增量更新 | 答案逐渐出现 | 已经产生可交付内容 |

三者不能互相替代。typing 不承诺答案马上完成，占位消息也不是一次业务成功。至于内部思考信息，默认没必要全部展示；真正对用户有帮助的是明确、克制的进度。

平台支持情况也不同。有的平台有 typing API，有的平台适合更新同一条消息，有的平台只适合发送完整文本。设计时应先确认实际能力，再决定呈现方式。

## 处理器产生事件，渠道决定怎么显示

如果处理器只返回一个字符串，网关只能等它全部完成。项目让 `MessageProcessor` 返回异步事件流，于是交付层可以区分：

- `DELTA`：一小段正文。
- `MESSAGE`：一条完整消息。
- `FLUSH`：把当前缓冲内容发出去。
- `TOOL_START`、`TOOL_END`：工具活动状态。
- `ERROR`、`COMPLETED`：错误与结束。

下面的示意处理器只说明事件接口，不包含真实检索：

```python
async def processor(message):
    yield MessageEvent.typing()
    yield MessageEvent.delta("我先把资料分成")
    yield MessageEvent.delta("三个部分。")
    yield MessageEvent.completed()
```

不过，有事件流不代表用户一定看到逐字输出。默认 `BaseChannel` 会积累正文增量，在刷新、完整消息或完成等节点发送；企微适配器则使用 `reply_stream` 逐步更新同一个流。

![同一事件流的两种交付方式](/blogs/ai-gateway-03-streaming/delivery.svg)

[下载事件交付图的 Mermaid 源文件](/blogs/ai-gateway-03-streaming/delivery.mmd)

这个区别看似细小，却决定了产品承诺：接入新渠道后，必须实际观察输出，不能只因为处理器用了异步生成器，就写“所有渠道均支持原生流式回复”。

## 为什么不把每个 token 都直接发成消息

模型的输出粒度和聊天平台的交付粒度，通常并不一致。一小段增量有时只有几个字，如果每段都发送，用户会收到一串通知，平台也会承受大量请求。

我会先用缓冲把这两件事解开：处理器照常输出细粒度事件，交付层按适合平台的节奏发送。下面是一个只演示正文缓冲的函数，省略工具事件和媒体：

```python
async def deliver_events(events, emit_text):
    buffer: list[str] = []

    async def flush():
        if not buffer:
            return
        text = "".join(buffer)
        buffer.clear()
        await emit_text(text)

    async for event in events:
        if event.type == MessageEventType.DELTA:
            buffer.extend(
                part.text
                for part in event.content
                if isinstance(part, TextContent)
            )
        elif event.type == MessageEventType.FLUSH:
            await flush()
        elif event.type == MessageEventType.COMPLETED:
            await flush()
            return
```

这里用列表积累片段，在发送节点一次拼接。它让“模型已经生成了一些内容”和“现在应该对用户发送一条消息”不再绑在一起。

为什么 `FLUSH` 要成为一种事件？因为有时处理器已经完成一个有独立意义的段落，后面却还要执行工具。交付层仅靠猜测字符串长度，很难知道这个边界。显式刷新让业务处理器表达“这部分现在可以交付”。

代价是协议更丰富了。处理器和渠道必须约定：完整消息到来时，旧缓冲如何处理；错误之前的半段内容要不要保留；完成事件能否重复。这些问题需要通过测试固定下来，而不是让每个平台自由理解。

## 原生流式更新，发送的未必是“新增那几个字”

以更新同一条消息的协议为例，模型刚输出“资料有三个部分”，随后又输出“，第一部分……”。平台接口可能要求每次提交当前完整文本，而不是只提交新增片段。

```python
content_buffer: list[str] = []

async for event in events:
    if event.type != MessageEventType.DELTA:
        continue

    for part in event.content:
        if isinstance(part, TextContent):
            content_buffer.append(part.text)

    current_text = "".join(content_buffer)
    if current_text:
        await client.reply_stream(
            frame=frame,
            stream_id=stream_id,
            content=current_text,
            finish=False,
        )
```

`stream_id` 把这些请求关联到同一条用户可见消息，`finish=False` 表达尚未结束。这段结构与普通渠道“缓冲后发一次”不同，但不需要改变处理器输出的事件类型。

每次拼出完整文本也有成本。长答案、细碎增量会导致反复拼接和重复传输。若实际观察到接口频率或带宽压力，我会在交付层合并一小批增量，按时间或内容边界刷新，同时保留结束时的最终更新。

这是一项后续优化建议，不代表当前实现已经具有自动合并刷新功能。先把平台到底接收增量还是快照确认清楚，再讨论刷新间隔，能少走很多弯路。

## 超时的是这次等待，不一定是整个任务

处理长任务时，我最想避免的一个错误，是为了发送占位消息，反而把真正的生成任务取消了。

企微的实现会创建一个任务来读取处理器的第一个事件，然后用 `asyncio.wait` 等待一段时间。当前时间点是 `reply_timeout * 0.8`，它是提前反馈的策略，不应当当成外部平台永久不变的硬性规则。

如果这段时间内没有首个事件，先尝试发送占位回复，再继续等待原来的任务。

![先给反馈、再继续等待原任务](/blogs/ai-gateway-03-streaming/timeout.svg)

[下载超时处理图的 Mermaid 源文件](/blogs/ai-gateway-03-streaming/timeout.mmd)

以下是省略平台细节的逻辑示意：

```python
first_task = asyncio.create_task(iterator.__anext__())
done, _ = await asyncio.wait([first_task], timeout=feedback_deadline)

if not done:
    await send_placeholder()

first_event = await first_task
```

`asyncio.wait_for` 在超时时通常会取消被等待的任务；如果目标只是结束这一段等待，而希望生成继续，直接套用它就会改变业务含义。也可以用其他方式保护任务，但这里显式保留句柄，比较容易读懂。

还有一个需要准确命名的地方：代码等待的是**第一个处理器事件**。它可能是正文，也可能是 typing 或工具提示，因此不能把这一段机制等同于严格的“首个正文 token 时限”。

占位发送本身也可能失败。当前企微实现会捕获这次失败并继续等待生成。这避免了把“反馈没送到”误当成“生成不该继续”。

## 为什么“已经收到事件”还不等于“用户已经看到正文”

可以把一次处理分成几个时间点：消息被接收、处理器开始、首事件出现、首段正文出现、第一次发送成功、最终回复结束。

这些时间点看起来很接近，出问题时却能区分完全不同的原因：

| 等待发生在哪里 | 可能原因 | 优先检查 |
| --- | --- | --- |
| 接收后迟迟没开始 | 队列拥堵或会话锁等待 | 排队时间和 worker 状态 |
| 开始后没有正文 | 检索、工具或模型耗时 | 各阶段耗时 |
| 有正文但发不出去 | 限流、平台连接或协议问题 | 发送等待与失败记录 |
| 已发送但一直不结束 | 结束事件或清理路径缺失 | 任务状态与事件流关闭 |

这也是为什么我不想只打一个“总耗时”。平均总耗时相同，用户体验可能完全不同：一个系统几秒就开始显示内容，另一个系统到最后才一次吐出来。

占位反馈的触发条件也应跟着目标定义。如果产品要求“几秒内让用户看到任何反馈”，首事件可能够用；如果要求“尽快看到有效答案”，就要观察首段正文，而不能被工具状态提前满足条件。

## 把反馈计时和任务截止时间分开

“等一会儿先告知用户”和“任务最多运行多久”是两套规则。

前者到期后生成可以继续；后者到期后则需要终止本地任务或进入明确的超时状态。把它们共用一个 timeout，很容易出现占位刚发出、真正任务却被取消的矛盾。

下面展示一种更完整的首事件等待结构。它是针对退出清理的设计示例，不表示所有渠道已经按此实现：

```python
async def read_first_event(iterator, delay, send_placeholder):
    first_task = asyncio.create_task(iterator.__anext__())
    try:
        done, _ = await asyncio.wait(
            {first_task},
            timeout=delay,
        )
        if not done:
            try:
                await send_placeholder()
            except Exception:
                logger.exception("Placeholder delivery failed")

        return await first_task
    finally:
        if not first_task.done():
            first_task.cancel()
            try:
                await first_task
            except asyncio.CancelledError:
                pass
```

这个结构把首事件任务从创建开始就纳入清理范围。外层被取消时，不会只结束等待函数，却把子任务留在后台。首事件之后仍需要由上层负责继续消费或关闭整个迭代器。

异常处理也有意限定在占位发送上。占位失败只影响一条反馈，不应直接取消生成；真正的处理器异常则继续向上传递，由上层统一决定错误呈现和收尾。

这类代码最难的地方往往不是正常路径，而是“用户在占位发送期间点了停止”这样的交叉时机。把子任务所有权写清楚，才能知道退出时谁负责取消谁。

## 限流额度应该在哪里获取

发一条由文字和图片组成的消息时，外层可能调用 `reply_content`，内部再调用 `_send_text` 和 `_send_media`。

如果每一层都获取额度，一次逻辑发送就可能重复等待，特别是限额很紧时，问题会变得难以理解。

项目把职责分为两层：

- 公共的 `reply_*`、`push_*` 获取额度。
- 适配器中的 `_send_*` 执行发送，内部互相调用时不重复获取。

企微的流式回复也在整个流开始前获取一次额度，把多次更新视作同一条逻辑消息。

我会同时记下这个选择的边界：**一次逻辑消息，不一定等于一次 HTTP 或 SDK 请求。** 如果某个平台限制的是每秒接口调用次数，流式更新频率、分片发送和媒体上传还需要单独适配。公共层的一次计数不能替代全部平台配额管理。

## 从两段代码看懂“谁获取额度”

公共发送入口可以很短：

```python
async def reply_content(self, subject, parts):
    await self._acquire_rate_slot()
    await self._send_content(subject, parts)
```

适配器内部再拆分内容时，调用的是平台发送原语：

```python
async def _send_content(self, subject, parts):
    for part in parts:
        if isinstance(part, TextContent):
            await self._send_text(subject, part.text)
        else:
            await self._send_media(subject, part)
```

这样外层承担计量责任，内层承担协议责任。如果第二段改成调用 `self.reply_text`，就把公共入口再次嵌进去，额度会按内部拆分重新获取，单次逻辑发送可能经历多次等待。

这里的意义，是让计量单位可解释。先定义什么叫一次发送，再选择放在哪里计量，而不是见到发送代码就随手加一行限流。

项目的基础限流器使用滑动时间窗：记录最近发送时刻，清理窗口外记录；额度满时，等最旧记录离开窗口，再记录本次发送。计时采用单调时钟，避免系统时间被校准后影响间隔计算。

滑动窗口比“每分钟清零”更贴近最近一段时间的真实发送量，但等待者的公平性、不同消息优先级、平台接口粒度，仍然需要结合应用设计。比如停止确认是否允许优先发送，就是业务选择，不会被一个通用限流器自动回答。

## 失败以后，应该给用户看什么

如果已经输出了半段答案，再发生检索错误，我不希望系统突然装作一切完成。更合适的表现是保留已生成内容，并给出能够理解的状态，例如“当前资料读取未完成，请稍后重试”。

不过，部分内容也可能尚未经过业务校验。是否允许先展示，需要处理器决定。对普通摘要，逐步显示通常容易接受；对需要完整校验的结论，可以只展示进度，等结果确认后再发送正文。

错误提示还要区分给用户看和给维护者看。用户需要知道是否能继续、是否要重试；维护者需要关联 ID、失败阶段与异常记录。把完整堆栈直接发到群里，既难读，也不能代替服务端诊断。

我会让处理器输出结构化错误事件，渠道负责用统一方式交付。这样同一项业务失败，在不同入口至少有一致的状态含义。

## 回复结束以后，后台任务也要结束

typing、超时计时器、处理器事件流都有自己的生命周期。如果回复完成后 typing 还在不断发送，用户会觉得机器人没结束，后台也会持续做无用功。

默认处理链路在 `finally` 中取消超时辅助任务、停止 typing，并关闭事件流。设计上，我会把正常完成、处理异常、外部取消都当成需要检查的退出路径。

但不能因为一个地方出现了 `finally`，就认定所有路径已经覆盖。当前企微读取首事件的阶段发生在后续流循环的 `try/finally` 之前；如果继续做生产加固，我会专门检查这段等待中取消任务时，子任务和迭代器能否完整收尾。

## 我会怎么验收用户体验

我会准备三个可控的处理器：立即回答、等待后回答、输出一部分后抛错。然后逐个渠道观察：

1. 正文还没来时，有没有适合该平台的反馈。
2. 占位发出后，原来的回答是否继续。
3. 多个增量是更新同一条消息，还是形成多条完整消息。
4. 完成或异常后，typing 和计时器是否停止。
5. 一次公共发送是否重复获取额度。

仓库中的 `tests/test_constraints.py` 验证限流、超时和 typing；`tests/test_channel.py` 检查缓冲刷新及单次获取额度；企微测试覆盖流式交付路径。测试能证明特定行为，真实平台的窗口和频率仍需要接入环境验证。

这一篇可以结合公共渠道的事件消费、发送约束和平台流式实现阅读。不同代码块分别解释局部职责，不应直接拼成一套未经验证的生产实现。

我希望等待设计做到的，是用户能理解当前状态。至于机器人该不该对群里的每句话都反馈，是另一个需要单独决定的问题。

继续阅读：[听得到群聊，不等于每句话都要回答](/blog/ai-gateway-04-group-context)。
