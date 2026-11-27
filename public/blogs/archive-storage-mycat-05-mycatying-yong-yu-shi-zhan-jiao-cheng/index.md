# 6.MyCat2 实现分库分表

## 6.1 分库分表概念回顾

### 6.1.1 分库操作

- **水平分库**：把同一个表的数据按一定规则拆到不同的数据库中
- **垂直分库**：按照业务、功能模块将表进行分类，不同功能模块对应的表分到不同的库中
- **分库原则**：将紧密关联关系的表划分在一个库里，没有关联关系的表可以分到不同的库里

### 6.1.2 分表操作

- **水平分表**：在同一个数据库内，把同一个表的数据按一定规则拆到多个表中
- **垂直分表**：将一个表按照字段分成多表，每个表存储其中一部分字段
- **分表原则**：减少节点数据库的访问，分表字段尤为重要，其决定了节点数据库的访问量。

## 6.2 分库分表环境准备

### 6.2.1 修改MyCat集群配置

1. 只保留一主一从

```shell 
cd /root/software/mycat/conf/clusters

vim prototype.cluster.json 

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
                "write1"
        ],
        "maxCon":2000,
        "name":"prototype",
        "readBalanceType":"BALANCE_ALL",
        "replicas":[
                "read1"
        ],
        "switchType":"SWITCH"
}
```

*（原站配图缺失）*

2. 将多余的数据源删除（修改后缀名即可）

```shell
cd /root/software/mycat/conf/datasources

mv read2.datasource.json read2.datasource.json_bak
mv write2.datasource.json write2.datasource.json_bak
```

*（原站配图缺失）*

### 6.2.2 添加数据源

端口3310的MySQL，同时作为写数据源和读数据源

```json
/*+ mycat:createDataSource{ 
"name":"db0_w",
"url":"jdbc:mysql://192.168.58.100:3310/mydb?useSSL=false&characterEncoding=UTF-8&useJDBCCompliantTimezoneShift=true", 
"user":"root",
"password":"123456" } */;

/*+ mycat:createDataSource{ 
"name":"db0_r",
"url":"jdbc:mysql://192.168.58.100:3310/mydb?useSSL=false&characterEncoding=UTF-8&useJDBCCompliantTimezoneShift=true", 
"user":"root",
"password":"123456" } */;
```

端口3312的MySQL，同时作为写数据源和读数据源

```json
 /*+ mycat:createDataSource{ 
 "name":"db1_w",
 "url":"jdbc:mysql://192.168.58.100:3312/mydb?useSSL=false&characterEncoding=UTF-8&useJDBCCompliantTimezoneShift=true", 
 "user":"root",
 "password":"123456" } */;
 
  /*+ mycat:createDataSource{ 
 "name":"db1_r",
 "url":"jdbc:mysql://192.168.58.100:3312/mydb?useSSL=false&characterEncoding=UTF-8&useJDBCCompliantTimezoneShift=true", 
 "user":"root",
 "password":"123456" } */;
```

查看数据源配置结果

```json
/*+ mycat:showDataSources{} */;
```

*（原站配图缺失）*

通过注释命名添加数据源后，在对应目录会生成相关配置文件，查看数据源配置文件：`mycat/conf/datasources`

*（原站配图缺失）*

### 6.2.2 添加集群配置

接下来我们将新添加的数据源配置成集群

> 注意： HASH型分片算法默认要求集群名字以 `c`为前缀数字为后缀，`c0`就是分片表第一个节点，`c1`就是第二个节点，以此类推。

添加集群节点：c0

```json
 /*! mycat:createCluster{"name":"c0","masters":["db0_w"],"replicas":["db0_r"]} */;
```

添加集群节点：c1

```json
  /*! mycat:createCluster{"name":"c1","masters":["db1_w"],"replicas":["db1_r"]} */;
```

查看集群配置信息

```json
 /*+ mycat:showClusters{} */;
```

*（原站配图缺失）*

查看集群配置文件

查看集群：`c0`

```json
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
                "db0_w"
        ],
        "maxCon":2000,
        "name":"c0",
        "readBalanceType":"BALANCE_ALL",
        "replicas":[
                "db0_r"
        ],
        "switchType":"SWITCH"
}
```

查看集群：`c1`

```json
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
                "db1_w"
        ],
        "maxCon":2000,
        "name":"c1",
        "readBalanceType":"BALANCE_ALL",
        "replicas":[
                "db1_r"
        ],
        "switchType":"SWITCH"
}
```

## 6.3 进行分库分表

### 6.3.1 实现数据分片

登录Mycat，运行建表语句进行数据分片

```sql
CREATE TABLE msb_user (
	id BIGINT primary key AUTO_INCREMENT,
	username VARCHAR(30) DEFAULT NULL,
	age INT,
	type INT
) ENGINE = INNODB DEFAULT CHARSET = utf8 
dbpartition BY mod_hash(type)
tbpartition BY mod_hash( id ) 
tbpartitions 1 
dbpartitions 2 ;
```

- dbpartition：数据库分片规则
- tbpartition ：表分片规则
- mod_hash ：分片规则
- tbpartitions 1 dbpartitions 2：创建2个库且每个库各创建1个分片表

插入数据

```sql
INSERT INTO mydb.msb_user(id,username,age,type)VALUES(1,'mycat1',15,1);
INSERT INTO mydb.msb_user(id,username,age,type)VALUES(2,'mycat2',20,2);
INSERT INTO mydb.msb_user(id,username,age,type)VALUES(3,'mycat3',15,1);
INSERT INTO mydb.msb_user(id,username,age,type)VALUES(4,'mycat4',20,2);
```

### 6.3.2 分片算法 mod_hash说明

1. 当分库键和分表键是不同键：

```erlang
分表下标= 分片值%分表数量

分库下标= 分片值%分库数量
```

2. 当分库键和分表键是同一个键：

```
分表下标=分片值%(分库数量*分表数量)

分库下标=分表下标/分表数量
```

我们使用 `mod_hash`分片规则，分库键和分表键是不同键，所以

- 分表下标：`1%1=0；2%1=0；3%1=0；4%1=0；`
- 分库下标：`1%2=1; 2%2=0;`

查看schema：`/mycat/conf/schemas/mydb.schema.json`，生成配置信息如下

```json
{
        "customTables":{},
        "globalTables":{},
        "normalProcedures":{},
        "normalTables":{
                "mytb":{
                        "createTableSQL":"CREATE TABLE mydb.mytb (\n\t`id` int DEFAULT NULL,\n\t`name` varchar(30) DEFAULT NULL\n) ENGINE = InnoDB CHARSET = utf8mb3",
                        "locality":{
                                "schemaName":"mydb",
                                "tableName":"mytb",
                                "targetName":"prototype"
                        }
                }
        },
        "schemaName":"mydb",
        "shardingTables":{
                "msb_user":{
                        "createTableSQL":"CREATE TABLE mydb.msb_user (\n\tid BIGINT PRIMARY KEY AUTO_INCREMENT,\n\tusername VARCHAR(30) DEFAULT NULL,\n\tage INT,\n\ttype INT\n) ENGINE = INNODB CHARSET = utf8\nDBPARTITION BY mod_hash(type) DBPARTITIONS 2\nTBPARTITION BY mod_hash(id) TBPARTITIONS 1",
                        "function":{
                                "properties":{
                                        "dbNum":"2",
                                        "mappingFormat":"c${targetIndex}/mydb_${dbIndex}/msb_user_${tableIndex}",
                                        "tableNum":"1",
                                        "tableMethod":"mod_hash(id)",
                                        "storeNum":2,
                                        "dbMethod":"mod_hash(type)"
                                }
                        },
                        "shardingIndexTables":{}
                }
        },
        "targetName":"prototype",
        "views":{}
}
```

### 6.3.3 查看分片节点数据

登录master1

```shell
[root@localhost ~]# docker exec -it msb-mysql-master1 env LANG=C.UTF-8 /bin/bash
bash-4.4# mysql -uroot -p

mysql> show databases;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mycat              |
| mydb               |
| mydb_0             |
| mysql              |
| performance_schema |
| sys                |
+--------------------+
7 rows in set (0.01 sec)

mysql> use mydb_0;

mysql> show tables;
+------------------+
| Tables_in_mydb_0 |
+------------------+
| msb_user_0       |
+------------------+
1 row in set (0.01 sec)

mysql> select * from msb_user_0;
+----+----------+------+------+
| id | username | age  | type |
+----+----------+------+------+
|  2 | mycat2   |   20 |    2 |
|  4 | mycat4   |   20 |    2 |
+----+----------+------+------+
2 rows in set (0.00 sec)

```

登录slave1

```sql
[root@localhost ~]# docker exec -it msb-mysql-slave1 env LANG=C.UTF-8 /bin/bash
bash-4.4# mysql -uroot -p
Enter password: 

mysql> use mydb_1;

mysql> select * from msb_user_0;
+----+----------+------+------+
| id | username | age  | type |
+----+----------+------+------+
|  1 | mycat1   |   15 |    1 |
|  3 | mycat3   |   15 |    1 |
+----+----------+------+------+
2 rows in set (0.00 sec)
```

### 6.3.4 实现ER表

ER表回顾

- Mycat提出了基于 E-R 关系的数据分片策略，子表的记录与所关联的父表记录存放在同一个数据分片上，即子表依赖于父表，通过表分组(Table Group)保证数据 join 不会跨库操作。
- 表分组(Table Group)是解决跨分片数据 join 的一种很好的思路，也是数据切分规划的重要一条规则。

> mycat2无需指定ER表,是自动识别的,具体看分片算法的接口

登录Mycat，创建ER表

```sql
CREATE TABLE msb_user_wx ( 
	id BIGINT PRIMARY KEY AUTO_INCREMENT,
	nickname VARCHAR(30) DEFAULT NULL,
	user_id INT
) ENGINE = INNODB DEFAULT CHARSET = utf8 
dbpartition BY mod_hash(id)
tbpartition BY mod_hash(user_id)
tbpartitions 1 
dbpartitions 2;
```

插入数据

```sql
INSERT INTO msb_user_wx(id,nickname,user_id) VALUES(1,'幸福生活',1);
INSERT INTO msb_user_wx(id,nickname,user_id) VALUES(2,'风和日丽',2);
INSERT INTO msb_user_wx(id,nickname,user_id) VALUES(3,'雄鹰展翅',3);
INSERT INTO msb_user_wx(id,nickname,user_id) VALUES(4,'出水芙蓉',4);
```

登录master1

```sql
mysql> select * from msb_user_wx_0 ;
+----+--------------+---------+
| id | nickname     | user_id |
+----+--------------+---------+
|  2 | 风和日丽     |       2 |
|  4 | 出水芙蓉     |       4 |
+----+--------------+---------+
2 rows in set (0.00 sec)
```

登录slave1

```sql
mysql>  select * from msb_user_wx_0 ;
+----+--------------+---------+
| id | nickname     | user_id |
+----+--------------+---------+
|  1 | 幸福生活     |       1 |
|  3 | 雄鹰展翅     |       3 |
+----+--------------+---------+
2 rows in set (0.00 sec)
```

查看配置的表是否具有ER关系，使用 `/*+ mycat:showErGroup{}*/`查看

> group_id表示相同的组,该组中的表具有相同的存储分布，即可以关联查询

```json
/*+ mycat:showErGroup{}*/;
```

*（原站配图缺失）*

关联查询

```sql
SELECT * FROM msb_user mu INNER JOIN msb_user_wx muw ON mu.id=muw.user_id;
```

*（原站配图缺失）*

### 6.3.5 实现广播表

**全局表（广播表）回顾：**

一个真实的业务系统中，往往存在大量的类似字典表的表，这些表基本上很少变动，字典表具有以下几个特 性:

- 变动不频繁;
- 数据量总体变化不大;
- 数据规模不大，很少有超过数十万条记录。

*（原站配图缺失）*

**添加数据库msb_db**

```sql
-- 在MyCat中创建逻辑库msb_db
CREATE DATABASE msb_db character set utf8;
```

**创建广播表**

```sql
-- 创建区域表
CREATE TABLE t_district  (
  id BIGINT(20) PRIMARY KEY COMMENT '区域ID',
  district_name VARCHAR(100) COMMENT '区域名称',
  LEVEL INT COMMENT '等级'
)ENGINE=InnoDB DEFAULT CHARSET=utf8 BROADCAST;
```

**查看schema配置，自动生成广播表配置信息**

```json
{
        "customTables":{},
        "globalTables":{
                "t_district":{
                        "broadcast":[
                                {
                                        "targetName":"c0" #广播表对应数据源
                                },
                                {
                                        "targetName":"c1"
                                }
                        ],
                        "createTableSQL":"CREATE TABLE msb_db.t_district (\n\tid BIGINT(20) PRIMARY KEY COMMENT '区域ID',\n\tdistrict_name VARCHAR(100) COMMENT '区域名称',\n\tLEVEL INT COMMENT '等级'\n) BROADCAST ENGINE = InnoDB CHARSET = utf8"
                }
        },
        "normalProcedures":{},
        "normalTables":{},
        "schemaName":"msb_db",
        "shardingTables":{},
        "views":{}
}
```

查看master1

```sql
mysql> use msb_db;

Database changed
mysql> show tables;
+------------------+
| Tables_in_msb_db |
+------------------+
| t_district       |
+------------------+
1 row in set (0.00 sec)
```

查看slave1

```sql
mysql> use msb_db;

Database changed
mysql> show tables;
+------------------+
| Tables_in_msb_db |
+------------------+
| t_district       |
+------------------+
1 row in set (0.00 sec)
```

测试广播表，在MyCat中插入数据，然后分区去对应的广播表查看是否插入成功

```sql
insert into t_district values(2,'海淀区',1);
```

## 6.4 常用的分片规则

### 6.4.1 分片算法介绍

Mycat2支持常用的(自动)HASH型分片算法也兼容1.6的内置的(cobar)分片算法.
HASH型分片算法默认要求集群名字以c为前缀,数字为后缀, c0就是分片表第一个节点, c1就是第二个节点.该命名规则允许用户手动改变。

**分片规则与适用性**

*（原站配图缺失）*

### 6.4.2 常用分片规则介绍

详细请参考

https://www.yuque.com/ccazhw/ml3nkf/394ccdc29b3813709d41992a0a4e035b?

**1.MOD_HASH**

> 如果分片值是字符串则先对字符串进行hash转换为数值类型

1.分库键和分表键是同1个键

```ruby
分表下标=分片值%(分库数量*分表数量)
分库下标=分表下标/分表数量
```

2.分库键和分表键是不同键

```erlang
分表下标= 分片值%分表数量
分库下标= 分片值%分库数量
复制代码
create table travelrecord (
 ....
) ENGINE=InnoDB DEFAULT CHARSET=utf8 
dbpartition by MOD_HASH (id) dbpartitions 6
tbpartition by MOD_HASH (id) tbpartitions 6;
```

**2.RIGHT_SHIFT**

```
RANGE_HASH(字段1, 字段2, 截取开始下标)
```

> 仅支持数值类型，字符串类型，分片值右移二进制位数,然后按分片数量取余

> 当字符串类型时候，第三个参数生效，根据下标截取其后部分字符串(截取下标不能少于实际值的长度)，然后该字符串hash成数值

> 两个字段的数值类型要求一致

```sql
create table travelrecord(
...
)ENGINE=InnoDB DEFAULT CHARSET=utf8 
dbpartition by RANGE_HASH(id,user_id,3) dbpartitions 3
tbpartition by RANGE_HASH(id,user_id,3) tbpartitions 3;
```

**3.RIGHT_SHIFT**

```sql
RIGHT_SHIFT(字段名,位移数)
仅支持数值类型

分片值右移二进制位数,然后按分片数量取余

create table travelrecord( 
 ...
)ENGINE=InnoDB DEFAULT CHARSET=utf8 
dbpartition by RIGHT_SHIFT(id,4) dbpartitions 3
tbpartition by RIGHT_SHIFT(user_id,4) tbpartitions 3;
```

**4.YYYYDD** `(YYYY*366+DD)%分库数`

仅用于分库，DD是一年之中的天数

```sql
create table travelrecord (
 ....
) ENGINE=InnoDB DEFAULT CHARSET=utf8 
dbpartition by YYYYMM(xxx) dbpartitions 8
tbpartition by xxx(xxx) tbpartitions 12;
```

**5.YYYYMM** `(YYYY*12+MM)%分库数`

> 仅用于分库，MM是1-12

```sql
create table travelrecord (
 ....
) ENGINE=InnoDB DEFAULT CHARSET=utf8 
dbpartition by YYYYMM(xxx) dbpartitions 8
tbpartition by xxx(xx) tbpartitions 12;
```

**6.MMDD**

> 仅用于分表，仅DATE/DATETIME适用

> 一年之中第几天%分表数，tbpartitions 不超过 366

```sql
create table travelrecord (
 ....
) ENGINE=InnoDB DEFAULT CHARSET=utf8 
dbpartition by xxx(xx) dbpartitions 8
tbpartition by MMDD(xx) tbpartitions 366;
```
