## 一、需求背景

在服务治理层面，我们通常会想到熔断、降级、限流、切量等各类操作，因此也把这些功能集成到统一的中间件中供业务系统使用。



但有些时候每个业务系统因需求的多样性，可能还会有一些额外的场景需要被治理，如果这个时候中间件原有的功能就不能满足了，不得已每一个业务系统又单独开发相应的功能，最终导致的情况就是这个中间件处于一个尴尬的存在，删也不行，留也不好。



因此我们需要让中间件在设计的时候，给业务留出一个可自定义逻辑的口子，让业务系统可以自行扩展一些服务功能。这样对于中间件来说，就有了成长的时间，可以再后续把通用的同类功能，完善在中间里，待后续版本发布时就可以迭代升级使用了。

## 二、方案设计

方案设计也是目标实现的具体路径，而我们的目标就是让方法可扩展的新增其他方法的调用。也就是原有的方法X，可以加入其他方法A并且优先调用。

那么我们可以通过在中间件里，加入其他方法的自定义注解配置和拦截操作，这样就可以在调用现有方法时先执行用户自己定义的配置方法。整体的设计方案如图 6-1 自定义拦截方法中间件设计。

![img](/blogs/_archive-2024-assets/558ae0b079145a91ea92.webp)

1. 使用自定义注解和切面技术，拦截和执行新增的扩展方法。
2. 拦截后到方法后，就可以执行此方法内容。这里需要注意，扩展的方法需要有一定的约束，例如相同的入参信息，以及固定的出参类型，这样我们使用布尔类型作为出参类型。

## 三、技术实现

### **1. 工程结构**

methodext-spring-boot-starter

└── src

  ├── main

  │  └── java

  │    └── cn.bugstack.middleware.methodext

  │      ├── annotation

  │      │  └── DoMethodExt.java

  │      └── DoMethodExtPoint.java

  └── test

​    └── java

​      └── cn.bugstack.middleware.test

​        └── ApiTest.java

**工程源码**：**https://gitcode.net/KnowledgePlanet/SpringBootStarter/methodext-spring-boot-starter**

超时熔断中间件类关系，如图 6-2

![img](/blogs/_archive-2024-assets/9a09974fa66b33cdf7cb.webp)



这个中间件的设计实现过程也非常简单，但这些都是不同思路的具体落地，在实现每一种形式的中间件时，可以作为参考。在此中间件的实现中主要包括以下几点：

1. DoMethodExt，扩展方法的自定义注解，用于配置新增方法和返回信息。*如果说你希望使用新增方法的返回值，那么也可以实现。在整篇阅读完以后可以迭代此类功能*
2. DoMethodExtPoint，切面拦截依然是以自定义注解为入口，拦截已经被扩展了的方法，做相应的操作。

### **2. 自定义注解**

```
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface DoMethodExt {
  String method() default "";
  String returnJson() default "";
}
```

1. @Retention(RetentionPolicy.RUNTIME) 标记注解在 JVM 运行时可见
2. @Target(ElementType.METHOD) 标记注解的作用域在方法层面 ElementType.METHOD
3. method，用于配置用户的新增扩展方法，这里目前支持的单个方法，也可以设计成多个方法或者其他类中的方法。
4. returnJson，调用扩展方法拦截时返回的结果配置。

### **3. 切面逻辑实现**

```
@Aspect
@Component
public class DoMethodExtPoint {

    private Logger logger = LoggerFactory.getLogger(DoMethodExtPoint.class);

    @Pointcut("@annotation(cn.bugstack.middleware.methodext.annotation.DoMethodExt)")
    public void aopPoint() {
    }

    @Around("aopPoint()")
    public Object doRouter(ProceedingJoinPoint jp) throws Throwable {
        // 获取内容
        Method method = getMethod(jp);
        DoMethodExt doMethodExt = method.getAnnotation(DoMethodExt.class);

        // 获取拦截方法
        String methodName = doMethodExt.method();

        // 功能处理
        Method methodExt = getClass(jp).getMethod(methodName, method.getParameterTypes());

        Class<?> returnType = methodExt.getReturnType();

        // 判断方法返回类型
        if (!returnType.getName().equals("boolean")) {
            throw new RuntimeException("annotation @DoMethodExt set method：" + methodName + " returnType is not boolean");
        }

        // 拦截判断正常，继续
        boolean invoke = (boolean) methodExt.invoke(jp.getThis(), jp.getArgs());

        // 返回结果
        return invoke ? jp.proceed() : JSON.parseObject(doMethodExt.returnJson(), method.getReturnType());
    }

    private Method getMethod(JoinPoint jp) throws NoSuchMethodException {
        Signature sig = jp.getSignature();
        MethodSignature methodSignature = (MethodSignature) sig;
        return jp.getTarget().getClass().getMethod(methodSignature.getName(), methodSignature.getParameterTypes());
    }

    private Class<? extends Object> getClass(JoinPoint jp) throws NoSuchMethodException {
        return jp.getTarget().getClass();
    }
}
```

根据自定义注解作为切点拦截到的方法以后，开始做切面处理。主要包含以下几点：

1. 获取自定义注解中的信息，主要是拿到扩展的方法名称和返回内容。
2. getClass(jp).getMethod(methodName, method.getParameterTypes()) 获取自定义方法，并在后面判断了此扩展方法的返回类型，这里我们设置为布尔类型校验。
3. 接下来就是自定义方法的调用，执行的就是用户在自定义方法中实现的内容。
4. 最后根据自定义方法的返回结果，如果是 true 则放行，否则返回 returnJson 中的配置结果。

## 四、测试验证

### **1. 工程结构**

methodext-spring-boot-starter-test

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

**工程源码**：**https://gitcode.net/KnowledgePlanet/SpringBootStarter/methodext-spring-boot-starter-test**

测试工程主要包括启动类 ApiTestApplication、Api接口类 UserController、配置信息 [application.yml](http://application.yml/)，这三面内容。

另外在工程 Maven 配置中会引入到我们开发好的自定义拦截方法中间件服务，如下：

```
<!-- 服务治理，扩展方法 -->
<dependency>
    <groupId>cn.bugstack.middleware</groupId>
    <artifactId>methodext-spring-boot-starter</artifactId>
    <version>1.0.0-SNAPSHOT</version>
</dependency>
```

### **2. 接口方法使用中间件注解**

```
/**
 * 放行：http://localhost:8081/api/queryUserInfo?userId=aaa
 * 拦截：http://localhost:8081/api/queryUserInfo?userId=bbb
 */
@DoMethodExt(method = "blacklist", returnJson = "{\"code\":\"1111\",\"info\":\"自定义校验方法拦截，不允许访问！\"}")
@RequestMapping(path = "/api/queryUserInfo", method = RequestMethod.GET)
public UserInfo queryUserInfo(@RequestParam String userId) {
    logger.info("查询用户信息，userId：{}", userId);
    return new UserInfo("虫虫:" + userId, 19, "天津市东丽区万科赏溪苑14-0000");
}

/**
 * 自定义黑名单，拦截方法
 */
public boolean blacklist(@RequestParam String userId) {
    if ("bbb".equals(userId) || "222".equals(userId)) {
        logger.info("拦截自定义黑名单用户 userId：{}", userId);
        return false;
    }
    return true;
}
```

1. @DoMethodExt，是用于添加自定义扩展方法的注解，method 配置的在本类中新增的方法。
2. blacklist，在这个方法中我们添加了一个类似黑名单用户拦截的方法，凡是黑名单中的用户，bbb、222，都会被拦截。

### **3. 测试结果**

**不在黑名单拦截调用**

**接口**：http://localhost:8081/api/queryUserInfo?userId=aaa
```json
{"code":"0000","info":"success","name":"虫虫:aaa","age":19,"address":"天津市东丽区万科赏溪苑14-0000"}
```

**被自定义黑名单拦截**

**接口**：http://localhost:8081/api/queryUserInfo?userId=bbb
```json
{"code":"1111","info":"自定义校验方法拦截，不允许访问！","name":null,"age":null,"address":null}
```

1. userId 入参在我们自定义的扩展方法中 blacklist，已经对 bbb、222做了拦截限制。
2. 接下来两个接口的不同入参访问，也可以看到对黑名单用户 bbb 已经拦截生效。
3. 其实并不一定非得是黑名单拦截，也可以是其他业务逻辑的拦截，可以自行扩展其他方式。、


## 五、开源项目
[源码地址]()
