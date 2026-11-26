# 一、基本介绍

**Sharding-JDBC**是当当网研发的开源分布式数据库中间件，从 3.0 开始Sharding-JDBC被包含在 Sharding-

Sphere中，之后该项目进入进入Apache孵化器，4.0版本之后的版本为Apache版本。

**ShardingSphere**是一套开源的分布式数据库中间件解决方案组成的生态圈，它由Sharding-JDBC、

ShardingProxy和Sharding-Sidecar（计划中）这3款相互独立的产品组成。 他们均提供标准化的数据分片、

分布式事务和 数据库治理功能，可适用于如Java同构、异构语言、容器、云原生等各种多样化的应用场景。 

官方地址：https://shardingsphere.apache.org/document/current/cn/overview/

咱们目前只需关注Sharding-JDBC，它定位为轻量级Java框架，在Java的JDBC层提供的额外服务。它使用客

户端 直连数据库，以jar包形式提供服务，无需额外部署和依赖，可理解为增强版的JDBC驱动，完全兼容

JDBC和各种ORM框架。

Sharding-JDBC的核心功能为**数据分片**和**读写分离**，通过Sharding-JDBC，应用可以**透明**的使用jdbc访问已

经分库 分表、读写分离的多个数据源，而不用关心数据源的数量以及数据如何分布。

- 适用于任何基于Java的ORM框架，如： Hibernate, Mybatis, Spring JDBC Template或直接使用

JDBC。

- 基于任何第三方的数据库连接池，如：DBCP, C3P0, BoneCP, Druid, HikariCP等。
- 支持任意实现JDBC规范的数据库。目前支持MySQL，Oracle，SQLServer和PostgreSQL。

![img](/blogs/_archive-2024-assets/54224ca665842b90cae1.webp)

上图展示了Sharding-Jdbc的工作方式，使用Sharding-Jdbc前需要人工对数据库进行分库分表，在应用程

序中加入Sharding-Jdbc的Jar包，应用程序通过Sharding-Jdbc操作分库分表后的数据库和数据表，由于

Sharding-Jdbc是对Jdbc驱动的增强，使用Sharding-Jdbc就像使用Jdbc驱动一样，在应用程序中是无需

指定具体要操作的分库和分表的。

# 二、与JDBC性能对比

1. 性能损耗测试：服务器资源充足、并发数相同，比较JDBC和Sharding-JDBC性能损耗，Sharding-JDBC

相对JDBC损耗不超过7%。![img](/blogs/_archive-2024-assets/1e05f89bd3891ce9650f.webp)

1. 性能对比测试：服务器资源使用到极限，相同的场景JDBC与Sharding-JDBC的吞吐量相当。
2. 性能对比测试：服务器资源使用到极限，Sharding-JDBC采用分库分表后，Sharding-JDBC吞吐量	

JDBC不分表有接近2倍的提升。

![img](/blogs/_archive-2024-assets/014cd354406a0d90b530.webp)
