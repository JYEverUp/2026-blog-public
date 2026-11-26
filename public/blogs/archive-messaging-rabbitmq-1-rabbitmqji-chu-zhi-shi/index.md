# 1. RabbitMQ

## 1.1.   分布式开发遇到的问题

随着微服务架构的流行，MQ成了解决微服务之间问题的常用工具。

以电商应用为例，应用中有订单系统、库存系统、物流系统、支付系统。用户创建订单后，如果耦合调用库存系统、物流系统、支付系统，任何一个子系统出了故障，都会造成下单操作异常。

当转变成基于消息队列的方式后，系统间调用的问题会减少很多，比如物流系统因为发生故障，需要几分钟来修复。在这几分钟的时间里，物流系统要处理的内存被缓存在消息队列中，用户的下单操作可以正常完成。当物流系统恢复后，继续处理订单信息即可，中单用户感受不到物流系统的故障。提升系统的可用性。

![mq-fenxi](/blogs/_archive-2024-assets/46e26aa7012db1a7881f.jpg)

## 1.2.   消息队列（MQ）

### 1.2.1.   什么是消息队列

消息队列，即MQ，Message Queue。

![1527063872737](/blogs/_archive-2024-assets/0982bcd4be94eca0ff5f.webp)

**消息传递：**指的是程序之间通过消息发送数据进行通信，而不是通过直接调用彼此来通信，直接调用通常是用于诸如远程过程调用的技术。

**排队：**指的是应用程序通过队列来通信。

**业务场景说明：**

消息队列在大型电子商务类网站，如京东、淘宝、去哪儿等网站有着深入的应用，为什么会产生消息队列？有几个原因：

不同进程（process）之间传递消息时，两个进程之间**耦合**程度过高，改动一个进程，引发必须修改另一个进程，为了**隔离**这两个进程，在两进程间抽离出一层（一个模块），所有两进程之间传递的消息，都必须通过消息队列来传递，单独修改某一个进程，不会影响另一个；

不同进程（process）之间传递消息时，为了实现标准化，将消息的格式规范化了，并且，某一个进程接受的**消息太多**，一下子无法处理完，并且也有先后顺序，必须对收到的消息**进行排队**，因此诞生了事实上的消息队列；

消息队列是典型的：生产者、消费者模型。生产者不断向消息队列中生产消息，消费者不断的从队列中获取消息。因为消息的生产和消费都是异步的，而且只关心消息的发送和接收，没有业务逻辑的侵入，这样就实现了生产者和消费者的解耦。

结合前面所说的问题：

- 商品服务对商品增删改以后，无需去操作索引库，只是发送一条消息，也不关心消息被谁接收。
- 搜索服务服务接收消息，去处理索引库。

如果以后有其它系统也依赖商品服务的数据，同样监听消息即可，商品服务无需任何代码修改。



### 1.2.2 消息队列主要作用

#### 1、异步处理

串行和并行：

(1) **串行方式：**

> 将注册信息写入数据库后，发送注册邮件，再发送注册短信，以上三个任务全部完成后才返回给客户端。 这有一个问题是，邮件，短信并不是必须的，它只是一个通知，而这种做法让客户端等待没有必要等待的东西。

(2) **并行方式：**

> 将注册信息写入数据库后，发送邮件的同时，发送短信，以上三个任务完成后，返回给客户端，并行的方式能提高处理的时间。

传统模式的缺点：

- 一些非必要的业务逻辑以同步(串行)的方式运行，太耗费时间。

![mq-tongbu](/blogs/_archive-2024-assets/76807ee30b5f6f8cd2c1.jpg)

中间件模式的的优点：

- 将消息写入消息队列，非必要的业务逻辑以异步的方式运行，加快响应速度

![mq-yibu](/blogs/_archive-2024-assets/add711938131e78c49d7.jpg)

#### 2、解耦服务

传统模式的缺点：

- 系统间耦合性太强，系统A在代码中直接调用系统B和系统C的代码，如果将来D系统接入，系统A还需要修改代码，过于麻烦！

**![mq-weijieou](/blogs/_archive-2024-assets/c9281cf087f1dc9615d4.jpg)**

消息中间件模式的的优点：

- 将消息写入消息队列，需要消息的系统自己从消息队列中订阅，从而系统A不需要做任何修改。

**![mq-jieou](/blogs/_archive-2024-assets/87f115ae2ea07fd9882a.jpg)**

#### 3、流量削峰(削峰填谷)

流量削峰一般在秒杀活动中应用广泛
场景: 秒杀活动，一般会因为流量过大，导致应用挂掉,为了解决这个问题，一般在应用前端加入消息队列。

**传统模式**

如订单系统，在下单的时候就会往数据库写数据。但是数据库只能支撑每秒1000左右的并发写入，并发量再高就容易宕机。低峰期的时候并发也就100多个，但是在高峰期时候，并发量会突然激增到5000以上，这个时候数据库肯定卡死了。

![mq-miaosha](/blogs/_archive-2024-assets/c5bfcdea32c56231c1fb.jpg)

**中间件模式**

消息被MQ保存起来了，然后系统就可以按照自己的消费能力来消费，比如每秒1000个数据，这样慢慢写入数据库，这样就不会卡死数据库了。

![mq-miaoshamq](/blogs/_archive-2024-assets/1d2d7fb0e7d157d08d2f.jpg)

### 1.2.2.   AMQP和JMS

MQ是消息通信的模型，并不是具体实现。现在实现MQ的有两种主流方式：AMQP、JMS。

![1527064480681](/blogs/_archive-2024-assets/3a66d11b79d6211868e6.webp)

![1527064487042](/blogs/_archive-2024-assets/e958425670d32f2c10bb.webp)



两者间的区别和联系：

- JMS是定义了统一的接口，来对消息操作进行统一；AMQP是通过规定协议来统一数据交互的格式
- JMS限定了必须使用Java语言；AMQP只是协议，不规定实现方式，因此是跨语言的。
- JMS规定了两种消息模型；而AMQP的消息模型更加丰富



### 1.2.3.   常见MQ产品

![1527064606029](/blogs/_archive-2024-assets/43aece6bc8855b3d3d92.webp)

- ActiveMQ：基于JMS
- RabbitMQ：基于AMQP协议，erlang语言开发，稳定性好
- RocketMQ：基于JMS，阿里巴巴产品，目前交由Apache基金会
- Kafka：分布式消息系统，高吞吐量



### 1.2.4.   RabbitMQ

RabbitMQ由erlang语言开发，是基于AMQP的一款消息管理系统

官网： http://www.rabbitmq.com/

官方教程：http://www.rabbitmq.com/getstarted.html

![1532758972119](/blogs/_archive-2024-assets/0f4f9e16be1c71a4b546.webp)



 ![1527064762982](/blogs/_archive-2024-assets/5061bdd2f316411e9ab5.webp)

RabbitMQ 基础架构如下图：

![mq-jiaggoutu](/blogs/_archive-2024-assets/23e18b2b1be3f89b8bcc.jpg)

**Broker：**接收和分发消息的应用，RabbitMQ Server就是 Message Broker

**Virtual host：**出于多租户和安全因素设计的，把 AMQP 的基本组件划分到一个虚拟的分组中，类似于网络中的 namespace 概念。当多个不同的用户使用同一个 RabbitMQ server 提供的服务时，可以划分出多个vhost，每个用户在自己的 vhost 创建 exchange／queue 等

**Connection：**publisher／consumer 和 broker 之间的 TCP 连接

**Channel：**如果每一次访问 RabbitMQ 都建立一个 Connection，在消息量大的时候建立 TCP Connection的开销将是巨大的，效率也较低。Channel 是在 connection 内部建立的逻辑连接，如果应用程序支持多线程，通常每个thread创建单独的 channel 进行通讯，AMQP method 包含了channel id 帮助客户端和message broker 识别 channel，所以 channel 之间是完全隔离的。Channel 作为轻量级的 Connection 极大减少了操作系统建立 TCP connection 的开销

**Exchange：**message 到达 broker 的第一站，根据分发规则，匹配查询表中的 routing key，分发消息到queue 中去。常用的类型有：direct (point-to-point), topic (publish-subscribe) and fanout (multicast)

**Queue：**消息最终被送到这里等待 consumer 取走

**Binding：**exchange 和 queue 之间的虚拟连接，binding 中可以包含 routing key。Binding 信息被保存到 exchange 中的查询表中，用于 message 的分发依据



## 1.3.   下载和安装

### 1.3.1.   下载

官网下载地址：http://www.rabbitmq.com/download.html

![1532759070767](/blogs/_archive-2024-assets/9b1c252b569a08fd0ac6.webp)



### 1.3.2.   安装

#### 1. 方式1-docker中安装

下载镜像：`docker pull rabbitmq:management`

创建实例并启动：

```
docker run -d --name rabbitmq --publish 5671:5671 \
--publish 5672:5672 --publish 4369:4369 --publish 25672:25672 --publish 15671:15671 --publish 15672:15672 \
rabbitmq:management
```

注：
4369 -- erlang发现口
5672 --client端通信口

15672 -- 管理界面ui端口
25672 -- server间内部通信口

#### 2.  方式2-安装包安装

##### 2.1 安装Erlang、Socat、RabbitMQ

拷贝课件中的安装包到虚拟机/opt目录下

![1591519836757](/blogs/_archive-2024-assets/b7503fca337c6945d692.webp)

执行安装命令：

```sh
rpm -ivh erlang-21.3.8.9-1.el7.x86_64.rpm

rpm -ivh socat-1.7.3.2-1.el6.lux.x86_64.rpm 

rpm -ivh  rabbitmq-server-3.8.1-1.el7.noarch.rpm
#如果rabbitmq安装报错，在线安装socat
yum install -y socat
```

安装成功后rabbitmq命令存放在：/usr/lib/rabbitmq/lib/rabbitmq_server-3.8.1/sbin 

**![1591519974961](/blogs/_archive-2024-assets/66685f1b3cdf633f761c.webp)**

##### 2.2 启用管理插件

```
rabbitmq-plugins enable rabbitmq_management
```

##### 2.3 RabbitMQ启停命令

```
# 第一次启动时会比较慢
systemctl start rabbitmq-server.service

systemctl status rabbitmq-server.service

systemctl restart rabbitmq-server.service

systemctl stop rabbitmq-server.service 
```

##### 2.4 查看进程

```
ps -ef | grep rabbitmq
```

rabbitmq启动时会监听三个端口号：

​	5672： 其他程序和rabbitmq交互的端口[比如：java程序需要使用rabbitmq，就和此端口建立连接]

​	15672：rabbitmq的后台管理系统的端口号[rabbitmq的客户端]

​	25672：集群环境搭建的端口号

![image-20200905205613090](/blogs/_archive-2024-assets/a3a9ceddcc0ea7225635.webp)

### 1.3.3.   测试

在web浏览器中输入地址：http://虚拟机ip:15672/

输入默认账号: guest   : guest，默认不允许远程连接

![1591520236484](/blogs/_archive-2024-assets/1a7041cbc28bdc92eef0.webp)

解决：

增加管理员账号：

```
rabbitmqctl add_user admin admin
```

![image-20200905205808224](/blogs/_archive-2024-assets/48dc4247317fbb316981.png)

如果新增慢，然后报错新增失败，解决方案：

```sh
//查询当前主机的名称
cat /etc/hostname
//将主机名称和本机的ip 127.0.0.1绑定映射存到hosts文件中
vim /etc/hosts
127.0.0.1    查询到的主机名称
//然后再次添加用户
rabbitmqctl add_user admin admin
```



给账号分配角色：

```
# 角色:
# 1、超级管理员(administrator)：所有权限
# 2、监控者(monitoring): 登录控制台、查看mq信息权限
# 3、策略制定者(policymaker)：登录控制台、管理policy权限
# 4、普通管理者(management)：只能登录控制台
rabbitmqctl set_user_tags admin administrator
```

修改角色密码：

```
rabbitmqctl change_password admin 123456
```

查看用户列表：

```
rabbitmqctl list_users
```

测试，使用新建账号登录

![1591521171660](/blogs/_archive-2024-assets/62102a02d9ee157c40c7.webp)



overview：概览

connections：无论生产者还是消费者，都需要与RabbitMQ建立连接后才可以完成消息的生产和消费，在这里可以查看连接情况

channels：通道，建立连接后，会形成通道，消息的投递获取依赖通道。

Exchanges：交换机，用来实现消息的路由

Queues：队列，即消息队列，消息存放在队列中，等待消费，消费后被移除队列。

 

端口：

5672: rabbitMq的编程语言客户端连接端口

15672：rabbitMq管理界面端口

25672：rabbitMq集群的端口

### 1.3.4. 卸载

1、停止rabbitmq服务

```
systemctl stop rabbitmq-server
```


2、卸载erlang
查看erlang安装的相关列表

```
yum list|grep erlang
```


卸载erlang所有内容

```
yum -y remove erlang-*
```


删除erlang目录

```
rm -rf /usr/lib64/erlang
```

3、卸载rabbitmq
查看rabbitmq安装的相关列表

```
yum list|grep rabbitmq
```


卸载rabbitmq所有内容

```
yum -y remove rabbitmq-server.noarch
```


查找并删除rabbitmq相关目录

```
find / -name rabbit*
```

依次删除对应目录：rm -rf 路径
例如：

```sh
rm -rvf /var/lib/rabbitmq
rm -rvf /usr/lib/rabbitmq
rm -rvf /var/log/rabbitmq
```



## 1.4.   管理界面

### 1.4.1.   管理界面添加用户

通过管理界面我们也可以自己创建一个用户：

![1570341128229](/blogs/_archive-2024-assets/59096e80988d62565c4b.webp)

1、 超级管理员(administrator)

可登陆管理控制台，可查看所有的信息，并且可以对用户，策略(policy)进行操作。

2、 监控者(monitoring)

可登陆管理控制台，同时可以查看rabbitmq节点的相关信息(进程数，内存使用情况，磁盘使用情况等)

3、 策略制定者(policymaker)

可登陆管理控制台, 同时可以对policy进行管理。但无法查看节点的相关信息(上图红框标识的部分)。

4、 普通管理者(management)

仅可登陆管理控制台，无法看到节点信息，也无法对策略进行管理。

5、 其他

无法登陆管理控制台，通常就是普通的生产者和消费者。

 

### 1.4.2.   创建Virtual Hosts

虚拟主机：类似于mysql中的database。他们都是以“/”开头

![1570341361306](/blogs/_archive-2024-assets/a63b065cc8f7aadecf5c.webp)



### 1.4.3.   设置权限

![1570341470699](/blogs/_archive-2024-assets/1cb142df2de7101fd9e8.webp)

![1570341567294](/blogs/_archive-2024-assets/101ce44448818384becf.webp)

![1570341637530](/blogs/_archive-2024-assets/e77c6946cecba47084f0.webp)
