# 3.Mycat2 安装与启动

## 3.1 制作安装包

Mycat2不提供安装包,只提供核心JAR包,JAR包可以独立运行,安装包是使用Java Service Wrapper做壳的,如果需要安装包，需要自己制作。

JAR可以作为Java库引入自己业务项目中使用,Mycat2中的各个组件的设计都是可以独立使用的

步骤如下：

1. 下载对应的tar或zip安装包,以及对应的jar包

   zip包地址：[http://dl.mycat.io/2.0/install-template/mycat2-install-template-1.20.zip]()

   jar包地址：[http://dl.mycat.io/2.0/1.21-release/mycat2-1.21-release-jar-with-dependencies-2022-3-14.jar]()

2. 解压下载下来的zip包， 然后将下载好的jar包放入到 mycat/lib 目录下，如下图：

   *（原站配图缺失）*

3. 上传到Linux，这里我们将MyCat上传到192.168.58.200，这台服务器。Mycat 作为数据库中间件要和数据库部署在不同机器上。

```shell
# 授予 bin 目录下所有命令 可执行权限
[root@localhost mycat]# chmod +x bin/*
```

4. 安装 JDK1.8

```
1.查看云端yum库中目前支持安装的jdk软件包
yum search java|grep jdk

2.选择版本安装jdk
yum install -y java-1.8.0-openjdk*

3.安装完成后，验证是否安装成功
java -version


4.查找jdk安装位置
find / -name 'java'

默认安装路径一般为：
/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.151-5.b12.el7_4.x86_64/jre/bin/java
```

## 3.2 启动MyCat

**1）MyCat需要连接的MySQL数据库中，创建用户，并赋予权限 (也可以直接使用root用户)**

```sql
-- 修改默认密码校验方式
ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '123456';

-- 用户名mycat，密码123456
CREATE USER 'mycat'@'%' IDENTIFIED BY '123456';

-- 官方文档强调要给root账号添加XA RECOVER权限
GRANT XA_RECOVER_ADMIN  ON *.* TO 'root'@'%';

-- 视情况给mycat赋予权限
GRANT ALL PRIVILEGES ON *.* TO 'mycat'@'%' ;
flush privileges;
```

**2）配置mycat要连接的数据源**

mycat连接真正数据库的信息目录是在 `/mycat/conf/datasources`

配置原型库的数据源信息 `prototypeDs.datasource.json`,  主要是 **url、user、password**这三个参数

```json
{
        "dbType":"mysql",
        "idleTimeout":60000,
        "initSqls":[],
        "initSqlsGetConnection":true,
        "instanceType":"READ_WRITE",
        "maxCon":1000,
        "maxConnectTimeout":3000,
        "maxRetryCount":5,
        "minCon":1,
        "name":"prototypmysql
        "password":"123456",
        "type":"JDBC",
        "url":"jdbc:mysql://192.168.58.100:3310/mysql?useUnicode=true&serverTimezone=Asia/Shanghai&characterEncoding=UTF-8",
        "user":"mycat",
        "weight":0
}
```

**3）mycat相关命令**

```shell
进入bin目录

./mycat status 状态
./mycat start 启动
./mycat stop 停止
./mycat restart 重启服务
./mycat pause 暂停
```

**4）Mycat用户配置**

文件目录及配置文件

```shell
cd /root/software/mycat/conf/users

[root@localhost users]# ll
总用量 4
-rw-r--r--. 1 root root 107 12月  3 04:06 root.user.json

[root@localhost users]# vim root.user.json 
```

只需要配置用户名，密码

```json
{
        "dialect":"mysql",
        "ip":null,
        "password":"123456",  
        "transactionType":"xa",
        "username":"root"
}
```

**5）启动mycat，使用图形工具链接，mycat默认端口8066**

*（原站配图缺失）*

## 3.3 连接Mycat

**1）连接成功后，创建执行下面的建库建表语句**

```sql
-- 创建数据库
CREATE DATABASE user_db CHARACTER SET utf8;

-- 创建表
CREATE TABLE users (
  id INT(11) PRIMARY KEY AUTO_INCREMENT,
  NAME VARCHAR(20) DEFAULT NULL,
  age INT(11) DEFAULT NULL
); 

-- 插入数据
INSERT INTO users VALUES(NULL,'user1',20);
INSERT INTO users VALUES(NULL,'user2',21);
INSERT INTO users VALUES(NULL,'user3',22);
```

**2）在Mycat中执行成功，Mycat所代理的数据库中也会增加一个user_db数据库和users表**

*（原站配图缺失）*

*（原站配图缺失）*

> mycat.xa_log 是事务日志表会在Mycat2启动时候在存储节点上建立。
>
> mycat.spm_plan mycat执行计划相关的表

# 4.Mycat2 核心概念

* 分库分表
  * 按照一定的规则把数据库中的表拆分为多个带有数据库实例，物理库，物理表访问路径的分表。
* 逻辑库
  * 对数据进行分片之后，从原来的与一个库，被切分为了多个分片数据库，所有的分片数据库构成了整个完整的数据库存储。Mycat在操作时，使用逻辑库代表整个完整的数据库集群，方便对于整个集群进行操作。
* 物理库
  * MySQL中真实存在的数据库
* 物理表
  * MySQL中真实存在的表
* 分片键
  * 用于分片的数据库字段，是将数据库进行水平拆分的关键字段
  * 例：将订单表的订单主键设置为分片键，根据订单主键进行取模分片。
* 物理分表
  * 指的是已经进行数据拆分的，在数据库上面的物理表，是分片表的一个分区，多个物理分表中的数据汇总起来就是逻辑表的全部数据。
* 物理分库
  * 一般是指包含多个分表的库，数据切分之后每一个大表被分不到不同的数据库上面，每个表分片所在的数据库就是物理分库。
* 单表
  * 没有分片，没有数据冗余的表
* 全局表
  * 变动不频繁
  * 数据总量变化不大
  * 经常被用来进行关联查询
  * 比如说： 地址表 、字典表 这一类都是属于全局表，在每个数据库中都有这样一张或几张全局表，每个数据库中的全局表的数据是要保持一致的。
* ER表
  * Mycat提出了基于E-R关系的数据分片策略，子表的记录与所有关联的父表的记录存放在同一个数据分片上，子表依赖于父表，通过表分组保证 数据的join不会跨库。
* 集群
  * 多个数据节点组成的逻辑节点。
* 数据源
  * 连接后端数据库的组件，它是数据库代理中连接后端数据库的客户端。
* 原型库
  * 原型库是Mycat2后面的数据库，MySQL

# 5.Mycat2 核心配置文件

Mycat2作为一个数据库中间件，它所有的功能其实都是通过一些列配置文件定制一系列业务规则，通过与MySQL协作，提供具体的业务功能。所有Mycat2的所有功能都体现在他的配置文件中。

服务相关配置文件所在的目录是： `mycat/conf`

*（原站配图缺失）*

## 5.1 用户配置

1）配置用户相关信息的目录在： `mycat/conf/users`

2）命名方式：`{用户名}.user.json`

3）配置内容如下：

```json
{
        "dialect":"mysql",
        "ip":null,
        "password":"123456",
        "transactionType":"xa",
        "username":"root"
}

字段含义
ip:客户端访问ip，建议为空,填写后会对客户端的ip进行限制
username:用户名
password:密码
isolation:设置初始化的事务隔离级别
	READ_UNCOMMITTED :1
	READ_COMMITTED :2
	REPEATED_READ:3,默认
	SERIALIZABLE:4

tractionType:事务类型,可选值, 可以通过语句实现切换
	set transaction policy ='xa'
	set transaction.policy ='proxy'

proxy 表示本地事务,在涉及大于1个数据库的事务, commit阶段失败会导致不一致,但是兼容性最好xa事务,需要确认存储节点集群类型是否支持XA.
```

## 5.2 数据源配置

配置Mycat连接的数据源信息
1）所在目录 `mycat/conf/datasources`
2）命名方式 `{数据源名字} . datasource.json`
3）配置内容如下:

```JSON
{
        "dbType":"mysql",
        "idleTimeout":60000,
        "initSqls":[],
        "initSqlsGetConnection":true,
        "instanceType":"READ_WRITE",
        "maxCon":1000,
        "maxConnectTimeout":3000,
        "maxRetryCount":5,
        "minCon":1,
        "name":"prototypeDs",
        "password":"123456",
        "type":"JDBC",
        "url":"jdbc:mysql://192.168.58.100:3310/mysql?useUnicode=true&serverTimezone=Asia/Shanghai&characterEncoding=UTF-8",
        "user":"mycat",
        "weight":0
}

字段含义
	dbType:数据库类型，mysql
	name:用户名
	password:密码
	type:数据源类型，默认JDBC
	url:访问数据库地址
	idleTimeout:空闲连接超时时间 
	initSqls:初始化sql
	initSqlsGetConnection:对于jdbc每次获取连接是否都执行initSqls
	nstanceType:配置实例只读还是读写, 可选值:READ_WRITE,READ,WRITE
	weight:负载均衡权重

连接相关配置
	"maxCon": 100,
	"maxConnectTimeout" : 3000,
	"RetryCount" : 5,
	"minCon": 1,
```

## 5.3 集群配置

1）配置集群信息，所在目录 `mycat/conf/clusters`
2）命名方式：`{集群名字} . cluster.json`
3）配置内容如下：

```json
{
        "clusterType":"MASTER_SLAVE",   //主从集群
        "heartbeat":{                      //心跳检查
                "heartbeatTimeout":1000,
                "maxRetry":3,
                "minSwitchTimeInterval":300,
                "slaveThreshold":0
        },
        "masters":[
                "prototypeDs"    //主节点
        ],
        "maxCon":200,
        "name":"prototype",
        "readBalanceType":"BALANCE_ALL",   //负载均衡策略
        "switchType":"SWITCH"     //表示进行主从切换
}

字段含义
clusterType:集群类型,可选值:
	SINGLE_NODE:单一节点
	MASTER_SLAVE:普通主从
	JSTER:garela- cluster/PXC 集群
	MHA: MHA集群
	MGR: MGR集群

readBalanceType:查询负载均衡策略,可选值:
	BALANCE_ALL(默认值),获取集群中所有数据源
	BALANCE_ALL_READ,获取集群中允许读的数据源
	BALANCE_READ_WRITE,获取集群中允许读写的数据源,但允许读的数据源优先
	BALANCE_NONE,获取集群中允许写数据源,即主节点中选择

switchType:切换类型
```

## 5.4 逻辑库表

1）配置逻辑库表，实现分库分表，所在目录 `mycat/conf/schemas`
2）命名方式  `{库名} . schema.json`
3）配置内容如下：

```json
vim mysql.schema.json

{
	"customTables":{},
	"globalTables":{},       //全局表配置
	"normalProcedures":{},
	"normalTables":{   // MySQL中真实表信息
		"users":{
      //建表语句
			"createTableSQL":"CREATE TABLE user_db.users (\n\tid INT(11) PRIMARY KEY AUTO_INCREMENT,\n\tNAME VARCHAR(20) DEFAULT NULL,\n\tage INT(11) DEFAULT NULL\n)",
			"locality":{
				"schemaName":"user_db",  //物理库
				"tableName":"users",     //物理表
				"targetName":"prototype" //指向集群或者数据源
			}
		}
	},
	"schemaName":"user_db",   
	"shardingTables":{}, //分片表配置
	"views":{}
}

//详细分库分表配置，后面的内容会有讲解
```

**注意：配置的schema的逻辑库逻辑表必须在原型库(prototype)中有对应的物理库物理表,否则不能启动**
