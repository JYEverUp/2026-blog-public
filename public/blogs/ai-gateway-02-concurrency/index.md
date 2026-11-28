系列导航：[第一篇 · 职责与架构](/blog/ai-gateway-01-architecture) / **第二篇 · 消息调度** / [第三篇 · 回复与等待](/blog/ai-gateway-03-streaming) / [第四篇 · 群聊上下文](/blog/ai-gateway-04-group-context) / [第五篇 · 图片与文件](/blog/ai-gateway-05-media)

> 本系列以面向中国华能集团的企业知识助手为设计场景，业务对话均为示例。代码节选与结构示意用于说明设计原因、作用和取舍，省略了无关细节。

## 用户发消息，通常不会一次说完

假设同事先发：“帮我找一下培训资料。”

隔一秒又发：“去年那次的。”

接着补一句：“只看安全培训。”

如果每条消息一到，就立即创建一个独立任务，这三个任务可能同时读写同一份上下文。有时后一句先完成，有时第一句的回答覆盖了后面的补充。用户看到的是三段互相对不上的回答。

但把所有人的消息塞进一条串行流程，也不合适。小李的检索慢，不应该让小王连一句简单问答都要等着。

所以，这里的目标有两个：**同一会话避免交错处理，不同会话尽可能并行。**

## 第一层：先把线程边界处理对

平台 SDK 不一定运行在 asyncio 主循环里。有些 SDK 在自己的线程中执行回调。如果回调直接操作异步队列或随意创建协程任务，问题往往不在业务逻辑，而在线程与事件循环的边界。

项目的 `ChannelManager.enqueue` 保存了主事件循环，通过：

```python
loop.call_soon_threadsafe(
    self._put_to_queue,
    queue,
    channel_id,
    payload,
)
```

把后续入队操作安排回事件循环线程。这段代码中的“threadsafe”不是修饰词，它决定了平台回调可以从哪里调用入口。

接入新 SDK 时，我会先搞清楚它的回调在哪个线程执行，再考虑业务处理速度。

## 第二层：队列接住消息，worker 负责处理

项目按渠道实例创建队列和 worker。默认配置是每渠道 4 个 worker、队列上限 1000。这只是当前默认值，不能当成压测结论或容量承诺。

队列可以暂时吸收接收速度与处理速度的差异；worker 数量则限制普通处理任务的并发数量。

![线程回调、渠道队列和会话锁](/blogs/ai-gateway-02-concurrency/scheduling.svg)

[下载调度图的 Mermaid 源文件](/blogs/ai-gateway-02-concurrency/scheduling.mmd)

这里很容易产生一个误解：队列先进先出，所以后面的所有执行就一定严格按接收顺序完成。实际上，多个 worker 取出消息后，还会经历解析、合并、锁前钩子等步骤。**互斥能防止同时进入临界区，却不能单独证明端到端严格顺序。**

如果业务要求每条指令严格按平台序号执行，还需要围绕序号、分区调度或每会话独立消费设计更明确的保证。

## 第三层：锁要锁住“会话”，不能锁住整个系统

项目用 `channel_id + session_key` 查找共享锁：

```python
lock_key = f"{channel_id}:{session_key}"
lock = self._session_locks.setdefault(lock_key, asyncio.Lock())
```

worker 在锁内调用渠道的 `handle_inbound`。

默认 `session_key` 来自回复目标的 `subject_id`。私聊时是用户；群聊时是群会话，因此群里的多人讨论默认共享同一条处理边界。

为什么还要带上 `channel_id`？因为平台 ID 并不一定全局唯一。两个机器人实例遇到相同字符串 ID，也不该无意中共用一把锁。

这是一种朴素但清楚的隔离方式：锁跟着实际会话目标走，渠道实例负责划定 ID 的命名空间。

## 把 worker 拆开看：它到底保护了哪一段

下面把调度主线压缩成一段结构示意。它省略了错误隔离、超时轮询和控制消息分支，重点看“取消息”和“处理消息”并没有被同一把全局锁包住。

```python
async def worker_loop(self, channel_id):
    queue = self._queues[channel_id]
    channel = self._channels[channel_id]

    while self._running:
        payload = await queue.get()
        message = channel.parse_inbound(payload)
        session_key = channel.get_debounce_key(message)

        batch = [message]
        if channel.should_batch_inbound(message):
            batch.extend(
                self._drain_same_session(
                    queue,
                    channel,
                    session_key,
                )
            )

        merged = (
            channel.merge_inbound(batch)
            if len(batch) > 1
            else message
        )

        async with self._session_lock(channel_id, session_key):
            await channel.handle_inbound(merged)
```

为什么锁放在处理调用外面？因为一次处理可能不只是模型生成，还包括读取上下文、写回结果和发送回答。如果模型部分互斥，写历史却在锁外，同一会话仍然可能观察到不完整状态。

为什么不让所有操作都持有全局锁？因为解析 A 的平台消息、处理 B 的知识问答，通常没有必须互相排斥的共享状态。把它们全锁住，会把一个异步系统退化成单任务执行器。

不过，锁内包含发送也有代价：平台发送变慢时，同会话下一轮也会等待。我会先把“本轮何时算结束”定义清楚，再决定是否拆分。对要求回答顺序清楚的聊天助手，发送仍属于本轮的一部分；对后台批处理任务，完成生成后异步投递可能更合理。

这段示意也刻意没有加入 `queue.task_done()`。如果系统依靠 `queue.join()` 做排空退出，就必须逐一核对每次取出的消息，包括合并时取出的额外消息，都有对应的完成计数。不能只在最外层补一行，就以为批处理计数自然正确。

## 为什么协程已经是单线程了，还需要锁

asyncio 常在一个线程中执行 Python 代码，但只要遇到 `await`，其他任务就可能接着运行。单线程避免了某些同时执行的情况，并不意味着一整段业务不会交错。

例如两个任务都先读取会话历史，然后各自等待模型返回。任务 A 等待期间，任务 B 也拿到了同一份旧历史。最后二者分别写回，可能让后一次写入覆盖前一次结果。

锁的作用，是跨越这些等待点，把需要观察一致状态的一次处理组织为互斥区间。它保护的是业务时序，不只是某一行内存操作。

但锁也只约束使用同一把锁的参与者。如果定时任务绕过管理器，直接修改会话历史，它不会自动受到保护。因此，主动任务若要与入站处理共享会话状态，应接入同一会话锁约定，而不是自己另建一个名称相似的锁。

## 连续消息合并，可以减少一些无效工作

用户分三次补充一个问题时，如果这几条已经连续积在队列里，项目会尝试取出同会话的消息，合并后交给处理器。当前额外最多取 20 条，避免一次无限扫队列。

这个实现有两个边界：

第一，它是对队列中已有连续消息的合并，不等同于“收到消息后固定等几秒，再收齐所有补充”。如果后一条在本轮处理已经开始后才到，它未必会被合并。

第二，遇到别的会话或控制消息，会把对应消息放回队列并停止本轮扫描。它不会为了凑齐某个人的消息，把整个队列翻一遍。

我觉得这个取舍适合先做小：能减少已经积压的碎片请求，行为又比较容易解释。代价是它既不保证最大合并率，也不适用于要求逐条留痕的指令流。

## 合并消息之前，要先问“合并会不会改变意思”

文字补充适合合并，不代表所有消息都适合。

假设用户发“创建新会话”，紧接着发一份资料。这两条之间存在状态切换，不能把它们拼成一个长字符串交给模型。类似地，`/stop` 是控制信号，拼到“帮我总结资料”后面，就可能从命令退化成普通正文。

群聊还有另一种风险：小李说“用去年版本”，小王说“我想看今年版本”。如果合并时只保留一份作者信息，模型会误以为是同一个人在改口。

因此，公共渠道有一个判断入口：

```python
def should_batch_inbound(self, message):
    return not self._group_context.handles(message)
```

这段逻辑让启用了群聊上下文管理的消息保留独立事件身份。它牺牲一部分合并机会，换取作者归属和上下文顺序的可解释性。

我会把合并看成一种有条件的优化，而不是收消息的默认真理。必须逐条审计的指令、涉及身份切换的消息、需要单独确认的业务动作，都应该先保证语义，再谈减少调用次数。

## worker 数量不是越大越好

如果一次处理主要在等待网络，增加 worker 往往能提高不同会话同时推进的机会；如果瓶颈在模型配额或存储，继续增加 worker 可能只是让更多请求一起等待。

可以做一个粗略的容量推演。假设四个 worker，一次普通任务平均占用八秒，那么在理想独立、没有会话锁争用的条件下，处理能力大约是每秒半条。若流入速率持续高于这个量级，队列迟早增长。

这只是帮助理解的算例，没有测量依据时不能作为实际容量。任务耗时分布、外部 API 并发限制和热门会话比例，都会改变结果。

有界队列的目的也不是保证不丢，而是为内存增长划一道边界。到达边界时，需要明确选择：拒绝、丢弃、落盘，还是让上游减速。当前入口采用非阻塞入队和记录丢弃，优点是 SDK 回调不会长时间卡住；代价是消息可能无法交付。

我会分别观察“收到多少、入队多少、开始多少、完成多少”，并记录队列等待时长。只有一个“请求耗时”指标，无法分清用户是在排队，还是模型真正生成得慢。

## “停止”不能等正在停止的任务先结束

这是整条链路里最值得单独画图的地方。

假设检索任务拿着会话锁运行，用户发来 `/stop`。如果停止指令也必须拿到同一把锁，结果就是：只有等原任务做完，才能告诉它停止。

![停止指令绕过繁忙 worker 的时序](/blogs/ai-gateway-02-concurrency/interrupt.svg)

[下载停止链路的 Mermaid 源文件](/blogs/ai-gateway-02-concurrency/interrupt.mmd)

项目提供了两个不同的入口：

- **锁前钩子 `on_pre_lock`**：worker 拿到消息后，在竞争会话锁之前，先让宿主处理控制信号。
- **紧急消息旁路 `interrupt_message_predicate`**：在事件循环入队入口识别紧急消息，创建独立任务处理，绕过普通队列和会话锁。

只有一个 worker 且它正忙时，锁前钩子也需要等待 worker 取到下一条消息；紧急旁路解决的是更前面这一层等待。

旁路并不自动知道如何取消模型请求。宿主仍然需要保存任务句柄、识别目标会话，并完成实际取消和清理。也不能把所有命令都标成紧急消息：重置会话、修改状态等操作如果随意绕过锁，反而会制造并发写入。

## 紧急任务为什么要被一个集合持有

绕过普通队列后，紧急消息仍然是后台任务。创建后不保存句柄，会让关闭时的清理、状态观察和异常追踪变得困难。

调度入口可以采用下面这种结构，示例只展示任务持有方式：

```python
task = asyncio.create_task(
    self._run_interrupt(channel_id, channel, message),
    name=f"gateway-interrupt-{channel_id}",
)
self._interrupt_tasks.add(task)
task.add_done_callback(self._interrupt_tasks.discard)
```

集合保存运行中的任务，完成回调及时移除，避免完成任务一直被引用。独立处理入口还需要记录普通异常，让一条畸形控制消息不会破坏后续处理。

当管理器退出时，也应当取消并等待这些任务结束。否则普通 worker 都关闭了，紧急任务还可能在访问已经关闭的连接。

这说明“走旁路”只改变调度顺序，没有免除任务生命周期管理。

## 收到停止信号，和撤销业务动作是两回事

宿主可以为每个会话保存一个专门的业务子任务。下面是停止请求的简化处理，`running_tasks` 中放的是业务子任务，不能随意把长期运行的渠道 worker 当成取消目标。

```python
async def request_stop(key, running_tasks):
    task = running_tasks.get(key)
    if task is None or task.done():
        return False

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    return True
```

`cancel()` 发出取消请求，等待任务退出才更接近“本地执行已停止”。如果任务内部吞掉取消异常，或者正在做不能及时中断的同步操作，停止仍然可能延迟。

还有一个业务边界：本地任务停止，不代表刚刚提交给外部系统的动作被回滚。查询资料通常可以直接终止等待，但如果已经创建工单，就需要单独确定工单状态，而不能给用户一个笼统的“已全部撤销”。

在这个设计场景里，我会先把助手限制为只读知识问答，再为写操作设计明确的确认与结果查询。停止链路因此更容易解释，也能把取消和业务补偿分开。

## 我更想看行为测试，而不是“睡两秒没出错”

仓库有一个很有说明力的测试：`test_interrupt_message_bypasses_busy_session_worker`。

它用 `asyncio.Event` 暂时挂住普通任务，确认普通任务已经开始，再发出 `/stop`。测试要求停止消息在普通任务尚未释放时就被观察到。

这验证的是“绕过繁忙 worker”的行为，而不是测试机器刚好跑得快。它没有声称底层业务真的取消成功，两者应当分开验证。

相关的另两项测试检查：控制消息不会并入普通文本；配置控制消息识别后，普通文本仍然能够正常合并。一个入口的加入，不该悄悄关掉另一项原有能力。

可在项目环境中复现：

```bash
uv run pytest tests/test_manager.py -k "interrupt or control or pre_lock or run_in_session"
```

## 用可控事件，复现“还没做完就收到停止”

下面是一个独立的异步测试示例，用最少对象说明验收目标。它验证的是停止通知能够在普通任务完成之前到达，不是完整网关的集成测试。

```python
import asyncio

import pytest


@pytest.mark.asyncio
async def test_stop_can_arrive_before_work_finishes():
    started = asyncio.Event()
    release = asyncio.Event()
    stop_seen = asyncio.Event()

    async def work():
        started.set()
        await release.wait()

    async def handle_stop():
        stop_seen.set()

    work_task = asyncio.create_task(work())
    try:
        await asyncio.wait_for(started.wait(), timeout=1)

        stop_task = asyncio.create_task(handle_stop())
        await asyncio.wait_for(stop_seen.wait(), timeout=1)

        assert not work_task.done()
        await stop_task
    finally:
        release.set()
        await work_task
```

这段测试先建立“工作确实已经开始”的前提，再触发停止。相比固定睡眠，它不会把调度快慢当成正确性的证据。

在真实管理器测试里，还要把独立的 `handle_stop` 替换成公开的入队入口，并配置紧急消息识别。这样才能验证是系统旁路生效，而不只是 Python 能同时运行两个协程。

## 这套方案还没有解决所有拥堵问题

我不会因为有了队列和锁，就把它描述成可靠消息系统。

目前队列在内存中，满了会记录日志并丢弃，进程重启也没有持久化回放。多个 worker 还可能都在等待同一个热门会话的锁，让其他会话暂时得不到处理机会。锁注册表也需要结合长期运行的会话数量评估回收策略。

如果只是有限用户范围的第一版，我会先观察队列长度、等待时间和丢弃次数。等确认瓶颈是热门会话占住 worker，再考虑按会话调度；如果要求重启后不丢消息，再设计持久化、确认与重试。

一次把消息队列、中间件和分布式锁全部加进来，并不能免掉这些语义上的判断。

这一篇可以结合管理器的入队、worker、会话锁与紧急消息入口阅读。代码示例用于解释关键调度关系，省略的生命周期与错误处理仍需在实际系统中落实。

队列解决的是“轮到谁处理”。用户真正感受到的，还有“轮到我之后，为什么半天没有反应”。下一篇继续看这段等待。

继续阅读：[回答还没出来，先让用户知道系统在工作](/blog/ai-gateway-03-streaming)。
