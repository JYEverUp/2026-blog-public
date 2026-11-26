# 手撸一个接口性能压测工具类
## 常用的好用的压测工具
1. Apache服务器安装目录的 ab.exe
2. Jmeter
3. LoadRunner
## 为什么要自己实现一个压测工具？
高并发有很多知识点，工具类（如：线程池、JUC四个常用工具类【CountDownLatch、CyclicBarrier、Semaphore、ExChange】等），但是很多同学，学了之后不知道如何使用，主要是缺少实战的场景，所以我在课程中，通过不同的场景案例，带大家去实战演练，才能深入掌握这些知识点，然后才能够灵活地去解决业务问题。
## 本文目标
带大家手写一个接口性能压测工具类，能够加深对下面3个知识点的理解，同时可以得到一个常用的压测工具类，方便自己或他人使用。
## 涉及的知识点
1. 线程池（ThreadPoolExecutor）
2. CountDownLatch
3. AtomicInteger
## 要实现的功能：写一个通用的压测工具类
### 类名
```java
LoadRunnerUtils
```
### 类中定义一个通用的压测方法
方法定义如下，提供3个参数，可以对第3个参数需要执行的业务进行压测，最终将压测的结果返回。
```java
/**
   * 对 command 执行压测
   *
   * @param requests    总请求数
   * @param concurrency 并发数量
   * @param command     需要执行的压测代码
   * @param <T>
   * @return 压测结果 {@link LoadRunnerResult}
   * @throws InterruptedException
   */
public static <T> LoadRunnerResult run(int requests, int concurrency, Runnable command) 
```
### 方法返回压测结果（LoadRunnerResult）
LoadRunnerResult 包含了压测结果，定义如下，主要有下面这些指标
```java
public static class LoadRunnerResult {
    // 请求总数
    private int requests;
    // 并发量
    private int concurrency;
    // 成功请求数
    private int successRequests;
    // 失败请求数
    private int failRequests;
    // 请求总耗时(ms)
    private int timeTakenForTests;
    // 每秒请求数（吞吐量）
    private float requestsPerSecond;
    // 每个请求平均耗时(ms)
    private float timePerRequest;
    // 最快的请求耗时(ms)
    private float fastestCostTime;
    // 最慢的请求耗时(ms)
    private float slowestCostTime;
}
```
## 压测工具类源码
```java
com.itsoku.lesson003.utils.LoadRunnerUtils
```
完整源码加我微信：itsoku，获取。
## 2个测试案例，先带大家看效果
### 案例1：总请求1000个，并发100，压测一个简单的接口
接口代码如下，test1接口，很简单，没有任何逻辑，这个接口效率很高
```java
@GetMapping("/test1")
public String test1() {
    log.info("test1");
    return "ok";
}
```
#### 对应的压测用例代码
LoadRunnerUtilsTest 中的 test1方法
```java
@Test
public void test1() throws InterruptedException {
    //需要压测的接口地址，这里我们压测test1接口
    //压测参数，总请求数量1000，并发100
    int requests = 1000;
    int concurrency = 100;
    String url = "http://localhost:8080/test1";
    System.out.println(String.format("压测接口:%s", url));
    RestTemplate restTemplate = new RestTemplate();
    //调用压测工具类开始压测
    LoadRunnerUtils.LoadRunnerResult loadRunnerResult = LoadRunnerUtils.run(requests, concurrency, () -> {
        restTemplate.getForObject(url, String.class);
    });
    //输出压测结果
    print(loadRunnerResult);
}
```
#### 运行test1用例，效果如下
```html
压测接口:http://localhost:8080/test1
11:47:56 - 压测开始......
11:47:57 - 压测结束，总耗时(ms):601
压测结果如下：
==============================
请求总数: 1000
并发量: 100
成功请求数: 1000
失败请求数: 0
请求总耗时(ms): 601
每秒请求数(吞吐量): 1663.8936
每个请求平均耗时(ms): 0.601
最快的请求耗时(ms): 0.0
最慢的请求耗时(ms): 565.0
```
### 案例2：总请求1000个，并发100，压测一个耗时的接口
接口代码如下，test2接口，内部休眠了100毫秒，用于模拟业务耗时操作
```java
@GetMapping("/test2")
public String test2() throws InterruptedException {
    //接口中休眠100毫秒，用来模拟业务操作
    TimeUnit.MILLISECONDS.sleep(100);
    return "ok";
}
```
#### 对应的压测用例代码
LoadRunnerUtilsTest 中的 test2方法
```java
@Test
public void test2() throws InterruptedException {
    //需要压测的接口地址，这里我们压测test2接口
    //压测参数，总请求数量10000，并发100
    int requests = 1000;
    int concurrency = 100;
    String url = "http://localhost:8080/test2";
    System.out.println(String.format("压测接口:%s", url));
    RestTemplate restTemplate = new RestTemplate();
    //调用压测工具类开始压测
    LoadRunnerUtils.LoadRunnerResult loadRunnerResult = LoadRunnerUtils.run(requests, concurrency, () -> {
        restTemplate.getForObject(url, String.class);
    });
    //输出压测结果
    print(loadRunnerResult);
}
```
#### 运行test2用例，效果如下
```html
压测接口:http://localhost:8080/test2
11:48:20 - 压测开始......
11:48:22 - 压测结束，总耗时(ms):1231
压测结果如下：
==============================
请求总数: 1000
并发量: 100
成功请求数: 1000
失败请求数: 0
请求总耗时(ms): 1231
每秒请求数(吞吐量): 812.34766
每个请求平均耗时(ms): 1.231
最快的请求耗时(ms): 100.0
最慢的请求耗时(ms): 281.0
==============================
```
## 压测工具类,源码解析
```java
com.itsoku.lesson003.utils.LoadRunnerUtils
```
