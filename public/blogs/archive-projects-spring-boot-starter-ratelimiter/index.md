## **一、需求背景**

通常我们可以知道一个系统服务在正常的业务增速下的流量大小，基本也是基于这个流量大小的几倍来扩容服务和系统压测验证的。如果后续有相应的业务推广或者活动，一般都会提前报备，再由研发侧做相应的扩容。

但如果我们的系统服务已经基本稳定在一个可承载的安全体量范围，对于突发或者恶意攻击的访问都需要拦截在外，避免系统被这样的流量拖垮或者打挂掉。

因此我们需要在系统开发中使用限流机制来保护系统，但同样的这部分功能并不属于业务系统逻辑范围，它只是通用非业务的一部分共性需求，所以我们提出统一的解决方案，免去所有研发都做重复的工作。

## **三、方案设计**

RateLimiter 是令牌桶思想的一个实现，可实现流量整形、资源访问速率控制，在分布式部署的系统中大多数也是使用 RateLimiter 做限流处理。

这里的方案是为了简化对于 RateLimiter 的使用，也就是不需要研发人员关心怎么实例化到硬编码在业务代码中。因此我们需要把这样的组件型功能服务，包装到中间件里，让使用方可以更简单的集成到开发系统中。整体的设计方案如图 5-1 调用限流中间件框架设计。

![img](/blogs/_archive-2024-assets/17d537addace579db578.webp)

1. 使用自定义注解和切面技术，拦截需要被限流保护的方法。
2. 拦截后到方法后，就可以通过 RateLimiter 给方法设定已配置好的调用限流处理。

## **四、技术实现**

### **1. 工程结构**

ratelimiter-spring-boot-starter

└── src

  ├── main

  │  └── java

  │    └── cn.bugstack.middleware.ratelimiter

  │      ├── annotation

  │      │  └── DoRateLimiter.java

  │      ├── valve

  │      │  ├── impl

  │      │  │ └── RateLimiterValve.java 

  │      │  └── IValveService.java

  │      └── DoRateLimiterPoint.java

  └── test

​    └── java

​      └── cn.bugstack.middleware.test

​        └── ApiTest.java

**工程源码**：**https://gitcode.net/KnowledgePlanet/SpringBootStarter/ratelimiter-spring-boot-starter**

超时熔断中间件类关系，如图 5-2

![img](/blogs/_archive-2024-assets/67aa343fcb7cbabce05c.webp)

在这个中间件的实现中也没有额外的 yml 配置，仅是对切面的运用和 RateLimiter 的包装，包含如下信息：

1. DoRateLimiter 自定义注解中需要配置方法的超时时长和拦截后的返回信息。
2. DoRateLimiterPoint 自定义切面的实现比较简单，只是拦截方法和处理相应的操作。
3. RateLimiterValve 是限流的具体实现，这里的接口实现方式扩展过熔断保护，在实际使用中可以把同类的功能开发到一个中间件里。

### **2. 自定义注解**

```
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface DoRateLimiter {

  double permitsPerSecond() default 0D;  // 限流许可量
  String returnJson() default "";     // 失败结果 JSON
}
```

1. @Retention(RetentionPolicy.RUNTIME) 标记注解在 JVM 运行时可见
2. @Target(ElementType.METHOD) 标记注解的作用域在方法层面 ElementType.METHOD
3. permitsPerSecond，方法限流许可量，超过这个量就会返回 returnJson 中的配置信息
4. returnJson，调用限流时返回的结果

### **3. 限流调用服务包装**

```
public class RateLimiterValve implements IValveService {

    @Override
    public Object access(ProceedingJoinPoint jp, Method method, DoRateLimiter doRateLimiter, Object[] args) throws Throwable {
        // 判断是否开启
        if (0 == doRateLimiter.permitsPerSecond()) return jp.proceed();

        String clazzName = jp.getTarget().getClass().getName();
        String methodName = method.getName();
        String key = clazzName + "." + methodName;

        if (null == Constants.rateLimiterMap.get(key)) {
            Constants.rateLimiterMap.put(key, RateLimiter.create(doRateLimiter.permitsPerSecond()));
        }

        RateLimiter rateLimiter = Constants.rateLimiterMap.get(key);
        if (rateLimiter.tryAcquire()) {
            return jp.proceed();
        }

        return JSON.parseObject(doRateLimiter.returnJson(), method.getReturnType());
    }
}
```

1. RateLimiterValve 中主要包装了对 RateLimiter 的简单使用，如果对 RateLimiter 还没使用过或者想多了解，可以单独学习下。
2. 这里的 String key = clazzName + "." + methodName; 会给每一个方法记录不同的调用限流设置保留，如果在实际的使用中会需要加锁处理，避免创建重复对象。
3. 最后是rateLimiter.tryAcquire()的使用判断是否限流保护，如果超过限流就返回我们预设的 doRateLimiter.returnJson() 信息。

### **4. 切面逻辑实现**

```
@Component
public class DoRateLimiterPoint {

    @Pointcut("@annotation(cn.bugstack.middleware.ratelimiter.annotation.DoRateLimiter)")
    public void aopPoint() {
    }

    @Around("aopPoint() && @annotation(doRateLimiter)")
    public Object doRouter(ProceedingJoinPoint jp, DoRateLimiter doRateLimiter) throws Throwable {
        IValveService valveService = new RateLimiterValve();
        return valveService.access(jp, getMethod(jp), doRateLimiter, jp.getArgs());
    }

    private Method getMethod(JoinPoint jp) throws NoSuchMethodException {
        Signature sig = jp.getSignature();
        MethodSignature methodSignature = (MethodSignature) sig;
        return jp.getTarget().getClass().getMethod(methodSignature.getName(), methodSignature.getParameterTypes());
    }
}
```

1. @Aspect 定义切面、@Component 定义组件以求被实例化、@Pointcut 定义切点，这些与我们之前的内容一样。
2. @Around("aopPoint() && @annotation(doRateLimiter)") ，这块的处理可以直接通过方法入参的方式可以更加方便的拿到注解，处理起来也更优雅。
3. 接下来就是方法内容的调用逻辑，[valveService.access](http://valveservice.access/)(jp, getMethod(jp), doGovern, jp.getArgs()); ，这步调用的就是我们包装好的限流保护服务。*这里的调用可以和熔断保护联想起来，也就是这些服务可以统一包装在一起。*

## **五、测试验证**

### **1. 工程结构**

ratelimiter-spring-boot-starter-test

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

**工程源码**：**https://gitcode.net/KnowledgePlanet/SpringBootStarter/ratelimiter-spring-boot-starter-test**

测试工程主要包括启动类 ApiTestApplication、Api接口类 UserController、配置信息 [application.yml](http://application.yml/)，这三面内容。

另外在工程 Maven 配置中会引入到我们开发好的调用限流中间件服务，如下：

```
<!-- 服务治理，限流 -->
<dependency>
    <groupId>cn.bugstack.middleware</groupId>
    <artifactId>ratelimiter-spring-boot-starter</artifactId>
    <version>1.0.0-SNAPSHOT</version>
</dependency>
```

### **2. 接口方法使用中间件注解**

```
/**

 * 测试：http://localhost:8081/api/queryUserInfo?userId=aaa

 */

@DoRateLimiter(permitsPerSecond = 1, returnJson = "{\"code\":\"1111\",\"info\":\"调用方法超过最大次数，限流返回！\"}")

@RequestMapping(path = "/api/queryUserInfo", method = RequestMethod.GET)

public UserInfo queryUserInfo(@RequestParam String userId) throws InterruptedException {

  logger.info("查询用户信息，userId：{}", userId);

  return new UserInfo("虫虫:" + userId, 19, "天津市东丽区万科赏溪苑14-0000");

}
```

1. @DoRateLimiter 配置需要被限流保护的方法上，这里设置方法的最大每秒的调用次数，如果超过限流保护了则返回 returnJson 中的信息。

### **3. 测试结果**

**接口**：http://localhost:8081/api/queryUserInfo?userId=aaa

**方法调用次数每秒小于1次**

```json
{"code":"0000","info":"success","name":"虫虫:aaa","age":19,"address":"天津市东丽区万科赏溪苑14-0000"}
```

**方法调用次数每秒大于1次**
```json
{"code":"1111","info":"调用方法超过最大次数，限流返回！","name":null,"age":null,"address":null}
```

1. 通过两次不同的调用结果可以看到，超时调用限流保护已经生效了。
2. 有了中间件包装我们再使用这样的功能就方便多了，同时我们还可以把类似的功能包装在一起。

## 五、开源项目
[源码地址]()
