## 5.3 Docker搭建MySQL主从复制集群 (双主双从)

### 5.3.1 双主双从架构介绍

虽然一主一从或一主多从集群解决了并发读的问题，但由于主节点只有一台，如果主节点宕机了，则数据库的写操作便无法完成，从而无法做到高可用。

因此，接下来我们来完成Mysql双主双从的集群搭建，双主双从的原理很简单，相当于有两个一主一从，然后两个主节点再互为主从，互相复制数据，然后借助MyCat的机制，先把一台主作为写库，另一台主和两台从作为读库，当作为写库的主宕机后，另一台主则作为写库提供服务，从而实现高可用。如下图所示：

*（原站配图缺失）*

| 角色    | 端口 | 机器名            |
| ------- | ---- | ----------------- |
| master1 | 3310 | msb-mysql-master1 |
| slave1  | 3311 | msb-mysql-slave1  |
| master2 | 3312 | msb-mysql-master2 |
| slave2  | 3313 | msb-mysql-slave2  |

### 5.3.2 双主MySQL配置

**1) 将之前搭建的MySQL集群拍摄快照， 然后删除。使用Docker命令，创建两个新的主机，分别是：**

- msb-mysql-master1
- msb-mysql-master2

```shell
docker run -d \
-p 3310:3306 \
-v /msb/mysql/master1/conf:/etc/mysql/conf.d \
-v /msb/mysql/master1/data:/var/lib/mysql \
-e MYSQL_ROOT_PASSWORD=123456 \
--name msb-mysql-master1 \
mysql:8.0.29

docker run -d \
-p 3311:3306 \
-v /msb/mysql/master2/conf:/etc/mysql/conf.d \
-v /msb/mysql/master2/data:/var/lib/mysql \
-e MYSQL_ROOT_PASSWORD=123456 \
--name msb-mysql-master2 \
mysql:8.0.29
```

**2) 配置Master1，修改配置文件 `vim /msb/mysql/master1/conf/my.cnf`**

```properties
[mysqld]
#开启二进制日志
log-bin=mysql-bin
#设置服务id
server-id=1
# 设置不要复制的数据库
binlog-ignore-db=mysql
binlog-ignore-db=performance_schema
binlog-ignore-db=sys
#设置需要复制的数据库
binlog-do-db=mydb
#设置logbin格式;可选值：STATEMENT、ROW、MIXED
binlog_format=STATEMENT
# 作为从数据库的时候，有写入操作也要更新二进制日志文件
log-slave-updates
# 自增长字段从哪个数开始
auto-increment-offset=1
# 自增长字段每次递增的量
auto-increment-increment=2
```

**MySQL 配置参数 -- logs-slave-updates**

正常情况下，一个 `slave`节点是不会将其从 `master`节点同步的数据更新操作记录至自己的二进制日志 `bin-log`中的。

在多主的场景下，各 `master节点`其实又相互作为另一方的 `slave节点`进行着数据的一致性同步操作。例如 `masterA` 会以 `slave`的角色同步 `masterB` 上的数据，`masterB` 也会以 `slave`的角色同步 `masterA` 上的数据，如果没有开启 `logs-slave-updates`参数配置，则 `masterA` \ `masterB` 虽然也能保证数据的一致性和完整性，但二者的 `bin-log` 中都只记录了作用在自身实例上的数据更新操作。

```sql
-- masterA 插入数据row1，并记录到binlog
masterA insert row1 bin-logA add row1

-- masterB 插入数据row2，并记录到binlog
masterB insert row2 bin-logB add row2

-- masterA 同步数据row2，但是没有记录到binlog
masterA replicate row2 from masterB But bin-logA will not log this update

-- masterB 同步数据row1，但是没有记录到binlog
masterB replicate row1 from masterA But bin-logB will not log this update

-- slaveA只能同步row1到binlog
slaveA replicate row1 form bin-logA

-- slaveB只能同步row2到binlog
slaveB replicate row2 form bin-logB
```

因为主从复制是使用 `bin-log` 完成的，`masterA` `masterB` 互补同步数据时并没有将对方同步的数据写入自己的 `bin-log`，则会导致自己的从实例只能同步到集群的部分数据。

**3) 配置Master2，修改配置文件 `vim /msb/mysql/master2/conf/my.cnf`**

```sql
[mysqld]

#开启二进制日志
log-bin=mysql-bin
#设置服务id
server-id=2
# 设置不要复制的数据库
binlog-ignore-db=mysql
binlog-ignore-db=performance_schema
binlog-ignore-db=sys
#设置需要复制的数据库
binlog-do-db=mydb
#设置logbin格式;可选值：STATEMENT、ROW、MIXED
binlog_format=STATEMENT
# 作为从数据库的时候，有写入操作也要更新二进制日志文件
log-slave-updates
# 自增长字段从哪个数开始
auto-increment-offset=2
# 自增长字段每次递增的量
auto-increment-increment=2
```

### 5.3.3 双从MySQL配置

**1) 使用Docker命令，创建两个新的从机，分别是：**

- msb-mysql-slave1
- msb-mysql-slave2

```shell
docker run -d \
-p 3312:3306 \
-v /msb/mysql/slave1/conf:/etc/mysql/conf.d \
-v /msb/mysql/slave1/data:/var/lib/mysql \
-e MYSQL_ROOT_PASSWORD=123456 \
--name msb-mysql-slave1 \
mysql:8.0.29

docker run -d \
-p 3313:3306 \
-v /msb/mysql/slave2/conf:/etc/mysql/conf.d \
-v /msb/mysql/slave2/data:/var/lib/mysql \
-e MYSQL_ROOT_PASSWORD=123456 \
--name msb-mysql-slave2 \
mysql:8.0.29
```

**2)配置slave1，修改配置文件 `vim /msb/mysql/slave1/conf/my.cnf`**

```properties
[mysqld]

#开启二进制日志
log-bin=mysql-bin
#设置服务id
server-id=3
#启用中继日志
relay-log=mysql-relay
```

**3)配置slave2，修改配置文件 `vim /msb/mysql/slave2/conf/my.cnf`**

```properties
[mysqld]

#开启二进制日志
log-bin=mysql-bin
#设置服务id
server-id=4
#启用中继日志
relay-log=mysql-relay
```

### 5.3.4 重启双主、双从MySQL服务

```shell
docker restart msb-mysql-master1

docker restart msb-mysql-master2

docker restart msb-mysql-slave1

docker restart msb-mysql-slave2
```

### 5.3.5 创建授权账号

在Master1节点的MySQL上建立帐户并授权，用于登录主节点，进行数据同步复制

```sql
[root@localhost ~]# docker exec -it msb-mysql-master1 env LANG=C.UTF-8 /bin/bash

bash-4.4# mysql -uroot -p
Enter password: 输入密码

mysql> ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '123456';

# 授权主备复制专用账号
mysql> CREATE USER 'slave1'@'%' IDENTIFIED BY '123456';

mysql> GRANT REPLICATION SLAVE ON *.* TO 'slave1'@'%';

mysql> ALTER USER 'slave1'@'%' IDENTIFIED WITH mysql_native_password BY '123456';

# 刷新权限
mysql> FLUSH PRIVILEGES;
```

在Master2节点的MySQL上建立帐户并授权，用于登录主节点，进行数据同步复制

```sql
[root@localhost ~]# docker exec -it msb-mysql-master2 env LANG=C.UTF-8 /bin/bash
bash-4.4# mysql -uroot -p
Enter password: 输入密码

mysql> ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '123456';

# 授权主备复制专用账号
mysql> CREATE USER 'slave2'@'%' IDENTIFIED BY '123456';

mysql> GRANT REPLICATION SLAVE ON *.* TO 'slave2'@'%';

mysql> ALTER USER 'slave2'@'%' IDENTIFIED WITH mysql_native_password BY '123456';

# 刷新权限
mysql> FLUSH PRIVILEGES;

```

查询Master1的状态：`show master status;`，记录下File和Position的值

*（原站配图缺失）*

```sql
mysql> show master status;
+------------------+----------+--------------+------------------------------+-------------------+
| File             | Position | Binlog_Do_DB | Binlog_Ignore_DB             | Executed_Gtid_Set |
+------------------+----------+--------------+------------------------------+-------------------+
| mysql-bin.000001 |      157 | mydb         | mysql,performance_schema,sys |                   |
+------------------+----------+--------------+------------------------------+-------------------+
```

查询Master2的状态：`show master status;`，分别记录下File和Position的值

*（原站配图缺失）*

```sql
mysql> show master status;
+------------------+----------+--------------+------------------------------+-------------------+
| File             | Position | Binlog_Do_DB | Binlog_Ignore_DB             | Executed_Gtid_Set |
+------------------+----------+--------------+------------------------------+-------------------+
| mysql-bin.000001 |      157 | mydb         | mysql,performance_schema,sys |                   |
+------------------+----------+--------------+------------------------------+-------------------+

```

### 5.3.6 设置从库向主库同步/复制数据

操作slava1

```sql
[root@localhost ~]# docker exec -it msb-mysql-slave1 env LANG=C.UTF-8 /bin/bash

bash-4.4# mysql -uroot -p
Enter password: 输入密码

ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '123456';

CHANGE MASTER TO MASTER_HOST='192.168.58.100', 
MASTER_USER='slave1',
MASTER_PASSWORD='123456', 
MASTER_PORT=3310,
MASTER_LOG_FILE='mysql-bin.000001',
MASTER_LOG_POS=1451; 
```

操作slava2

```sql
[root@localhost ~]# docker exec -it msb-mysql-slave2 env LANG=C.UTF-8 /bin/bash

bash-4.4# mysql -uroot -p
Enter password: 输入密码

ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '123456';

CHANGE MASTER TO MASTER_HOST='192.168.58.100', 
MASTER_USER='slave2',
MASTER_PASSWORD='123456', 
MASTER_PORT=3311,
MASTER_LOG_FILE='mysql-bin.000001',
MASTER_LOG_POS=1452; 
```

分别启动两从MySQL服务的复制功能，查看服务器状态；`Slave_IO_Runing`和 `Slave_SQL_Runing`都为Yes说明同步成功

```sql
start slave;
```

查看双从服务器状态

```sql
show slave status\G;
```

**slave1状态**

![image-20221223180625839](../../../../../congqing/Library/Application Support/typora-user-images/image-20221223180625839.png)

**slave2状态**

![image-20221223180659637](../../../../../congqing/Library/Application Support/typora-user-images/image-20221223180659637.png)

出现异常：

```java
ERROR 1872 (HY000): Slave failed to initialize relay log info structure from the repository
复制代码
```

解决方案：

```java
stop slave;
start slave;

or

reset slave;
start slave;
```

### 5.3.7  配置双主互相复制

master1复制master2，master2复制Master1

操作master1

```sql
CHANGE MASTER TO MASTER_HOST='192.168.58.100',
MASTER_USER='slave2',
MASTER_PASSWORD='123456',
MASTER_LOG_FILE='mysql-bin.000001',
MASTER_LOG_POS=1452,
MASTER_PORT=3311;
```

操作Master2

```sql
CHANGE MASTER TO MASTER_HOST='192.168.58.100',
MASTER_USER='slave1',
MASTER_PASSWORD='123456',
MASTER_LOG_FILE='mysql-bin.000001',
MASTER_LOG_POS=1451,
MASTER_PORT=3310;
```

分别启动两主MySQL服务的复制功能，查看从服务器状态：`Slave_IO_Runing`和 `Slave_SQL_Runing`都为Yes说明同步成功

```java
start slave;
```

查看从服务器状态

```java
show slave status;

show slave status\G;
```

### 5.3.8 测试双主双从的同步复制

注意：在测试双主双从复制时，一定要确保每个节点MySQL的 `Slave_IO_Runing`和 `Slave_SQL_Runing`都为Yes。

在Master1节点新建库、新建表、插入数据

```sql
mysql>  CREATE DATABASE mydb CHARACTER SET utf8;
Query OK, 1 row affected (0.01 sec)

mysql> use mydb;
Database changed

mysql> CREATE TABLE mytb(id INT,name VARCHAR(30));
Query OK, 0 rows affected (0.02 sec)

mysql> INSERT INTO mytb VALUES(1,'mycat');
Query OK, 1 row affected (0.01 sec)

mysql> select * from mytb;
+------+-------+
| id   | name  |
+------+-------+
|    1 | mycat |
+------+-------+
1 row in set (0.00 sec)

```

在Master2和从机验证数据是否进行了复制

## 5.4 Mycat2读写分离配置 (双主两从)

### 5.4.1 配置Mycat2原型库的数据源（database）信息

- 在master1主节点创建mycat数据库，供mycat内部使用，Mycat 在启动时，会自动在原型库下创建其运行时所需的数据表。

```sql
CREATE DATABASE mycat CHARACTER SET utf8;
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
        "url":"jdbc:mysql://192.168.58.100:3310/mycat?useUnicode=true&serverTimezone=Asia/Shanghai&characterEncoding=UTF-8",
        "user":"root",
        "weight":0
}
```

创建逻辑库

```sql
CREATE DATABASE mydb CHARACTER SET utf8;
```

执行创建库语句后，将在 `/mycat/conf/schemas/`自动生成 `mydb.schema.json`文件

```json
{
        "customTables":{},
        "globalTables":{},
        "normalProcedures":{},
        "normalTables":{},
        "schemaName":"mydb",
        "shardingTables":{},
        "views":{}
}

customTables：mycat默认的表的配置

globalTables：全局表的配置

shardingTables：分片表的配置

normalTables：普通表的配置
```

修改schema的配置，指定mydb逻辑库默认的targetName，mycat会自动加载mydb下已经有的物理表或者视图作为单表

```json
{
	"customTables":{},
	"globalTables":{},
	"normalProcedures":{},
	"normalTables":{},
	"schemaName":"mydb",
	"targetName":"prototype"
	"shardingTables":{},
	"views":{}
}
```

修改之后重启Mycat

```shell
[root@localhost bin]# ./mycat restart
```

连接Mycat，然后进行查询

![image-20221223185303712](../../../../../congqing/Library/Application Support/typora-user-images/image-20221223185303712.png)

### 5.4.2 注解方式-配置 master和slave 数据库的数据源信息

添加Master1数据源

```json
/*+ mycat:createDataSource{ "name":"write1","url":"jdbc:mysql://192.168.58.100:3310/mydb?useSSL=false&characterEncoding=UTF-8&useJDBCCompliantTimezoneShift=true", "user":"root","password":"123456" } */;
```

添加Master2数据源

```json
/*+ mycat:createDataSource{ "name":"write2","url":"jdbc:mysql://192.168.58.100:3311/mydb?useSSL=false&characterEncoding=UTF-8&useJDBCCompliantTimezoneShift=true", "user":"root","password":"123456" } */;
```

添加Slave1数据源

```json
 /*+ mycat:createDataSource{ "name":"read1","url":"jdbc:mysql://192.168.58.100:3312/mydb?useSSL=false&characterEncoding=UTF-8&useJDBCCompliantTimezoneShift=true", "user":"root","password":"123456" } */;
```

添加Slave2数据源

```json
/*+ mycat:createDataSource{ "name":"read2","url":"jdbc:mysql://192.168.58.100:3313/mydb?useSSL=false&characterEncoding=UTF-8&useJDBCCompliantTimezoneShift=true", "user":"root","password":"123456" } */;
```

查询配置数据源结果

```json
/*+ mycat:showDataSources{} */;
```

![image-20221223190547292](../../../../../congqing/Library/Application Support/typora-user-images/image-20221223190547292.png)

通过注释命名添加数据源后，在对应目录会生成相关配置文件，查看数据源配置文件：`mycat/conf/datasources`

```shell
[root@localhost conf]# cd datasources/
[root@localhost datasources]# ll
总用量 20
-rw-r--r--. 1 root root 422 12月  3 20:33 prototypeDs.datasource.json
-rw-r--r--. 1 root root 484 12月  3 20:56 read1.datasource.json
-rw-r--r--. 1 root root 484 12月  3 20:56 read2.datasource.json
-rw-r--r--. 1 root root 485 12月  3 20:53 write1.datasource.json
-rw-r--r--. 1 root root 485 12月  3 20:55 write2.datasource.json
```

### 5.4.3 注解方式-配置 master和slave 数据源的集群（cluster）信息

使用mycat自带的默认集群:`prototype`，对其修改更新

```json
 /*! mycat:createCluster{"name":"prototype","masters":["write1","write2"],"replicas":["read1","read2","write2"]} */;
```

查看配置集群信息

```json
/*+ mycat:showClusters{} */;
```



查看集群配置文件，发现集群配置信息已经更新

```java
vim conf/clusters/prototype.cluster.json
```

```java
{
        "clusterType":"MASTER_SLAVE",
        "heartbeat":{
                "heartbeatTimeout":1000,
                "maxRetryCount":3,
                "minSwitchTimeInterval":300,
                "showLog":false,
                "slaveThreshold":0.0
        },
        "masters":[
                "write1",
                "write2"
        ],
        "maxCon":2000,
        "name":"prototype",
        "readBalanceType":"BALANCE_ALL",
        "replicas":[
                "read1",
                "read2",
                "write2"
        ],
        "switchType":"SWITCH"
}
```

### 5.4.4 读写分离测试

1. 修改MySQL的配置文件：`my.cnf`，设置logbin格式 `binlog_format=STATEMENT`，重启MySQL，确保此时主从复制正常

> binlog_format=STATEMENT：记录每一条 sql 语句，日志记录的是主机数据库的 `写指令`，性能高，但是now()之类的函数以及获取系统参数的操作会出现主从数据不同步的问题。

2. 登录MyCat，向数据表插入 `系统变量`值，以此造成主从数据不一致，便于验证读写分离。

```sql
INSERT INTO mytb VALUES(2,@@hostname);
```

3. 登录双主双从MySQL4个库查看表数据

```
SELECT * FROM mytb;
```

4. 在Mycat里查询mytb表，可以看到查询语句在主从两个主机间切换

```
mysql> select * from mytb;
+----+--------------+
| id | name         |
+----+--------------+
|  1 | mycat        |
|  2 | 7d7d92ddd51e |
+----+--------------+
2 rows in set (0.04 sec)
 
mysql> select * from mytb;
+----+--------------+
| id | name         |
+----+--------------+
|  1 | mycat        |
|  2 | f1cc8223fc73 |
+----+--------------+
2 rows in set (0.04 sec)

mysql> select * from mytb;
+----+--------------+
| id | name         |
+----+--------------+
|  1 | mycat        |
|  2 | 7d7d92ddd51e |
+----+--------------+
2 rows in set (0.04 sec)
 
mysql> select * from mytb;
+----+--------------+
| id | name         |
+----+--------------+
|  1 | mycat        |
|  2 | f1cc8223fc73 |
+----+--------------+
2 rows in set (0.01 sec)
 
mysql> select * from mytb;
+----+--------------+
| id | name         |
+----+--------------+
|  1 | mycat        |
|  2 | 7d7d92ddd51e |
+----+--------------+
2 rows in set (0.01 sec)
 
mysql> select * from mytb;
+----+--------------+
| id | name         |
+----+--------------+
|  1 | mycat        |
|  2 | 83526eafc910 |
+----+--------------+
2 rows in set (0.01 sec)
```
