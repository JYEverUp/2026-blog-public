## 单机的安装与启动

### 准备工作

#### 硬件

准备一台linux，我用的vm虚拟机centos，输入`ifconfig`获得`ens33`的ip为`inet 192.168.146.128`

在`C:\Windows\System32\drivers\etc\`修改host文件，将ip指向我自定义命名的centos域名

#### 环境

1. 64bit OS, Linux/Unix/Mac is recommended;(Windows user see guide below)
2. 64bit JDK 1.8+
3. Maven 3.2.x
4. Git
5. 4g+ free disk for Broker server

查看我的linux有没有jdk环境`echo $JAVA_HOME`，答案是没有

去官网下载linux的安装包，传到虚拟机



配置环境变量，输入3个值保存后，刷新profile

```bash
vi /etc/profile

# java
export JAVA_HOME=/usr/bin/java/jdk1.8.0_291
export PATH=$JAVA_HOME/bin:$PATH
export CLASSPATH=.:$JAVA_HOME/lib/dt.jar:$JAVA_HOME/lib

source /etc/profile
```

测试java环境

```bash
javac
java -version
echo $JAVA_HOME
```

#### linux防火墙开放端口

> CentOS升级到7之后，发现无法使用iptables控制Linux的端口，因为Centos 7使用firewalld代替了原来的iptables。下面记录如何使用firewalld开放Linux端口：

**开启端口**

```bash
firewall-cmd --zone=public --add-port=9800/tcp --permanent
```

**查询端口是否开启**

```bash
firewall-cmd --query-port=9800/tcp
```

**重启防火墙**

```bash
firewall-cmd --reload
```

**查询有哪些端口是开启的**

```bash
firewall-cmd --list-port
```

这里方法先放着，等会如果出现开启控制台无法访问时，应该是端口号没打开，例如我rocketmq-console选择9800为端口，所以需要开放9800端口

### 下载RocketMQ

[官网地址](http://rocketmq.apache.org/)

![在这里插入图片描述](/blogs/_archive-2024-assets/f47c1f136c2f03e2ad56.webp)



我这里下载的4.9.1版本的，根据自己需求下载即可

[北京外国语镜像地址](https://mirrors.bfsu.edu.cn/apache/rocketmq/4.9.1/)

- Source源码版本
- Binary编译后的文件

我们下载Binary文件，zip文件，然后传到linux上

`unzip rocketmq-all-4.9.1-bin-release.zip`解压文件

### 修改启动内存

因为默认的内存太大了，2G、4G啥的，服务器的配置可能起不来，所以修改一下配置

**runserver.sh**

修改为256m

![在这里插入图片描述](/blogs/_archive-2024-assets/e1f960577d9a83eccb1f.webp)

**runbroker.sh**

修改为256m

![在这里插入图片描述](/blogs/_archive-2024-assets/c2dfca8ac319fdc36fe6.webp)



### Linux下启动rocketmq



#### Start Name Server

```bash
 	# 启动nameserver服务
  > nohup sh bin/mqnamesrv &
  	# 查看日志是否启动成功
  > tail -f ~/logs/rocketmqlogs/namesrv.log
  The Name Server boot success...
  	# 查看当前java进程
  > jps
  240921 NamesrvStartup
  246169 Jps
```



#### Start Broker

```bash
  > nohup sh bin/mqbroker -n localhost:9876 -c conf/broker.conf &
  > tail -f ~/logs/rocketmqlogs/broker.log
  The broker[%s, 172.30.30.233:10911] boot success...
  > jps
  253009 BrokerStartup
  254698 Jps
  240921 NamesrvStartup
```

**端口必须开放9876和10911端口**

#### Send & Receive Messages

在发送/接收消息之前，我们需要告诉客户端名称服务器的位置。RocketMQ提供了多种方法来实现这一点。为了简单起见，我们使用环境变量`namersv_ADDR`

以下为官方提供的一个发消息和消费消息的用例

```bash
 > export NAMESRV_ADDR=localhost:9876
 > sh bin/tools.sh org.apache.rocketmq.example.quickstart.Producer
 SendResult [sendStatus=SEND_OK, msgId=7F0000011BE34AA298B76656B91103E7, offsetMsgId=C0A8928000002A9F000000000002ECD2, messageQueue=MessageQueue [topic=TopicTest, brokerName=centos, queueId=2], queueOffset=249]
 close the connection to remote address[127.0.0.1:9876] result: true
 
 > sh bin/tools.sh org.apache.rocketmq.example.quickstart.Consumer
 ConsumeMessageThread_2 Receive New Messages: [MessageExt [brokerName=centos, queueId=0, storeSize=192, queueOffset=145, sysFlag=0, bornTimestamp=1634734558909, bornHost=/192.168.146.128:33198, storeTimestamp=1634734558910, storeHost=/192.168.146.128:10911, msgId=C0A8928000002A9F000000000001B352, commitLogOffset=111442, bodyCRC=953417484, reconsumeTimes=0, preparedTransactionOffset=0, toString()=Message{topic='TopicTest', flag=0, properties={MIN_OFFSET=0, MAX_OFFSET=250, CONSUME_START_TIME=1634734753329, UNIQ_KEY=7F0000011BE34AA298B76656B6BD0245, CLUSTER=DefaultCluster, TAGS=TagA}, body=[72, 101, 108, 108, 111, 32, 82, 111, 99, 107, 101, 116, 77, 81, 32, 53, 56, 49], transactionId='null'}]]
 
```



#### Shutdown Servers

```bash
> sh bin/mqshutdown broker
The mqbroker(36695) is running...
Send shutdown request to mqbroker(36695) OK

> sh bin/mqshutdown namesrv
The mqnamesrv(36664) is running...
Send shutdown request to mqnamesrv(36664) OK
```



### rocketmq控制台

[github地址](https://github.com/apache/rocketmq-externals/tags)

下载解压，是一个maven项目

#### 修改配置

进入src、resource文件夹，修改properties文件

![在这里插入图片描述](/blogs/_archive-2024-assets/19785d742f1c22495b48.webp)

默认端口是8080，这我们当然要改动了

而且他也是相当于一个client，所以需要去获取nameserver，所以需要配置nameserver的地址

```shell
server.port=9800
rocketmq.config.namesrvAddr=localhost:9876
```

#### 导入依赖

导入JAXB依赖：Java Architecture for XML Binding 

> 允许Java开发人员将Java类映射为XML表示方式。
>
> JAXB提供两种主要特性：
>
> - 将一个Java对象序列化为XML，以及反向操作，将XML解析成Java对象。
> - 换句话说，JAXB允许以XML格式存储和读取数据，而不需要程序的类结构实现特定的读取XML和保存XML的代码。 



```xml
<dependency>
    <groupId>javax.xml.bind</groupId>
    <artifactId>jaxb-api</artifactId>
    <version>2.3.0</version>
</dependency>
<dependency>
    <groupId>com.sun.xml.bind</groupId>
    <artifactId>jaxb-impl</artifactId>
    <version>2.3.0</version>
</dependency>
<dependency>
    <groupId>com.sun.xml.bind</groupId>
    <artifactId>jaxb-core</artifactId>
    <version>2.3.0</version>
</dependency>
<dependency>
    <groupId>javax.activation</groupId>
    <artifactId>activation</artifactId>
    <version>1.1.1</version>
</dependency>
```

#### 打包启动

跳过测试环节，目前不满足测试条件，会报错

```shell
mvn clean package -Dmaven.test.skip=true
```

得到结果则打包成功

```shell
[INFO] Building jar: E:\speciality_apps\RocketMQ\rocketmq-console-1.0.0\rocketmq-externals-rocketmq-console-1.0.0\rocketmq-console\target\rocketmq-console-ng-1.0.0-sources.jar
[INFO] ------------------------------------------------------------------------
[INFO] BUILD SUCCESS
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  54.114 s
[INFO] Finished at: 2021-10-20T21:29:12+08:00
[INFO] ------------------------------------------------------------------------
```

`rocketmq-console-ng-1.0.0-sources.jar`就是我们打包后的可执行jar，输入指令运行

```shell
java -jar rocketmq-console-ng-1.0.0.jar
```

出现运行成功和端口即可

```shell
[2021-10-20 21:41:23.209]  INFO Tomcat started on port(s): 9800 (http)
```

接下来访问我们的控制台，我这里访问的虚拟机

在OPS运维栏好像是可以添加删除和更新rocketmq的地址的

![在这里插入图片描述](/blogs/_archive-2024-assets/68929c6f8fe70a9c761d.webp)

#### 测试访问message

我们重新发送消息测试样例

```bash
export NAMESRV_ADDR=localhost:9876
sh bin/tools.sh org.apache.rocketmq.example.quickstart.Producer
```

然后在导航栏选中`Message`，选中`TopicTest`点击search

查询出来刚刚发送过去但是还未消费的消息

![在这里插入图片描述](/blogs/_archive-2024-assets/7f75ba235943ff038f8b.webp)



## 集群的搭建

![在这里插入图片描述](/blogs/_archive-2024-assets/395efb00200e98b2de3a.webp)

producer和consumer集群只需要写入相同的group_name即可成为集群，启动一个就会增加一个节点，这里暂且不论

nameserver呢相互之间没有通讯，所以也是启动即节点，这里也不论

所以本章讲解的是**broker集群**

### 数据复制与刷盘策略

![在这里插入图片描述](/blogs/_archive-2024-assets/e43bd42c47688695dc10.webp)

#### 复制策略

复制策略是Broker的Master与Slave间的数据同步方式

分为同步复制与异步复制：

- 同步复制:消息写入master后，master会等待slave同步数据成功后才向producer返回成功ACK
- 异步复制:消息写入master后，master立即向producer返回成功ACK， 无需等待slave同步数据成功



#### 刷盘策略

由内存到磁盘的过程，就叫刷盘（持久化？）

刷盘策略指的是broker中消息的落盘方式，即**消息发送到broker内存后消息持久化到磁盘的方式**

分为同步刷盘与异步刷盘:

- 同步刷盘:当消息持久化到broker的磁盘后才算是消息写入成功
- 异步刷盘:当消息写入到broker的内存后即表示消息写入成功，无需等待消息持久化到磁盘

> 1. 异步策略当然会降低延迟，提高吞吐量
> 2. 消息写入到Broker的内存，一般是写入了PageCache
> 3. 对于异步策略来说，写入到PageCache后不会立马进行刷盘操作，而是等待数据达到一定量的时候再进行落盘（应该也是提高效率，减少频繁的io）

### Broker集群模式

#### 单master

只有一个broker (其本质上就不能称为集群)。这种方式也只能是在测试时使用，生产环境下不能使用

因为存在**单点问题**

> 什么是单点问题？
>
> 指系统中一点失效，就会让整个系统无法运作的部件，换句话说，单点故障即会整体故障 

#### 多master

broker集群仅由多个master构成，不存在Slave。 同一Topic的各个Queue会平均分布在各个master节点上

- 优点：配置简单，单个Master宕机或重启维护对应用无影响，在磁盘配置为RAID10时，即使机器宕机不可恢复情况下，由于RAID10磁盘非常可靠，消息也不会丢(异步刷盘丢失少量消息，同步刷盘一条不丢)，性能最高

- 缺点：单台机器宕机期间，这台机器上未被消费的消息在机器恢复之前不可订阅(不可消费)，消息实时性会受到影响

> 什么是raid10？
>
> Raid 10是一个Raid 1与Raid0的组合体，它是利用奇偶校验实现条带集镜像，所以它继承了Raid0的快速和Raid1的安全。我们知道，RAID 1在这里就是一个冗余的备份阵列，而RAID 0则负责数据的读写阵列。其实，概述图只是一种RAID 10方式，更多的情况是从主通路分出两路，做Striping操作，即把数据分割，而这分出来的每一路则再分两路，做Mirroring操作，即互做镜像



#### 多master多slave模式——异步复制

broker集群由多个master构成，每个master又配置了多个slave 

注：在配置了RAID磁盘阵列的情况下，一个master一般配置一个slave即可

master 与slave的关系是主备关系，即**master负责处理消息的读写请求**，而**slave仅负责消息的备份与master宕机后的角色切换**



异步复制即前面所讲的复制策略中的异步复制策略，即消息写入master成功后，master立即向producer返回成功ACK，无需等待slave同步数据成功

该模式的最大特点之一是：**当master宕机后，slave能够自动切换为master**

不过由于slave从master的同步具有短暂的延迟(毫秒级)，所以当master宕机后，这种异步复制方式可能会存在少量消息的丢失问题

#### 多master多slave模式——同步双写

该模式是多Master多slave模式的同步复制实现

所谓同步双写，指的是消息写入master成功后，master会等待slave同步数据成功后才向producer返回成功ACK，即**master 与slave都要写入成功后才会返回成功ACK**，也即双写

该模式与异步复制模式相比，优点是消息的安全性更高，不存在消息丢失的情况。但单个消息的RT略高，从而导致性能要略低(大约低10%)

该模式存在一个大的问题：**对于目前的版本，Master宕机后， Slave不能自动切换到Master**

#### 最佳方案

> 一般会为Master配置RAID10磁盘阵列，然后再为其配置一个Slave
>
> 即利用了RAID10磁盘阵列的高效、安全性，又解决了可能会影响订阅的问题



但是RAID10磁盘阵列价格较高且可能会影响订阅的问题，所以个人认为还是多Master+slave+异步策略为最佳



## 集群搭建实践

### 配置

将linux系统克隆一份，选用两台机器进行集群的搭建



进入conf文件夹，查看文件夹，有系统默认给出的3个方案

![在这里插入图片描述](/blogs/_archive-2024-assets/bbca8a332a0147b37b20.webp)

- 2m-2s-async：2主2从异步策略
- 2m-2s-sync：2主2从同步策略
- 2m-noslave：2主策略

我们就进去2m2s异步策略文件夹

```bash
[root@centos conf]# cd 2m-2s-async/
[root@centos 2m-2s-async]# ll
总用量 16
-rwxr-xr-x 1 root root 929 8月  16 06:20 broker-a.properties
-rwxr-xr-x 1 root root 922 8月  16 06:20 broker-a-s.properties
-rwxr-xr-x 1 root root 929 8月  16 06:20 broker-b.properties
-rwxr-xr-x 1 root root 922 8月  16 06:20 broker-b-s.properties
```

很明显的可以看出，-s是slave配置文件，正常的就是master配置文件

我们这是选用

- broker-a.properties+broker-b-s.properties
- broker-b.properties+broker-a-s.properties

即

- master1+slave2
- master2+slave1



vim修改配置文件broker-a.properties

```properties
#指定整个broker集群的名称，或者说是RocketMQ集群的名称
brokercluste rName=Defaultcluster
#指定master-slave集群的名称。一个RocketMQ集群可以包含多个master-slave集群，所以m和s保持一致
brokerName=broker-a
# master的brokerId为0，0代表master，1代表slave
brokerId=0
#指定删除消息存储过期文件的时间为凌晨4点
deletewhen=04
#指定未发生更新的消息存储文件的保留时长为48小时，48小时后过期，将会被删除
fileReservedTime=48
#指定当前broker为异步复制master
brokerRole=ASYNC_MASTER
#指定刷盘策略为异步刷盘
f1ushDi skType=ASYNC_FLUSH
```

我们需要配置，指定Name Server的地址

```properties
#指定Name Server的地址
namesrvAddr=192.168.59.164:9876;192.168.59.165:9876
```



修改配置文件broker-b-s.properties

```properties
brokercluste rName=Defaultcluster
#指定这是另外个master-slave集群
brokerName=broker-b
# slave的brokerId为非0
brokerId=1
deletewhen=04
fileReservedTime=48
#指定当前broker为slave后
brokerRole=SLAVE
flushDiskType=ASYNC_FLUSH
namesrvAddr=192.168.59.164:9876;192.168.59.165:9876
#指定Broker对外提供服务的端口，即Broker与producer与consumer通信的端口。默认10911。由于当前主机同时充当着master1与s]ave2，而前面的master1使用的是默认端口。这里需要将这两个端口加以区分，以区分出master1与s1ave2
listenPort=11911
#指定消息存储相关的路径。 默认路径为~/store目录。由于当前主机同时充当着master1与slave2, master1使用的是默认路径，这里就需要再指定一个不同路径
storePathRootDir=~/store-s
storePathcommi tLog=~/store-s/commit1og
storepathconsumeQueue=~/store-s/consumequeue
storepathIndex=~/store-s/ i ndex
storeCheckpoint=~/store-s/checkpoint
abortFile=~/store-s/abort
```



另一台机器同理设置另外两个配置



### 启动

#### 启动nameserver

上文有写

```bash
nohup sh bin/mqnamesrv &
tail -f ~/logs/rocketmqlogs/namesrv.log
```



#### 启动两个master

与上文不同，启动时需要指定文件启动

分别启动两个机器的broker master

```bash
nohup sh bin/mqbroker -C conf/2m-2s-async /broker-a.properties &
tail -f ~/logs/rocketmqlogs/broker.log 
```

 

```bash
nohup sh bin/mqbroker -C conf/2m-2s-async /broker-b.properties &
tail -f ~/logs/rocketmqlogs/broker.log
```





#### 启动两个slave

```bash
nohup sh bin/mqbroker -C conf/2m-2s-async /broker-b-s.properties &
tail -f ~/logs/rocketmqlogs/broker.log 
```



```bash
nohup sh bin/mqbroker -C conf/2m-2s-async /broker-a-s.properties &
tail -f ~/logs/rocketmqlogs/broker.log 
```



#### 修改控制台配置

```properties
rocketmq.config.namesrvAddr=ipA:9876;ipB:9877
```

应该也可以直接在控制台添加一个nameserver



## mqadmin命令

在mq的bin目录有一个mqadmin命令，该命令是一个运维命令，用于对mq的主题、集群、broker等信息进行管理

这个命令能够完成的功能在控制台都可以完成

这里就不再阐述了，贴一个[博客地址](https://blog.csdn.net/wulitaot/article/details/79551499)



## RocketMQ工作原理

这个是一个重点、难点、面试高频考点

![在这里插入图片描述](/blogs/_archive-2024-assets/68bc603e65e7dd00f1b1.webp)

### 消息的生产

#### 消息的生产过程

Producer可以将消息写入到某Broker中的某Queue中，其经历了如下过程：

- Producer发送消息之前，会先向NameServer发出获取**消息Topic的路由信息**的请求

- NameServer返回该Topic的**路由表**及**Broker列表**

  - > 路由表：实际是一个Map, key为Topic名称，value是一个QueueData实例列表
    >
    > QueueData并不是一个Queue, 对应一个QueueData, 而是一个Broker中该Topic的所有Queue对应一个QueueData即，只要涉及到该Topic的Broker，一个Broker对应一 个QueueData，QueueData中包含BrokerName
    >
    > 简单来说，路由表的key为Topic名称，value则为所有涉及该Topic的BrokerName列表
    >
    > 
    >
    > Broker列表：实际上也是一个Map，key为BrokerName，value是BrokerData
    >
    > 一个BrokerData对应了一套BrokerName相同的Master-Slave的小集群
    >
    > BrokerData中包含了一个BrokerName和一个map
    >
    > map的key为BrokerId（0-master，1-slave），value为broker的地址

- Producer根据代码中指定的Queue选择策略，从Queue列表中选出一个队列，用于后续存储消息

- Produer对消息做一些特殊处理，例如，消息本身超过4M,则会对其进行压缩

- Producer向选择出的Queue所在的Broker发出RPC请求，将消息发送到选择出的Queue



#### Queue选择算法

有序消息可以指定queue，无序消息则由系统自己选择

对于无序消息，其Queue选择算法也称为消息投递算法，常见的有两种：

**轮询算法**：

默认选择算法。该算法保证了每个Queue中可以均匀的获取到消息

> 该算法存在一个问题:由于某些原因，在某些Broker. 上的Queue可能投递延迟较严重
>
> 从而导致Producer的缓存队列中出现较大的消息积压，影响消息的投递性能

**最小投递延迟算法**：

该算法会统计每次消息投递的时间延迟，然后根据统计出的结果将消息投递到时间延迟最小的Queue

如果延迟相同，则采用轮询算法投递。

> 如果存在一个queue一直延迟最低，则所有消息都会堆积到该queue中，分配不均，导致压力暴增



### 消息的储存

RocketMQ中的消息存储在本地文件系统中，这些相关文件默认在当前用户主目录下的store目录中。

![在这里插入图片描述](/blogs/_archive-2024-assets/9eb679d8a9058165624a.webp)



- abort：该文件在Broker启动后会自动创建，正常关闭Broker,该文件会自动消失。若在没有启动Broker的情况下，发现这个文件是存在的，则说明之前Broker的关闭是非正常关闭。
- checkpoint：其中存储着commitlog、 consumequeue、 index文件的最后刷盘时间戳
- commitlog：其中存放着commitlog文件，而消息是写在commitlog文件中的
- config：存放着Broker运行期间的一些配置数据
- consumequeue：其中存放着consumequeue文件，队列就存放这个目录中
- index：其中存放着消息索引文件indexfile
- lock：运行期间使用到的全局资源锁



RocketMQ中，无论是消息本身还是消息索引，都是存储在磁盘上的。其不会影响消息的消费吗?

当然不会。其实RocketMQ的性能在目前的MQ产品中性能是非常高的。因为系统通过一系列相关机制大大提升了性能。

首先，RocketMQ对文件的读写操作是通过mmap零拷贝进行的，将对文件的操作转化为直接对内存地址进行操作，从而极大地提高了文件的读写效率。

其次，consumequeue中的数据是顺序存放的，还引入了PageCache的预读取机制，使得对consumequeue文件的读取几乎接近于内存读取，即使在有消息堆积情况下也不会影响性能。

RocketMQ中可能会影响性能的是对commitlog文件的读取。因为对commitlog文件来说， 读取消息时会产生大量的随机访问，而随机访问会严重影响性能。

不过，如果选择合适的系统IO调度算法，比如设置调度算法为Deadline (采用SSD固态硬盘的话)，随机读的性能也会有所提升。



### indexFile

除了通过通常的**指定Topic进行消息消费**外，RocketMQ还提供了**根据key进行消息查询**的功能。

该查询是通过store目录中的index子目录中的indexFile进行索引实现的快速查询。

当然，这个indexFile中的索引数据是在包含了key的消息被发送到Broker时写入的。如果消息中没有包含key,则不会写入。

每个Broker中会包含一组indexFile, 每个indexFile都是以一 个时间戳命名的(这个indexFile被创建时的时间戳)。每个indexFile文件由三部分构成：

- indexHeader
- slots槽位
- indexes索引数据

每个indexFile文件中包含500w个slot槽。而每个slot槽又可能会挂载很多的index索引单元。

![在这里插入图片描述](/blogs/_archive-2024-assets/ec8b2a21c3c80f64ab06.webp)

indexHeader固定40个字节，其中存放着如下数据：

![在这里插入图片描述](/blogs/_archive-2024-assets/3dfc10212977c97925f3.webp)

- beginTimestamp:该indexFile中第一 条消息的存储时间
- endTimestamp:该indexFile中最后一 -条消息存储时间
- beginPhyoffset:该indexFile中第一 条消息在commitlog中的偏移量commitlog offset
- endPhyoffset:该indexFile中最后一 条消息在commitlog中的偏移量commitlog offset
- hashSlotCount:已经填充有index的slot数量（并不是每个slot都有挂载的index索引单元，这里统计的是所有已经挂载了的index索引单元的数量）
- indexCount:该indexFile中包含的索引个数



indexFile中最复杂的是Slots与Indexes间的关系。在实际存储时，Indexes 是在Slots后面的，但为了便于理解，将它们的关系展示为如下形式:

### 消息的消费

消费者从Broker中获取消息的方式有两种：

- pull拉取方式
- push推动方式

消费者组对于消息消费的模式又分为两种：

- 集群消费Clustering
- 广播消费Broadcasting



#### 推拉获取消费类型



**pull拉取模式**：

Consumer主动从Broker中拉取消息，主动权由Consumer控制。一旦获取了批量消息，就会启动消费过程

不过，该方式的实时性较弱，即Broker中有了新的消息时消费者并不能及时发现并消费



**push推送模式**：

该模式下Broker收到数据后会主动推送给Consumer。该消费模式一般实时性较高。

该消费类型是典型的**发布-订阅**模式，即Consumer向其关联的Queue注册了监听器，一旦发现有新的消息到来就会触发回调的执行，回调方法是Consumer去Queue中拉取消息。

而这些都是基于Consumer与Broker间的长连接的。长连接的维护是需要消耗系统资源的。



**对比**：

- pull：需要应用去实现对关联Queue的遍历，实时性差；但便于应用控制消息的拉取（想拉就拉）
- push：封装了对关联Queue的遍历，实时性强，但会占用较多的系统资源



#### 消费模式



**广播消费**

![在这里插入图片描述](/blogs/_archive-2024-assets/f044126516920be1d541.webp)

广播消费模式下，相同Consumer Group的每个Consumer实例都接收同一个Topic的全量消息

即：每条消息都会被发送到Consumer Group中的==每个==Consumer



**集群消费**

集群消费模式下，相同Consumer Group的每个Consumer实例**平均分摊**同一个Topic的消息。

即：每条消息只会被发送到Consumer Group中的==某个==Consumer



**广播和集群模式的对比**

- 广播模式：

  - 消费进度保存在**consumer端**。因为广播模式下consumer group中每个consumer都会消费所有消息，但它们的消费进度是不同。所以consumer各自**保存各自的消费进度**。

- 集群模式：

  - 消费进度保存在**broker**中。consumer group中的所有consumer共同消费同一个Topic中的消息，同一条消息只会被消费一次。消费进度会参与到了消费的负载均衡中，故消费进度是需要**共享**的。

  

#### Rebalance机制



**什么是Rebalance**：

Rebalance即**再均衡**，指的是，将一个Topic 下的多个Queue在同一个Consumer Group中的多个Consumer间进行重新分配的过程

Rebalance机制的本意是为了**提升消息的并行消费能力**

例如，一个Topic下5个队列，在只有1个消费者的情况下，这个消费者将负责消费这5个队列的消息。如果此时我们增加一一个消费者，那么就可以给其中一个消费者分配2个队列，给另一个分配3个队列，从而提升消息的并行消费能力

![在这里插入图片描述](/blogs/_archive-2024-assets/888ad479f32867accd84.webp)



**rebalance的限制**：

由于一个队列最多分配给一个消费者， 因此当某个消费者组下的消费者实例数量大于队列的数量时，多余的消费者实例将分配不到任何队列

**rebalance的缺点**：

- 消费暂停：

  - 在只有一一个Consumer时， 其负责消费所有队列；在新增了一个Consumer后会触发Rebalance的发生。此时原Consumer就需要**暂停队列的消费**,等到这些队列分配给新的Consumer后，这些暂停消费的队列才能继续被消费。

- 消费重复：

  - Consumer 在消费新分配给自己的队列时，必须接着之前Consumer提交的消费进度的offset继续消费。然而默认情况下，offset是异步提交的，这个异步性导致提交到Broker的offset与Consumer实际消费的消息并不一致。这个不一致的差值就是可能会**重复消费消息**。

  - > 同步提交: consumer提交了其消费完毕的一批消息的offset给broker后， 需要等待broker的成功ACK。当收到ACK后，consumer才会继续获取并消费下一批消息。在等待ACK期间，consumer是阻塞的。
    > 异步提交: consumer提交了其消费完毕的一批消息的offset给broker后， 不需要等待broker的成功ACK。consumer 可以直接获取并消费下一批消息

- 消费突刺：

  - 由于Rebalance可能导致重复消费， 如果需要重复消费的消息过多，或者因为Rebalance暂停时间过长从而导致积压了部分消息。那么有可能会导致在Rebalance结束之后**瞬间需要消费很多消息**。

**Rebalance产生的原因**
导致Rebalance产生的原因，无非就两个：

- 消费者所订阅的Queue数量发生变化
- 消费者组中消费者的数量发生变化。

**Rebalance过程**

在Broker中维护着多个Map集合，这些集合中动态存放着当前Topic中Queue的信息、Consumer Group中Consumer实例的信息。

一旦发现消费者所订阅的Queue数量发生变化，或消费者组中消费者的数量发生变化，立即向Consumer Group中的每个实例发出Rebalance通知

> TopicConfigManager: key是topic 名称，value是TopicConfig. TopicConfig 中维护着该Topic中所有Queue的数据。
> ConsumerManager: key是Consumer Group Id, value 是ConsumerGroupInfo。ConsumerGroupInfo中维护着该Group中所有Consumer实例数据。
>
> ConsumeroffsetManager: key为 Topic与订阅该Topic c的Group的组合，value是一 个内层Map。内层Map的key为QueueId,内层Map的value 为该Queue的消费进度offset。

Consumer实例在接收到通知后会采用Queue分配算法自己获取到相应的Queue,即由Consumer实例自主进行Rebalance



#### Queue分配算法

一个Topic中的Queue只能由Consumer Group中的一个Consumer进行消费，而一个Consumer可以同时消费多个Queue中的消息。那么Queue与Consumer间的配对关系是如何确定的

即Queue要分配给哪个Consumer进行消费，也是有算法策略的。

常见的有四种策略，这些策略是通过在创建Consumer时的构造器传进去的。



**平均分配策略**

![在这里插入图片描述](/blogs/_archive-2024-assets/bfcace2c8782bcf4813f.webp)

该算法是要根据`avg = QueueCount / ConsumerCount`的计算结果进行分配的。如果能够整除，则按顺序将avg个Queue逐个分配Consumer.如果不能整除，则将多余出的Queue按照Consumer顺序逐个分配。



**环形平均策略**

![在这里插入图片描述](/blogs/_archive-2024-assets/af585b8adbee796e7149.webp)

环形平均算法是指，根据消费者的顺序，依次在由queue队列组成的环形图中逐个分配。

即：直接轮询一个一个来



**一致性hash策略**

![在这里插入图片描述](/blogs/_archive-2024-assets/9050eb670492ce81bfb9.webp)

该算法会将consumer的hash值作为Node节点存放到hash环上，然后将queue的hash值也放到hash环上，
通过顺时针方向，距离queue最近的那个consumer就是该queue要分配的consumer。

> 存在问题：分配不均



**同机房策略**

![在这里插入图片描述](/blogs/_archive-2024-assets/96b946f60930f784e061.webp)

该算法会根据queue的部署机房位置和consumer的位置，过滤出当前consumer相同机房的queue

然后按照**平均分配策略**或**环形平均策略**对同机房queue进行分配

如果没有同机房queue，则按照平均分配策略或环形平均策略对所有queue进行分配



#### 至少一次原则

RocketMQ有一个原则：**每条消息必须要被成功消费一次**
那么什么是成功消费呢？

 Consumer在消费完消息后会向其**消费进度记录器**提交其消费消息的offset，offset被成功记录到记录器中，那么这条消费就被成功消费了。

> 什么是消费进度记录器？
>
> 对于广播模式来说，Consumer本身就是消费进度记录器
>
> 对于集群模式来说，Broker是消费进度记录器



![在这里插入图片描述](/blogs/_archive-2024-assets/597d3ff3c919215ceab7.webp)



### 订阅关系的一致性

订阅关系的一致性指的是

> 同一个消费者组(Group ID相同)下所有Consumer实例所订阅的Topic与Tag及对消息的处理逻辑必须完全一致。否则，消息消费的逻辑就会混乱，甚至导致消息丢失



#### 正确订阅关系

多个消费者组订阅了多个Topic，并且每个消费者组里的多个消费者实例的订阅关系保持了一致

![在这里插入图片描述](/blogs/_archive-2024-assets/607d8f2e6296dfd88ff7.webp)



#### 错误订阅关系

一个消费者组订阅了多个Topic，但是该消费者组里的多个Consumer实例的订阅关系并没有保持一致。

![在这里插入图片描述](/blogs/_archive-2024-assets/bea37d9b7581d1e881d2.webp)

- **订阅了不同的Topic**
  - 同一个消费者组中的两个Consumer实例订阅了不同的Topic
- **订阅了不同的Tag**
  - 同一个消费者组中的两个Consumer订阅了相同Topic的不同Tag。
- **订阅了不同数量的Topic**
  - 同一个消费者组中的两个Consumer订阅了不同数量的Topic。



### offset管理

> 这里的offset指的是Consumer中的消费进度offset

消费进度offset是用来`记录每个Queue的不同消费组中每个consumer的消费进度`的

根据消费进度记录器的不同，可以分为两种模式：**本地模式**和**远程模式**

广播模式下，同消费组的消费者相互独立，消费进度要单独存储

集群模式下，同一条消息只会被同一个消费组消费一次，消费进度会参与到负载均衡中，故消费进度是需要共享的 

#### offset本地管理模式

当消费模式为广播消费时，offset使用本地模式存储。因为每条消息会被所有的消费者消费，每个消费者管理自己的消费进度，各个消费者之间不存在消费进度的交集。

相关数据以json形式，储存在Consumer的本地磁盘下

#### offset远程管理模式

当消费模式为集群消费时，offset使用远程模式管理。因为所有Consumer实例对消息采用的是均衡消费,所有Consumer共享Queue的消费进度。

相关数据以json形式，储存在Broker的本地磁盘下

当发生Rebalance时， 新的Consumer会从Broker中获取到相应的数据来继续消费

#### offset用途

消费者是如何从最开始持续消费消息的?消费者要消费的第一条消息的起始位置是用户自 己通过consumer. setConsumeFromWhere()方法指定的。
在Consumer启动后，其要消费的第一条消息的起始位置常用的有三种，这三种位置可以通过枚举类型常量设置。这个枚举类型为ConsumeFromWhere。

![在这里插入图片描述](/blogs/_archive-2024-assets/324ac090a889d8133db1.webp)

当消费完一-批消息后，Consumer会提交其消费进度offset给Broker, Broker在收到消费进度后会将其更新到那个双层Map及consumerOffset.json文件中，然后向该Consumer进行ACK

而ACK内容中包含三项数据：当前消费队列的最小offset (minOffset) 、最大offset (minOffset) 、及下次消费的起始offset (nextBeginOffset) 

> CONSUME_FROM_LAST_OFFSET：从queue的当前最后一条消息开始消费
> CONSUME_FROM_FIRST_ OFFSET：从queue的第一条消息开始消费
> CONSUME_FROM_TIMESTAMP：从指定的具体时间戳位置的消息开始消费
>
> 这个具体时间戳是通过另外一个语句指定的。
> consumer.setConsumeTimestamp(“20210701080000") yyyMMddHHmmss

#### 重试队列

当rocketMQ对消息的消费出现异常时,会将发生异常的消息的offset提交到Broker中的重试队列

系统在发生消息消费异常时会为当前的topic@group创建一个重试队列， 该队列以%RETRY%开头，到达重试时间后进行消费重试

#### 集群模式下offset的同步提交与异步提交

集群消费模式下，Consumer消费完消息后会向Broker提交消费进度offset

提交了offset后，需要继续向broker拿取下一批消息的位置nextBeginOffset

其提交方式分为两种

- **同步提交**：

  消费者在消费完一批消息后会向broker提交这些消息的offset,然后等待broker的成功响应。若在等待超时之前收到了成功响应，则继续读取下一批消息进行消费。若没有收到响应，则会重新提交，直到获取到响应。而在这个等待过程中，消费者是阻塞的。其严重影响了消费者的吞吐量。

- **异步提交**：

  消费者在消费完一-批消息后向broker提交offset ，但无需等待Broker的成功响应，可以继续读取并消费下一批消息。这种方式增加了消费者的吞吐量。但需要注意，broker在收到提交的offset后，还是会向消费者进行响应的。



### 消费幂等

#### 什么是消费幂等？

> 当出现消费者对某条消息重复消费的情况时，重复消费的结果与消费一次的结果是相同的，并且多次消费并未对业务系统产生任何负面影响，那么这个消费过程就是消费幂等的
>
> 幂等：若某操作执行多次与执行次对系统产生的影响是相同的，则称该操作是幂等的。

在互联网应用中，尤其在网络不稳定的情况下，消息很有可能会出现重复发送或重复消费。如果重复的消息可能会影响业务处理，那么就应该对消息做**幂等处理**

#### 消息重复的场景分析

什么情况可能会发生消息的重复消费呢？

**发送消息时重复：应答失败导致重复发送**

当-条消息已被成功发送到Broker并完成持久化，此时出现了网络闪断，从而导致Broker对Producer应答失败

如果此时Producer意识到消息发送失败并尝试再次发送消息，此时Broker中就可能会出现两条内容相同并且Message ID也相同的消息，那么后续Consumer就一定会消费两次该消息。

**消费时消息重复：应答失败导致重复投递消费**

消息已投递到Consumer并完成业务处理,当Consumer给Broker反馈应答时网络闪断， Broker没有接收到消费成功响应。为了保证消息至少被消费一次的原则， Broker将在网络恢复后再次尝试投递之前已被处理过的消息。此时消费者就会收到与之前处理过的内容相同、Message ID也相同的消息。

**rebalance时消息重复**

当Consumer Group中的Consumer数量发生变化时，或其订阅的Topic的Queue数量发生变化时，会触发Rebalance,此时Consumer可能会收到曾经被消费过的消息。

#### 通用解决方案

**两要素**
幂等解决方案的设计中涉及到两项要素：**幂等令牌**与**唯一性处理**。

只要充分利用好这两要素，就可以设计出好的幂等解决方案。

- 幂等令牌：是生产者和消费者两者中的既定协议，**通常指具备唯一业务标识**的字符串。（订单号、流水号）一般由生产者Producer传消息时一起传递
- 唯一性处理：服务端通过采用一定的**算法策略**，保证同一个业务逻辑不会被重复执行成功多次。例如：一个订单的多次支付操作，只会成功一次



**解决方案**
对于常见的系统，幂等性操作的通用性解决方案是:

1. 首先通过**缓存去重**。在缓存中如果已经存在了某幂等令牌，则说明本次操作是重复性操作；若缓存没有命中，则进入下一步
2. 在唯一性处理之前， 先在数据库中**查询幂等令牌作为索引的数据是否存在**。若存在，则说明本次操作为重复性操作；若不存在，则进入下一一步
3. 在**同一事务**中完成项操作: 唯一性处理后，将幂等令牌写入到缓存，并将幂等令牌作为唯一索引的数据写入到DB中

因为缓存具有有效期，所以当然需要加一层db的判断

**以支付场景举例**：

1. 当支付请求到达后，首先在Redis缓存中却获取key为支付流水号的缓存value。若value不空， 则说明本次支付是重复操作，业务系统直接返回调用侧重复支付标识;若value为空，则进入下一步操作
2. 到DBMS中根据支付流水号查询是否存在相应实例。若存在，则说明本次支付是重复操作，业务系统直接返回调用侧重复支付标识:若不存在，则说明本次操作是首次操作，进入下一步完成唯一性处理
3. 在分布式事务中完成三项操作: 

- 完成支付任务（唯一性处理）
- 将当前支付流水号作为key,任意字符串作为value,通过set(key, value, expireTime)将数据写入到Redis缓存

- 将当前支付流水号作为主键，与其它相关数据共同写入到DBMS



#### 消费幂等的实现

消费幂等的解决方案很简单：**为消息指定不会重复的唯一标识**

因为Message ID有可能出现重复的情况，所以真正安全的幂等处理，不建议以Message ID作为处理依据。

最好的方式是**以业务唯一标识作为幂等处理的关键依据**，而业务的唯一标识可以通过消息Key设置。

![在这里插入图片描述](/blogs/_archive-2024-assets/9cc364782593c0ce1cca.webp)

处理消息的时候就根据业务id去进行缓存和db判断即可

### 消息堆积与消费延迟

#### 概念

消息处理流程中，如果Consumer的消费速度跟不上Producer的发送速度，MQ中未处理的消息会越来越多(进的多出的少)，这部分消息就被称为**堆积消息**

**消息出现堆积，进而会造成消息的消费延迟**

以下场景需要重点关注消息堆积和消费延迟问题：

- 业务系统上下游能力不匹配造成的持续堆积，且无法自行恢复。
- 业务系统对消息的消费实时性要求较高，即使是短暂的堆积造成的消息延迟也无法接受。

一般只需要解决了消息堆积，就不会有消息延迟了

#### 消息拉取

Consumer通过长轮询Pull模式批量拉取的方式从服务端获取消息，将拉取到的消息缓存到本地缓冲队列中。

对于拉取式消费，在内网环境下会有很高的吞吐量,所以这一阶段一般不会成为消息堆积的瓶颈。

**消息消费**

Consumer将本地缓存的消息提交到消费线程中，使用业务消费逻辑对消息进行处理，处理完毕后获取到一个结果。这是真正的消息消费过程。此时Consumer的消费能力就完全依赖于消息的**消费耗时**和**消费并发度**了

如果由于业务处理逻辑复杂等原因，导致处理单条消息的耗时较长，则整体的消息吞吐量肯定不会高，此时就会导致Consumer本地缓冲队列达到上限，停止从服务端拉取消息



**消息堆积的主要瓶颈在于客户端的消费能力，而消费能力由消费耗时和消费并发度决定**

优先解决消费耗时的问题（降低处理时间），再考虑消费并发度（增加线程等）



#### 消费耗时

影响消息处理时长的主要因素是**代码逻辑**

而代码逻辑中可能会影响处理时长的主要有两种类型的代码：**CPU内部计算型代码**和**外部I/O操作型代码**

通常情况下代码中如果没有复杂的递归和循环的话，内部计算耗时相对外部I/0操作来说几乎可以忽略

所以**外部IO型代码是影响消息处理时长的主要症结所在**

#### 消费并发度

一般情况下，消费者端的消费并发度由单节点线程数和节点数量共同决定，其值为单节点线程数节点数量

不过，通常需要优先调整单节点的线程数，若单机硬件资源达到了上限，则需要通过横向扩展来提高消费并发度



### 消息的清理

消息被消费完后会被清理嘛？不会的

消息是被顺序存储在commitlog文件的，且消息大小不定长，所以消息的清理是不可能以消息为单位进行清理的，而是以commitlog文件 为单位进行清理的。否则会极具下降清理效率，并实现逻辑复杂

commitlog文件存在一个过期时间， 默认为72小时，即三天。

除了用户手动清理外，在以下情况下也会被自动清理，无论文件中的消息是否被消费过:

- 文件过期，且到达清理时间点(默认为凌晨4点)后，自动清理过期文件
- 文件过期，且磁盘空间占用率已达过期清理警戒线(默认75%)后，无论是否达到清理时间点，都会自动清理过期文件
- 磁盘占用率达到清理警戒线(默认85%)后，开始按照设定好的规则清理文件，无论是否过期。默认会从最老的文件开始清理

- 磁盘占用率达到系统危险警戒线(默认90%)后，Broker将拒绝消息写入
