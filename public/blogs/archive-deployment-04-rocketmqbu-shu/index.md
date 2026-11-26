# rocketMQ部署

参考：[链接](https://blog.csdn.net/oschina_41731918/article/details/123115102),[帐号密码](https://www.cnblogs.com/binz/p/15252277.html)，[官方文档](https://github.com/apache/rocketmq/blob/master/docs/cn/acl/user_guide.md)

rocketmq的坑很多，一定要记得按照文档的步骤一步步的部署，血与泪的经验！！！

### 不配置密码

如果要给rokcetmq上密码，请直接跳过这里，看下面目录

创建挂载目录

```bash
#创建挂载目录
mkdir -p /data/rocketmq/namesrv ;
mkdir -p /data/rocketmq/broker/conf ;
```

创建yml文件

```bash
vim /data/rocketmq/docker-compose.yml
```

填入配置

```bash
version: '3.5'
services:
  rocketmq-namesrv:
    image: foxiswho/rocketmq:4.8.0
    container_name: rocketmq-namesrv
    restart: always
    ports:
      - 9876:9876
    volumes:
      - ./namesrv/logs:/home/rocketmq/logs
      - ./namesrv/store:/home/rocketmq/store
    environment:
      JAVA_OPT_EXT: "-Duser.home=/home/rocketmq -Xms128M -Xmx128M -Xmn128m"
    command: ["sh","mqnamesrv"]
    networks:
      rocketmq_net:
        aliases:
          - rocketmq-namesrv


  rocketmq-broker:
    image: foxiswho/rocketmq:4.8.0
    container_name: rocketmq-broker
    restart: always
    ports:
      - 10909:10909
      - 10911:10911
    volumes:
      - ./broker/logs:/home/rocketmq/logs
      - ./broker/store:/home/rocketmq/store
      - ./broker/conf/broker.conf:/etc/rocketmq/broker.conf
    environment:
      JAVA_OPT_EXT: "-Duser.home=/home/rocketmq -Xms128m -Xmx128m -Xmn128m"
    command: ["sh","mqbroker","-c","/etc/rocketmq/broker.conf"]
    depends_on:
      - rocketmq-namesrv
    networks:
      rocketmq_net:
        aliases:
          - rocketmq-broker


  rocketmq-console:
    image: iamverygood/rocketmq-console:4.7.1
    container_name: rocketmq-console
    restart: always
    ports:
      - 8180:8080
    environment:
      JAVA_OPTS: "-Drocketmq.namesrv.addr=rocketmq-namesrv:9876 -Dcom.rocketmq.sendMessageWithVIPChannel=false"
    depends_on:
      - rocketmq-namesrv
    networks:
      rocketmq_net:
        aliases:
          - rocketmq-console

networks:
  rocketmq_net:
    name: rocketmq_net
    driver: bridge
```

创建挂载的配置文件

```
vim /data/rocketmq/broker/conf/broker.conf
#所属集群名字
brokerClusterName=DefaultCluster

#broker名字，注意此处不同的配置文件填写的不一样，如果在broker-a.properties使用:broker-a,
#在broker-b.properties使用:broker-b
brokerName=broker-a

#0 表示Master，>0 表示Slave
brokerId=0

#nameServer地址，分号分割
#namesrvAddr=rocketmq-nameserver1:9876;rocketmq-nameserver2:9876
namesrvAddr=rocketmq-namesrv:9876

#启动IP,如果 docker 报 com.alibaba.rocketmq.remoting.exception.RemotingConnectException: connect to <192.168.0.120:10909> failed
# 解决方式1 加上一句producer.setVipChannelEnabled(false);，解决方式2 brokerIP1 设置宿主机IP，不要使用docker 内部IP
brokerIP1=10.0.12.13

#在发送消息时，自动创建服务器不存在的topic，默认创建的队列数
defaultTopicQueueNums=4

#是否允许 Broker 自动创建Topic，建议线下开启，线上关闭 ！！！这里仔细看是false，false，false
autoCreateTopicEnable=true

#是否允许 Broker 自动创建订阅组，建议线下开启，线上关闭
autoCreateSubscriptionGroup=true

#Broker 对外服务的监听端口
listenPort=10911

#此参数控制是否开启密码,不开启可设置false
aclEnable=false

#删除文件时间点，默认凌晨4点
deleteWhen=04

#文件保留时间，默认48小时
fileReservedTime=120

#commitLog每个文件的大小默认1G
mapedFileSizeCommitLog=1073741824

#ConsumeQueue每个文件默认存30W条，根据业务情况调整
mapedFileSizeConsumeQueue=300000

#destroyMapedFileIntervalForcibly=120000
#redeleteHangedFileInterval=120000
#检测物理文件磁盘空间
diskMaxUsedSpaceRatio=88
#存储路径
#storePathRootDir=/home/ztztdata/rocketmq-all-4.1.0-incubating/store
#commitLog 存储路径
#storePathCommitLog=/home/ztztdata/rocketmq-all-4.1.0-incubating/store/commitlog
#消费队列存储
#storePathConsumeQueue=/home/ztztdata/rocketmq-all-4.1.0-incubating/store/consumequeue
#消息索引存储路径
#storePathIndex=/home/ztztdata/rocketmq-all-4.1.0-incubating/store/index
#checkpoint 文件存储路径
#storeCheckpoint=/home/ztztdata/rocketmq-all-4.1.0-incubating/store/checkpoint
#abort 文件存储路径
#abortFile=/home/ztztdata/rocketmq-all-4.1.0-incubating/store/abort
#限制的消息大小
maxMessageSize=65536

#flushCommitLogLeastPages=4
#flushConsumeQueueLeastPages=2
#flushCommitLogThoroughInterval=10000
#flushConsumeQueueThoroughInterval=60000

#Broker 的角色
#- ASYNC_MASTER 异步复制Master
#- SYNC_MASTER 同步双写Master
#- SLAVE
brokerRole=ASYNC_MASTER

#刷盘方式
#- ASYNC_FLUSH 异步刷盘
#- SYNC_FLUSH 同步刷盘
flushDiskType=ASYNC_FLUSH

#发消息线程池数量
#sendMessageThreadPoolNums=128
#拉消息线程池数量
#pullMessageThreadPoolNums=128
```

`brokerIP1=10.0.12.13`填上自己服务器公网ip，客户端发送消息要联这个

授权目录

```bash
#目录权限（不加会有坑，rocketmq没法操作挂载目录）：
chmod -R 777 /data/rocketmq/namesrv/;
chmod -R 777 /data/rocketmq/broker/;
```

### 设置密码

创建挂载目录,一次性执行

```bash
#创建挂载目录
mkdir -p /data/rocketmq/namesrv;
mkdir -p /data/rocketmq/broker/conf;
mkdir -p /data/rocketmq/broker/lib;
mkdir -p /data/rocketmq/console/data;
```

创建挂载的配置文件

```
vi /data/rocketmq/broker/conf/broker.conf
#所属集群名字
brokerClusterName=DefaultCluster

#broker名字，注意此处不同的配置文件填写的不一样，如果在broker-a.properties使用:broker-a,
#在broker-b.properties使用:broker-b
brokerName=broker-a

#0 表示Master，>0 表示Slave
brokerId=0

#nameServer地址，分号分割
#namesrvAddr=rocketmq-nameserver1:9876;rocketmq-nameserver2:9876
namesrvAddr=rocketmq-namesrv:9876

#启动IP,如果 docker 报 com.alibaba.rocketmq.remoting.exception.RemotingConnectException: connect to <192.168.0.120:10909> failed
# 解决方式1 加上一句producer.setVipChannelEnabled(false);，解决方式2 brokerIP1 设置宿主机IP，不要使用docker 内部IP
brokerIP1=10.0.12.13

#在发送消息时，自动创建服务器不存在的topic，默认创建的队列数
defaultTopicQueueNums=4

#是否允许 Broker 自动创建Topic，建议线下开启，线上关闭 ！！！这里仔细看是false，false，false
autoCreateTopicEnable=true

#是否允许 Broker 自动创建订阅组，建议线下开启，线上关闭
autoCreateSubscriptionGroup=true

#Broker 对外服务的监听端口
listenPort=10911

#此参数控制是否开启密码,不开启可设置false
aclEnable=true

#删除文件时间点，默认凌晨4点
deleteWhen=04

#文件保留时间，默认48小时
fileReservedTime=120

#commitLog每个文件的大小默认1G
mapedFileSizeCommitLog=1073741824

#ConsumeQueue每个文件默认存30W条，根据业务情况调整
mapedFileSizeConsumeQueue=300000

#destroyMapedFileIntervalForcibly=120000
#redeleteHangedFileInterval=120000
#检测物理文件磁盘空间
diskMaxUsedSpaceRatio=88
#存储路径
#storePathRootDir=/home/ztztdata/rocketmq-all-4.1.0-incubating/store
#commitLog 存储路径
#storePathCommitLog=/home/ztztdata/rocketmq-all-4.1.0-incubating/store/commitlog
#消费队列存储
#storePathConsumeQueue=/home/ztztdata/rocketmq-all-4.1.0-incubating/store/consumequeue
#消息索引存储路径
#storePathIndex=/home/ztztdata/rocketmq-all-4.1.0-incubating/store/index
#checkpoint 文件存储路径
#storeCheckpoint=/home/ztztdata/rocketmq-all-4.1.0-incubating/store/checkpoint
#abort 文件存储路径
#abortFile=/home/ztztdata/rocketmq-all-4.1.0-incubating/store/abort
#限制的消息大小
maxMessageSize=65536

#flushCommitLogLeastPages=4
#flushConsumeQueueLeastPages=2
#flushCommitLogThoroughInterval=10000
#flushConsumeQueueThoroughInterval=60000

#Broker 的角色
#- ASYNC_MASTER 异步复制Master
#- SYNC_MASTER 同步双写Master
#- SLAVE
brokerRole=ASYNC_MASTER

#刷盘方式
#- ASYNC_FLUSH 异步刷盘
#- SYNC_FLUSH 同步刷盘
flushDiskType=ASYNC_FLUSH

#发消息线程池数量
#sendMessageThreadPoolNums=128
#拉消息线程池数量
#pullMessageThreadPoolNums=128
```

`brokerIP1=10.0.12.13`填上自己服务器公网ip，客户端发送消息要联这个

#### 如果有设置密码的需求，先给broker.conf开启acl密码配置 true

![image-20240924175017562](/blogs/_archive-2024-assets/9c13a63bd0d4ae3c1803.webp)

#### 创建acl文件，用于开启用户名密码

```
vi /data/rocketmq/broker/conf/plain_acl.yml
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# 全局白名单，如果配置了则不需要走acl校验，慎重配置
globalWhiteRemoteAddresses:
#  - 47.100.93.*
#  - 156.254.120.*
 
accounts:
  - accessKey: RocketMQ
    secretKey: 12345678
    whiteRemoteAddress:
    admin: false
    defaultTopicPerm: DENY
    defaultGroupPerm: SUB
    topicPerms:
      - topicA=DENY
      - topicB=PUB|SUB
      - topicC=SUB
    groupPerms:
      # the group should convert to retry topic
      - groupA=DENY
      - groupB=PUB|SUB
      - groupC=SUB

  - accessKey: mallchat
    secretKey: 12345678
    whiteRemoteAddress: 
    # if it is admin, it could access all resources 上面的用于教学，我们用超级管理员账号
    admin: true
```

密码不能小于6位数，血的教训

名称也不能小于6位，血的教训！！！

权限的描述可参考[链接](https://github.com/apache/rocketmq/blob/master/docs/cn/acl/user_guide.md)

#### 给console加上账号密码

```
vi  /data/rocketmq/console/data/users.properties
# This file supports hot change, any change will be auto-reloaded without Console restarting.
# Format: a user per line, username=password[,N] #N is optional, 0 (Normal User); 1 (Admin)

# Define Admin
# =============用户名和密码规则「用户名=密码,权限」，这里的权限为1表示管理员>，为0表示普通用户=============
# 例如：admin=admin123,1
mallchat=123456,1


# Define Users
# =============屏蔽下边两个账户=============
#user1=user1
#user2=user2
```

#### 创建yml文件

```bash
vi /data/rocketmq/docker-compose.yml
```

填入配置

```bash
version: '3.5'
services:
  rocketmq-namesrv:
    image: foxiswho/rocketmq:4.8.0
    container_name: rocketmq-namesrv
    restart: always
    ports:
      - 9876:9876
    volumes:
      - ./namesrv/logs:/home/rocketmq/logs
      - ./namesrv/store:/home/rocketmq/store
    environment:
      JAVA_OPT_EXT: "-Duser.home=/home/rocketmq -Xms128M -Xmx128M -Xmn128m"
    command: ["sh","mqnamesrv"]
    networks:
      rocketmq_net:
        aliases:
          - rocketmq-namesrv


  rocketmq-broker:
    image: foxiswho/rocketmq:4.8.0
    container_name: rocketmq-broker
    restart: always
    ports:
      - 10909:10909
      - 10911:10911
    volumes:
      - ./broker/logs:/home/rocketmq/logs
      - ./broker/store:/home/rocketmq/store
      - ./broker/conf/plain_acl.yml:/home/rocketmq/rocketmq-4.8.0/conf/plain_acl.yml
      - ./broker/conf/broker.conf:/etc/rocketmq/broker.conf
    environment:
      JAVA_OPT_EXT: "-Duser.home=/home/rocketmq -Xms128m -Xmx128m -Xmn128m"
    command: ["sh","mqbroker","-c","/etc/rocketmq/broker.conf"]
    depends_on:
      - rocketmq-namesrv
    networks:
      rocketmq_net:
        aliases:
          - rocketmq-broker


  rocketmq-console:
    image: iamverygood/rocketmq-console:4.7.1
    container_name: rocketmq-console
    restart: always
    ports:
      - 8180:8080
    volumes:
      - ./console/data:/tmp/rocketmq-console/data
    environment:
      JAVA_OPTS: "-Drocketmq.namesrv.addr=rocketmq-namesrv:9876 -Dcom.rocketmq.sendMessageWithVIPChannel=false -Drocketmq.config.loginRequired=true -Drocketmq.config.aclEnabled=true -Drocketmq.config.accessKey=mallchat -Drocketmq.config.secretKey=12345678"
    depends_on:
      - rocketmq-namesrv
    networks:
      rocketmq_net:
        aliases:
          - rocketmq-console

networks:
  rocketmq_net:
    name: rocketmq_net
    driver: bridge
```

如果你的acl密码改了，记得把yml的console帐号密码也一同更改

```
-Drocketmq.config.accessKey=mallchat -Drocketmq.config.secretKey=12345678
```

授予目录权限

```bash
#目录权限：
chmod -R 777 /data/rocketmq/namesrv/;
chmod -R 777 /data/rocketmq/broker/;
chmod -R 777 /data/rocketmq/console/;
```

**记得防火墙开端口号 9876,10911,8180 !!!**

### 启动容器

到对应目录下启动容器

```bash
cd /data/rocketmq
docker-compose up -d
```

docker ps，可以看见一直在重启中

![image-20240924174958574](/blogs/_archive-2024-assets/73eced9d4e201ce2b1da.webp)

注意，第一次会启动不成功，因为broker需要创建一堆文件，没有权限。再执行一遍权限命令

```sql
#目录权限：
chmod -R 777 /data/rocketmq/namesrv/;
chmod -R 777 /data/rocketmq/broker/;
chmod -R 777 /data/rocketmq/console/;
#然后强制重新构建
docker-compose up --force-recreate -d
```

安装过程中踩过一个坑，感兴趣可以看看

此处为语雀内容卡片，点击链接查看：https://www.yuque.com/snab/mallchat/tt9mcnc6t0g125ow

#### docker-compose版本升级

可能有的小伙伴启动会报错。是因为我们的docker-compose版本太低了，识别不了networks命令需要更新一下。速度比较慢，等等就好

```bash
#更新版本
curl -L https://github.com/docker/compose/releases/download/1.28.6/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
#将可执行权限应用于二进制文件
sudo chmod +x /usr/local/bin/docker-compose
```

![img](/blogs/_archive-2024-assets/9158db6e44e59a4362f0.webp)

#### 登录控制台

启动后可以登录控制台，记得开防火墙！！！

```
http://ip:8180/
```

输入帐号密码 mallchat 123456

![image-20240924174934472](/blogs/_archive-2024-assets/b624032b4f7a45a27207.webp)

### win下启动rocketmq

https://blog.csdn.net/liuerchong/article/details/120548579

进入至‘MQ文件夹\bin’下，然后执行‘ mqnamesrv.cmd’，启动NAMESERVER

cmd 进入至‘MQ文件夹\bin’下，然后执行‘ start mqbroker.cmd -n localhost:9876 autoCreateTopicEnable=true & ’

```plain
mqnamesrv.cmd
start mqbroker.cmd -n localhost:9876 autoCreateTopicEnable=true & 
```

http://localhost:18080/#/cluster
