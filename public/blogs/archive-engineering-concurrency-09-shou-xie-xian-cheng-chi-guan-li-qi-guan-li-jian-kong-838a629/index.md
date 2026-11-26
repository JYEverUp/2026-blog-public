# 实现一个线程池管理器
## 要解决什么问题？
平时我们在开发中，创建了不少线程池，这些线程池都处于游离状态，不方便管理和监控，我们是无法知道目前系统中有哪些线程池、以及每个线程池当前的一个状态，负载情况等，所以我们可以开发一个线程池管理器来解决这个问题。
## 线程池管理器
统管系统中所有线程池，负责所有线程池的创建、监控等操作。
## 代码
```java
com.itsoku.lesson009.common.ThreadPoolManager
```
主要2个方法
- newThreadPool：创建一个线程池
- threadPoolInfoList：获取线程池管理器中所有的线程池列表，包含每个线程池的各种指标（名称、核心线程数、最大线程数、当前活动线程数、队列容量、队列当前大小等信息），监控系统采集这些信息进行监控告警等处理。
## 案例
1. ThreadPoolConfiguration：使用线程池创建2个线程池，一个用户发送邮件，一个用户发送短信，在业务上，通常不同的业务使用不同的线程池，这也叫线程池隔离，互不影响，如果用同一个线程池，比如发邮件和发短信共用一个，那么邮件太多的时候，会导致短信发送延后，影响业务
2. EmailSendService：模拟使用线程池发送邮件
3. ThreadPoolManagerController 中暴露了一个接口用于获取线程池管理器中所有线程池列表，可用于监控
4. 启动应用Lesson009Application
5. 访问`http://localhost:8080/threadPoolManager/threadPoolInfoList`
   ```json
   [{
   	"name": "emailThreadPool",
   	"corePoolSize": 5,
   	"maxPoolSize": 10,
   	"activeCount": 5,
   	"queueCapacity": 1000,
   	"queueSize": 84
   }, {
   	"name": "smsThreadPool",
   	"corePoolSize": 16,
   	"maxPoolSize": 32,
   	"activeCount": 0,
   	"queueCapacity": 1000,
   	"queueSize": 0
   }]
   ```
