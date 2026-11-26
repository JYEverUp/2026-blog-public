## 慢查询定位总结
1、介绍一下当时产生问题的场景(我们当时的一个接口测试的时候非常的慢，压测的结果大概5秒钟)
2、我们系统中当时采用了运维工具(Skywalking)，可以监测出哪个接口，最终因为是sq!的问题
3、在mysal中开启了慢日志查询，我们设置的值就是2秒，一旦sql执行超过2秒就会记录到日志中(调试阶段)
4、上线前的压力测试，观察相关的指标 tps/qps/rt/io/cpu总结:
## 慢 SQL 处理思路
### 发现:
系统监控:基于 arthars 运维工具、promethues、skywalkingmysql 慢日志: 会影响一部分系统性能
慢 SQL 处理 由宏观到微观

1、检査 系统相关性能 top/mpstat/pidstat/vmstat 检查 CPU/I0 占比，由进程到线程

2、检査 MySQL 性能情况，show processlist 查看相关进程|基于 MySQL Workbench 进行分析

3、检査 SQL 语句索引执行情况，explain 关注 type key extra rows 等关键字

4、检査是否由于 SQL 编写不当造成的不走索引，例如 使用函数、not in、%like%、or 等

5、其他情况: 深分页、数据字段査询过多、Join 连表不当、业务大事物问题、死锁、索引建立过

6、对于热点数据进行前置，降低 MySQL 的压力 redis、mongodb、memory

7、更改 MySQL 配置 ， 处理线程设置一般是 cpu*核心数 的 2倍，日志大小 bin-log

8、升级机器性能 or 加机器

9、分表策略，分库策略

10、数据归档
