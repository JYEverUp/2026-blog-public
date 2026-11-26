## **一、需求背景**



如果说你正在开发一个交易或支付系统中的核心服务，可能有这样一个场景，用户在电商平台下单后开始跳转到在线收银台进行支付。由于支付渠道和网络环境随时都有可能发生问题，那么你该怎么保证支付系统的可靠性呢？



保证支付系统的可靠性需要考虑的点非常多，但这里有一个最直接和重点的内容就支付响应时长，如果支付时间过长，那么暴增的支付请求可能会把整个服务拖垮，最终导致所有服务瘫痪。



这时你可能会想到一个功能组件，超时熔断 hystrix。这也是大多数支付系统中必用的组件，但怎么用呢，我们是在所有的接口上都加一个这样的功能组件吗？显然这样做是不合适的，一般类似这样的组件可能会嵌入到你的RPC接口或者自研的网关上，也可能是在整个服务治理层的功能编排上。总之，它不会轻易的暴漏给你，让你硬编码到业务逻辑实现中。



那么，本章我们就抽丝剥茧把组件包装使用的最核心实现方式展示给你。记住任何实现方案都是以当前系统环境最适合方式设计的，并不一定非得拘泥于某种形式。



## **二、方案设计**

很多时候你遇到的复杂场景问题，市面基本都有相应的解决方案，尤其是一些常见的问题都可以找到对应的技术实现工具。就像我们本章节所需要的调用超时要熔断保护系统，就有相应的技术组件 hystrix，它是 Netflix 公司开源的一款容错框架，在大部分 RPC 服务中也都有引入使用。

那如果我们只是想方便、简单并且不需要关心如何创建和返回结果的使用这样一个服务，就可以把 hystrix 的框架包装在中间里，屏蔽调用逻辑。整体的设计方案如图 4-1 超时熔断中间件框架设计。

![img](/blogs/_archive-2024-assets/40680a422c392754f9c6.webp)

1. 使用自定义注解和切面技术，拦截需要被熔断保护的方法。
2. 拦截后到方法后，就可以通过 hystrix 给方法设定已配置好的超时熔断处理。

## 三、技术实现

### **1. 工程结构**

hystrix-spring-boot-starter

└── src

  ├── main

  │  └── java

  │    └── cn.bugstack.middleware.hystrix

  │      ├── annotation

  │      │  └── DoHystrix.java

  │      ├── valve

  │      │  ├── impl

  │      │  │ └── HystrixValveImpl.java 

  │      │  └── IValveService.java

  │      └── DoHystrixPoint.java

  └── test

​    └── java

​      └── cn.bugstack.middleware.test

​        └── ApiTest.java



**工程源码**：**https://gitcode.net/KnowledgePlanet/SpringBootStarter/hystrix-spring-boot-starter**

超时熔断中间件类关系，如图 4-2

![img](/blogs/_archive-2024-assets/6e5a776155e8d30c2ce0.webp)

屏蔽已有成熟组件的使用细节并不会太复杂，这种开发不会像是重新开发一套调用JDBC一样会涉及很多逻辑实现。

在这个中间件的实现中也没有额外的 yml 配置，仅是对切面的运用和 hystrix 的包装，包含如下信息：

1. DoHystrix 自定义注解中需要配置方法的超时时长和拦截后的返回信息。
2. DoHystrixPoint 自定义切面的实现比较简单，只是拦截方法和处理相应的操作。
3. HystrixValveImpl 是熔断的具体实现，这里之所以添加接口的实现方式，是为了可以扩展更多的插件包服务。

### **2. 自定义注解**

```
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface DoHystrix {
  String returnJson() default "";     // 失败结果 JSON
  int timeoutValue() default 0;      // 超时熔断
}
```

1. @Retention(RetentionPolicy.RUNTIME) 标记注解在 JVM 运行时可见
2. @Target(ElementType.METHOD) 标记注解的作用域在方法层面 ElementType.METHOD
3. returnJson，熔断保护下返回的结果
4. timeoutValue，方法的调用安全范围时长，一般指的是 TP99、TP999 的调用稳定值

### 3. 熔断服务包装

```
public class HystrixValveImpl extends HystrixCommand<Object> implements IValveService {

    private ProceedingJoinPoint jp;
    private Method method;
    private DoHystrix doHystrix;

    public HystrixValveImpl() {
        /***************************************************************
         * 置HystrixCommand的属性
         * upKey：该命令属于哪一个组，可以帮助我们更好的组织命令。
         * CommandKey：该命令的名称
         * ThreadPoolKey：该命令所属线程池的名称，同样配置的命令会共享同一线程池，若不配置，会默认使用GroupKey作为线程池名称。
         * CommandProperties：该命令的一些设置，包括断路器的配置，隔离策略，降级设置，以及一些监控指标等。
         * ThreadPoolProperties：关于线程池的配置，包括线程池大小，排队队列的大小等
         *****************************************************************/
        super(Setter.withGroupKey(HystrixCommandGroupKey.Factory.asKey("GovernGroup"))
                .andCommandKey(HystrixCommandKey.Factory.asKey("GovernKey"))
                .andThreadPoolKey(HystrixThreadPoolKey.Factory.asKey("GovernThreadPool"))
                .andCommandPropertiesDefaults(HystrixCommandProperties.Setter()
                        .withExecutionIsolationStrategy(HystrixCommandProperties.ExecutionIsolationStrategy.THREAD))
                .andThreadPoolPropertiesDefaults(HystrixThreadPoolProperties.Setter().withCoreSize(10)));
    }

    @Override
    public Object access(ProceedingJoinPoint jp, Method method, DoHystrix doHystrix, Object[] args) {
        this.jp = jp;
        this.method = method;
        this.doHystrix = doHystrix;

        // 设置熔断超时时间
        Setter.withGroupKey(HystrixCommandGroupKey.Factory.asKey("GovernGroup"))
                .andCommandPropertiesDefaults(HystrixCommandProperties.Setter()
                        .withExecutionTimeoutInMilliseconds(doHystrix.timeoutValue()));

        return this.execute();
    }

    @Override
    protected Object run() throws Exception {
        try {
            return jp.proceed();
        } catch (Throwable throwable) {
            return null;
        }
    }

    @Override
    protected Object getFallback() {
        return JSON.parseObject(doHystrix.returnJson(), method.getReturnType());
    }
}
```



1. 本文主要是关于中间件对现有解决方案组件的包装，如果对熔断保护的内容感兴趣可以深入学习 Hystrix
2. HystrixValveImpl 主要是对 Hystrix 熔断保护的封装，通过继承 HystrixCommand 构造函数中配置启动参数
3. 在切面接口方法调用中，设置超时熔断时间，withExecutionTimeoutInMilliseconds(doHystrix.timeoutValue()) 这个时间信息就是自定义注解中的配置信息
4. 另外这里有一个抽象方法 run() 和 重写的方法 getFallback()，它们分别是返回正确方法调用结果和熔断保护时候返回的对象信息。

### **4. 切面逻辑实现**

**[cn.bugstack.middleware.hystrix.annotation.DoHystrixPoint.java](http://cn.bugstack.middleware.hystrix.annotation.dohystrixpoint.java/)**

```

@Aspect
@Component
public class DoHystrixPoint {

    @Pointcut("@annotation(cn.bugstack.middleware.hystrix.annotation.DoHystrix)")
    public void aopPoint() {
    }

    @Around("aopPoint() && @annotation(doGovern)")
    public Object doRouter(ProceedingJoinPoint jp, DoHystrix doGovern) throws Throwable {
        IValveService valveService = new HystrixValveImpl();
        return valveService.access(jp, getMethod(jp), doGovern, jp.getArgs());
    }

    private Method getMethod(JoinPoint jp) throws NoSuchMethodException {
        Signature sig = jp.getSignature();
        MethodSignature methodSignature = (MethodSignature) sig;
        return jp.getTarget().getClass().getMethod(methodSignature.getName(), methodSignature.getParameterTypes());
    }
}
```



1. @Aspect 定义切面、@Component 定义组件以求被实例化、@Pointcut 定义切点，这些与我们之前的内容一样。
2. @Around("aopPoint() && @annotation(doGovern)") ，这块的处理是本章节新增的，一般在方法入参中并没有直接提供自定义注解的获取，而是通过类和方法再反向找出来。而直接通过方法入参的方式可以更加方便的拿到注解，处理起来也更优雅。
3. 接下来就是方法内容的调用逻辑，[valveService.access](http://valveservice.access/)(jp, getMethod(jp), doGovern, jp.getArgs()); ，这步调用的就是我们包装好的熔断保护服务。

## 四、测试验证

### **1. 工程结构**

hystrix-spring-boot-starter-test

└── src

  └── main

​    └── java

​      ├── cn.bugstack.middleware.test

​      │  ├── interfaces

​      │  │  ├── UserController.java

​      │  │  └── UserInfo.java

​      │  └── ApiTestApplication.java

​      └── resources

​        └── META-INF 

​          └── application.yml

**工程源码**：**https://gitcode.net/KnowledgePlanet/SpringBootStarter/hystrix-spring-boot-starter-test**

测试工程主要包括启动类 ApiTestApplication、Api接口类 UserController、配置信息 [application.yml](http://application.yml/)，这三面内容。

另外在工程 Maven 配置中会引入到我们开发好的超时熔断中间件服务，如下：

```
<!-- 服务治理，熔断 -->
<dependency>
    <groupId>cn.bugstack.middleware</groupId>
    <artifactId>hystrix-spring-boot-starter</artifactId>
    <version>1.0.0-SNAPSHOT</version>
</dependency>
```

### **2. 接口方法使用中间件注解**

```
/**
 * 测试：http://localhost:8081/api/queryUserInfo?userId=aaa
 */
@DoHystrix(timeoutValue = 350, returnJson = "{\"code\":\"1111\",\"info\":\"调用方法超过350毫秒，熔断返回！\"}")
@RequestMapping(path = "/api/queryUserInfo", method = RequestMethod.GET)
public UserInfo queryUserInfo(@RequestParam String userId) throws InterruptedException {
  logger.info("查询用户信息，userId：{}", userId);
  Thread.sleep(1000);
  return new UserInfo("虫虫:" + userId, 19, "天津市东丽区万科赏溪苑14-0000");
```

1. @DoHystrix 配置需要被熔断保护的方法上，这里设置方法的安全调用时长是 350毫秒，如果熔断保护了则返回 returnJson 中的信息。

### **3. 测试结果**

**接口**：http://localhost:8081/api/queryUserInfo?userId=aaa

queryUserInfo 方法中有一个 [Thread.sleep](http://thread.sleep/)(1000);，在测试的时候可以去掉和添加验证不同的情况。

**方法调用时长小于350毫秒访问**
```json
{"code":"0000","info":"success","name":"虫虫:aaa","age":19,"address":"天津市东丽区万科赏溪苑14-0000"}
```

**方法调用时长大于350毫秒访问**
```json
{"code":"1111","info":"调用方法超过350毫秒，熔断返回！","name":null,"age":null,"address":null}
```

1. 通过两次不同的调用结果可以看到，超时调用熔断保护已经生效了。
2. 有了中间件包装我们再使用这样的功能就方便多了，也能感受到中间件对于底层调用的屏蔽。

## 五、开源项目
[源码地址]()
