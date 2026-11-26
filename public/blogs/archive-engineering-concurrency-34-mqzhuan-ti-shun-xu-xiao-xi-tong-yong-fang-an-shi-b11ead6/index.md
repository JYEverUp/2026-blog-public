#  MQ顺序消息通用方案 & 代码落地
## 什么是顺序消息
投递消息的顺序和消费消息的顺序一致。
比如生产者按顺序投递了1/2/3/4/5 这 5 条消息，那么消费的时候也必须按照1到5的顺序消费这些消息。
## 顺序消息如何实现？（2种方案）
1. 方案1：生产者串行发送+同一个队列+消费者单线程消费
2. 方案2：生产方消息带上连续递增编号+同一个队列+消费按编号顺序消费消息
## 方案1：生产者串行发送+同一个队列+消费者单线程消费
### 生产者串行发送消息
- 使用分布式锁，让消息投递串行执行
- 确保顺序消息到达同一个队列
### 消费者单线程消费
- 消费者这边只能有一个线程，拉取一个消费一个，消费完成后再拉取下一个消费
## 方案2：生产方消息带上连续递增编号+同一个队列+消费按编号顺序消费消息
### 生产方消息带上连续递增编号
- 顺序消息携带连续递增的编号，从1开始，连续递增，比如发送了3条消息，编号分别是1、2、3，后面再投递消息，编号就从4开始了
- 确保顺序消息到达同一个队列
### 消费方按照编号顺序消费消息
- 消费方需要记录消息消费的位置：当前轮到哪个编号的消息了
- 收到消息后，将消息的编号和当前消费的位置对比下，是不是轮着这条消息消费了，如果是则进行消费，如果不是，则排队等待，等待前一个到达后，且消费成功后，将自己唤醒进行消费
这里举个例子，如下
- 生产者发送了编号为看1、2、3 的3条消息
- 到达的消费端顺序刚好相反，3先到，发现没有轮到自己，会进行排队
- 然后2到了，发现也没有轮到自己，也会排队
- 然后过了一会1到了，发现轮到自己了，然后1被消费了
- 1消费后，会唤醒下一个编号的2进行消费
- 2消费完了，会唤醒下一个编号的3进行消费。
本文我们会落地方案2。
## 先看效果，然后再带大家看源码
### 发送顺序消息
如下模拟发送订单相关的5条顺序消息
```java
com.itsoku.lesson034.controller.TestController#sendSequential
@PostMapping("/sendSequential")
public Result<Void> sendSequential() {
    String orderId = IdUtil.fastSimpleUUID();
    List<String> list = Arrays.asList("订单创建消息",
            "订单支付消息",
            "订单已发货",
            "买家确认收货",
            "订单已完成");
    for (String type : list) {
        msgSender.sendSequentialWithBody(orderId,
                RabbitMQConfiguration.Order.EXCHANGE,
                RabbitMQConfiguration.Order.ROUTING_KEY,
                OrderMsg.builder().orderId(orderId).type(type).build());
    }
    return ResultUtils.success();
}
```
### 演示：没有确保顺序消费的情况
```java
com.itsoku.lesson034.consume.TestConsumer.dispose
@Override
@RabbitListener(queues = RabbitMQConfiguration.Order.QUEUE, concurrency = "5")
public void dispose(Message message) {
    Msg<OrderMsg> msg = getMsg(message);
    String log = "☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆顺序消息消费,消息编号：" + msg.getSequentialMsgNumbering() + ",消息体：" + JSONUtil.toJsonStr(msg.getBody());
    System.err.println(log);
//        super.dispose(message);
}
```
输出：
```
☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆顺序消息消费,消息编号：4,消息体：{"orderId":"06e7e2d9195444a4a145c31c28297b20","type":"买家确认收货"}
☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆顺序消息消费,消息编号：1,消息体：{"orderId":"06e7e2d9195444a4a145c31c28297b20","type":"订单创建消息"}
☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆顺序消息消费,消息编号：2,消息体：{"orderId":"06e7e2d9195444a4a145c31c28297b20","type":"订单支付消息"}
☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆顺序消息消费,消息编号：3,消息体：{"orderId":"06e7e2d9195444a4a145c31c28297b20","type":"订单已发货"}
☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆顺序消息消费,消息编号：5,消息体：{"orderId":"06e7e2d9195444a4a145c31c28297b20","type":"订单已完成"}
```
### 演示：顺序消费的情况
需要调整：com.itsoku.lesson034.consume.TestConsumer.dispose 代码，如下
```
@Override
@RabbitListener(queues = RabbitMQConfiguration.Order.QUEUE, concurrency = "5")
public void dispose(Message message) {
    super.dispose(message);
}
```
然后重启服务，测试效果，输出如下：
```
☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆顺序消息消费,消息编号：1,消息体：{"orderId":"0ca696d9fb6340a2a3b3133428de90b7","type":"订单创建消息"}
☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆顺序消息消费,消息编号：2,消息体：{"orderId":"0ca696d9fb6340a2a3b3133428de90b7","type":"订单支付消息"}
☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆顺序消息消费,消息编号：3,消息体：{"orderId":"0ca696d9fb6340a2a3b3133428de90b7","type":"订单已发货"}
☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆顺序消息消费,消息编号：4,消息体：{"orderId":"0ca696d9fb6340a2a3b3133428de90b7","type":"买家确认收货"}
☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆顺序消息消费,消息编号：5,消息体：{"orderId":"0ca696d9fb6340a2a3b3133428de90b7","type":"订单已完成"}
```
## 如何使用？源码解析
### 投递顺序消息
```java
com.itsoku.lesson034.mq.sender.IMsgSender#sendSequentialWithBody
/**
 * 发送顺序消息，可确保（busId+exchange+routingKey）相同的情况下，消息的顺序性
 * 这里我们使用的是rabbitmq，rabbitmq中 exchange+routingKey 可以确保消息被路由到相同的队列
 * <p>
 * 这里为什么要加入busId？
 * 以订单消息举例，所有订单消息都会进入同样的队列，订单有3种类型消息（创建、支付、发货）
 * 同一个订单的这3种类型的消息是要有序的，但是不同订单之间，他们不需要有序，所以这里加了个busId，此时就可以将订单id作为busId
 *
 * @param busId      业务id
 * @param exchange
 * @param routingKey
 * @param msgBody    消息体
 */
default void sendSequentialWithBody(String busId, String exchange, String routingKey, Object msgBody) {
    this.sendSequentialMsg(busId, exchange, routingKey, this.build(msgBody));
}
```
### 消费端确保顺序消费
参考：com.itsoku.lesson034.consume.TestConsumer，需要继承 AbstractSequentialMsgConsumer 类，如下，便可确保顺序消费
```java
@Component
@Slf4j
public class TestConsumer extends AbstractSequentialMsgConsumer<OrderMsg, Msg<OrderMsg>> {
    @Override
    @RabbitListener(queues = RabbitMQConfiguration.Order.QUEUE, concurrency = "5")
    public void dispose(Message message) {
        super.dispose(message);
    }
    @Override
    protected void sequentialMsgConsume(Msg<OrderMsg> msg) {
        String log = "☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆顺序消息消费,消息编号：" + msg.getSequentialMsgNumbering();
        System.err.println(log);
        //这里休眠500ms，模拟耗时的业务操作
        try {
            TimeUnit.MILLISECONDS.sleep(500);
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }
    }
}
```
