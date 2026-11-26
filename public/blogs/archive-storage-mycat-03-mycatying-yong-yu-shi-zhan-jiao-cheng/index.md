# 5.Mycat2实现读写分离

**读写分离原理**：读写分离就是让主库处理事务性操作，从库处理select查询。数据库复制被用来把事务性查询导致的数据变更同步到从库，同时主库也可以select查询。

> 实现读写分离是基于MySQL的主从复制架构的，通过一主多从的配置方式，可以将查询请求均匀的分散到多个数据副本，能够进一步的提升系统的处理能力。 所以这里我们先要搭建一下MySQL的主从复制集群。

*（原站配图缺失）*

## 5.1 Docker搭建MySQL主从复制集群

### 5.1.1 MySQL主从同步原理

MySQL通过binlog完成主备同步，实现最终一致性。

- Mysql 中有一种日志叫做 binlog（二进制日志）。这个日志会记录下所有修改了数据库的SQL 语句（insert,update,delete,create/alter/drop table, grant 等等）
- 主从复制的原理其实就是把主服务器上的 binlog 复制到从服务器上执行一遍，这样从服务器上的数据就和主服务器上的数据相同了。

与主从复制相关的线程有三个

- 主库上的dump_thread
- 备库上的io_thread、sql_thread

与主从复制相关的日志有binlog、relaylog

- binlog: 记录数据库的写入操作,以二进制的形式保存在日志文件;
- relaylog: Slave 接收 Master 的同步日志,会先放到中继日志 relay log 里, slave 的读操作也会基于 relay log。

*（原站配图缺失）*

1. master将数据改变记录到 `二进制日志（binary log）`中。
2. 当slave上执行 `start slave` 命令之后，slave会创建一个 `IO 线程`用来连接master，请求master中的binlog。
3. 当slave连接master时，master会创建一个 **`binlog dump 线程`，用于发送 binlog 的内容。在读取 binlog 的内容的操作中，会对主节点上的 binlog 加锁，当读取完成并发送给从服务器后解锁。
4. IO 线程接收主节点 binlog dump 进程发来的更新之后，保存到 `中继日志（relay log）` 中。
5. slave的 `SQL线程`，读取relay log日志，并解析成具体操作，从而实现主从操作一致，最终数据一致。

**主从部署必要条件**

- 主库开启binlog日志（设置log-bin参数）
- 主从server-id不同
- 从库服务器能连通主库

**服务器创建方式**

- 使用 `docker`方式创建MySQL服务器，主从服务器IP一致，使用端口号区分。

*（原站配图缺失）*

### 5.1.2 主服务器搭建

1. 在docker中创建并启动MySQL主服务器：`端口3306`

```shell
docker run -d \
-p 3306:3306 \
-v /msb/mysql/master/conf:/etc/mysql/conf.d \
-v /msb/mysql/master/data:/var/lib/mysql \
-e MYSQL_ROOT_PASSWORD=123456 \
--name msb-mysql-master \
mysql:8.0.29
```

2. 创建MySQL主服务器配置文件

默认情况下MySQL的binlog日志是自动开启的，可以通过如下配置定义一些可选配置

```shell
vim /msb/mysql/master/conf/my.cnf

[mysqld]
# 服务器唯一id，默认值1
server-id=1
# 设置日志格式，默认值ROW
binlog_format=STATEMENT
# 二进制日志名，默认binlog
# log-bin=binlog
# 设置需要复制的数据库，默认复制全部数据库
#binlog-do-db=mytestdb
# 设置不需要复制的数据库
#binlog-ignore-db=mysql
#binlog-ignore-db=infomation_schema
```

重启MySQL容器

```shell
docker ps

docker restart msb-mysql-master
```

binlog格式说明：

- binlog_format=STATEMENT：日志记录的是主机数据库的 `写指令`，性能高，但是now()之类的函数以及获取系统参数的操作会出现主从数据不同步的问题。
- binlog_format=ROW（默认）：日志记录的是主机数据库的 `写后的数据`，批量操作时性能较差，解决now()或者  user()或者  @@hostname 等操作在主从机器上不一致的问题。
- binlog_format=MIXED：是以上两种level的混合使用，有函数用ROW，没函数用STATEMENT，但是无法识别系统变量

3. 登录MySQL主服务器

   ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '123456';

```shell
#启动容器，在容器内访问MySQL env LANG=C.UTF-8 避免容器中显示中文乱码
[root@localhost ~]# docker exec -it msb-mysql-master env LANG=C.UTF-8 /bin/bash

bash-4.4# mysql -uroot -p
Enter password: 输入密码

#修改默认密码校验方式
ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '123456';
```

4. 在主数据库上, 创建一个允许从数据库来访问的用户账号

   用户:  `msb_slave`

   密码：`123456`

   主从复制使用 `REPLICATION SLAVE` 赋予权限

```sql
-- 创建slave用户
CREATE USER 'msb_slave'@'%';

-- 设置密码
ALTER USER 'msb_slave'@'%' IDENTIFIED WITH mysql_native_password BY '123456';

-- 授予复制权限
GRANT REPLICATION SLAVE ON *.* TO 'msb_slave'@'%';

-- 刷新权限
FLUSH PRIVILEGES;
```

5. 主机中查询master状态

执行完此步骤后,不要再操作主服务器，防止主服务器状态值变化,可以选择锁住主服务器

```sql
-- 执行以下命令锁定数据库以防止写入数据。
FLUSH TABLES WITH READ LOCK;
```

到主服务器上查看主机状态, 记录File和Position对应的值

```sql
-- 在主机查看mater状态
SHOW MASTER STATUS;

+---------------+----------+--------------+------------------+-------------------+
| File          | Position | Binlog_Do_DB | Binlog_Ignore_DB | Executed_Gtid_Set |
+---------------+----------+--------------+------------------+-------------------+
| binlog.000003 |     1092 |              |                  |                   |
+---------------+----------+--------------+------------------+-------------------+

+---------------+----------+--------------+------------------+-------------------+
| File          | Position | Binlog_Do_DB | Binlog_Ignore_DB | Executed_Gtid_Set |
+---------------+----------+--------------+------------------+-------------------+
| binlog.000003 |     1345 |              |                  |                   |
+---------------+----------+--------------+------------------+-------------------+
```

### 5.1.3 从服务器搭建

我们可以选择配置多台从服务器，配置方式都是一样的。

1. 在docker中创建并启动MySQL从服务器：名称 `msb-mysql-slave1`, 端口 `3307`

```shell
docker run -d \
-p 3307:3306 \
-v /msb/mysql/slave1/conf:/etc/mysql/conf.d \
-v /msb/mysql/slave1/data:/var/lib/mysql \
-e MYSQL_ROOT_PASSWORD=123456 \
--name msb-mysql-slave1 \
mysql:8.0.29

docker run -d \
-p 3308:3306 \
-v /msb/mysql/slave2/conf:/etc/mysql/conf.d \
-v /msb/mysql/slave2/data:/var/lib/mysql \
-e MYSQL_ROOT_PASSWORD=123456 \
--name msb-mysql-slave2 \
mysql:8.0.29
```

2. 创建slave1的配置文件

```shell
vim /msb/mysql/slave1/conf/my.cnf

vim /msb/mysql/slave2/conf/my.cnf
```

配置下面的内容

```shell
[mysqld]
# 服务器唯一id，每台服务器的id必须不同，如果配置其他从机，注意修改id
server-id=2

[mysqld]
server-id=3
```

重启从服务器

```shell
docker restart msb-mysql-slave1

docker restart msb-mysql-slave2
```

登录MySQL主服务器

```shell
[root@localhost ~]# docker exec -it msb-mysql-slave1 env LANG=C.UTF-8 /bin/bash

bash-4.4# mysql -uroot -p
Enter password: 输入密码

ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '123456';

[root@localhost ~]# docker exec -it msb-mysql-slave2 env LANG=C.UTF-8 /bin/bash

bash-4.4# mysql -uroot -p
Enter password: 输入密码

ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '123456';
```

3. 在从机上配置主从关系

```sql
CHANGE MASTER TO MASTER_HOST='192.168.58.100', 
MASTER_USER='msb_slave',MASTER_PASSWORD='123456', MASTER_PORT=3306,
MASTER_LOG_FILE='binlog.000003',MASTER_LOG_POS=1345; 
```

4. 启动从服务器，查看状态

```sql
START SLAVE;
-- 查看状态（不需要分号）
SHOW SLAVE STATUS\G
```

### 5.1.4 主从同步测试

在主库创建数据库、表，插入数据，测试从库是否同步数据

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

### 5.1.5 停止和重置

需要的时候，可以使用如下SQL语句

```sql
-- 在从机上执行。功能说明：停止I/O 线程和SQL线程的操作。
stop slave; 

-- 在从机上执行。功能说明：用于删除SLAVE数据库的relaylog日志文件，并重新启用新的relaylog文件。
reset slave;

-- 在主机上执行。功能说明：删除所有的binglog日志文件，并将日志索引文件清空，重新开始所有新的日志文件。
-- 用于第一次进行搭建主从库时，进行主库binlog初始化工作；
reset master;
```

### 5.1.6 常见问题解决

启动主从同步后，常见错误是 `Slave_IO_Running： No 或者 Connecting` 的情况

*（原站配图缺失）*

**解决方案1：**

1. 首先停掉Slave服务

```sql
-- 在从机停止slave
stop slave;
```

2. 到主服务器上查看主机状态, 记录File和Position对应的值

```sql
-- 在主机查看mater状态
SHOW MASTER STATUS;
```

*（原站配图缺失）*

4. 然后到slave服务器上执行手动同步：

```sql
-- MASTER_LOG_FILE和MASTER_LOG_POS与主库保持一致
CHANGE MASTER TO MASTER_HOST='192.168.58.100', 
MASTER_USER='slave',
MASTER_PASSWORD='123456',
MASTER_PORT=3306,
MASTER_LOG_FILE='mysql-bin.000015',
MASTER_LOG_POS=442,
MASTER_CONNECT_RETRY=10;
```

**解决方案2**

1. 程序可能在slave上进行了写操作
2. 也可能是slave机器重起后，事务回滚造成的.
3. 一般是事务回滚造成的,解决办法

```sql
mysql> slave stop;
mysql> set GLOBAL SQL_SLAVE_SKIP_COUNTER=1;
mysql> slave start;
```

## 5.2 Mycat2读写分离配置 (一主两从)

在⼀些⼤型⽹站业务场景中，单台数据库提供的并发量已经⽆法满⾜业务需求;为了提供数据库的并发能⼒和负载能⼒,⼀般通过读写分离来实现。

当我们的数据库实现读写分离的时候，在应⽤中需要对数据源进⾏切换， MyCat能够帮我们更好的实现数据源的动态切换，也就是应⽤程序只需要连接MyCat中间件，⾃动帮我们读取读写的数据库。

*（原站配图缺失）*

### 5.2.1 配置Mycat2原型库的数据源（database）信息

- 在主节点(主库)创建mycat数据库，供mycat内部使用，Mycat 在启动时，会自动在原型库下创建其运行时所需的数据表。

  ```sql
  CREATE DATABASE mycat CHARACTER SET utf8;
  ```

- 创建一个读写分离的测试库

  ```sql
  CREATE DATABASE rw_db CHARACTER SET utf8;
  ```

- 配置原型库的数据源信息prototypeDs.datasource.json

```java
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
        "url":"jdbc:mysql://192.168.58.100:3306/mycat?useUnicode=true&serverTimezone=Asia/Shanghai&characterEncoding=UTF-8",
        "user":"root",
        "weight":0
}
```

### 5.2.2 配置 master和slave 数据库的数据源信息（一主两从）

- 首先将原型库配置文件拷贝两份，并修改名称

```
cp prototypeDs.datasource.json master.datasource.json
cp prototypeDs.datasource.json slave01.datasource.json
cp prototypeDs.datasource.json slave02.datasource.json
```

- 配置主库

```shell
vim master.datasource.json
```

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
        "name":"master",
        "password":"123456",
        "type":"JDBC",
        "url":"jdbc:mysql://192.168.58.100:3306/rw_db?useUnicode=true&serverTimezone=Asia/Shanghai&characterEncoding=UTF-8",
        "user":"root",
        "weight":0
}
```

- 配置从库1

```
vim slave01.datasource.json
```

```json
{
        "dbType":"mysql",
        "idleTimeout":60000,
        "initSqls":[],
        "initSqlsGetConnection":true,
        "instanceType":"READ",
        "maxCon":1000,
        "maxConnectTimeout":3000,
        "maxRetryCount":5,
        "minCon":1,
        "name":"slave01",
        "password":"123456",
        "type":"JDBC",
        "url":"jdbc:mysql://192.168.58.100:3307/rw_db?useUnicode=true&serverTimezone=Asia/Shanghai&characterEncoding=UTF-8",
        "user":"root",
        "weight":0
}
```

- 配置从库2

```
vim slave02.datasource.json
```

```json
{
        "dbType":"mysql",
        "idleTimeout":60000,
        "initSqls":[],
        "initSqlsGetConnection":true,
        "instanceType":"READ",
        "maxCon":1000,
        "maxConnectTimeout":3000,
        "maxRetryCount":5,
        "minCon":1,
        "name":"slave02",
        "password":"123456",
        "type":"JDBC",
        "url":"jdbc:mysql://192.168.58.100:3308/rw_db?useUnicode=true&serverTimezone=Asia/Shanghai&characterEncoding=UTF-8",
        "user":"root",
        "weight":0
}
```

### 5.2.3 配置 master和slave 数据源的集群（cluster）信息

复制 master-slave.cluster.json

```shell
cp prototype.cluster.json master-slave.cluster.json
```

**注意：**这里不要删除 prototype.cluster.json，否则启动 Mycat 时会报错

```java
vim master-slave.cluster.json
```

```json
{
        "clusterType":"MASTER_SLAVE",
        "heartbeat":{
                "heartbeatTimeout":1000,
                "maxRetry":3,
                "minSwitchTimeInterval":300,
                "slaveThreshold":0
        },
        "masters":[
                "master"
        ],
        "replicas":[
                "slave01",
                "slave02"
        ],
        "maxCon":200,
        "name":"master-slave",
        "readBalanceType":"BALANCE_ALL_READ",

        "switchType":"NOT_SWITCH"
}

{
	 //集群类型：SINGLE_NODE（单节点）、MASTER_SLAVE（普通主从）、GARELA_CLUSTER（garela cluster/PXC集群）等
  "clusterType":"MASTER_SLAVE",
	"heartbeat":{
		"heartbeatTimeout":1000,
		"maxRetry":3,
		"minSwitchTimeInterval":300,
		"slaveThreshold":0
	},
	"masters":[
    // 主节点数据源名称
		"master"
	],
	"replicas":[
    // 从节点数据源名称
		"slave01",
		"slave02"
	],
	"maxCon":200,
  // 集群名称。在后面配置物理库（schema）时会用到
	"name":"master-slave",
  //查询负载均衡策略
	"readBalanceType":"BALANCE_ALL_READ",
  // NOT_SWITCH（不进行主从切换）、SWITCH（进行主从切换）
	"switchType":"NO_SWITCH"
}
```

参数说明

```
readBalanceType: 查询负载均衡策略
  BALANCE_ALL(默认值)： 获取集群中所有数据源
  BALANCE_ALL_READ：获取集群中允许读的数据源
  BALANCE_READ_WRITE：获取集群中允许读写的数据源,但允许读的数据源优先
  BALANCE_NONE：获取集群中允许写数据源,即主节点中选择

switchType: 主从切换设置
	NOT_SWITCH:不进行主从切换
	SWITCH:进行主从切换
```

### 5.2.4  配置物理库（schema）和 Mycat 中数据源/数据源集群的关系

```json
cd /root/software/mycat/conf/schemas

vim master_slave.schema.json

{
    "schemaName": "rw_db",
    "targetName": "master-slave",
    "normalTables": {}
}
{
    // 物理库
    "schemaName": "rw_db",
    // 指向集群，或者数据源
    "targetName": "master-slave",
    // 这里可以配置数据表相关的信息，在物理表已存在或需要启动时自动创建物理表时配置此项
    "normalTables": {}
}
```

### 5.2.5 修改 Mycat 登录用户信息

```
vim root.user.json
```

```java
{
	"dialect":"mysql",
	"ip":null,
	"password":"123456",
	"transactionType":"xa",
	"username":"root"
}
```

### 5.2.6 测试一主两从-读写分离

Step1 ：通过Navicat连接Mycat数据库

Step2 ：执行建表语句

```SQL
-- 创建表
CREATE TABLE products (
  pid INT(11) PRIMARY KEY AUTO_INCREMENT,
  pname VARCHAR(20) DEFAULT NULL
); 
```

Step3 ：执行插入和查询语句语句

```sql
-- 插入数据
INSERT INTO products VALUES(NULL,'phone');
INSERT INTO products VALUES(NULL,'book');
INSERT INTO products VALUES(NULL,'gun');

-- 查询数据
select * from products;
```

Step4 : 开启主从的日志

```sql
#日志输出到表中 对应的表是mysql.general_log 
SET GLOBAL log_output = 'TABLE'; 

#打开general_log，重启后失效
SET GLOBAL general_log = 'ON';

SET GLOBAL general_log = 'OFF'; #关闭
```

Step5 : 查询主从各自的日志信息

- general log 通用日志： 会记录所有MySQL的SQL。
- 默认不开启，对性能有影响，只在排查错误时开启，使用完关闭。

```sql
SELECT event_time,
       user_host,
       thread_id,
       server_id,
       command_type,
       CAST(argument AS CHAR(500) CHARACTER SET utf8mb4) argument
FROM mysql.general_log
ORDER BY event_time DESC;
```

表字段含义。

- event_time：查询日志记录到表的那一刻的log_timestamps系统变量值，用于标记查询日志记录何时入库。
- user_host： 表示该查询日志记录的来源，其中有用户名和主机名信息。
- thread_id：表示该查询日志记录执行时的process_id。
- server_id：表示执行该查询的数据库实例ID。
- command_type：表示该查询的command类型，通常都为query。
- argument：表示执行查询的SQL语句文本。
