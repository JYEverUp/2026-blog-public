## RocketMQ应用

切记切记开启防火墙，9876和10911端口！不然会连接不上

### 一、普通消息

**消息发送分类**

Producer对于消息的发送也有许多的选择，不同的方法会产生不同的效果

#### 同步发送消息

同步发送消息是指，Producer发出一条消息后， 会在收到MQ返回的ACK之后才发下一条消息

该方式的消息可靠性最高，但消息发送效率太低

![在这里插入图片描述](/blogs/_archive-2024-assets/483734c00399a7316a5e.webp)

同步消息发送示例

```java
import org.apache.rocketmq.client.exception.MQBrokerException;
import org.apache.rocketmq.client.exception.MQClientException;
import org.apache.rocketmq.client.producer.DefaultMQProducer;
import org.apache.rocketmq.client.producer.SendResult;
import org.apache.rocketmq.common.message.Message;
import org.apache.rocketmq.remoting.exception.RemotingException;

/**
 * @Author if
 * @Description: 同步生产者
 * @Date 2021-10-24 下午 05:52
 */
public class SyncProducer {
    public static void main(String[] args) throws MQClientException, RemotingException, InterruptedException, MQBrokerException {
        //创建一个producer，参数为producerGroup名称
        DefaultMQProducer producer=new DefaultMQProducer("pg");
        //设置name server地址
        producer.setNamesrvAddr("centos:9876");
        //启动生产者
        producer.start();

        //当发送失败时重试发送的次数，默认2次
        producer.setRetryTimesWhenSendFailed(3);
        //设置发送超时时间5000ms（5s），默认3000ms
        producer.setSendMsgTimeout(5000);

        //测试生产并发送100条消息
        for(int i=0;i<100;i++){
            byte[] body=("Hi,"+i).getBytes();
            //创建Message，指定topic、tag和具体内容byte[]类型的body
            Message msg=new Message("someTopic","someTag",body);
            //发送消息并获得result
            SendResult sendResult = producer.send(msg);
            System.out.println(sendResult);
        }
        //关闭producer
        producer.shutdown();
    }
}
```

SendResult类是一个枚举类，有如下状态

```java
public enum SendStatus {
    SEND_OK,			//发送成功
    FLUSH_DISK_TIMEOUT,  //刷盘超时（Broker刷盘策略设置同步刷盘可能产生这个状态）
    FLUSH_SLAVE_TIMEOUT, //slave同步超时（Broker集群设置同步复制可能会导致）
    SLAVE_NOT_AVAILABLE; //从站slave不可用（Broker集群设置同步复制可能会导致）

    private SendStatus() {
    }
}
```

出现下列文字则是消息发送成功`sendStatus=SEND_OK`

> SendResult [sendStatus=SEND_OK, msgId=7F00000112D818B4AAC27A729CB90062, offsetMsgId=C0A8E98000002A9F00000000000667D4, messageQueue=MessageQueue [topic=someTopic, brokerName=centos, queueId=2], queueOffset=49]





#### 异步发送消息

异步发送消息是指，Producer发出消息后无需等待(异步发送响应)MQ返回ACK，直接发送下一条消息

该方式的消息可靠性可以得到保障，消息发送效率也可以

![在这里插入图片描述](/blogs/_archive-2024-assets/08abfed45cf3ebaf29af.webp)



异步和同步只是发送时选用的方法不同`public void send(Message msg, SendCallback sendCallback)`

而且发送的时候需要TimeUnit.SECONDS.sleep(3);一下，不能让他立即关闭了

需要一个回调类SendCallback

```java
public interface SendCallback {
    void onSuccess(SendResult var1);

    void onException(Throwable var1);
}
```



异步发送消息代码示例

```java
import org.apache.rocketmq.client.exception.MQBrokerException;
import org.apache.rocketmq.client.exception.MQClientException;
import org.apache.rocketmq.client.producer.DefaultMQProducer;
import org.apache.rocketmq.client.producer.SendCallback;
import org.apache.rocketmq.client.producer.SendResult;
import org.apache.rocketmq.common.message.Message;
import org.apache.rocketmq.remoting.exception.RemotingException;
import java.util.concurrent.TimeUnit;

/**
 * @Author if
 * @Description: 异步生产者
 * @Date 2021-10-24 下午 05:52
 */
public class AsyncProducer {
    public static void main(String[] args) throws MQClientException, RemotingException, InterruptedException, MQBrokerException {
        //创建一个producer，参数为producerGroup名称
        DefaultMQProducer producer=new DefaultMQProducer("pg");
        //设置name server地址
        producer.setNamesrvAddr("centos:9876");
        //启动生产者
        producer.start();

        //设置异步发送不重试
        producer.setRetryTimesWhenSendAsyncFailed(0);
        //设置发送超时时间5000ms（5s），默认3000ms
        producer.setSendMsgTimeout(5000);
        //设定新创建的topic的queue数量为2，默认4
        producer.setDefaultTopicQueueNums(2);

        //测试生产并发送100条消息
        for(int i=0;i<100;i++){
            byte[] body=("Hi,"+i).getBytes();
            //创建Message，指定topic、tag和具体内容byte[]类型的body
            Message msg=new Message("AsyncTopic","AsyncTopic",body);
            //发送消息并获得result
            producer.send(msg, new SendCallback() {
                @Override
                public void onSuccess(SendResult sendResult) {
                    System.out.println(sendResult);
                }

                @Override
                public void onException(Throwable throwable) {
                    throwable.printStackTrace();
                }
            });
        }
        //这一步的休眠很重要！因为是异步发送，还没发送完就关闭producer了
        TimeUnit.SECONDS.sleep(3);
        //关闭producer
        producer.shutdown();
    }
}
```





#### 单向发送消息

单向发送消息是指，Producer仅负责发送消息， 不等待、不处理MQ的ACK。该发送方式时MQ也不返回ACK

该方式的消息发送效率最高，但消息可靠性较差

![在这里插入图片描述](/blogs/_archive-2024-assets/d964d03c24c1aecbd96c.webp)



单向发送消息代码示例

```java
import org.apache.rocketmq.client.exception.MQClientException;
import org.apache.rocketmq.client.producer.DefaultMQProducer;
import org.apache.rocketmq.common.message.Message;
import org.apache.rocketmq.remoting.exception.RemotingException;

/**
 * @Author if
 * @Description: 单向消息生产者
 * @Date 2021-10-24 下午 07:21
 */
public class OneWayProducer {
    public static void main(String[] args) throws MQClientException, RemotingException, InterruptedException {
        DefaultMQProducer producer=new DefaultMQProducer("pg");
        producer.setNamesrvAddr("centos:9876");
        producer.start();

        for(int i=0;i<100;i++){
            byte[] body=("Hi,"+i).getBytes();
            Message msg=new Message("OneWayTopic","OneWayTopic",body);
            //单向发送
            producer.sendOneway(msg);
        }
        producer.shutdown();
        System.out.println("producer shutdown");
    }
}
```



#### 消费者消费代码示例

```java
import org.apache.rocketmq.client.consumer.DefaultMQPullConsumer;
import org.apache.rocketmq.client.consumer.DefaultMQPushConsumer;
import org.apache.rocketmq.client.consumer.listener.ConsumeConcurrentlyContext;
import org.apache.rocketmq.client.consumer.listener.ConsumeConcurrentlyStatus;
import org.apache.rocketmq.client.consumer.listener.MessageListenerConcurrently;
import org.apache.rocketmq.client.exception.MQClientException;
import org.apache.rocketmq.common.consumer.ConsumeFromWhere;
import org.apache.rocketmq.common.message.MessageExt;
import org.apache.rocketmq.common.protocol.heartbeat.MessageModel;
import java.util.List;

/**
 * @Author if
 * @Description: 消费者
 * @Date 2021-10-24 下午 07:25
 */
public class SomeConsumer {
    public static void main(String[] args) throws MQClientException {
        //定义一个Pull消费者
//        DefaultMQPullConsumer pullConsumer=new DefaultMQPullConsumer("cg");
        //定义一个Push消费者
        DefaultMQPushConsumer consumer=new DefaultMQPushConsumer("cg");
        consumer.setNamesrvAddr("centos:9876");
        //指定从第一条消息开始消费
        consumer.setConsumeFromWhere(ConsumeFromWhere.CONSUME_FROM_FIRST_OFFSET);
        //订阅消费的topic与tag（此处tag为通配符表示所有）
        consumer.subscribe("someTopic","*");

        //指定消费模式：广播模式，默认为集群模式
        consumer.setMessageModel(MessageModel.BROADCASTING);


        //注册消息监听器
        consumer.registerMessageListener(new MessageListenerConcurrently() {
            //消费消息代码，一旦broker中有了其订阅的消息就会触发该代码的执行
            //返回值为当前消费的状态
            @Override
            public ConsumeConcurrentlyStatus consumeMessage(List<MessageExt> list, ConsumeConcurrentlyContext consumeConcurrentlyContext) {
                for (MessageExt messageExt : list) {
                    System.out.println(messageExt);
                }
                //CONSUME_SUCCESS消费成功
                return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
            }
        });
        //开启消费
        consumer.start();
        System.out.println("consumer start");
    }
}
```

结果

> MessageExt [brokerName=centos, queueId=1, storeSize=182, queueOffset=43, sysFlag=0, bornTimestamp=1635071931511, bornHost=/192.168.233.1:53685, storeTimestamp=1635071929343, storeHost=/192.168.233.128:10911, msgId=C0A8E98000002A9F000000000006560E, commitLogOffset=415246, bodyCRC=1980703418, reconsumeTimes=0, preparedTransactionOffset=0, toString()=Message{topic='someTopic', flag=0, properties={MIN_OFFSET=0, MAX_OFFSET=75, CONSUME_START_TIME=1635075197904, UNIQ_KEY=7F00000112D818B4AAC27A729C770049, CLUSTER=DefaultCluster, TAGS=someTag}, body=[72, 105, 44, 55, 51], transactionId='null'}]



我们清楚控制台内容，不关闭消费者，然后开启同步生产者生成消息发送，消费者就会处理刚刚生产的消息

我们可以rocket-console看到所以运行的消费者及其信息状态

![在这里插入图片描述](/blogs/_archive-2024-assets/b6f65f0dd8831cb6402b.webp)

### 二、顺序消息

#### 什么是顺序消息？

顺序消息指的是，严格按照消息的**发送顺序**进行消费的消息

默认情况下生产者会把消息以Round Robin轮询方式发送到不同的Queue分区队列

而消费消息时会从多个Queue上拉取消息，这种情况下的发送和消费是不能保证顺序的



如果将消息仅发送到同一个Queue中，消费时也只从这个Queue上拉取消息，就严格保证了消息的顺序性

#### 为什么需要顺序消息？

用例子说明：假设我们一个订单topic，有4个queue队列，该topic中不同的消息用于描述订单不同的状态

假设订单有4个状态：未支付、已支付、发货中、发货成功、发货失败



根据以上订单状态，生产者从时序上可以生成如下几个消息: 

订单T0000001:未支付-->订单T0000001:已支付-->订单T0000001:发货中-->订单T0000001:发货失败

消息发送到MQ中之后，Queue的选择如果采用轮询策略，消息在MQ的存储可能如下:

![在这里插入图片描述](/blogs/_archive-2024-assets/bf015704d16c4e0be9de.webp)

这种情况下，我们希望Consumer消费消息的顺序和我们发送是一致的， 然而上述MQ的投递和消费方式，我们无法保证顺序是正确的

对于顺序异常的消息，Consumer即使设置有一定的状态容错，也不能完全处理好这么多种随机出现组合情况



基于上述的情况，可以设计如下方案:对于相同订单号的消息，通过-定的策略，将其放置在一个Queue中，然后消费者再采用一定的策略(例如，一个线程独立处理一个queue, 保证处理消息的顺序性)，能够保证消费的顺序性。

![在这里插入图片描述](/blogs/_archive-2024-assets/a3d258f6308cecc3a8ab.webp)

#### 消息的有序性分类

根据有序范围的不同，RocketMQ可以严格地保证两种消息的有序性：**分区有序**与**全局有序**

**分区有序**

如果有多个Queue参与，其仅可保证在该Queue分区队列上的消息顺序，则称为分区有序

也就是一个订单选用一个queue

> 如何实现Queue的选择?
>
> 在定Producer时我们可以指定消息队列选择器，而这个选择器是我们自己实现了MessageQueueSelector接口定义的。
>
> 在定义选择器的选择算法时，一般需要使用选择key。 这个选择key可以是消息key也可以是其它数据。但无论谁做选择key，都不能重复，都是唯一的，一般可以用业务id，即例子中的订单id
>
> 一般性的选择算法是， 让选择key（或其hash值）与该Topic所包含的Queue的数量取模，其结果即为选择出的Queue的Queueld
>
> 取模算法存在一个问题：
>
> 不同选择key与Queue数量取模结果可能会是相同的，即不同选择key的消息可能会出现在相同的Queue,即同一个Consumer可能会消费到不同选择key的消息。
>
> 这个问题如何解决? 
>
> 一般性的作法是，从消息中获取到选择key，对其进行判断。
>
> 若是当前Consumer需要消费的消息，则直接消费，否则，什么也不做。这种做法要求选择key要能够随着消息一起被Consumer获取到。此时使用消息key作为选择key是比较好的做法
>
> 以上做法会不会出现如下新的问题呢?
>
> 不属于那个Consumer的消息被拉取走了，那么应该消费该消息的Consumer是否还能再消费该消息呢?同一个Queue中的消息不可能被同一个Group中的不同Cosuner同时消费所以，消费现一个Queue的不同选择key的消息的Consumer一定属于不同的Group。 而不同的Group中的Consumer间的消费是相互隔离的，互不影响的。



![在这里插入图片描述](/blogs/_archive-2024-assets/2b05fa8bdf1ebffcb987.webp)

分区有序代码示例：两种选择算法

```java
import org.apache.rocketmq.client.exception.MQBrokerException;
import org.apache.rocketmq.client.exception.MQClientException;
import org.apache.rocketmq.client.producer.DefaultMQProducer;
import org.apache.rocketmq.client.producer.MessageQueueSelector;
import org.apache.rocketmq.client.producer.SendResult;
import org.apache.rocketmq.common.message.Message;
import org.apache.rocketmq.common.message.MessageQueue;
import org.apache.rocketmq.remoting.exception.RemotingException;
import java.util.List;

/**
 * @Author if
 * @Description: 顺序消息生产者
 * @Date 2021-10-24 下午 08:25
 */
public class OrderedProducer {
    public static void main(String[] args) throws MQClientException, RemotingException, InterruptedException, MQBrokerException {
        DefaultMQProducer producer=new DefaultMQProducer("pg");
        producer.setNamesrvAddr("centos:9876");
        producer.start();
        for(int i=0;i<100;i++){
            //oderId表示订单id
            int orderId=i;
            byte[] body=("Hi,"+i).getBytes();
            Message msg=new Message("OrderedTopic","OrderedTag",body);
            //将oderId当做消息key并充当选择算法中的选择key
            msg.setKeys(orderId+"");
            //send()方法的第三个参数Object arg我们这使用业务id，即订单id
            //这个arg会传递给选择器
            //该send为同步发送，当然也可以加一个SendCallback将其变为异步发送
            SendResult sendResult = producer.send(msg, new MessageQueueSelector() {
                //订单选择器的选择算法
                @Override
                public MessageQueue select(List<MessageQueue> list, Message message, Object o) {
                    //以下是使用消息key作为选择key的选择算法
                    String key=message.getKeys();
                    int id=Integer.parseInt(key);

                    //以下是使用arg作为选择key
//                    int id=(int) o;

                    int index=id % list.size();
                    return list.get(index);
                }
            },orderId);
            System.out.println(sendResult);
        }
        producer.shutdown();
    }
}
```



**全局有序**

当发送和消费参与的Queue只有**一个**时所保证的有序是整个Topic中消息的顺序，称为全局有序

3个方式指定topic的queue数量

1. producer发送时可以指定数量`producer.setDefaultTopicQueueNums(2);`

2. 可视化控制台里手动创建topic时指定queue数量
3. mqadmin命令手动创建topic时指定queue数量



![在这里插入图片描述](/blogs/_archive-2024-assets/071602b4ab22ce798bc5.webp)



全局有序的实现就指定数量就行了



### 三、延时消息

#### 什么是延时消息？

当消息写入到Broker后，在**指定的时长后才可被消费处理的消息**，称为延时消息

采用RocketMQ的延时消息可以实现`定时任务`的功能，而无需使用定时器

典型的应用场景是，电商交易中**超时未支付关闭订单**的场景，12306平台订票超时未支付取消订票的场景。

#### 延时等级

延时消息的延迟时长不支持随意时长的延迟，是通过特定的延迟等级来指定的

延时等级定义在RocketMQ服务端的MessageStoreConfig类中的如下变量中：

![在这里插入图片描述](/blogs/_archive-2024-assets/45bf1a61b97d7f8990e7.webp)

若指定延时等级为3，则表示延时为10s（从1开始计数）

如果需要自定义延时等级，可以去conf里修改broker的配置

> messageDelayLevel=1s 5s10s 30s 1m 2m 3m 4m 5m 6m 7m 8m 9m 10m 20m 30m 1h 2h 1d



#### 延时消息原理

![在这里插入图片描述](/blogs/_archive-2024-assets/d2c6797f1db64e6a4ad3.webp)

**修改消息**

Producer将消息发送到Broker后，Broker会 首先将消息写入到commitlog文件，然后需要将其分发到相应的consumequeue。

不过，在分发之前，系统会先判断消息中是否带有延时等级`msg.setDelayTimeLevel(3);`

若没有，则直接正常分发

若有，则需要经历一个复杂的过程：

- 修改消息的Topic为SCHEDULE _TOPIC_XXXX
- 根据延时等级，在consumequeue目录中SCHEDULE_TOPIC_XXXX主题下创建出相应的queueId目录与consumequeue文件(如果没有这些目录与文件的话)
- 修改消息索引单元内容。索引单元中的Message Tag HashCode部分原本存放的是消息的Tag的Hash值。现修改为**消息的投递时间**。投递时间是指该消息被重新修改为原Topic后再次被写入到commitlog中的时间。**投递时间=消息存储时间+延时等级时间**。消息存储时间指的是消息被发送到Broker时的时间戳
- 将消息索引写入到SCHEDULE_TOPIC_XXXX主题下相应的consumequeue中

**投递消息服务类**

Broker内部有一个延迟消息服务类ScheuleMessageService,其会消费SCHEDULE TOPIC XXXX中的消息，即按照每条消息的投递时间，将延时消息投递到目标Topic中。

不过，在投递之前会从commitlog中将原来写入的消息再次读出，并将其原来的延时等级设置为0，即原消息变为了一条不延迟的普通消息。然后再次将消息投递到目标Topic中。

**将消息重新写入commitlog**
延迟消息服务类将延迟消息再次发送给了commitlog,并再次形成新的消息索引条目，分发到相应Queue

#### 原理总结

判断有无延迟等级->有则修改原topic为SCHEDULE _TOPIC并填入时间->时间到了将其变为普通消息并投到原topic



#### 延时消费代码示例

DelayConsumer表示消费者，创建并运行

```java
import org.apache.rocketmq.client.consumer.DefaultMQPushConsumer;
import org.apache.rocketmq.client.consumer.listener.ConsumeConcurrentlyContext;
import org.apache.rocketmq.client.consumer.listener.ConsumeConcurrentlyStatus;
import org.apache.rocketmq.client.consumer.listener.MessageListenerConcurrently;
import org.apache.rocketmq.client.exception.MQClientException;
import org.apache.rocketmq.common.consumer.ConsumeFromWhere;
import org.apache.rocketmq.common.message.MessageExt;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;

/**
 * @Author if
 * @Description: What is it
 * @Date 2021-10-25 下午 05:32
 */
public class DelayConsumer {
    public static void main(String[] args) throws MQClientException {
        DefaultMQPushConsumer consumer=new DefaultMQPushConsumer("cg");
        consumer.setNamesrvAddr("centos:9876");
        consumer.setConsumeFromWhere(ConsumeFromWhere.CONSUME_FROM_FIRST_OFFSET);
        consumer.subscribe("DelayTopic","*");
        consumer.registerMessageListener(new MessageListenerConcurrently() {
            @Override
            public ConsumeConcurrentlyStatus consumeMessage(List<MessageExt> list, ConsumeConcurrentlyContext consumeConcurrentlyContext) {
                for (MessageExt messageExt : list) {
                    //输出消费时的时间
                    System.out.println(new SimpleDateFormat("mm:ss").format(new Date()));
                    System.out.println(messageExt);
                }
                //CONSUME_SUCCESS消费成功
                return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
            }
        });
        consumer.start();
        System.out.println("consumer start");
    }
}
```

DelayProducer为延时消息生产者，创建并运行

```java
import org.apache.rocketmq.client.exception.MQBrokerException;
import org.apache.rocketmq.client.exception.MQClientException;
import org.apache.rocketmq.client.producer.DefaultMQProducer;
import org.apache.rocketmq.client.producer.SendResult;
import org.apache.rocketmq.common.message.Message;
import org.apache.rocketmq.remoting.exception.RemotingException;
import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * @Author if
 * @Description: What is it
 * @Date 2021-10-25 下午 05:29
 */
public class DelayProducer {
    public static void main(String[] args) throws MQClientException, RemotingException, InterruptedException, MQBrokerException {
        DefaultMQProducer producer = new DefaultMQProducer("pg");
        producer.setNamesrvAddr("centos:9876");
        producer.start();

        for(int i=0;i<100;i++){
            byte[] body=("Hi,"+i).getBytes();
            Message msg=new Message("DelayTopic","DelayTag",body);
            //指定消息延迟等级为3，即10s
            msg.setDelayTimeLevel(3);
            SendResult sendResult = producer.send(msg);
            //输出消息发送的时间
            System.out.println(new SimpleDateFormat("mm:ss").format(new Date()));
            //输出消息返回结果
            System.out.println(" , "+sendResult);
        }
        producer.shutdown();
    }
}
```

查看输出结果，举例

先是生产者发送消息，可以看见时间为34分46秒

> 34:46
> , SendResult [sendStatus=SEND_OK, msgId=7F000001258818B4AAC27F5E4D880063, offsetMsgId=C0A8E98000002A9F000000000008342E, messageQueue=MessageQueue [topic=DelayTopic, brokerName=centos, queueId=0], queueOffset=99]

然后是消费者消费消息，这时已经是延时结束了，时间为35分16秒

> 35:16
> MessageExt [brokerName=centos, queueId=2, storeSize=235, queueOffset=4, sysFlag=0, bornTimestamp=1635154486499, bornHost=/192.168.233.1:5949, storeTimestamp=1635154495928, storeHost=/192.168.233.128:10911, msgId=C0A8E98000002A9F00000000000844B3, commitLogOffset=541875, bodyCRC=657998117, reconsumeTimes=0, preparedTransactionOffset=0, toString()=Message{topic='DelayTopic', flag=0, properties={MIN_OFFSET=0, REAL_TOPIC=DelayTopic, MAX_OFFSET=25, CONSUME_START_TIME=1635154516164, UNIQ_KEY=7F000001258818B4AAC27F5E4CE30011, CLUSTER=DefaultCluster, DELAY=3, WAIT=true, TAGS=DelayTag, REAL_QID=2}, body=[72, 105, 44, 49, 55], transactionId='null'}]



### 四、事务消息

#### 问题引入

这里的一个需求场景是：工行用户A向建行用户B转账1万元

我们可以使用同步消息来处理该需求场景：

![在这里插入图片描述](/blogs/_archive-2024-assets/1fd16471704351f9f42b.webp)

1. 工行系统发送一个给B增款1万元的同步消息M给Broker
2. 消息被Broker成功接收后，向工行系统发送成功ACK
3. 工行系统收到成功ACK后从用户A中扣款1万元
4. 建行系统从Broker中获取到消息M
5. 建行系统消费消息M,即向用户B中增加1万元

> 如果扣款失败，可是消息已经到了mq，只要消息写入成功就可以被消费，就会出现问题

解决思路是，让第1、2、3步具有原子性，要么全部成功，要么全部失败

即消息发送成功后，必须要保证扣款成功。如果扣款失败，则回滚发送成功的消息。而该思路即使用**事务消息**



#### 解决思路

这里要使用**分布式事务**解决方案

![在这里插入图片描述](/blogs/_archive-2024-assets/821b8b1bd18c49cb09ba.webp)

1. 事务管理器TM向事务协调器TC发起指令，开启**全局事务**
2. 工行系统发一个给B增款1万元的事务消息M给TC
3. TC会向Broker发送**半事务消息prepareHalf**，将消息M**预提交**到Broker。此时的建行系统是看不到Broker中的消息M的
4. Broker会将预提交执行结果Report给TC。
5. 如果预提交失败，则TC会向TM上报预提交失败的响应，全局事务结束;如果预提交成功，TC会调用工行系统的回调操作，去完成工行用户A的预扣款1万元的操作
6. 工行系统会向TC发送预扣款执行结果，即**本地事务**的执行状态
7. TC收到预扣款执行结果后，会将结果上报给TM。
8. TM会根据_上报结果向TC发出不同的确认指令
   1. 若预扣款成功(本地事务状态为COMMIT MESSAGE)，则TM向TC发送Global Commit指令
   2. 若预扣款失败(本地事务状态为ROLLBACK_ MESSAGE)，则TM向TC发送Global Rollback指令
   3. 若现未知状态(本地事务状态为UNKNOW)，则会触发工行系统的本地事务状态回查操作。回查操作会将回查结果，即COMMIT MESSAGE或ROLLBACK MESSAGE Report给TC。TC将结果上报给TM, TM会再向TC发送最终确认指令Global Commit或Global Rollback
9. TC在接收到指令后会向Broker与工行系统发出确认指令
   1. TC接收的若是Global Commit指令，则向Broker与工行系统发送Branch Commit指令。此时Broker中的消息M才可被建行系统看到;此时的工行用户A中的扣款操作才真正被确认
   2. TC接收到的若是Global Rollback指令，则向Broker与工行系统发送Branch Rollback指令。此时Broker中的消息M将被撤销;工行用户A中的扣款操作将被回滚



#### 基础

**分布式事务**

分布式事务通俗地说就是，一次操作由若干分支操作组成，这些分支操作分属不同应用，分布在不同服务器上

分布式事务需要保证这些分支操作要么全部成功，要么全部失败

分布式事务与普通事务一样，就是为了保证操作结果的一致性

**事务消息**

RocketMQ提供了类似X/Open XA的分布式事务功能，通过事务消息能达到分布式事务的最终一致

XA是一种分布式事务解决方案，一 种分布式事务处理模式

**半事务消息**

暂不能投递的消息，发送方已经成功地将消息发送到了Broker,但是Broker未收到最终确认指令，此时该消息被标记成‘暂不能投递”状态，即不能被消费者看到

处于该种状态下的消息即半事务消息

**本地事务状态**

Producer回调操作执行的结果为本地事务状态，其会发送给TC,而TC会再发送给TM

TM会根据TC发送来的本地事务状态来决定全局事务确认指令

**消息回查**

消息回查，即重新查询本地事务的执行状态。本例就是重新到DB中查看预扣款操作**是否执行成功**

![在这里插入图片描述](/blogs/_archive-2024-assets/dbe5e7eae67c50eef95c.webp)

> 常见的两个引发消息回查的原因：
>
> 1. 回调操作返回UNKNWON
> 2. TC没有接收到TM的最终全局事务确认指令



#### XA三剑客

**XA协议**

XA (Unix Transaction)是一种**分布式事务解决方案**，一种分布式事务处理模式，是基于XA协议的

XA协议由Tuxedo (Transaction for Unix has been Extended for Distributed Operation,分布式操作扩展之后的Unix事务系统)首先提出的，并交给X/Open组织，作为资源管理器与事务管理器的接口标准

XA模式中有三个重要组件: TC、TM、RM

**TC**

`事务协调者`，Transaction Coordinator

维护全局和分支事务的状态，驱动全局事务提交或回滚

> RocketMQ中Broker充当着TC事务协调者



**TM**

`事务管理器`，Transaction Manager

定义全局事务的范围：开始全局事务、提交或回滚全局事务。它实际是全局事务的发起者

> RocketMQ中Producer充当着TM事务管理器



**RM**

`资源管理器`，Resource Manager

管理分支事务处理的资源，与TC交谈以注册分支事务和报告分支事务的状态，并驱动分支事务提交或回滚

> RocketMQ中Broker和Producer均充当着RM资源管理器



#### 注意事项

- 事务消息不支持延时消息
- 对于事务消息要做好幂等性检查，因为事务消息可能不止一次被消费(因为存在回滚后再提交的情况)



#### 事务消息代码示例

创建事务监听器`IcbcTransactionListener`类

```java
import org.apache.commons.lang3.StringUtils;
import org.apache.rocketmq.client.producer.LocalTransactionState;
import org.apache.rocketmq.client.producer.TransactionListener;
import org.apache.rocketmq.common.message.Message;
import org.apache.rocketmq.common.message.MessageExt;

/**
 * @Author if
 * @Description: 爱存不存事务监听器
 * @Date 2021-10-25 下午 09:56
 */
public class IcbcTransactionListener implements TransactionListener {
    /**
     * 回调操作
     * 消息预提交成功就会触发该方法的执行，用于执行本地事务
     * 这里模拟一下
     * tagA就是扣款成功
     * tagB就是扣款失败
     * tagC就是不知道成没成功，要执行消息回查
     * @param message
     * @param o
     * @return
     */
    @Override
    public LocalTransactionState executeLocalTransaction(Message message, Object o) {
        System.out.println("预提交消息成功："+message);
        if(StringUtils.equals("TAGA",message.getTags())){
            return LocalTransactionState.COMMIT_MESSAGE;
        }else if(StringUtils.equals("TAGB",message.getTags())){
            return LocalTransactionState.ROLLBACK_MESSAGE;
        }else if(StringUtils.equals("TAGC",message.getTags())){
            return LocalTransactionState.UNKNOW;
        }
        return LocalTransactionState.UNKNOW;
    }

    /**
     * 消息回查方法
     * 这里模拟出来表示回查就返回成功状态
     *
     * 常见的两个引发消息回查的原因：
     *  1. 回调操作返回UNKNWON
     *  2. TC没有接收到TM的最终全局事务确认指令
     * @param messageExt
     * @return
     */
    @Override
    public LocalTransactionState checkLocalTransaction(MessageExt messageExt) {
        System.out.println("执行消息回查："+messageExt.getTags());
        return LocalTransactionState.COMMIT_MESSAGE;
    }
}
```

创建生产者`TransactionProducer`类

```java
import org.apache.rocketmq.client.exception.MQClientException;
import org.apache.rocketmq.client.producer.TransactionMQProducer;
import org.apache.rocketmq.client.producer.TransactionSendResult;
import org.apache.rocketmq.common.message.Message;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/**
 * @Author if
 * @Description: What is it
 * @Date 2021-10-25 下午 09:44
 */
public class TransactionProducer {
    public static void main(String[] args) throws MQClientException {
        TransactionMQProducer producer=new TransactionMQProducer("tpg");
        producer.setNamesrvAddr("centos:9876");

        /**
         * 定义一个线程池
         * @param corePoolSize，核心线程数
         * @param maximumPoolSize，最多线程数
         * @param keepAliveTime，保持活跃的时间：当线程池中线程数量大于核心线程数量时，多余空闲线程的存活时长
         * @param unit，时间单位
         * @param workQueue，临时存放任务的工作队列
         * @param threadFactory，线程工厂
         */
        ThreadPoolExecutor executorService = new ThreadPoolExecutor(
                2,
                5,
                100,
                TimeUnit.SECONDS,
                new ArrayBlockingQueue<>(200),
                new ThreadFactory() {
            @Override
            public Thread newThread(Runnable r) {
                Thread thread = new Thread(r);
                thread.setName("client-transaction-msg-check-thread");
                return thread;
            }
        });

        //为生产者指定刚刚定义的线程池
        producer.setExecutorService(executorService);
        //为生产者指定任务监听器
        producer.setTransactionListener(new IcbcTransactionListener());
        
        producer.start();
        String[] tags={"TAGA","TAGB","TAGC"};
        for(int i=0;i<3;i++){
            byte[] body=("Hi"+i).getBytes();
            Message msg=new Message("TransactionTopic",tags[i],body);
            //发送事务消息
            //第二个参数用于指定在执行本地事务时需要使用的业务参数
            TransactionSendResult result = producer.sendMessageInTransaction(msg, null);
            System.out.println("发送结果为："+result.getSendStatus());
        }
    }
}
```



启动生产者得到结果

> 预提交消息成功：Message{topic='TransactionTopic', flag=0, properties={TRAN_MSG=true, UNIQ_KEY=7F0000011DC018B4AAC280588D660000, WAIT=true, PGROUP=tpg, TAGS=TAGA}, body=[72, 105, 48], transactionId='7F0000011DC018B4AAC280588D660000'}
> 发送结果为：SEND_OK
>
> 预提交消息成功：Message{topic='TransactionTopic', flag=0, properties={TRAN_MSG=true, UNIQ_KEY=7F0000011DC018B4AAC280588DF80001, WAIT=true, PGROUP=tpg, TAGS=TAGB}, body=[72, 105, 49], transactionId='7F0000011DC018B4AAC280588DF80001'}
> 发送结果为：SEND_OK
>
> 预提交消息成功：Message{topic='TransactionTopic', flag=0, properties={TRAN_MSG=true, UNIQ_KEY=7F0000011DC018B4AAC280588E210002, WAIT=true, PGROUP=tpg, TAGS=TAGC}, body=[72, 105, 50], transactionId='7F0000011DC018B4AAC280588E210002'}
> 发送结果为：SEND_OK
> 执行消息回查：TAGC

可以看到TAGC时，监听器返回了`LocalTransactionState.UNKNOW`表示不知道成没成功，所以执行了消息回查方法



此时我们使用消费者去消费`TransactionTopic`消息

> consumer start
>
> MessageExt [brokerName=centos, queueId=0, storeSize=284, queueOffset=0, sysFlag=8, bornTimestamp=1635170887201, bornHost=/192.168.233.1:18864, storeTimestamp=1635170920413, storeHost=/192.168.233.128:10911, msgId=C0A8E98000002A9F0000000000089736, commitLogOffset=562998, bodyCRC=2099282948, reconsumeTimes=0, preparedTransactionOffset=562706, toString()=Message{topic='TransactionTopic', flag=0, properties={MIN_OFFSET=0, REAL_TOPIC=TransactionTopic, TRANSACTION_CHECK_TIMES=1, MAX_OFFSET=1, TRAN_MSG=true, CONSUME_START_TIME=1635171216788, UNIQ_KEY=7F0000011DC018B4AAC280588E210002, CLUSTER=DefaultCluster, PGROUP=tpg, WAIT=true, TAGS=**TAGC**, REAL_QID=0}, body=[72, 105, 50], transactionId='7F0000011DC018B4AAC280588E210002'}]
>
> MessageExt [brokerName=centos, queueId=2, storeSize=258, queueOffset=0, sysFlag=8, bornTimestamp=1635170887015, bornHost=/192.168.233.1:18864, storeTimestamp=1635170886680, storeHost=/192.168.233.128:10911, msgId=C0A8E98000002A9F0000000000089402, commitLogOffset=562178, bodyCRC=321840424, reconsumeTimes=0, preparedTransactionOffset=561380, toString()=Message{topic='TransactionTopic', flag=0, properties={MIN_OFFSET=0, REAL_TOPIC=TransactionTopic, MAX_OFFSET=1, TRAN_MSG=true, CONSUME_START_TIME=1635171216902, UNIQ_KEY=7F0000011DC018B4AAC280588D660000, CLUSTER=DefaultCluster, PGROUP=tpg, WAIT=true, TAGS=**TAGA**, REAL_QID=2}, body=[72, 105, 48], transactionId='7F0000011DC018B4AAC280588D660000'}]

可以看见只消费了正常的TAGA和执行了消息回查的TAGC，而TAGB因为在监听器里触发时返回了失败状态，所以在整体回滚之后，消息就没有被提交到broker，自然就没有被消费者消费



### 五、批量消息

#### 批量发送

查看`DefaultMQPushConsumer`生产者类可以看见，send消息不仅是参数可以为单条Message，也可以说集合类型

`public SendResult send(Collection<Message> msgs)`

**发送限制**

生产者进行消息发送时可以一次发送多条消息，这可以大大提升Producer的发送效率

不过需要注意以下几点:

- 批量发送的消息必须具有**相同的Topic**
- 批量发送的消息必须具有**相同的刷盘策略**
- 批量发送的消息**不能是延时消息与事务消息**



**批量发送大小**

默认情况下，一批发送的消息总大小不能超过4MB字节。如果想超出该值，有两种解决方案：

- 方案一：将批量消息进行拆分，拆分为若干不大于4M的消息集合分多次批量发送
- 方案二：在Producer端与Broker端修改属性
  - Producer端需要在发送之前设置Producer的maxMessageSize属性
  - Broker端需要修改其加载的配置文件中的maxMessageSize属性



生产者通过send()方法发送的Message,并不是直接将Message序列化后发送到网络上的，而是通过这个Message生成了一个字符串发送出去的

这个字符串由四部分构成：**Topic**、 **消息Body**、**消息日志**(占20字节)，及用于**描述消息的一堆属性key-value**

这些属性中包含例如生产者地址、生产时间、要发送的Queueld等。最终写入到Broker中消息 单元中的数据都是来自于这些属性



#### 批量消费

Consumer的MessageListenerConcurrently监听接口的consumeMessage(方法的第一个参数为消息列表，但默认情况下每次只能消费一条消息。

```java
        //注册消息监听器
        consumer.registerMessageListener(new MessageListenerConcurrently() {
            //消费消息代码，一旦broker中有了其订阅的消息就会触发该代码的执行
            //返回值为当前消费的状态
            @Override
            public ConsumeConcurrentlyStatus consumeMessage(List<MessageExt> list, ConsumeConcurrentlyContext consumeConcurrentlyContext) {
                for (MessageExt messageExt : list) {
                    System.out.println(messageExt);
                }
                //CONSUME_SUCCESS消费成功
                return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
            }
        });
```





若要使其一次可以消费多条消息， 则可以通过修改Consumer的consumeMessageBatchMaxSize属性来指定

`consumer.setConsumeMessageBatchMaxSize(10);`

默认值为1，,该值不能超过32，即消费者每次可以拉取的消息最多是32条

```java
	/**
     * Batch consumption size 批量消费规模
     */
    private int consumeMessageBatchMaxSize = 1;
```



若要修改一次拉取的最大值，则可通过修改Consumer的pullBatchSize属性来指定

`consumer.setPullBatchSize(32);`

默认值为32

```java
    /**
     * Batch pull size 批量拉取大小
     */
    private int pullBatchSize = 32;
```



**存在的问题**

Consumer的pullBatchSize属性与consumeMessageBatchMaxSize属性是否设置的越大越好？当然不是

- pullBatchSize值设置的越大， Consumer每拉取一-次需要的时间就会越长，且在网络上传输出现问题的可能性就越高。若在拉取过程中若出现了问题， 那么本批次所有消息都需要全部重新拉取。
- consumeMessageBatchMaxSize值设置的越大， Consumer的消息并发消费能力越低，且这批被消费的消息具有相同的消费结果。因为consumeMesageBatchMaxSize指定的一批消息只会使用一个线程进行处理，且在处理过程中只要有一 个消息处理异常，则这批消息需要全部重新再次消费处理。



### 六、消息过滤

消息者在进行消息订阅时，除了可以指定要订阅消息的Topic外，还可以对指定Topic中的消息根据指定条件进行过滤，即可以订阅比Topic更加细粒度的消息类型

对于指定Topic消息的过滤有两种过滤方式：**Tag过滤**与**SQL过滤**



#### Tag过滤

通过consumer的subscribe()方法指定要订阅消息的Tag.如果订阅多个Tag的消息，Tag间使用或运算符`双竖线||`连接。

```java
        DefaultMQPushConsumer consumer=new DefaultMQPushConsumer("cg");
        consumer.subscribe("Topic","TAGA || TAGB || TAGC");
```



#### SQL过滤

SQL过滤是一种通过特定表达式对事先埋入到消息中的**用户属性**进行筛选过滤的方式。

通过SQL过滤，可以实现对消息的复杂过滤。

不过，只有使用**PUSH模式**的消费者才能使用SQL过滤。

SQL过滤表达式中支持多种常量类型与运算符。



支持的常量类型：

- 数值:比如: 123, 3.1415
- 字符:必须用单引号包裹起来，比如: 'abc'
- 布尔: TRUE或FALSE
- NULL:特殊的常量，表示空



支持的运算符：

- 数值比较: >, >=, <，<=，BETWEEN, =
- 字符比较: =，<>, IN
- 逻辑运算: AND, OR, NOT
- NULL判断: IS NULL或者IS NOT NULL



#### 代码示例

先来个**Tag过滤**

定义消费者`FilterConsumer`

```java
import org.apache.rocketmq.client.consumer.DefaultMQPushConsumer;
import org.apache.rocketmq.client.consumer.listener.ConsumeConcurrentlyContext;
import org.apache.rocketmq.client.consumer.listener.ConsumeConcurrentlyStatus;
import org.apache.rocketmq.client.consumer.listener.MessageListenerConcurrently;
import org.apache.rocketmq.client.exception.MQClientException;
import org.apache.rocketmq.common.consumer.ConsumeFromWhere;
import org.apache.rocketmq.common.message.MessageExt;
import org.apache.rocketmq.common.protocol.heartbeat.MessageModel;
import java.util.List;

/**
 * @Author if
 * @Description: What is it
 * @Date 2021-10-25 下午 10:43
 */
public class FilterConsumer {
    public static void main(String[] args) throws MQClientException {
        DefaultMQPushConsumer consumer=new DefaultMQPushConsumer("cg");
        consumer.setNamesrvAddr("centos:9876");
        consumer.setConsumeFromWhere(ConsumeFromWhere.CONSUME_FROM_FIRST_OFFSET);
        //消费FilterTopic中的TagA和TagB（TagC过滤）
        consumer.subscribe("FilterTopic","TagA || TagB");
        consumer.setMessageModel(MessageModel.BROADCASTING);

        consumer.registerMessageListener(new MessageListenerConcurrently() {
            @Override
            public ConsumeConcurrentlyStatus consumeMessage(List<MessageExt> list, ConsumeConcurrentlyContext consumeConcurrentlyContext) {
                for (MessageExt messageExt : list) {
                    System.out.println("消费的tag为："+messageExt.getTags());
                }
                return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
            }
        });
        consumer.start();
        System.out.println("consumer start");
    }
}
```

定义生产者`FilterProducer`

```java
import org.apache.rocketmq.client.exception.MQBrokerException;
import org.apache.rocketmq.client.exception.MQClientException;
import org.apache.rocketmq.client.producer.DefaultMQProducer;
import org.apache.rocketmq.client.producer.SendResult;
import org.apache.rocketmq.common.message.Message;
import org.apache.rocketmq.remoting.exception.RemotingException;

/**
 * @Author if
 * @Description: What is it
 * @Date 2021-10-25 下午 10:43
 */
public class FilterProducer {
    public static void main(String[] args) throws MQClientException, RemotingException, InterruptedException, MQBrokerException {
        DefaultMQProducer producer=new DefaultMQProducer("pg");
        producer.setNamesrvAddr("centos:9876");
        producer.start();

        //创建3中tag，让消费者过滤掉TagC
        String[] tags={"TagA","TagB","TagC"};
        for(int i=0;i<10;i++){
            byte[] body=("Hi,"+i).getBytes();
            String tag=tags[i % tags.length];
            Message msg=new Message("FilterTopic",tag,body);
            SendResult sendResult = producer.send(msg);
            System.out.println(sendResult);
        }
        producer.shutdown();
    }
}
```

可以看见消费者消费的结果为

> consumer start
> 消费的tag为：TagB
> 消费的tag为：TagB
> 消费的tag为：TagB
> 消费的tag为：TagA
> 消费的tag为：TagA
> 消费的tag为：TagA
> 消费的tag为：TagA

也就是说通过`consumer.subscribe("FilterTopic","TagA || TagB");`将TagC过滤掉了（只消费A和B）



再来个**SQL过滤**

创建消费者`SQLFilterConsumer`

```java
import org.apache.rocketmq.client.consumer.DefaultMQPushConsumer;
import org.apache.rocketmq.client.consumer.MessageSelector;
import org.apache.rocketmq.client.consumer.listener.ConsumeConcurrentlyContext;
import org.apache.rocketmq.client.consumer.listener.ConsumeConcurrentlyStatus;
import org.apache.rocketmq.client.consumer.listener.MessageListenerConcurrently;
import org.apache.rocketmq.client.exception.MQClientException;
import org.apache.rocketmq.common.consumer.ConsumeFromWhere;
import org.apache.rocketmq.common.message.MessageExt;
import org.apache.rocketmq.common.protocol.heartbeat.MessageModel;

import java.util.List;

/**
 * @Author if
 * @Description: What is it
 * @Date 2021-10-25 下午 10:43
 */
public class SQLFilterConsumer {
    public static void main(String[] args) throws MQClientException {
        DefaultMQPushConsumer consumer=new DefaultMQPushConsumer("cg");
        consumer.setNamesrvAddr("centos:9876");
        consumer.setConsumeFromWhere(ConsumeFromWhere.CONSUME_FROM_FIRST_OFFSET);

        //消费SQLFilterTopic，根据MessageSelector.bySql()方法过滤出age在0到6的消息
        consumer.subscribe("SQLFilterTopic", MessageSelector.bySql("age between 0 and 6"));

        consumer.setMessageModel(MessageModel.BROADCASTING);
        consumer.registerMessageListener(new MessageListenerConcurrently() {
            @Override
            public ConsumeConcurrentlyStatus consumeMessage(List<MessageExt> list, ConsumeConcurrentlyContext consumeConcurrentlyContext) {
                for (MessageExt messageExt : list) {
                    System.out.println("消费的用户属性为："+messageExt.getProperty("age"));
                }
                return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
            }
        });
        consumer.start();
        System.out.println("consumer start");
    }
}
```

创建生产者`SQLFilterProducer`

```java
import org.apache.rocketmq.client.exception.MQBrokerException;
import org.apache.rocketmq.client.exception.MQClientException;
import org.apache.rocketmq.client.producer.DefaultMQProducer;
import org.apache.rocketmq.client.producer.SendResult;
import org.apache.rocketmq.common.message.Message;
import org.apache.rocketmq.remoting.exception.RemotingException;

/**
 * @Author if
 * @Description: What is it
 * @Date 2021-10-25 下午 10:43
 */
public class SQLFilterProducer {
    public static void main(String[] args) throws MQClientException, RemotingException, InterruptedException, MQBrokerException {
        DefaultMQProducer producer=new DefaultMQProducer("pg");
        producer.setNamesrvAddr("centos:9876");
        producer.start();

        for(int i=0;i<10;i++){
            byte[] body=("Hi,"+i).getBytes();
            Message msg=new Message("SQLFilterTopic","SQLFilterTopic",body);
            //在message中put用户属性
            msg.putUserProperty("age",i + "");
            SendResult sendResult = producer.send(msg);
            System.out.println(sendResult);
        }
        producer.shutdown();
    }
}
```

查看结果

> consumer start
> 消费的用户属性为：5
> 消费的用户属性为：6
> 消费的用户属性为：0
> 消费的用户属性为：1
> 消费的用户属性为：4
> 消费的用户属性为：3
> 消费的用户属性为：2

证明sql过滤`MessageSelector.bySql("age between 0 and 6")`成功



如果运行报错

> CODE: 1 DESC: The broker does not support consumer to filter message by SQL9

可能是broker不支持属性过滤，需要在conf中修改broker.conf文件，加上`enablePropertyFilter=true `，且在运行broker时用`-c`命令指定conf文件，即可解决



### 七、消息发送重试机制

#### 什么是消息发送重试机制

Producer对发送失败的消息进行重新发送的机制，称为**消息发送重试机制**，也称为**消息重投机制**

对于消息重投，需要注意以下几点：

- 生产者在发送消息时，若采用**同步**或**异步**发送方式，发送失败**会重试**，但**单向消息**发送方式发送失败是**没有**重试机制的
- 只有普通消息具有发送重试机制，顺序消息是没有的
- 消息重投机制可以保证消息尽可能发送成功、不丢失，但可能会造成消息重复。消息重复在RocketMQ中是无法避免的问题
- 消息重复在一般情况下不会发生I当出现消息量大、网络抖动，消息重复就会成为大概率事件
- producer主动重发、consumer负载变化也会导致重复消息
- 消息重复无法避免，但要避免消息的重复消费。
- 避免消息重复消费的解决方案是，为消息添加唯一标识，使消费者对消息进行消费判断来避免重复消费
- 消息发送重试有三种策略可以选择:同步发送失败策略、异步发送失败策略、消息刷盘失败策略



#### 同步发送失败策略

对于普通消息，消息发送**默认采用轮询round robin策略**来选择所发送到的队列。

如果发送失败，默认重试2次。但在重试时是不会选择上次发送失败的Broker，而是选择其它Broker。

```java
        //当发送失败时重试发送的次数，默认2次
        producer.setRetryTimesWhenSendFailed(3);
```

同时，Broker还具有失败隔离功能，使Producer尽量选择未发生过发送失败的Broker作为目标Broker。

如果超过重试次数，则抛出异常，由Producer去保证消息不丢。 当然当生产者出现RemotingException、MQClientException和MQBrokerException时，Producer会自动重投消息。



#### 异步发送失败策略

异步发送失败重试时，异步重试不会选择其他broker, 仅在**同一个**broker上做重试，所以该策略无法保证消息不丢。

```java
        //设置异步发送不重试
        producer.setRetryTimesWhenSendAsyncFailed(0);
```



#### 消息刷盘发送失败策略

消息刷盘超时（master或slave不可用）或slave不可用(返回状态非SEND OK)时，默认是不会将消息尝试发送到其他Broker的。

不过，对于重要消息可以通过在Broker的配置文件设置retryAnotherBrokerWhenNotStoreOK属性为true来开启。



### 八、消息消费重试机制

#### 顺序消息的消费重试

对于顺序消息，当Consumer消费消息失败后，为了保证消息的顺序性，其会自动**不断地**进行消息重试，直到消费成功。重试期间应用会出现消息消费**被阻塞**的情况。

> 由于对顺序消息的重试是无休止的，不间断的，直至消费成功，所以对于顺序消息的消费，务必要保证应用能够及时监控并处理消费失败的情况，避免消费被永久性阻塞

```java
        //顺序消息消费失败的消费重试时间间隔，默认为1000亳秒，其取值范围为[10,30000]毫秒
        consumer.setSuspendCurrentQueueTimeMillis(100);
```



#### 无序消息的消费重试

对于无序消息，当Consumer消费消息失败时，可以通过设置返回状态达到消息重试的效果。不过需要注意，无序消息的重试**只对集群消费方式生效**，**广播消费方式不提供失败重试**特性

即对于广播消费，消费失败后，失败消息不再重试，继续消费后续消息。



#### 消费重试次数与间隔

对于**无序消息集群消费**下的重试消费，每条消息**默认最多重试16次**

```java
        //设定消息重试最多10次
        consumer.setMaxReconsumeTimes(10);
```

对于这个自定义次数：

> 若修改值小于16，则按照指定间隔进行重试
> 若修改值大于16，则超过16次的重试时间间隔均为2小时
>
> 对于Consumer Group,若仅修改了-个Consumer的消费重试次数，则会应用到该Group中所有其它Consumer实例
>
> 若出现多个Consumer均做了修改的情况，则采用覆盖方式生效。即最后被修改的值会覆盖前面设置的值

但每次重试的间隔时间是不同的，会逐渐变长。每次重试的间隔时间如下表。

![在这里插入图片描述](/blogs/_archive-2024-assets/93db524da4ae58a16609.webp)



#### 重试队列

对于需要重试消费的消息，并不是Consumer在等待了指定时长后再次去拉取原来的消息进行消费

而是将这些需要重试消费的消息放入到了一个特殊Topic的队列中，而后进行再次消费的

这个特殊的队列就是重试队列

当出现需要进行重试消费的消息时Broker会为每个消费组都设置一个Topic名称为`%RETRY%consumerGroup@consumerGroup`的重试队列



#### 消费重试的配置方式

集群消费方式下，消息消费失败后若希望消费重试，则需要在消息监听器接口的实现中明确进行如下三种方式之一的配置：

- 方式1:返回ConsumeConcurrentlyStatus.RECONSUME_LATER
  - `return ConsumeConcurrentlyStatus.RECONSUME_LATER;`
- 方式2:返回Null
- 方式3:抛出异常



### 消费不重试配置文件


集群消费方式下，消息消费失败后若不希望消费重试，则在捕获到异常后同样也返回与消费成功后的相同的结果，即ConsumeConcurrentlyStatus.CONSUME_SUCCESS，则不进行消费重试。

`return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;`



### 九、死信队列

#### 什么是死信队列

当一条消息初次消费失败，消息队列会自动进行消息重试

达到最大重试次数后，若消费依然失败，则表明消费者在正常情况下无法正确地消费该消息，此时消息队列不会立刻将消息丢弃，而是将其发送到该消费者对应的特殊队列中



这个队列就是**死信队列**(Dead-Letter Queue, DLQ)

其中的消息则称为**死信消息**(Dead-Letter Message, DLM)



#### 死信队列的特征

- 死信队列中的消息不会再被消费者正常消费
- 死信存储有效期与正常消息相同，均为3天，3天后会被自动删除
- 死信队列就是一个特殊的Topic, 名称为%DLQ%consumerGroup@consumerGroup
- 如果一个消费者组未产生死信消息，则不会为其创建相应的死信队列



#### 死信队列的处理

实际上，当一条消息进入死信队列，就意味着系统中某些地方出现了问题，从而导致消费者无法正常消费该消息，比如代码中原本就存在Bug

因此，对于死信消息，通常需要开发人员进行特殊处理。最关键的步骤是要排查可疑因素，解决代码中可能存在的Bug.然后再将原来的死信消息再次进行投递消费
