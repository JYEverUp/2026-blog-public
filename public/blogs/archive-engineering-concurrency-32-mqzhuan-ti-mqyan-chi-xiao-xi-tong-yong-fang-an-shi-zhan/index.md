#  MQ延迟消息通用方案实战
## 本文主要内容
本文将带大家手写一个MQ延迟消息的通用方案。
本文的方案不依赖于MQ中间件，依靠MySQL和DelayQueue解决，不管大家用的是什么MQ，具体是RocketMQ、RabbitMQ还是kafka，本文这个方案你都可以拿去直接使用，可以轻松实现任意时间的延迟消息投递。
## 本文涉及到的技术点
1. SpringBoot2.7
2. MyBatisPlus
3. MySQL
4. 线程池
5. java中的延迟队列：DelayQueue
6. 分布式锁
## 延迟消息常见的使用场景
### 1、订单超时处理
比如下单后15分钟，未支付，则自动取消订单，回退库存。
可以采用延迟队列实现：下单的时候可以投递一条延迟15分钟的消息，15分钟后消息将被消费。
### 2、消息消费失败重试
比如MQ消息消费失败后，可以延迟一段时间再次消费。
可以采用延迟消息实现：消费失败，可以投递一条延迟消息，触发再次消费
### 3、其他任意需要延迟处理的业务
业务中需要延迟处理的场景，都可以使用延迟消息来搞定。
## 延迟消息常见的实现方案
### 方案1：MySQL + job定时轮询
由于延迟消息的时间不确定，若要达到实时性很高的效果，也就是说消息的延迟时间是不知道的，那就需要轮询每一秒才能确保消息在指定的延迟时间被处理，这就要求job需要每秒查询一次db中待投递的消息。
这种方案访问db的频率比较高，对数据库造成了一定的压力。
### 方案2：RabbitMQ 中的TTL+死信队列
rabbitmq中可以使用TTL消息 + 死信队列实现，也可以安装延时插件。
此方案对中间件有依赖，不同的MQ实现是不一样的，若换成其他的MQ，方案要重新实现
### 方案3：MySQL + job定时轮询 + DelayQueue
可以对方案1进行改进，引入java中的 DelayQueue。
job可以采用1分钟执行一次，每次拉取未来2分钟内需要投递的消息，将其丢到java自带的 DelayQueue 这个延迟队列工具类中去处理，这样便能做到实时性很高的投递效果，且对db的压力也降低了很多。
这种方案对db也没什么压力，实时性非常高，且对MQ没有依赖，这样不管切换什么MQ，这种方案都不需要改动。
我比较推荐这种，但是实现可能有点难度，本文将落地该方案。
## 需要一张本地消息表（t_msg）
```sql
create table if not exists t_msg_lesson032
(
    id               varchar(32) not null primary key comment '消息id',
    body_json        text        not null comment '消息体,json格式',
    status           smallint    not null default 0 comment '消息状态，0：待投递到mq，1：投递成功，2：投递失败',
    expect_send_time datetime    not null comment '消息期望投递时间，大于当前时间，则为延迟消息，否则会立即投递',
    actual_send_time datetime comment '消息实际投递时间',
    create_time      datetime comment '创建时间',
    fail_msg         text comment 'status=2 时，记录消息投递失败的原因',
    fail_count       int         not null default 0 comment '已投递失败次数',
    send_retry       smallint    not null default 1 comment '投递MQ失败了，是否还需要重试？1：是，0：否',
    next_retry_time  datetime comment '投递失败后，下次重试时间',
    update_time      datetime comment '最近更新时间',
    key idx_status (status)
) comment '本地消息表';
```
## 先看效果
本案例会模拟电商创建订单，投递一条mq消息的场景。
### 数据库初始化脚本
lesson032/src/main/resources/db/init.sql，系统启动的时候会自动执行，创建2张表，一个订单表，一个本地消息表。
```sql
-- 创建订单表
drop table if exists t_order_lesson032;
create table if not exists t_order_lesson032
(
    id    varchar(32)    not null primary key comment '订单id',
    goods varchar(100)   not null comment '商品',
    price decimal(12, 2) not null comment '订单金额'
) comment '订单表';
-- 创建本地消息表
drop table if exists t_msg_lesson032;
create table if not exists t_msg_lesson032
(
    id               varchar(32) not null primary key comment '消息id',
    body_json        text        not null comment '消息体,json格式',
    status           smallint    not null default 0 comment '消息状态，0：待投递到mq，1：投递成功，2：投递失败',
    expect_send_time datetime    not null comment '消息期望投递时间，大于当前时间，则为延迟消息，否则会立即投递',
    actual_send_time datetime comment '消息实际投递时间',
    create_time      datetime comment '创建时间',
    fail_msg         text comment 'status=2 时，记录消息投递失败的原因',
    fail_count       int         not null default 0 comment '已投递失败次数',
    send_retry       smallint    not null default 1 comment '投递MQ失败了，是否还需要重试？1：是，0：否',
    next_retry_time  datetime comment '投递失败后，下次重试时间',
    update_time      datetime comment '最近更新时间',
    key idx_status (status)
) comment '本地消息表';
```
### 启动应用
```java
com.itsoku.lesson032.Lesson032Application
```
### 案例1：演示：创建订单，模拟立即投递消息
```http
POST http://localhost:8080/order/createOrder
Accept: application/json
Content-Type: application/json
{
  "goods": "立即投递消息",
  "price": "59.00",
  "delaySeconds": 0
}
```
执行完毕后看下数据库中的t_msg_lesson032表的记录，关注下消息的状态，创建时间，期望投递时间，具体投递时间
```sql
select * from t_msg_lesson032;
```
### 案例2：演示：创建订单，模拟投递延迟消息，延迟时间是 5 秒
#### 运行测试用例
```http
POST http://localhost:8080/order/createOrder
Accept: application/json
Content-Type: application/json
{
  "goods": "投递延迟消息，延迟时间 5s",
  "price": "59.00",
  "delaySeconds": 5
}
```
执行完毕后看下数据库中的t_msg_lesson032表的记录，关注下消息的状态，创建时间，期望投递时间，具体投递时间
```sql
select * from t_msg_lesson032;
```
## 源码解析
### 源码位置
源码主要在lesson032模块中，而mq相关的所有核心代码在`com.itsoku.lesson032.mq`包中。
![image-20240505143416356](/blogs/_archive-2024-assets/722b7393e0d0cc1af4c0.webp)
下面主要介绍核心的几个类的代码。
### IMsgSender：负责消息投递
> 业务方直接使用这个类进行消息投递，将这个类注入到自己的类中，然后调用send相关的方法，便可投递消息。
>
> 主要看4个send方法。
```java
com.itsoku.lesson032.mq.sender.IMsgSender
```
### DefaultMsgSender：IMsgSender默认实现类
消息投递的逻辑都在这个类中。
```java
com.itsoku.lesson032.mq.sender.DefaultMsgSender
```
### MqSendRetryJob：消息投递补偿的job
每分钟执行一次，会从本地消息表中查询出未来2分钟内需要投递的消息，然后会进行投递重试，入口代码
```
com.itsoku.lesson032.mq.sender.MqSendRetryJob#sendRetry
```
### 业务方如何使用IMsgSender投递消息（2步）
1. 先注入 IMsgSender
   ```java
   @Autowired
   private IMsgSender msgSender;
   ```
2. 调用 msgSender.send方法投递消息
   ```java
   //投递普通消息
   this.msgSender.send(消息);
   //投递延迟消息
   this.msgSender.send(延迟时间, 延迟时间单位, 消息);
   ```
## 使用注意
### 替换分布式锁
生产上，服务都是集群部署的，同一条消息可能会被多个服务同时处理，会出现重复投递，为了避免这个问题，系统中使用了分布锁。
本文的代码中，分布锁默认是使用java中的ReentrantLock搞的，集群中会有问题，大家用的时候，一定要把这个分布式锁给替换掉，可以引入redisson分布式锁来解决这个问题。
### 本地消息表性能问题
本文中用到了一个本地消息表t_msg，会存储所有消息，数据量大了会有性能问题，建议将投递成功的和投递失败不需要重试的消息，移到备份表，这样可以确保t_msg表的压力比较小，性能也就上去了。
