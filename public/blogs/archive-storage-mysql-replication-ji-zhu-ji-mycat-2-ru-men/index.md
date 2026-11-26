# 一、需求

由于 tb_order 表中数据量很大，磁盘IO及容量都到达了瓶颈，现在需要对 tb_order 表进行数据分片，分为三个

数据节点，每一个节点主机位于不同的服务器上, 具体的结构，参考下图

![img](/blogs/_archive-2024-assets/ddf0f3f947c9c34625e0.webp)二、环境准备

准备3台服务器：

- 192.168.200.210：MyCat中间件服务器，同时也是第一个分片服务器。
- 192.168.200.213：第二个分片服务器。
- 192.168.200.214：第三个分片服务器。

![image-20241228123449843](/blogs/_archive-2024-assets/2814fde547acd10fff5a.webp)

并且在上述3台数据库中创建数据库 db01 

# 三、配置

## 1. schema.xml

在schema.xml中配置逻辑库、逻辑表、数据节点、节点主机等相关信息。

具体的配置如下：

```xml
<?xml version="1.0"?>
<!DOCTYPE mycat:schema SYSTEM "schema.dtd">
<mycat:schema xmlns:mycat="http://io.mycat/">
    <schema name="DB01" checkSQLschema="true" sqlMaxLimit="100">
        <table name="TB_ORDER" dataNode="dn1,dn2,dn3" rule="auto-sharding-long" />
    </schema>

    
    <dataNode name="dn1" dataHost="dhost1" database="db01" />
    <dataNode name="dn2" dataHost="dhost2" database="db01" />
    <dataNode name="dn3" dataHost="dhost3" database="db01" />
    
    <dataHost name="dhost1" maxCon="1000" minCon="10" balance="0"
              writeType="0" dbType="mysql" dbDriver="jdbc" switchType="1"  slaveThreshold="100">
        <heartbeat>select user()</heartbeat>

        
        <writeHost host="master" url="jdbc:mysql://192.168.200.210:3306?useSSL=false&amp;serverTimezone=Asia/Shanghai&amp;characterEncoding=utf8" user="root" password="1234" />
    </dataHost>

    
    <dataHost name="dhost2" maxCon="1000" minCon="10" balance="0"
              writeType="0" dbType="mysql" dbDriver="jdbc" switchType="1"  slaveThreshold="100">
        <heartbeat>select user()</heartbeat>

        
        <writeHost host="master" url="jdbc:mysql://192.168.200.213:3306?useSSL=false&amp;serverTimezone=Asia/Shanghai&amp;characterEncoding=utf8" user="root" password="1234" />
    </dataHost>

    
    <dataHost name="dhost3" maxCon="1000" minCon="10" balance="0"
              writeType="0" dbType="mysql" dbDriver="jdbc" switchType="1"  slaveThreshold="100">
        <heartbeat>select user()</heartbeat>

        
        <writeHost host="master" url="jdbc:mysql://192.168.200.214:3306?useSSL=false&amp;serverTimezone=Asia/Shanghai&amp;characterEncoding=utf8" user="root" password="1234" />
    </dataHost>

</mycat:schema>
```

## 2. server.xml

需要在server.xml中配置用户名、密码，以及用户的访问权限信息，具体的配置如下：

```xml
    <user name="root" defaultAccount="true">
        <property name="password">123456</property>

        <property name="schemas">DB01</property>

        
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

        <property name="schemas">DB01</property>

        <property name="readOnly">true</property>

    </user>
```

上述的配置表示，定义了两个用户 root 和 user，这两个用户都可以访问 DB01 这个逻辑库，访问密码都是

123456，但是root用户访问DB01逻辑库，既可以读，又可以写，但是user用户访问DB01逻辑库是只读的。

# 四、测试

## 1. 启动

配置完毕后，先启动涉及到的3台分片服务器，然后启动MyCat服务器。

切换到Mycat的安装目录，执行如下指令，启动Mycat：

```shell
#启动
bin/mycat start

#停止
bin/mycat stop
```

Mycat启动之后，占用端口号 8066。

启动完毕之后，可以查看logs目录下的启动日志，查看Mycat是否启动完成。

![img](/blogs/_archive-2024-assets/3bf4f437294d391c5cdc.webp)

## 2. 测试

### 2.1. 连接MyCat

通过如下指令，就可以连接并登陆MyCat。

```shell
mysql -h 192.168.200.210 -P 8066 -uroot -p123456
```

我们看到我们是通过MySQL的指令来连接的MyCat，因为MyCat在底层实际上是模拟了MySQL的协议。

### 2.2. 数据测试

然后就可以在MyCat中来创建表，并往表结构中插入数据，查看数据在MySQL中的分布情况。

```sql
CREATE TABLE TB_ORDER (
    id BIGINT(20) NOT NULL,
    title VARCHAR(100) NOT NULL ,
    PRIMARY KEY (id)
) ENGINE=INNODB DEFAULT CHARSET=utf8 ;

INSERT INTO TB_ORDER(id,title) VALUES(1,'goods1');
INSERT INTO TB_ORDER(id,title) VALUES(2,'goods2');
INSERT INTO TB_ORDER(id,title) VALUES(3,'goods3');

INSERT INTO TB_ORDER(id,title) VALUES(1,'goods1');
INSERT INTO TB_ORDER(id,title) VALUES(2,'goods2');
INSERT INTO TB_ORDER(id,title) VALUES(3,'goods3');
INSERT INTO TB_ORDER(id,title) VALUES(5000000,'goods5000000');
INSERT INTO TB_ORDER(id,title) VALUES(10000000,'goods10000000');
INSERT INTO TB_ORDER(id,title) VALUES(10000001,'goods10000001');
INSERT INTO TB_ORDER(id,title) VALUES(15000000,'goods15000000');
INSERT INTO TB_ORDER(id,title) VALUES(15000001,'goods15000001');
```

经过测试，我们发现，在往 TB_ORDER 表中插入数据时：

- 如果id的值在1-500w之间，数据将会存储在第一个分片数据库中。
- 如果id的值在500w-1000w之间，数据将会存储在第二个分片数据库中。
- 如果id的值在1000w-1500w之间，数据将会存储在第三个分片数据库中。
- 如果id的值超出1500w，在插入数据时，将会报错。

为什么会出现这种现象，数据到底落在哪一个分片服务器到底是如何决定的呢？ 

这是由逻辑表配置时的一个参数 rule 决定的，而这个参数配置的就是分片规则，关于分片规则的配置，在后面的

课程中会详细讲解。
