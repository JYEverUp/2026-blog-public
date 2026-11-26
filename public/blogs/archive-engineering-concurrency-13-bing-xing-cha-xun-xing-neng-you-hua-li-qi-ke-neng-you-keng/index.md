# 并行查询，可能有坑
## 需求：后端提供一个接口获取商品信息
接口传入一个商品id，需要返回商品下面这些信息，这些信息都在不同的表中，通过商品id就可以查到
- 商品基本信息（如商品名称、价格等基本信息)
- 商品描述信息（可能是富文本，放在单独的表中）
- 商品收藏量
- 商品评论量
## 常规版本实现（性能低）
按照id一步步查询，组装结果然后返回，代码如下
```java
com.itsoku.lesson006.GoodsController#getGoodsDetail
```
`http://localhost:8080/getGoodsDetail?goodsId=1`耗时如下：
```java
获取商品信息，普通版耗时：402 ms
```
## 有没有更快的方法呢？
这里面的4个查询并没有任何依赖，这些没有依赖的查询其实是可以并行查询的，那么我们可以使用线程池同时去拿这4个结果，然后等4个结果都拿到后，组装好，返回，这样效率将大大提升。
### 高性能版本实现（性能高）
使用线程池对4个方法并行查询，代码如下
```
com.itsoku.lesson006.GoodsController#getGoodsDetailNew
```
`http://localhost:8080/getGoodsDetailNew?goodsId=1`耗时如下：
```java
获取商品信息，使用线程池并行查询耗时：106 ms
```
## 小结
建议：当接口中，需要执行多个步骤，而多个步骤没有依赖的时候，那么可以采用线程池并行去执行这些步骤，可以大大提升接口的性能。
## 并行查询可能存在的问题？
如果上面执行并行查询用到的线程池配置不当，可能导致比较严重的性能问题。
比如将核心线程数设置为了1，而队列大小没有限制，那么所有的请求都变成串行了，会导致请求响应非常慢，出现大事故。
或者核心线程数设置的比较小，比如10，而队列大小没有设置上限，那么这个线程池同时只可支持10个任务并行，其他的请求进入这个接口后都变成串行执行了，进入队列排队，从而导致接口响应特别慢。
## 怎么解决这个问题？
解决这个问题本质是不要让任务排队或者排队时间不要太长，这个时候我们就要先说一下线程池的原理了，了解原理之后，就知道如何破解这个问题
![image-20240405093250650](/blogs/_archive-2024-assets/6744d65015b406986bba.webp)
了解了这个过程我们就有优化办法了，如下：
- 可以将核心线程数、最大线程数调大，但是也不能随便调，比如调的很大，反而会降低系统性能，建议调的过程中根据业务的指标进行压测得到一个合理的值
- 将队列大小设置的比较小，这样排队的时间大概率会比较短，或者排队失败，直接后面的流程
  > `LinkedBlockingQueue、ArrayBlockingQueue` 容量是不允许为0的，如果需要用到容量为0的队列，则需要使用同步阻塞队列`SynchronousQueue`
- 将队列大小设置为0，这样任务就不会进入队列，而直接创建新的线程去执行，或者走拒绝策略
- 拒绝策略可以使用`CallerRunsPolicy`，这个策略是直接在当前线程执行，即如果线程池执行不了，则自己去执行，这样至少不会一直等着
- 线程池隔离，不同的业务最好使用不同的线程池，互不影响，强烈建议核心业务一定要使用单独的线程池。
优化后的线程池配置如下
```java
@Bean
public ThreadPoolTaskExecutor goodsThreadPool() {
    ThreadPoolTaskExecutor threadPoolTaskExecutor = new ThreadPoolTaskExecutor();
    threadPoolTaskExecutor.setThreadNamePrefix("ThreadPool-Goods-");
    // 核心线程数为cpu核数 * 4，最大线程数据为cpu核数 * 8
    threadPoolTaskExecutor.setCorePoolSize(Runtime.getRuntime().availableProcessors() * 4);
    threadPoolTaskExecutor.setMaxPoolSize(Runtime.getRuntime().availableProcessors() * 8);
    // 队列容量为0，则任务就不会进入队列
    threadPoolTaskExecutor.setQueueCapacity(0);
    // 拒绝策略使用CallerRunsPolicy，让当前线程去兜底去执行任务
    threadPoolTaskExecutor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
    return threadPoolTaskExecutor;
}
```
