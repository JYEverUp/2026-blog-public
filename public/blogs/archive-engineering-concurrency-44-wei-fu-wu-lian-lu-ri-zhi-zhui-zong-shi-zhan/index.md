#  微服务链路日志追踪实战
## 1、微服务中，接口报错，如何快速定位问题？
需要日志的辅助，一般错误日志中有详细的堆栈信息，具体是哪行代码报错，都可以看到。
要想快速定位问题，前提是要能够快速定位日志。
但是微服务调用链路通常比较复杂，先来看下微服务常见的调用流程，如下图，一个请求可能会调用多个服务。
![image-20240605154330516](/blogs/_archive-2024-assets/97af46b4b2ee69ac9fce.webp)
## 2、解决方案：链路日志追踪
1. 服务端入口处，也就是gateway接收到请求后，可以生成一个唯一的id，记做：traceId，然后传给被调用的服务
2. 整个请求过程中，所有参与者，均需要将traceId向下传递，且日志中需要输出traceId的值
3. 给客户端的返回值中，添加一个通用的字段：traceId，将上面的traceId作为这个字段的值
4. 这样客户端发现接口有问题的时候，直接将这个traceId提供给我们，我们便可以在日志中快速查询出对应的日志
> 系统需要将所有日志收集起来，存到ElasticSearch中，可以就可以通过traceId快速检索了
## 3、代码落地
### 1）gateway改造
所有的请会先到达gateway，这里可以添加一个拦截器，拦截所有的请求，在请求转发前，生成一个traceId，放到请求头中，向下传递即可。
```java
com.itsoku.lesson044.gateway.TraceFilter
```
### 2）下层微服务改造
下层微服务，也就是上图中最下面的部分：service1、service2、service3
添加一个Filter，拦截所有请求，从请求头中读取调用者传递过来的traceId，然后丢到ThreadLocal中和Logback中，这样日志中就会输出traceId
```java
com.itsoku.lesson044.common.trace.TraceFilter
```
MDC是logback为我们提供的一个扩展的入口，可以向里面放入一些键值对，然后在logback中的日志中就可以通过这个traceId获取到对应的值
如下，logback.xml中使用`%X{traceId}`可以获取到MDC中设置的traceId
![image-20240605161758457](/blogs/_archive-2024-assets/0941861f8dbf25ff86a0.webp)
### 3）OpenFeign改造
拦截 OpenFeign 所有请求，在 OpenFeign 发送请求前，将traceId放到请求头中，传递给被调用者
```java
com.itsoku.lesson044.common.trace.TraceRequestInterceptor
```
### 4）RestTemplate 改造
拦截RestTemplate所有请求，在 RestTemplate 发送请求前，将traceId放到请求头中，传递给被调用者
```java
com.itsoku.lesson044.common.trace.TraceRestTemplateRequestCustomizer
```
### 5）线程池改造
为什么需要改造线程池？
Logback日志中能输出traceId，底层是将traceId放到ThreadLocal中，但是ThreadLocal中的数据，在线程池中是获取不到的，所以需要对线程池进行改造
需要使用我们自定义的线程池，如下
```java
com.itsoku.lesson044.common.thread.CommonThreadPoolExecutor
```
重写了submit和execute方法，可以实现调用者和线程池间ThreadLocal中的数据共享，这个自定义线程池，更详细的介绍可以看 26 节。
这个自定义线程池，如何使用呢？
看个案例，代码如下，可以实现线程池使用者和线程池中的线程间traceId共享。
```java
private ThreadPoolExecutor threadPoolExecutor = new CommonThreadPoolExecutor(new CommonThreadPoolExecutor.ThreadLocalContext() {
    @Override
    public Object getContext() {
        return TraceUtils.getTraceId();
    }
    @Override
    public void setContext(Object traceId) {
        TraceUtils.setTraceId((String) traceId);
    }
}, 5, 5, 10, TimeUnit.SECONDS, new LinkedBlockingQueue<>(100));
```
> 原理比较简单：使用线程池执行任务，最终都会调用execute、submit这两个方法，自定义线程池重写了这2个方法
>
> 调用这两个方法执行任务之前，会先调用ThreadLocalContext的第一个方法getContext从当前线程中拿到traceId，然后线程池内部真正执行任务的时候，又会调用ThreadLocalContext的第二个方法setContext，把第一个方法的返回值作为参数传递进去，这样线程池中执行任务的线程就可以拿到这个traceId了。
>
> 更详细的信息直接看源码，一看就懂。
## 4、测试效果
### 测试代码
```
com.itsoku.lesson044.service1.Service1Controller#test1
```
### 启动3个springboot应用
```java
com.itsoku.lesson044.gateway.Lesson044GatewayApplication
com.itsoku.lesson044.service1.Lesson044Service1Application
com.itsoku.lesson044.service2.Lesson044Service2Application
```
### 浏览器中访问
```
http://localhost:8080/lesson044-service1/service1/test1
```
- 此请求链路：gateway->service1->service2
- 大家注意看geteway以及2个服务中，输出的日志中traceId是不是一样
