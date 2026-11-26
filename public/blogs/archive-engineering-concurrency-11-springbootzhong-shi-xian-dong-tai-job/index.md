# 使用SpringBoot实现动态Job实战
## 功能
- 会创建一个job表
- 可以通过接口，对这些job表进行增删改查
- 支持动态增加、删除、修改、启动、停止Job等
- 系统均无需重启，会自动监控job表的变化，实现job的动态执行
## 用到的技术
- SpringBoot
- MyBatis-Plus
- MySql
- cron表达式（job执行的一种表达式，如`* * * * * *`表示每秒执行一次 ）
## 先看效果
### 系统启动后会自动执行下面的脚本
> 创建job表，插入2条记录
```sql
-- 创建job表
create table if not exists t_job
(
    id          varchar(50) primary key comment 'id，主键',
    name        varchar(100) not null comment 'job名称，可以定义一个有意义的名称',
    cron        varchar(50)  not null comment 'job的执行周期，cron表达式',
    bean_name   varchar(100) not null comment 'job需要执行那个bean，对应spring中bean的名称',
    bean_method varchar(100) not null comment 'job执行的bean的方法',
    status      smallint     not null default 0 comment 'job的状态,0：停止，1：执行中'
);
-- 为了方便测试，清理数据
delete from t_job;
-- 创建2个测试用的job，job1每1秒执行1次，job2每2秒执行一次
insert ignore into t_job values ('1', '第1个测试job', '* * * * * *', 'job1', 'execute', 1);
insert ignore into t_job values ('2', '第2个测试job', '*/2 * * * * *', 'job2', 'execute', 1);
```
### 原理
应用启动后，会自动去job表拉取需要执行的job，进行执行。
并每隔5秒对这个 job 表进行一次监控，监控其有没有发生变化，比如这个表中的 job 发生变化（有新增、删除、修改、暂停、启动等操作）都会被自动监控到，然后便实现了 job 的动态执行。
### 系统中定义了3个测试用的job
```java
com.itsoku.lesson011.test.Job1
com.itsoku.lesson011.test.Job2
com.itsoku.lesson011.test.Job3
```
### 启动应用
```java
com.itsoku.lesson011.Lesson011Application
```
### 可以看到job1和job2在执行了
```
[main] 18:02:17 ：Tomcat started on port(s): 8080 (http) with context path ''
[main] 18:02:17 ：Started Lesson011Application in 4.123 seconds (JVM running for 5.989)
[main] 18:02:17 ：启动 job 成功:{"id":"1","name":"第1个测试job","cron":"* * * * * *","beanName":"job1","beanMethod":"execute"}
[main] 18:02:17 ：启动 job 成功:{"id":"2","name":"第2个测试job","cron":"*/2 * * * * *","beanName":"job2","beanMethod":"execute"}
[taskExecutor-2] 18:02:18 ：job1
[taskExecutor-3] 18:02:18 ：job2
[taskExecutor-4] 18:02:19 ：job1
[taskExecutor-1] 18:02:20 ：job2
[taskExecutor-1] 18:02:20 ：job1
[taskExecutor-3] 18:02:21 ：job1
[taskExecutor-6] 18:02:22 ：job1
```
### 测试各种场景
下面提供了5个测试案例，一个个运行下，给大家看下效果。
```http
### 停止job1
POST http://localhost:8080/jobStop?id=1
Accept: application/json
### 启动job1
POST http://localhost:8080/jobStart?id=1
Accept: application/json
### 删除job1
POST http://localhost:8080/jobDelete?id=1
Accept: application/json
### 变更job2，将其执行周期改为每5秒一次
POST http://localhost:8080/jobUpdate
Accept: application/json
Content-Type: application/json
{
  "id": "2",
  "name": "第2个job",
  "cron": "*/5 * * * * *",
  "beanName": "job2",
  "beanMethod": "execute",
  "status": 1
}
### 添加一个job3，每秒执行一次
POST http://localhost:8080/jobCreate
Content-Type: application/json
Accept: application/json
{
  "name": "第3个job",
  "cron": "* * * * * *",
  "beanName": "job3",
  "beanMethod": "execute",
  "status": 1
}
```
## 源码解析
### JobController：job对外暴露的接口
提供对job表的增删改查、job的暂停、启动等接口
### ThreadPoolTaskScheduler：Spring 框架中用于任务调度的组件
系统中最终job的执行，就是调用`ThreadPoolTaskScheduler`这个类的一些方法去执行的，稍后带大家看下源码。
```java
@Bean
public ThreadPoolTaskScheduler threadPoolTaskScheduler() {
    ThreadPoolTaskScheduler threadPoolTaskScheduler = new ThreadPoolTaskScheduler();
    //线程池大小
    threadPoolTaskScheduler.setPoolSize(100);
    //线程名称前缀
    threadPoolTaskScheduler.setThreadNamePrefix("taskExecutor-");
    //等待时长
    threadPoolTaskScheduler.setAwaitTerminationSeconds(60);
    //关闭任务线程时是否等待当前被调度的任务完成
    threadPoolTaskScheduler.setWaitForTasksToCompleteOnShutdown(true);
    return threadPoolTaskScheduler;
}
```
### SpringJobRunManager：动态job执行的的核心代码
这个类是自己写的，内部会监控job表变化，然后动态执行job，目前系统默认是5秒监控一次。
## 扩展
### 如何让job支持集群？
目前这个job是单机版本的，可能有朋友会问，线上会是集群的方式执行，那怎么办？这里给2个方案
1. 可以在配置文件中加个开关，用开关配置，是否需要这台机器执行，这个方案可能不太友好
2. 对每个job加分布式锁，加锁成功才去执行
### 让job支持其他方式调用
案例中job是通过beanName、beanMethod结合反射去调用的，不够灵活。
大家可以对这个进行改造，比如支持http接口的方式去调用job或者其他更多方式，大家自由扩展，这样你开发出来的这个job就是比较通用的了，可以直接当成公司的一个job平台去用，会让领导对你刮目相看，同时也提升了技术，双赢。
