# 一、schema.xml

schema.xml 作为MyCat中最重要的配置文件之一 , 涵盖了MyCat的逻辑库 、 逻辑表 、 分片规则、分片节点及

数据源的配置。

![img](/blogs/_archive-2024-assets/18b27bb67a41db0ec4fd.webp)

**主要包含以下三组标签：**

- schema标签
- datanode标签
- datahost标签

## 1. schema标签

### 1.1. schema 定义逻辑库

schema 标签用于定义 MyCat 实例中的逻辑库 , 一个MyCat实例中, 可以有多个逻辑库 , 可以通过 schema 标签

来划分不同的逻辑库。

![img](/blogs/_archive-2024-assets/8d11e1138b590ce7359a.webp)

MyCat中的逻辑库的概念，等同于MySQL中的database概念 , 需要操作某个逻辑库下的表时, 也需要切换逻辑库

(use xxx)。

**核心属性：**

- name：指定自定义的逻辑库库名
- checkSQLschema：在SQL语句操作时指定了数据库名称，执行时是否自动去除；true：自动去除，false：不自动去除
- sqlMaxLimit：如果未指定limit进行查询，列表查询模式查询多少条记录

### 1.2. schema 中的table定义逻辑表

![img](/blogs/_archive-2024-assets/4eddf9409e74c6eb689b.webp)

table 标签定义了MyCat中逻辑库schema下的逻辑表 , 所有需要拆分的表都需要在table标签中定义 。

**核心属性：**

- name：定义逻辑表表名，在该逻辑库下唯一
- dataNode：定义逻辑表所属的dataNode，该属性需要与dataNode标签中name对应；多个dataNode逗号分隔
- rule：分片规则的名字，分片规则名字是在rule.xml中定义的
- primaryKey：逻辑表对应真实表的主键
- type：逻辑表的类型，目前逻辑表只有全局表和普通表，如果未配置，就是普通表；全局表，配置为 global

## 2. datanode标签

![img](/blogs/_archive-2024-assets/fc25e07202c89e811f3c.webp)

**核心属性：**

- name：定义数据节点名称
- dataHost：数据库实例主机名称，引用自 dataHost 标签中name属性
- database：定义分片所属数据库

## 3. datahost标签

![img](/blogs/_archive-2024-assets/0036d582c5cdc79dd2ae.webp)

该标签在MyCat逻辑库中作为底层标签存在, 直接定义了具体的数据库实例、读写分离、心跳语句。

**核心属性：**

- name：唯一标识，供上层标签使用
- maxCon/minCon：最大连接数/最小连接数
- balance：负载均衡策略，取值 0,1,2,3
- writeType：写操作分发方式（0：写操作转发到第一个writeHost，第一个挂了，切换到第二个；1：写操作随机分发到配置的writeHost）
- dbDriver：数据库驱动，支持 native、jdbc

# 二、rule.xml

rule.xml中定义所有拆分表的规则, 在使用过程中可以灵活的使用分片算法, 

或者对同一个分片算法使用不同的参数, 它让分片过程可配置化。

主要包含两类标签：tableRule、Function。

![img](/blogs/_archive-2024-assets/c286bd4c1aecc8b20d09.webp)

# 三、server.xml

server.xml配置文件包含了MyCat的系统配置信息，主要有两个重要的标签：system、user。

## 1. system标签

![img](/blogs/_archive-2024-assets/680e2bce384ec2a412e0.webp)

主要配置MyCat中的系统配置信息，对应的系统配置项及其含义，如下：

| 属性                      | 取值       | 含义                                                         |
| ------------------------- | ---------- | ------------------------------------------------------------ |
| charset                   | utf8       | 设置Mycat的字符集, 字符集需要与MySQL的字符集保持一致         |
| nonePasswordLogin         | 0,1        | 0为需要密码登陆、1为不需要密码登陆 ,默认为0，设置为1则需要指定默认账户 |
| useHandshakeV10           | 0,1        | 使用该选项主要的目的是为了能够兼容高版本的jdbc驱动, 是否采用HandshakeV10Packet来与client进行通信, 1:是, 0:否 |
| useSqlStat                | 0,1        | 开启SQL实时统计, 1 为开启 , 0 为关闭 ;开启之后, MyCat会自动统计SQL语句的执行情况 ; mysql -h 127.0.0.1 -P 9066 -u root -p 查看MyCat执行的SQL, 执行效率比较低的SQL , SQL的整体执行情况、读写比例等 ; show @@sql ; show @@sql.slow ; show @@sql.sum ; |
| useGlobleTableCheck       | 0,1        | 是否开启全局表的一致性检测。1为开启 ，0为关闭 。             |
| sqlExecuteTimeout         | 1000       | SQL语句执行的超时时间 , 单位为 s ;                           |
| sequnceHandlerType        | 0,1,2      | 用来指定Mycat全局序列类型，0 为本地文件，1 为数据库方式，2 为时间戳列方式，默 认使用本地文件方式，文件方式主要用于测试 |
| sequnceHandlerPattern     | 正则表达式 | 必须带有MYCATSEQ或者 mycatseq进入序列 匹配流程 注意MYCATSEQ_有空格的情况 |
| subqueryRelationshipCheck | true,false | 子查询中存在关联查询的情况下,检查关联字 段中是否有分片字段 .默认 false |
| useCompression            | 0,1        | 开启mysql压缩协议 ,0 : 关闭, 1 : 开 启                       |
| fakeMySQLVersion          | 5.5,5.6    | 设置模拟的MySQL版本号                                        |
| defaultSqlParser          |            | 由于MyCat的最初版本使用了FoundationDB的SQL解析器, 在MyCat1.3后增加了Druid解析器, 所以要设置defaultSqlParser属 性来指定默认的解析器; 解析器有两个 : druidparser 和 fdbparser, 在MyCat1.4之后,默认是druidparser, fdbparser已经废除了 |
| processors                | 1,2....    | 指定系统可用的线程数量, 默认值为CPU核心x 每个核心运行线程数量; processors 会 影响processorBufferPool, processorBufferLocalPercent, processorExecutor属性, 所有, 在性能调优时, 可以适当地修改processors值 |
| processorBufferChunk      |            | 指定每次分配Socket Direct Buffer默认 值为4096字节, 也会影响BufferPool长度,如果一次性获取字节过多而导致buffer不够 用, 则会出现警告, 可以调大该值 |
| processorExecutor         |            | 指定NIOProcessor上共享businessExecutor固定线程池的大小; MyCat把异步任务交给 businessExecutor线程池中, 在新版本的MyCat中这个连接池使 用频次不高, 可以适当地把该值调小 |
| packetHeaderSize          |            | 指定MySQL协议中的报文头长度, 默认4个字 节                    |
| maxPacketSize             |            | 指定MySQL协议可以携带的数据最大大小, 默 认值为16M            |
| idleTimeout               | 30         | 指定连接的空闲时间的超时长度;如果超时,将 关闭资源并回收, 默认30分钟 |
| txIsolation               | 1,2,3,4    | 初始化前端连接的事务隔离级别,默认为REPEATED_READ, 对应数字为3 READ_UNCOMMITED=1; READ_COMMITTED=2; REPEATED_READ=3; SERIALIZABLE=4; |
| sqlExecuteTimeout         | 300        | R执行SQL的超时时间, 如果SQL语句执行超时,                     |
| serverPort                | 8066       | 将关闭连接; 默认300秒;定义MyCat的使用端口, 默认8066          |
| managerPort               | 9066       | 定义MyCat的管理端口, 默认9066                                |

## 2. user标签

配置MyCat中的用户、访问密码，以及用户针对于逻辑库、逻辑表的权限信息，

具体的权限描述方式及配置说明如下：

![img](/blogs/_archive-2024-assets/1dd898e8a8bcb2c3192a.webp)在测试权限操作时，我们只需要将 privileges 标签的注释放开。 

在 privileges 下的schema标签中配置的dml属性配置的是逻辑库的权限。

 在privileges的schema下的table标签的dml属性中配置逻辑表的权限。
