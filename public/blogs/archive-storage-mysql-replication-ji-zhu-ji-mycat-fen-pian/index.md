# 一、垂直拆分

## 1. 场景

在业务系统中, 涉及以下表结构 ,但是由于用户与订单每天都会产生大量的数据, 

单台服务器的数据存储及处理能力是有限的, 可以对数据库表进行拆分, 原有的数据库表如下。

![img](/blogs/_archive-2024-assets/4c835330c5e1f9e0c615.webp)

现在考虑将其进行垂直分库操作，将商品相关的表拆分到一个数据库服务器，订单表拆分的一个数据库服

务器，用户及省市区表拆分到一个服务器。

最终结构如下：

![img](/blogs/_archive-2024-assets/1302d6db73c876406464.webp)

## 2. 准备

准备三台服务器，IP地址如图所示：

![img](/blogs/_archive-2024-assets/819e4a6c4e0558a11ff0.webp)

并且在192.168.200.210，192.168.200.213, 192.168.200.214上面创建数据库 shopping。

## 3. 配置

### schema.xml

```xml
<schema name="SHOPPING" checkSQLschema="true" sqlMaxLimit="100"> 
  <table name="tb_goods_base" dataNode="dn1" primaryKey="id" />
  <table name="tb_goods_brand" dataNode="dn1" primaryKey="id" />
  <table name="tb_goods_cat" dataNode="dn1" primaryKey="id" />
  <table name="tb_goods_desc" dataNode="dn1" primaryKey="goods_id" />
  <table name="tb_goods_item" dataNode="dn1" primaryKey="id" />

  <table name="tb_order_item" dataNode="dn2" primaryKey="id" />
  <table name="tb_order_master" dataNode="dn2" primaryKey="order_id" />
  <table name="tb_order_pay_log" dataNode="dn2" primaryKey="out_trade_no" />

  <table name="tb_user" dataNode="dn3" primaryKey="id" />
  <table name="tb_user_address" dataNode="dn3" primaryKey="id" />

  <table name="tb_areas_provinces" dataNode="dn3" primaryKey="id"/>
  <table name="tb_areas_city" dataNode="dn3" primaryKey="id"/>
  <table name="tb_areas_region" dataNode="dn3" primaryKey="id"/>
</schema>

<dataNode name="dn1" dataHost="dhost1" database="shopping" />
<dataNode name="dn2" dataHost="dhost2" database="shopping" />
<dataNode name="dn3" dataHost="dhost3" database="shopping" />

<dataHost name="dhost1" maxCon="1000" minCon="10" balance="0" writeType="0" dbType="mysql" dbDriver="jdbc" switchType="1"  slaveThreshold="100">
  <heartbeat>select user()</heartbeat>
  <writeHost host="master" url="jdbc:mysql://192.168.200.210:3306?useSSL=false&amp;serverTimezone=Asia/Shanghai&amp;characterEncoding=utf8" user="root" password="1234" /></dataHost>

<dataHost name="dhost2" maxCon="1000" minCon="10" balance="0" writeType="0" dbType="mysql" dbDriver="jdbc" switchType="1"  slaveThreshold="100">
  <heartbeat>select user()</heartbeat>
  <writeHost host="master" url="jdbc:mysql://192.168.200.213:3306?useSSL=false&amp;serverTimezone=Asia/Shanghai&amp;characterEncoding=utf8" user="root" password="1234" /></dataHost>

<dataHost name="dhost3" maxCon="1000" minCon="10" balance="0" writeType="0" dbType="mysql" dbDriver="jdbc" switchType="1"  slaveThreshold="100">
  <heartbeat>select user()</heartbeat>
  <writeHost host="master" url="jdbc:mysql://192.168.200.214:3306?useSSL=false&amp;serverTimezone=Asia/Shanghai&amp;characterEncoding=utf8" user="root" password="1234" />
</dataHost>
```

### server.xml

```xml
<user name="root" defaultAccount="true">
  <property name="password">123456</property>
  <property name="schemas">SHOPPING</property>

  <!-- 表级 DML 权限设置 -->
  <!--  
  <privileges check="true">
  <schema name="DB01" dml="0110" >
  <table name="TB_ORDER" dml="1110"></table>
</schema>
</privileges>
  -->
</user>

<user name="user">
  <property name="password">123456</property>
  <property name="schemas">SHOPPING</property>
  <property name="readOnly">true</property>
</user>
```

## 4. 测试

### 上传测试SQL脚本到服务器的/root目录

![img](/blogs/_archive-2024-assets/3d9dc8f91092a42b1d97.webp)

### 执行指令导入测试数据

重新启动MyCat后，在mycat的命令行中，通过source指令导入表结构，以及对应的数据，查看数据分布

情况。

```plain
source /root/shopping-table.sql

source /root/shopping-insert.sql
```

将表结构及对应的测试数据导入之后，可以检查一下各个数据库服务器中的表结构分布情况。 

检查是否和我们准备工作中规划的服务器一致。

![img](/blogs/_archive-2024-assets/4d94c01a2f64fb89c5b8.webp)

### 查询用户的收件人及收件人地址信息(包含省、市、区)

在MyCat的命令行中，当我们执行以下多表联查的SQL语句时，可以正常查询出数据。

```sql
select ua.user_id, ua.contact, p.province, c.city, r.area , ua.address from tb_user_address 
ua ,tb_areas_city c , tb_areas_provinces p ,tb_areas_region r where ua.province_id = p.provinceid 
and ua.city_id = c.cityid and ua.town_id = r.areaid ;
```

![img](/blogs/_archive-2024-assets/74924bed998d2391cbe5.webp)

### 查询每一笔订单及订单的收件地址信息(包含省、市、区)

实现该需求对应的SQL语句如下：

```plain
SELECT order_id , payment ,receiver, province , city , area FROM tb_order_master o , tb_areas_provinces p ,
tb_areas_city c , tb_areas_region r WHERE o.receiver_province = p.provinceid AND o.receiver_city = c.cityid 
AND o.receiver_region = r.areaid ;
```

但是现在存在一个问题，订单相关的表结构是在 192.168.200.213 数据库服务器中，

而省市区的数据库表是在 192.168.200.214 数据库服务器中。

那么在MyCat中执行是否可以成功呢？

![img](/blogs/_archive-2024-assets/67abcb824b6a30d4daa0.webp)

经过测试，我们看到，SQL语句执行报错。原因就是因为MyCat在执行该SQL语句时，

需要往具体的数据库服务器中路由，而当前没有一个数据库服务器完全包含了订单以及省市区的表结构，

造成SQL语句失败，报错。

**对于上述的这种现象，我们如何来解决呢？** 

下面我们介绍的全局表，就可以轻松解决这个问题。

### 1.5 全局表

对于省、市、区/县表tb_areas_provinces, tb_areas_city , tb_areas_region，是属于数据字典表，

在多个业务模块中都可能会遇到，可以将其设置为全局表，利于业务操作。

修改schema.xml中的逻辑表的配置，修改 tb_areas_provinces、tb_areas_city、tb_areas_region 三个逻辑表，增加 type 属

性，配置为global，就代表该表是全局表，就会在所涉及到的dataNode中创建给表。

对于当前配置来说，也就意味着所有的节点中都有该表了。

```plain
<table name="tb_areas_provinces" dataNode="dn1,dn2,dn3" primaryKey="id" type="global"/>

<table name="tb_areas_city" dataNode="dn1,dn2,dn3" primaryKey="id"  type="global"/>

<table name="tb_areas_region" dataNode="dn1,dn2,dn3" primaryKey="id"  type="global"/>
```

配置完毕后，重新启动MyCat。

1. 删除原来每一个数据库服务器中的所有表结构
2. 通过source指令，导入表及数据

```plain
source /root/shopping-table.sql
source /root/shopping-insert.sql
```

1. 检查每一个数据库服务器中的表及数据分布，看到三个节点中都有这三张全局表
2. 然后再次执行上面的多表联查的SQL语句

```plain
SELECT order_id , payment ,receiver, province , city , area FROM tb_order_master o , tb_areas_provinces p , 
tb_areas_city c , tb_areas_region r WHERE o.receiver_province = p.provinceid AND o.receiver_city = c.cityid 
AND o.receiver_region = r.areaid ;
```

是可以正常执行成功的。

1. 当在MyCat中更新全局表的时候，我们可以看到，所有分片节点中的数据都发生了变化，每个节点的全局表数据时刻保持一致。

# 二、水平拆分

## 1. 场景

在业务系统中, 有一张表(日志表), 业务系统每天都会产生大量的日志数据 , 

单台服务器的数据存储及处理能力是有限的, 可以对数据库表进行拆分。

## 2. 准备

准备三台服务器，具体的结构如下：

并且，在三台数据库服务器中分表创建一个数据库yjxz。

## 3. 配置

### schema.xml

```xml
<schema name="ITCAST" checkSQLschema="true" sqlMaxLimit="100">
  <table name="tb_log" dataNode="dn4,dn5,dn6" primaryKey="id" rule="mod-long" />
</schema>

<dataNode name="dn4" dataHost="dhost1" database="yjxz" />
<dataNode name="dn5" dataHost="dhost2" database="yjxz" />
<dataNode name="dn6" dataHost="dhost3" database="yjxz" />
```

tb_log表最终落在3个节点中，分别是 dn4、dn5、dn6 ，而具体的数据分别存储在 dhost1、dhost2、

dhost3的 itcast 数据库中。

### server.xml

配置root用户既可以访问 SHOPPING 逻辑库，又可以访问yjxz逻辑库。

```plain
<user name="root" defaultAccount="true">
	<property name="password">123456</property>
	<property name="schemas">SHOPPING,ITCAST</property>
	
	<!-- 表级 DML 权限设置 -->
		<!--
			<privileges check="true">
				<schema name="DB01" dml="0110" >
					<table name="TB_ORDER" dml="1110"></table>
				</schema>
			</privileges>
		-->
</user>
```

## 4. 测试

配置完毕后，重新启动MyCat，然后在mycat的命令行中，执行如下SQL创建表、并插入数据，查看数据分

布情况。

```sql
CREATE TABLE tb_log (
  id bigint(20) NOT NULL COMMENT 'ID',
  model_name varchar(200) DEFAULT NULL COMMENT '模块名',
  model_value varchar(200) DEFAULT NULL COMMENT '模块值',
  return_value varchar(200) DEFAULT NULL COMMENT '返回值',
  return_class varchar(200) DEFAULT NULL COMMENT '返回值类型',
  operate_user varchar(20) DEFAULT NULL COMMENT '操作用户',
  operate_time varchar(20) DEFAULT NULL COMMENT '操作时间',
  param_and_value varchar(500) DEFAULT NULL COMMENT '请求参数名及参数值',
  operate_class varchar(200) DEFAULT NULL COMMENT '操作类',
  operate_method varchar(200) DEFAULT NULL COMMENT '操作方法',
  cost_time bigint(20) DEFAULT NULL COMMENT '执行方法耗时, 单位 ms',
  source int(1) DEFAULT NULL COMMENT '来源 : 1 PC , 2 Android , 3 IOS',
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO tb_log (id, model_name, model_value, return_value, return_class, operate_user, operate_time, param_and_value, operate_class, operate_method, cost_time，source) VALUES('1','user','insert','success','java.lang.String','10001','2022-01-06 18:12:28','{\"age\":\"20\",\"name\":\"Tom\",\"gender\":\"1\"}','com.yj.nz.controller.UserController','insert','10',1);
INSERT INTO tb_log (id, model_name, model_value, return_value, return_class, operate_user, operate_time, param_and_value, operate_class, operate_method, cost_time，source) VALUES('2','user','insert','success','java.lang.String','10001','2022-01-06 18:12:27','{\"age\":\"20\",\"name\":\"Tom\",\"gender\":\"1\"}','com.yj.nz.controller.UserController','insert','23',1);
INSERT INTO tb_log (id, model_name, model_value, return_value, return_class, operate_user, operate_time, param_and_value, operate_class, operate_method, cost_time，source) VALUES('3','user','update','success','java.lang.String','10001','2022-01-06 18:16:45','{\"age\":\"20\",\"name\":\"Tom\",\"gender\":\"1\"}','com.yj.nz.controller.UserController','update','34',1);
INSERT INTO tb_log (id, model_name, model_value, return_value, return_class, operate_user, operate_time, param_and_value, operate_class, operate_method, cost_time，source) VALUES('4','user','update','success','java.lang.String','10001','2022-01-06 18:16:45','{\"age\":\"20\",\"name\":\"Tom\",\"gender\":\"1\"}','com.yj.nz.controller.UserController','update','13',2);
INSERT INTO tb_log (id, model_name, model_value, return_value, return_class, operate_user, operate_time, param_and_value, operate_class, operate_method, cost_time，source) VALUES('5','user','insert','success','java.lang.String','10001','2022-01-06 18:30:31','{\"age\":\"200\",\"name\":\"TomCat\",\"gender\":\"0\"}','com.yj.nz.controller.UserController','insert','29',3);
INSERT INTO tb_log (id, model_name, model_value, return_value, return_class, operate_user, operate_time, param_and_value, operate_class, operate_method, cost_time，source) VALUES('6','user','find','success','java.lang.String','10001','2022-01-06 18:30:31','{\"age\":\"200\",\"name\":\"TomCat\",\"gender\":\"0\"}','com.yj.nz.controller.UserController','find','29',2);
```

# 三、分片规则

## 1. 范围分片

### 1.1. 简介

根据指定的字段及其配置的范围与数据节点的对应情况， 来决定该数据属于哪一个分片。

![img](/blogs/_archive-2024-assets/c10b979869b8cab04620.webp)

### 1.2. 配置

schema.xml逻辑表配置： 

```xml
<table name="TB_ORDER" dataNode="dn1,dn2,dn3" rule="auto-sharding-long" />
```

schema.xml数据节点配置：

```xml
<dataNode name="dn1" dataHost="dhost1" database="db01" />
<dataNode name="dn2" dataHost="dhost2" database="db01" />
<dataNode name="dn3" dataHost="dhost3" database="db01" />
```

rule.xml分片规则配置：

```xml
<tableRule name="auto-sharding-long">
  <rule>
    <columns>id</columns>
    <algorithm>rang-long</algorithm>
  </rule>
</tableRule>

<function name="rang-long" class="io.mycat.route.function.AutoPartitionByLong">
  <property name="mapFile">autopartition-long.txt</property>
  <property name="defaultNode">0</property>
</function>
```

### 1.3. 分片规则属性含义

| **属性**    | **描述**                                                     |
| ----------- | ------------------------------------------------------------ |
| columns     | 标识将要分片的表字段                                         |
| algorithm   | 指定分片函数与function的对应关系                             |
| class       | 指定该分片算法对应的类                                       |
| mapFile     | 对应的外部配置文件                                           |
| type        | 默认值为0 ; 0 表示Integer , 1 表示String                     |
| defaultNode | 默认节点 默认节点的所用:枚举分片时,如果碰到不识别的枚举值, 就让它路 由到默认节点 ; 如果没有默认值,碰到不识别的则报错 。 |

在rule.xml中配置分片规则时，关联了一个映射配置文件 autopartition-long.txt，该配置文件的配置如下：

```plain
# range start-end ,data node index
# K=1000,M=10000.

0-500M=0
500M-1000M=1
1000M-1500M=2
```

**含义：**

0-500万之间的值，存储在0号数据节点(数据节点的索引从0开始) ； 

500万-1000万之间的数据存储在1号数据节点；

1000万-1500万的数据节点存储在2号节点 ；

该分片规则，主要是针对于数字类型的字段适用。 在MyCat的入门程序中，我们使用的就是该分片规则。

## 2. 取模分片

### 2.1. 简介

根据指定的字段值与节点数量进行求模运算，根据运算结果， 来决定该数据属于哪一个分片。

![img](/blogs/_archive-2024-assets/d9b8f22af56b80b67bf8.webp)

### 2.2. 配置

schema.xml逻辑表配置：

```xml
<table name="tb_log" dataNode="dn4,dn5,dn6" primaryKey="id" rule="mod-long" />
```

schema.xml数据节点配置：

```xml
<dataNode name="dn4" dataHost="dhost1" database="yjxz" />
<dataNode name="dn5" dataHost="dhost2" database="yjxz" />
<dataNode name="dn6" dataHost="dhost3" database="yjxz" />
```

rule.xml分片规则配置：

```xml
<tableRule name="mod-long">
  <rule>
    <columns>id</columns>
    <algorithm>mod-long</algorithm>
  </rule>
</tableRule>

<function name="mod-long" class="io.mycat.route.function.PartitionByMod">
  <property name="count">3</property>
</function>
```

### 2.3. 分片规则属性含义

| **属性**  | **描述**                         |
| --------- | -------------------------------- |
| columns   | 标识将要分片的表字段             |
| algorithm | 指定分片函数与function的对应关系 |
| class     | 指定该分片算法对应的类           |
| count     | 数据节点的数量                   |

该分片规则，主要是针对于数字类型的字段适用。 在前面水平拆分的演示中，我们选择的就是取模分片。

### 2.4. 测试

配置完毕后，重新启动MyCat，然后在mycat的命令行中，执行如下SQL创建表、并插入数据，查看数据分布情况。

## 3. 一致性hash分片

### 3.1. 简介

所谓一致性哈希，相同的哈希因子计算值总是被划分到相同的分区表中，不会因为分区节点的增加而改变

原来数据的分区位置，有效的解决了分布式数据的拓容问题。

![img](/blogs/_archive-2024-assets/c4c107ca1b03f52342f0.webp)

### 3.2. 配置

schema.xml中逻辑表配置：

```xml
<!-- 一致性hash -->
<table name="tb_order" dataNode="dn4,dn5,dn6" rule="sharding-by-murmur" />
```

schema.xml中数据节点配置：

```plain
<dataNode name="dn4" dataHost="dhost1" database="yjxz" />
<dataNode name="dn5" dataHost="dhost2" database="yjxz" />
<dataNode name="dn6" dataHost="dhost3" database="yjxz" />
```

rule.xml中分片规则配置：

```xml
<tableRule name="sharding-by-murmur">
  <rule>
    <columns>id</columns>
    <algorithm>murmur</algorithm>
  </rule>
</tableRule>

<function name="murmur" class="io.mycat.route.function.PartitionByMurmurHash">
  <property name="seed">0</property><!-- 默认是0 -->
  <property name="count">3</property>
  <property name="virtualBucketTimes">160</property>
</function>
```

### 3.3. 分片规则属性含义

| **属性**           | **描述**                                                     |
| ------------------ | ------------------------------------------------------------ |
| columns            | 标识将要分片的表字段                                         |
| algorithm          | 指定分片函数与function的对应关系                             |
| class              | 指定该分片算法对应的类                                       |
| seed               | 创建murmur_hash对象的种子，默认0                             |
| count              | 要分片的数据库节点数量，必须指定，否则没法分片               |
| virtualBucketTimes | 一个实际的数据库节点被映射为这么多虚拟节点，默认是160倍，也 就是虚拟节点数是物理节点数的160倍;virtualBucketTimes*count就是虚拟结点数量 ; |
| weightMapFile      | 节点的权重，没有指定权重的节点默认是1。以properties文件的 格式填写，以从0开始到count-1的整数值也就是节点索引为key， 以节点权重值为值。所有权重值必须是正整数，否则以1代替 |
| bucketMapPath      | 用于测试时观察各物理节点与虚拟节点的分布情况，如果指定了这个 属性，会把虚拟节点的murmur hash值与物理节点的映射按行输出 到这个文件，没有默认值，如果不指定，就不会输出任何东西 |

### 3.4. 测试

配置完毕后，重新启动MyCat，然后在mycat的命令行中，执行如下SQL创建表、并插入数据，查看数据分

布情况。

```sql
create table tb_order(
  id  varchar(100) not null primary key,
  money   int null,
  content varchar(200) null
);


INSERT INTO tb_order (id, money, content) VALUES ('b92fdaaf-6fc4-11ec-b831-482ae33c4a2d', 10, 'b92fdaf8-6fc4-11ec-b831-482ae33c4a2d');
INSERT INTO tb_order (id, money, content) VALUES ('b93482b6-6fc4-11ec-b831-482ae33c4a2d', 20, 'b93482d5-6fc4-11ec-b831-482ae33c4a2d');
INSERT INTO tb_order (id, money, content) VALUES ('b937e246-6fc4-11ec-b831-482ae33c4a2d', 50, 'b937e25d-6fc4-11ec-b831-482ae33c4a2d');
INSERT INTO tb_order (id, money, content) VALUES ('b93be2dd-6fc4-11ec-b831-482ae33c4a2d', 100, 'b93be2f9-6fc4-11ec-b831-482ae33c4a2d');
INSERT INTO tb_order (id, money, content) VALUES ('b93f2d68-6fc4-11ec-b831-482ae33c4a2d', 130, 'b93f2d7d-6fc4-11ec-b831-482ae33c4a2d');
INSERT INTO tb_order (id, money, content) VALUES ('b9451b98-6fc4-11ec-b831-482ae33c4a2d', 30, 'b9451bcc-6fc4-11ec-b831-482ae33c4a2d');
INSERT INTO tb_order (id, money, content) VALUES ('b9488ec1-6fc4-11ec-b831-482ae33c4a2d', 560, 'b9488edb-6fc4-11ec-b831-482ae33c4a2d');
INSERT INTO tb_order (id, money, content) VALUES ('b94be6e6-6fc4-11ec-b831-482ae33c4a2d', 10, 'b94be6ff-6fc4-11ec-b831-482ae33c4a2d');
INSERT INTO tb_order (id, money, content) VALUES ('b94ee10d-6fc4-11ec-b831-482ae33c4a2d', 123, 'b94ee12c-6fc4-11ec-b831-482ae33c4a2d');
INSERT INTO tb_order (id, money, content) VALUES ('b952492a-6fc4-11ec-b831-482ae33c4a2d', 145, 'b9524945-6fc4-11ec-b831-482ae33c4a2d');
INSERT INTO tb_order (id, money, content) VALUES ('b95553ac-6fc4-11ec-b831-482ae33c4a2d', 543, 'b95553c8-6fc4-11ec-b831-482ae33c4a2d');
INSERT INTO tb_order (id, money, content) VALUES ('b9581cdd-6fc4-11ec-b831-482ae33c4a2d', 17, 'b9581cfa-6fc4-11ec-b831-482ae33c4a2d');
INSERT INTO tb_order (id, money, content) VALUES ('b95afc0f-6fc4-11ec-b831-482ae33c4a2d', 18, 'b95afc2a-6fc4-11ec-b831-482ae33c4a2d');
INSERT INTO tb_order (id, money, content) VALUES ('b95daa99-6fc4-11ec-b831-482ae33c4a2d', 134, 'b95daab2-6fc4-11ec-b831-482ae33c4a2d');
INSERT INTO tb_order (id, money, content) VALUES ('b9667e3c-6fc4-11ec-b831-482ae33c4a2d', 156, 'b9667e60-6fc4-11ec-b831-482ae33c4a2d');
INSERT INTO tb_order (id, money, content) VALUES ('b96ab489-6fc4-11ec-b831-482ae33c4a2d', 175, 'b96ab4a5-6fc4-11ec-b831-482ae33c4a2d');
INSERT INTO tb_order (id, money, content) VALUES ('b96e2942-6fc4-11ec-b831-482ae33c4a2d', 180, 'b96e295b-6fc4-11ec-b831-482ae33c4a2d');
INSERT INTO tb_order (id, money, content) VALUES ('b97092ec-6fc4-11ec-b831-482ae33c4a2d', 123, 'b9709306-6fc4-11ec-b831-482ae33c4a2d');
INSERT INTO tb_order (id, money, content) VALUES ('b973727a-6fc4-11ec-b831-482ae33c4a2d', 230, 'b9737293-6fc4-11ec-b831-482ae33c4a2d');
INSERT INTO tb_order (id, money, content) VALUES ('b978840f-6fc4-11ec-b831-482ae33c4a2d', 560, 'b978843c-6fc4-11ec-b831-482ae33c4a2d');
```

## 4. 枚举分片

### 4.1. 简介

通过在配置文件中配置可能的枚举值, 指定数据分布到不同数据节点上, 本规则适用于按照省份、性别、状

态拆分数据等业务 。

![img](/blogs/_archive-2024-assets/0522b07564a3f6e0e96d.webp)

### 4.2. 配置

schema.xml中逻辑表配置：

```xml
<!-- 枚举 -->
<table name="tb_user" dataNode="dn4,dn5,dn6" rule="sharding-by-intfile-enumstatus" />
```

schema.xml中数据节点配置：

```xml
<dataNode name="dn4" dataHost="dhost1" database="yjxz" />
<dataNode name="dn5" dataHost="dhost2" database="yjxz" />
<dataNode name="dn6" dataHost="dhost3" database="yjxz" />
```

rule.xml中分片规则配置：

```xml
<tableRule name="sharding-by-intfile">
  <rule>
    <columns>sharding_id</columns>
    <algorithm>hash-int</algorithm>
  </rule>
</tableRule>

<!-- 自己增加 tableRule -->
<tableRule name="sharding-by-intfile-enumstatus">
  <rule>
    <columns>status</columns>
    <algorithm>hash-int</algorithm>
  </rule>
</tableRule>

<function name="hash-int" class="io.mycat.route.function.PartitionByFileMap">
  <property name="defaultNode">2</property>
  <property name="mapFile">partition-hash-int.txt</property>
</function>
```

partition-hash-int.txt ，内容如下 :

```properties
1=0
2=1
3=2
```

### 4.3. 分片规则属性含义

| **属性**    | **描述**                                                     |
| ----------- | ------------------------------------------------------------ |
| columns     | 标识将要分片的表字段                                         |
| algorithm   | 指定分片函数与function的对应关系                             |
| class       | 指定该分片算法对应的类                                       |
| mapFile     | 对应的外部配置文件                                           |
| type        | 默认值为0 ; 0 表示Integer , 1 表示String                     |
| defaultNode | 默认节点 ; 小于0 标识不设置默认节点 , 大于等于0代表设置默认节点 ;默认节点的所用:枚举分片时,如果碰到不识别的枚举值, 就让它路由到默认节 点 ; 如果没有默认值,碰到不识别的则报错 。 |

### 4.4. 测试

配置完毕后，重新启动MyCat，然后在mycat的命令行中，执行如下SQL创建表、并插入数据，查看数据分

布情况。

```sql
CREATE TABLE tb_user (
  id bigint(20) NOT NULL COMMENT 'ID',
  username varchar(200) DEFAULT NULL COMMENT '姓名',
  status int(2) DEFAULT '1' COMMENT '1: 未启用, 2: 已启用, 3: 已关闭',
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


insert into tb_user (id,username ,status) values(1,'Tom',1);
insert into tb_user (id,username ,status) values(2,'Cat',2);
insert into tb_user (id,username ,status) values(3,'Rose',3);
insert into tb_user (id,username ,status) values(4,'Coco',2);
insert into tb_user (id,username ,status) values(5,'Lily',1);
insert into tb_user (id,username ,status) values(6,'Tom',1);
insert into tb_user (id,username ,status) values(7,'Cat',2);
insert into tb_user (id,username ,status) values(8,'Rose',3);
insert into tb_user (id,username ,status) values(9,'Coco',2);
insert into tb_user (id,username ,status) values(10,'Lily',1);
```

## 5. 应用指定算法

### 5.1. 简介

运行阶段由应用自主决定路由到那个分片 , 直接根据字符子串（必须是数字）计算分片号。

![img](/blogs/_archive-2024-assets/7202057d7dc569058afb.webp)

### 5.2. 配置

schema.xml中逻辑表配置：

```xml
<!-- 应用指定算法 -->
<table name="tb_app" dataNode="dn4,dn5,dn6" rule="sharding-by-substring" />
```

schema.xml中数据节点配置：

```xml
<dataNode name="dn4" dataHost="dhost1" database="yjxz" />
<dataNode name="dn5" dataHost="dhost2" database="yjxz" />
<dataNode name="dn6" dataHost="dhost3" database="yjxz" />
```

rule.xml中分片规则配置：

```xml
<tableRule name="sharding-by-substring">
  <rule>
    <columns>id</columns>
    <algorithm>sharding-by-substring</algorithm>
  </rule>
</tableRule>

<function name="sharding-by-substring" class="io.mycat.route.function.PartitionDirectBySubString">
  <property name="startIndex">0</property><!-- zero-based -->
  <property name="size">2</property>
  <property name="partitionCount">3</property>
  <property name="defaultPartition">0</property>
</function>
```

### 5.3. 分片规则属性含义

| **属性**         | **描述**                                                     |
| ---------------- | ------------------------------------------------------------ |
| columns          | 标识将要分片的表字段                                         |
| algorithm        | 指定分片函数与function的对应关系                             |
| class            | 指定该分片算法对应的类                                       |
| startIndex       | 字符子串起始索引                                             |
| size             | 字符长度                                                     |
| partitionCount   | 分区(分片)数量                                               |
| defaultPartition | 默认分片(在分片数量定义时, 字符标示的分片编号不在分片数量内时, |

### 5.4. 示例说明 

id=05-100000002 , 在此配置中代表根据id中从 startIndex=0，开始，截取size=2位数字即05，

05就是获取的分区，如果没找到对应的分片则默认分配到defaultPartition。

### 5.5. 测试

配置完毕后，重新启动MyCat，然后在mycat的命令行中，执行如下SQL创建表、并插入数据，查看数据分

布情况。

```sql
CREATE TABLE tb_app (
  id varchar(10) NOT NULL COMMENT 'ID',
  name varchar(200) DEFAULT NULL COMMENT '名称',
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



insert into tb_app (id,name) values('0000001','Testx00001');
insert into tb_app (id,name) values('0100001','Test100001');
insert into tb_app (id,name) values('0100002','Test200001');
insert into tb_app (id,name) values('0200001','Test300001');
insert into tb_app (id,name) values('0200002','TesT400001');
```

## 6. 固定分片hash算法

### 6.1. 简介

该算法类似于十进制的求模运算，但是为二进制的操作，

例如，取 id 的二进制低 10 位 与 1111111111 进行位 & 运算，位与运算最小值为 0000000000，最大值

为1111111111，转换为十进制，也就是位于0-1023之间。

![img](/blogs/_archive-2024-assets/32ace3015364e81dd967.webp)

### 6.2. 特点

特点：

1. 如果是求模，连续的值，分别分配到各个不同的分片；但是此算法会将连续的值可能分配到相同的 分片，降低事务处理的难度。
2. 可以均匀分配，也可以非均匀分配。
3. 分片字段必须为数字类型。

### 6.3. 配置

schema.xml中逻辑表配置：

```xml
<!-- 固定分片hash算法 -->
<table name="tb_longhash" dataNode="dn4,dn5,dn6" rule="sharding-by-long-hash" />
```

schema.xml中数据节点配置：

```xml
<dataNode name="dn4" dataHost="dhost1" database="itcast" />

<dataNode name="dn5" dataHost="dhost2" database="itcast" />

<dataNode name="dn6" dataHost="dhost3" database="itcast" />
```

rule.xml中分片规则配置：

```xml
<tableRule name="sharding-by-long-hash">
  <rule>
    <columns>id</columns>
    <algorithm>sharding-by-long-hash</algorithm>
  </rule>
</tableRule>

<!-- 分片总长度为1024，count与length数组长度必须一致； -->
<function name="sharding-by-long-hash" class="io.mycat.route.function.PartitionByLong">
  <property name="partitionCount">2,1</property>
  <property name="partitionLength">256,512</property>
</function>
```

### 6.4. 分片规则属性含义

| **属性**        | **描述**                         |
| --------------- | -------------------------------- |
| columns         | 标识将要分片的表字段             |
| algorithm       | 指定分片函数与function的对应关系 |
| class           | 指定该分片算法对应的类           |
| partitionCount  | 分片个数列表                     |
| partitionLength | 分片范围列表                     |

约束 : 

1. 分片长度 : 默认最大2^10 , 为 1024 ;
2. count, length的数组长度必须是一致的 ;

以上分为三个分区:0-255,256-511,512-1023

示例说明 : 

![img](/blogs/_archive-2024-assets/cfbcc8e14120b3238462.webp)

### 6.5. 测试

配置完毕后，重新启动MyCat，然后在mycat的命令行中，执行如下SQL创建表、并插入数据，查看数 据

分布情况。

```plain
CREATE TABLE tb_longhash (
    id int(11) NOT NULL COMMENT 'ID',
 	name varchar(200) DEFAULT NULL COMMENT '名称',
 	firstChar char(1) COMMENT '首字母',
 	PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

insert into tb_longhash (id,name,firstChar) values(1,'七匹狼','Q');

insert into tb_longhash (id,name,firstChar) values(2,'八匹狼','B');

insert into tb_longhash (id,name,firstChar) values(3,'九匹狼','J');

insert into tb_longhash (id,name,firstChar) values(4,'十匹狼','S');

insert into tb_longhash (id,name,firstChar) values(5,'六匹狼','L');

insert into tb_longhash (id,name,firstChar) values(6,'五匹狼','W');

insert into tb_longhash (id,name,firstChar) values(7,'四匹狼','S');

insert into tb_longhash (id,name,firstChar) values(8,'三匹狼','S');

insert into tb_longhash (id,name,firstChar) values(9,'两匹狼','L');
```

## 7. 字符串hash解析算法

### 7.1. 简介

截取字符串中的指定位置的子字符串, 进行hash算法， 算出分片。

![img](/blogs/_archive-2024-assets/9ef2f80fa67a6d584fdb.webp)

### 7.2. 配置

schema.xml中逻辑表配置：

```xml
<!-- 字符串hash解析算法 -->
<table name="tb_strhash" dataNode="dn4,dn5" rule="sharding-by-stringhash" />
```

schema.xml中数据节点配置：

```xml
<dataNode name="dn4" dataHost="dhost1" database="itcast" />
<dataNode name="dn5" dataHost="dhost2" database="itcast" />
```

rule.xml中分片规则配置：

```xml
<tableRule name="sharding-by-stringhash">
  <rule>
    <columns>name</columns>
    <algorithm>sharding-by-stringhash</algorithm>
  </rule>
</tableRule>
<function name="sharding-by-stringhash" class="io.mycat.route.function.PartitionByString">
  <property name="partitionLength">512</property> <!-- zero-based -->
  <property name="partitionCount">2</property>
  <property name="hashSlice">0:2</property>
</function>
```

### 7.3. 分片规则属性含义

| **属性**        | **描述**                                                     |
| --------------- | ------------------------------------------------------------ |
| columns         | 标识将要分片的表字段                                         |
| algorithm       | 指定分片函数与function的对应关系                             |
| class           | 指定该分片算法对应的类                                       |
| partitionLength | hash求模基数 ; length*count=1024 (出于性能考虑)              |
| partitionCount  | 分区数                                                       |
| hashSlice       | hash运算位 , 根据子字符串的hash运算 ; 0 代表 str.length() , -1 代表 str.length()-1 , 大于0只代表数字自身 ; 可以理解 为substring（start，end），start为0则只表示0 |

示例说明：

![img](/blogs/_archive-2024-assets/6cbe96cedca9a326b8a1.webp)

### 7.4. 测试

配置完毕后，重新启动MyCat，然后在mycat的命令行中，执行如下SQL创建表、并插入数据，查看数 据分布情况。

```plsql
create table tb_strhash(
  name varchar(20) primary key,
  content varchar(100)
)engine=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO tb_strhash (name,content) VALUES('T1001', UUID());

INSERT INTO tb_strhash (name,content) VALUES('ROSE', UUID());

INSERT INTO tb_strhash (name,content) VALUES('JERRY', UUID());

INSERT INTO tb_strhash (name,content) VALUES('CRISTINA', UUID());

INSERT INTO tb_strhash (name,content) VALUES('TOMCAT', UUID());
```

## 8. 按天分片算法

### 8.1. 简介

按照日期及对应的时间周期来分片。

### 8.2. 配置

schema.xml中逻辑表配置：

```xml
<!-- 按天分片 -->
<table name="tb_datepart" dataNode="dn4,dn5,dn6" rule="sharding-by-date" />
```

schema.xml中数据节点配置：

```xml
<dataNode name="dn4" dataHost="dhost1" database="itcast" />
<dataNode name="dn5" dataHost="dhost2" database="itcast" />
<dataNode name="dn6" dataHost="dhost3" database="itcast" />
```

rule.xml中分片规则配置：

```xml
<tableRule name="sharding-by-date">
  <rule>
    <columns>create_time</columns>
    <algorithm>sharding-by-date</algorithm>
  </rule>
</tableRule>
<function name="sharding-by-date" class="io.mycat.route.function.PartitionByDate">
  <property name="dateFormat">yyyy-MM-dd</property>
  <property name="sBeginDate">2022-01-01</property>
  <property name="sEndDate">2022-01-30</property>
  <property name="sPartionDay">10</property>
</function>

<!--
从开始时间开始，每10天为一个分片，到达结束时间之后，会重复开始分片插入
配置表的 dataNode 的分片，必须和分片规则数量一致，例如 2022-01-01 到 2022-12-31 ，
每10天一个分片，一共需要37个分片。
-->
```

### 8.3. 分片规则属性含义

| **属性**    | **描述**                                                     |
| ----------- | ------------------------------------------------------------ |
| columns     | 标识将要分片的表字段                                         |
| algorithm   | 指定分片函数与function的对应关系                             |
| class       | 指定该分片算法对应的类                                       |
| dateFormat  | 日期格式                                                     |
| sBeginDate  | 开始日期                                                     |
| sEndDate    | 结束日期，如果配置了结束日期，则代码数据到达了这个日期的分片后，会重 复从开始分片插入 |
| sPartionDay | 分区天数，默认值 10 ，从开始日期算起，每个10天一个分区       |

### 8.4. 测试

配置完毕后，重新启动MyCat，然后在mycat的命令行中，执行如下SQL创建表、并插入数据，

查看数据分布情况。

```sql
create table tb_datepart(
  id bigint not null comment 'ID' primary key,
  name varchar(100) null comment '姓名',
  create_time date null
);

insert into tb_datepart(id,name ,create_time) values(1,'Tom','2022-01-01');
insert into tb_datepart(id,name ,create_time) values(2,'Cat','2022-01-10');
insert into tb_datepart(id,name ,create_time) values(3,'Rose','2022-01-11');
insert into tb_datepart(id,name ,create_time) values(4,'Coco','2022-01-20');
insert into tb_datepart(id,name ,create_time) values(5,'Rose2','2022-01-21');
insert into tb_datepart(id,name ,create_time) values(6,'Coco2','2022-01-30');
insert into tb_datepart(id,name ,create_time) values(7,'Coco3','2022-01-31');
```

## 9. 自然月分片

### 9.1. 简介

使用场景为按照月份来分片, 每个自然月为一个分片。

![img](/blogs/_archive-2024-assets/840cf68ac5e60340d051.webp)

### 9.2. 配置

schema.xml中逻辑表配置：

```xml
<!-- 按自然月分片 -->
<table name="tb_monthpart" dataNode="dn4,dn5,dn6" rule="sharding-by-month" />
```

schema.xml中数据节点配置：

```xml
<dataNode name="dn4" dataHost="dhost1" database="itcast" />
<dataNode name="dn5" dataHost="dhost2" database="itcast" />
<dataNode name="dn6" dataHost="dhost3" database="itcast" />
```

rule.xml中分片规则配置：

```xml
<tableRule name="sharding-by-month">
  <rule>
    <columns>create_time</columns>
    <algorithm>partbymonth</algorithm>
  </rule>
</tableRule>

<function name="partbymonth" class="io.mycat.route.function.PartitionByMonth">
  <property name="dateFormat">yyyy-MM-dd</property>
  <property name="sBeginDate">2022-01-01</property>
  <property name="sEndDate">2022-03-31</property>
</function>
<!-- 
从开始时间开始，一个月为一个分片，到达结束时间之后，会重复开始分片插入
配置表的 dataNode 的分片，必须和分片规则数量一致，例如 2022-01-01 到 2022-12-31 ，一共需要12个分片。
-->
```

### 9.3. 分片规则属性含义

| **属性**   | **描述**                                                     |
| ---------- | ------------------------------------------------------------ |
| columns    | 标识将要分片的表字段                                         |
| algorithm  | 指定分片函数与function的对应关系                             |
| class      | 指定该分片算法对应的类                                       |
| dateFormat | 日期格式                                                     |
| sBeginDate | 开始日期                                                     |
| sEndDate   | 结束日期，如果配置了结束日期，则代码数据到达了这个日期的分片后，会重 复从开始分片插入 |

### 9.4. 测试

配置完毕后，重新启动MyCat，然后在mycat的命令行中，执行如下SQL创建表、并插入数据，查看数据分

布情况。

```sql
create table tb_monthpart(
  id bigint not null comment 'ID' primary key,
  name varchar(100) null comment '姓名',
  create_time date null
);

insert into tb_monthpart(id,name ,create_time) values(1,'Tom','2022-01-01');
insert into tb_monthpart(id,name ,create_time) values(2,'Cat','2022-01-10');
insert into tb_monthpart(id,name ,create_time) values(3,'Rose','2022-01-31');
insert into tb_monthpart(id,name ,create_time) values(4,'Coco','2022-02-20');
insert into tb_monthpart(id,name ,create_time) values(5,'Rose2','2022-02-25');
insert into tb_monthpart(id,name ,create_time) values(6,'Coco2','2022-03-10');
insert into tb_monthpart(id,name ,create_time) values(7,'Coco3','2022-03-31');
insert into tb_monthpart(id,name ,create_time) values(8,'Coco4','2022-04-10');
insert into tb_monthpart(id,name ,create_time) values(9,'Coco5','2022-04-30');
```
