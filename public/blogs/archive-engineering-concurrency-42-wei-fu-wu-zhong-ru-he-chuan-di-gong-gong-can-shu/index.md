#  微服务中如何传递公共参数？
## 1、本文内容
本文是微服务中大概率会用到的一个知识点，非常实用，请大家用心看完。
## 2、背景
先来看下微服务调用的流程图：https://www.processon.com/view/link/665457cd50771c4b1ea0905b?cid=6654521d659699314de163c5
![](/blogs/_archive-2024-assets/494940fe2535a136374a.webp)
## 3、有5个地方需要考虑
### 1）、gateway将公共参数放到请求中传递给下层服务
gateway转发请求前，将公共的参数添加请求头中向下传递便可。
### 2）、微服务中需要一个Filter读取公共参数丢到ThreadLocal中
```java
com.itsoku.lesson042.common.context.SystemContextFilter
com.itsoku.lesson042.common.context.SystemContext
com.itsoku.lesson042.common.context.SystemContextHolder
```
### 3）、OpenFeign发送请求前，将公共参数丢到请求头中进行传递
```java
com.itsoku.lesson042.common.context.SystemContextRequestInterceptor
public class SystemContextRequestInterceptor implements RequestInterceptor {
    @Override
    public void apply(RequestTemplate template) {
        // 从ThreadLocal中拿到公共上线文参数，放到 OpenFeign 请求头中
        for (Pair<String, String> header : SystemContextHolder.getSystemContext().toHeaders()) {
            template.header(header.getKey(), header.getValue());
        }
    }
}
```
### 4）、RestTemplate发送请求前，将公共参数丢到请求头中进行传递
```java
com.itsoku.lesson042.common.context.SystemContextRestTemplateRequestCustomizer
public class SystemContextRestTemplateRequestCustomizer implements RestTemplateRequestCustomizer {
    @Override
    public void customize(ClientHttpRequest request) {
        // 从ThreadLocal中拿到公共上线文参数，放到 RestTemplate 请求头中
        for (Pair<String, String> header : SystemContextHolder.getSystemContext().toHeaders()) {
            request.getHeaders().add(header.getKey(), header.getValue());
        }
    }
}
```
RestTemplate定义需要采用下面这种方式
```java
@Bean
public RestTemplate restTemplate(RestTemplateBuilder restTemplateBuilder) {
    return restTemplateBuilder.build();
}
```
### 5）、线程池中需要要能够读取到这些公共参数
需要使用我们自定义的线程池，如下
```java
com.itsoku.lesson042.common.thread.CommonThreadPoolExecutor
```
重写了submit和execute方法，可以实现调用者和线程池间ThreadLocal中的数据共享。
看个案例，代码如下，这里会将公共参数放到线程池的线程中
```java
private ThreadPoolExecutor threadPoolExecutor = new CommonThreadPoolExecutor(new CommonThreadPoolExecutor.ThreadLocalContext() {
    @Override
    public Object getContext() {
        return SystemContextHolder.getSystemContext().getContextMap();
    }
    @Override
    public void setContext(Object context) {
        SystemContextHolder.getSystemContext().getContextMap().putAll((Map<? extends String, ? extends String>) context);
    }
}, 5, 5, 10, TimeUnit.SECONDS, new LinkedBlockingQueue<>(100));
```
## 4、测试用例
### 1）准备2个服务
- service1：com.itsoku.lesson042.service1.Lesson042Service1Application
- service2：com.itsoku.lesson042.service2.Lesson042Service2Application
### 2）service1中测试5中情况，代码如下
```
com.itsoku.lesson042.service1.Service1Controller#test1
```
### 3）运行看效果
src/test/resources/Service1Controller.http
```http
### 上下文测试
GET http://localhost:8080/service1/test1
itsoku-header-user_id: 10001
itsoku-header-local: zh_cn
itsoku-header-user_name: luren
```
### 4）走gateway看下效果
启动gateway服务
```
com.itsoku.lesson042.gateway.Lesson042GatewayApplication
```
通过gateway去访问刚才上面的接口
```http
### 走 gateway 访问 service1中的test1 接口
GET http://localhost:8080/lesson042-service1/service1/test1
itsoku-header-local: zh_cn
token: itsoku
```
这个请求会打到gateway，gateway中我们搞了个拦截器，如下，这里面会校验token，验证通过后，会放入用户id和用户名
```java
com.itsoku.lesson042.gateway.AuthFilter
```
运行测试用例看效果
