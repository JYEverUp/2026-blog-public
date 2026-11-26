# 动态线程池
## 什么是动态线程池？
无需重启的情况下，可以对线程池进行扩缩容，比如改变线程池的核心线程数量、最大线程数量、队列容量等。
## 还是先看效果
我们会创建一个线程池，然后让其去处理任务，然后对其进行扩缩容，并查看扩缩容前后线程池的各个指标的变化（核心线程数、最大线程数、活动线程数、队列容量、队列中当前元素数量）。
### 创建一个线程池
- 线程池名称：emailThreadPool
- 核心线程数：10
- 最大线程数：20
- 队列容量：1000
```java
@Bean
public ThreadPoolTaskExecutor emailThreadPool() {
    //使用线程池管理器创建线程池
    return ThreadPoolManager.newThreadPool("emailThreadPool", 10, 20, 1000);
}
```
### 启动应用
```java
com.itsoku.lesson009.Lesson009Application
```
为了能看到效果，系统中会使用上面刚创建的这个线程池去模拟批量发邮件的一个操作，这样线程池中的一些数据才会发生变化（如：活动线程数、队列中当前元素的数量queueSize 这些指标）
### 看下线程池的信息
系统中暴露了一个接口可以查看到线程池管理器中所有线程池的信息。
浏览器中访问：http://localhost:8080/threadPoolManager/threadPoolInfoList，返回如下：
```json
{
  "code": "1",
  "data": [
    {
      "name": "emailThreadPool", // 线程池名称
      "corePoolSize": 10,        // 核心线程数
      "maxPoolSize": 20,   	     // 最大线程数
      "activeCount": 10,   	     // 活动线程数
      "queueCapacity": 1000,     // 队列容量
      "queueSize": 288		     // 队列中当前元素数量
    }
  ],
  "msg": null
}
```
## 演示扩容
### 扩缩容接口
com.itsoku.lesson009.controller.ThreadPoolManagerController#threadPoolChange
```java
/**
 * 线程池扩缩容
 *
 * @return
 */
@PostMapping("/threadPoolChange")
public Result<Boolean> threadPoolChange(@RequestBody ThreadPoolChange threadPoolChange) {
    ThreadPoolManager.changeThreadPool(threadPoolChange);
    return ResultUtils.ok(true);
}
```
### 执行扩容
核心线程数、最大线程数、容量都扩容一倍
```http
### 测试扩容
POST http://localhost:8080/threadPoolManager/threadPoolChange
Accept: application/json
Content-Type: application/json
{
  "name": "emailThreadPool",
  "corePoolSize": 50,
  "maxPoolSize": 100,
  "queueCapacity": 2000
}
```
### 看下扩容后线程池的信息
浏览器中访问：http://localhost:8080/threadPoolManager/threadPoolInfoList，返回如下：
```json
{
  "code": "1",
  "data": [
    {
      "name": "emailThreadPool",
      "corePoolSize": 50,
      "maxPoolSize": 100,
      "activeCount": 50,
      "queueCapacity": 2000,
      "queueSize": 408
    }
  ],
  "msg": null
}
```
## 演示缩容
### 执行缩容
核心线程数、最大线程数、容量都扩容一倍
```http
### 测试缩容
POST http://localhost:8080/threadPoolManager/threadPoolChange
Accept: application/json
Content-Type: application/json
{
  "name": "emailThreadPool",
  "corePoolSize": 5,
  "maxPoolSize": 10,
  "queueCapacity": 500
}
```
### 看下扩容后线程池的信息
浏览器中访问：http://localhost:8080/threadPoolManager/threadPoolInfoList，返回如下：
```json
{
  "code": "1",
  "data": [
    {
      "name": "emailThreadPool",
      "corePoolSize": 5,
      "maxPoolSize": 10,
      "activeCount": 2,
      "queueCapacity": 500,
      "queueSize": 0
    }
  ],
  "msg": null
}
```
## 代码讲解
1. 线程池中会用到Java中的阻塞队列`java.util.concurrent.BlockingQueue`，目前jdk中自带几个阻塞队列都不支持动态扩容，比如`java.util.concurrent.LinkedBlockingQueue`，他里面的capacity是final的，不支持修改，为了是队列容量能够支持调整，我们创建了一个可扩容的阻塞队列`ResizeLinkedBlockingQueue`，代码是从`LinkedBlockingQueue`中拷贝过来的，然后添加了一个可以修改容量capacity的方法，如下，然后创建线程池的时候，我们使用自定义的这个阻塞队列便可以实现线程池的动态扩容。
   ```java
   /**
    * 设置容量
    * @param capacity
    */
   public void setCapacity(int capacity) {
       if (capacity <= 0) throw new IllegalArgumentException();
       final ReentrantLock putLock = this.putLock;
       putLock.lock();
       try {
           if (count.get() > capacity) {
               throw new IllegalArgumentException();
           }
           this.capacity = capacity;
       } finally {
           putLock.unlock();
       }
   }
   ```
2. 线程池扩容的方法：com.itsoku.lesson009.comm.ThreadPoolManager#changeThreadPool

## 推荐使用开源的动态线程池：dynamic-tp
https://github.com/dromara/dynamic-tp
这个动态线程池是美团开源的，star数量3.3k，支持通过配置中心nacos配置线程池、对线程池进行扩缩容，很强大。
![image-20240403090106396](/blogs/_archive-2024-assets/0137c01a571be92d49cb.webp)
![image-20240403085314597](/blogs/_archive-2024-assets/5deba3968da72be0b22f.webp)
# 
