## **一、需求背景**

在互联网这种多数面向C端用户场景下的产品功能研发完成交付后，通常并不会直接发布上线。尤其是在一个原有服务功能已经沉淀了大量用户时，不断的迭代开发新增需求下，更不会贸然发布上线。

虽然在测试环境、预发环境都有了相应功能的验证，但在真实的用户场景下可能还会存在其他隐患问题。那么为了更好的控制系统风险，通常需要研发人员在代码的接口层，提供白名单控制。上线初期先提供可配置的白名单用户进行访问验证，控制整体的交付风险程度。

白名单确实可以解决接口功能或者服务入口的访问范围风险，那么这里有一个技术方案实现问题。就是如果研发人员在所有的接口上都加这样的白名单功能，那么就会非常耗费精力，同时在功能不再需要时可能还需要将代码删除。在这个大量添加和修改重复功能的代码过程中，也在一定程度上造成了研发成本和操作风险。所以站在整体的系统建设角度来说，我们需要有一个通用的白名单服务系统，减少研发在这方面的重复开发。

## **二、方案设计**

白名单服务属于业务系统开发过程中可重复使用的通用功能，所以我们可以把这样的工具型功能单独提炼出来设计成技术组件，由各个需要的使用此功能的系统工程引入使用。整体的设计方案如图 3-1 白名单中间件框架设计。

![img](/blogs/_archive-2024-assets/f09b6691592c2b96d0f0.webp)



1. 使用自定义注解、切面技术和SpringBoot对于配置文件的处理方式，开发白名单中间件。
2. 在中间件中通过提取指定字段的入参与配置文件白名单用户列表做比对确认是否允许访问。
3. 最后把开发好的中间件引入到需要依赖白名单服务的系统，在SpringBoot启动时进行加载。

## **三、技术实现**

### **1. 工程结构**

whitelist-spring-boot-starter

└── src

  ├── main

  │  └── java

  │    ├── cn.bugstack.middleware.whitelist

  │    │  ├── annotation

  │    │  │  └── DoWhiteList.java

  │    │  ├── config

  │    │  │  ├── WhiteListAutoConfigure.java

  │    │  │  └── WhiteListProperties.java

  │    │  └── DoJoinPoint.java

  │    └── resources

  │      └── META-INF 

  │        └── spring.factories

  └── test

​    └── java

​      └── cn.bugstack.middleware.test

​        └── ApiTest.java

**工程源码**：**https://gitcode.net/KnowledgePlanet/SpringBootStarter/whitelist-spring-boot-starter**

白名单中间件类关系，如图 3-2

![img](/blogs/_archive-2024-assets/d02248883b02c220ced1.webp)

白名单控制中间件整个实现工程并不复杂，其核心点在于对切面的理解和运用，以及一些配置项需要按照 SpringBoot 中的实现方式进行开发。

1. DoWhiteList，是一个自定义注解。它作用就是在需要使用到的白名单服务的接口上，添加此注解并配置必要的信息。*接口入参提取字段属性名称、拦截后的返回信息*
2. WhiteListAutoConfigure，配置下是对 SpringBoot yml 文件的使用，这样就可以把配置到 yml 文件的中白名单信息读取到中间件中。
3. DoJoinPoint，是整个中间件的核心部分，它负责对所有添加自定义注解的方法进行拦截和逻辑处理。

那么，接下来我们就看一下每个类的实现过程和内容讲解。

### **2. 自定义注解**

@Retention(RetentionPolicy.RUNTIME)

@Target(ElementType.METHOD)

@Inherited

public @interface DoWhiteList {

  String key() default "";

  String returnJson() default "";

}

1. @Retention(RetentionPolicy.RUNTIME)，Annotations are to be recorded in the class file by the compiler and retained by the VM at run time, so they may be read reflectively.
2. @Retention 是注解的注解，也称作元注解。这个注解里面有一个入参信息 RetentionPolicy.RUNTIME 在它的注释中有这样一段描述：Annotations are to be recorded in the class file by the compiler and retained by the VM at run time, so they may be read reflectively.  其实说的就是加了这个注解，它的信息会被带到JVM运行时，当你在调用方法时可以通过反射拿到注解信息。除此之外，RetentionPolicy 还有两个属性 SOURCE、CLASS，其实这三个枚举正式对应了Java代码的加载和运行顺序，Java源码文件 -> .class文件 -> 内存字节码。并且后者范围大于前者，所以一般情况下只需要使用 RetentionPolicy.RUNTIME 即可。
3. @Target 也是元注解起到标记作用，它的注解名称就是它的含义，**目标**，也就是我们这个自定义注解 DoWhiteList 要放在类、接口还是方法上。*在 JDK1.8 中 ElementType 一共提供了10中目标枚举，TYPE、FIELD、METHOD、PARAMETER、CONSTRUCTOR、LOCAL_VARIABLE、ANNOTATION_TYPE、PACKAGE、TYPE_PARAMETER、TYPE_USE，可以参考自己的自定义注解作用域进行设置*
4. 自定义注解 @DoWhiteList 中有两个属性 key、returnJson。key 的作用是配置当前接口入参需要提取的属性，returnJson 的作用是在我们拦截到用户请求后需要给一个返回信息。

### **3. 白名单配置获取**

```
@ConfigurationProperties(prefix = "bugstack.whitelist")
public class WhiteListProperties {
  private String users;
  public String getUsers() {
    return users;
  }
  public void setUsers(String users) {
    this.users = users;
  }
}
```

1. @ConfigurationProperties，用于创建指定前缀( prefix = "bugstack.whitelist" )的自定义配置信息，这样就在 yml 或者 properties 中读取到我们自己设定的配置信息。

```
@Configuration
@ConditionalOnClass(WhiteListProperties.class)
@EnableConfigurationProperties(WhiteListProperties.class)
public class WhiteListAutoConfigure {
  @Bean("whiteListConfig")
  @ConditionalOnMissingBean
  public String whiteListConfig(WhiteListProperties properties) {
​    return properties.getUsers();
  }
}
```

1. @Configuration，可以算作是一个组件注解，在 SpringBoot 启动时可以进行加载创建出 Bean 文件。*因为 @Configuration 注解有一个 @Component 注解*
2. @ConditionalOnClass([WhiteListProperties.class](http://whitelistproperties.class/))，当 WhiteListProperties 位于当前类路径上，才会实例化一个类。除此之外还有其他属于此系列的常用的注解。
3. @ConditionalOnBean 仅仅在当前上下文中存在某个对象时，才会实例化一个 Bean
4. @ConditionalOnClass 某个 CLASS 位于类路径上，才会实例化一个 Bean
5. @ConditionalOnExpression 当表达式为 true 的时候，才会实例化一个 Bean
6. @ConditionalOnMissingBean 仅仅在当前上下文中不存在某个对象时，才会实例化一个 Bean
7. @ConditionalOnMissingClass 某个 CLASS 类路径上不存在的时候，才会实例化一个 Bean
8. @Bean，在 whiteListConfig 方法上我们添加了这个注解以及方法入参 WhiteListProperties properties。这里面包括如下几个内容：
9. properties 配置会被注入进来，当然你也可以选择使用 @Autowired 的方式配置注入在使用属性。
10. 整个方法会在配置信息和Bean注册完成后，开始被实例化加载到 Spring 中。
11. @ConditionalOnMissingBean，现在就用到了这个方法上，代表只会实例化一个 Bean 对象。

### **4. 切面逻辑实现**

```
```java
@Aspect
@Component
public class DoJoinPoint {

    private Logger logger = LoggerFactory.getLogger(DoJoinPoint.class);

    @Resource
    private String whiteListConfig;

    @Pointcut("@annotation(cn.bugstack.middleware.whitelist.annotation.DoWhiteList)")
    public void aopPoint() {
    }

    @Around("aopPoint()")
    public Object doRouter(ProceedingJoinPoint jp) throws Throwable {
        // 获取内容
        Method method = getMethod(jp);
        DoWhiteList whiteList = method.getAnnotation(DoWhiteList.class);

        // 获取字段值
        String keyValue = getFiledValue(whiteList.key(), jp.getArgs());

        logger.info("middleware whitelist handler method：{} value：{}", method.getName(), keyValue);

        if (null == keyValue || "".equals(keyValue)) return jp.proceed();

        String[] split = whiteListConfig.split(",");

        // 白名单过滤
        for (String str : split) {
            if (keyValue.equals(str)) {
                return jp.proceed();
            }
        }

        // 拦截
        return returnObject(whiteList, method);
    }

    private Method getMethod(JoinPoint jp) throws NoSuchMethodException {
        Signature sig = jp.getSignature();
        MethodSignature methodSignature = (MethodSignature) sig;
        return jp.getTarget().getClass().getMethod(methodSignature.getName(), methodSignature.getParameterTypes());
    }

    // 返回对象
    private Object returnObject(DoWhiteList whiteList, Method method) throws IllegalAccessException, InstantiationException {
        Class<?> returnType = method.getReturnType();
        String returnJson = whiteList.returnJson();

        if ("".equals(returnJson)) {
            return returnType.newInstance();
        }

        return JSON.parseObject(returnJson, returnType);
    }

    // 获取属性值
    private String getFiledValue(String filed, Object[] args) {
        String filedValue = null;
        for (Object arg : args) {
            try {
                if (null == filedValue || "".equals(filedValue)) {
                    filedValue = BeanUtils.getProperty(arg, filed);
                } else {
                    break;
                }
            } catch (Exception e) {
                if (args.length == 1) {
                    return args[0].toString();
                }
            }
        }
        return filedValue;
    }
}
```



所以这部分代码比较多，但整体的逻辑实现并不复杂，主要包括如下内容：

1. 使用注解 @Aspect，定义切面类。这是一个非常常用的切面定义方式。
2. @Component 注解，将类生成为 Bean 对象。虽然其他的注解也可以注册 Bean 对象，但 @Component 具有组件含义，符合 Spring 设计的定义。*如果你担心这个切面类在使用过程中有重名，那么还可以在 @Component 注解中指定 Bean 的名字*
3. @Pointcut("@annotation(cn.bugstack.middleware.whitelist.annotation.DoWhiteList)")，定义切点。在 Pointcut 中提供了很多的切点寻找方式，有指定方法名称的、有范围筛选表达式的，也有我们现在通过自定义注解方式的。一般在中间件开发中，自定义注解方式使用的比较多，因为它可以更加灵活的运用到各个业务系统中。
4. @Around("aopPoint()")，可以理解为是对方法增强的织入动作，有了这个注解的效果就是在你调用已经加了自定义注解 @DoWhiteList 的方法时，会先进入到此切点增强的方法。那么这个时候就你可以做一些对方法的操作动作了，比如我们实现的白名单用户拦截还是放行。
5. 在 doRouter 中拦截方法后，获取方法上的自定义注解。getMethod(jp)，其实只要获取到方法，就可以通过方法在拿到注解信息，这部分可以参照源码内容。*另外获取注解的手段还有其他方式，会在后文中展示出来*
6. 最后就是对当前拦截方法校验结果的操作，是拦截还是放行。其实拦截就是返回我们在自定义注解配置的 JSON 信息生成对象返回，放行则是调用 jp.proceed(); 方法，让整个代码块向下继续执行。

## 四、测试验证

### **1. 工程结构**

whitelist-spring-boot-starter-test

└── src

  └── main

​    └── java

​      ├── cn.bugstack.middleware.whitelist.test

​      │  ├── interfaces

​      │  │  ├── UserController.java

​      │  │  └── UserInfo.java

​      │  └── ApiTestApplication.java

​      └── resources

​        └── META-INF 

​          └── application.yml

**工程源码**：**[https://gitcode.net/KnowledgePlanet/SpringBootStarter](https://gitcode.net/KnowledgePlanet/SpringBootStarter/whitelist-spring-boot-starter-test)**

测试工程主要包括启动类 ApiTestApplication、Api接口类 UserController、配置信息 [application.yml](http://application.yml/)，这三面内容。

另外在工程 Maven 配置中会引入到我们开发好的白名单中间件服务，如下：

```
<dependency>
    <groupId>cn.bugstack.middleware</groupId>
    <artifactId>whitelist-spring-boot-starter</artifactId>
    <version>1.0.0-SNAPSHOT</version>
</dependency>
```

### **2. 在 yml 配置白名单用户**

```
server:
 port: 8081
# 白名单用户
bugstack:
 whitelist:
  users: aaa,111,xiaofuge
```

1. 以上的这种配置方式只是基于本地的配置，并没有服务端注册中心那种方式。
2. 通过这样的配置方式可以让学习中间件开发的研发人员更好的看到最核心的实现，也能让大家更加方便测试。如果你已经学会了，那么可以尝试在中间件中添加一种注册中心来配置白名单，这样就可以在不重启服务的情况下动态变化白名单列表了。
3. users，白名单用户ID是逗号相隔的，这里的配置用户ID都可以正常访问系统。

### **3. 接口方法使用中间件注解**

/**

 \* 通过：http://localhost:8081/api/queryUserInfo?userId=aaa

 \* 拦截：http://localhost:8081/api/queryUserInfo?userId=123

 */

```
@DoWhiteList(key = "userId", returnJson = "{\"code\":\"1111\",\"info\":\"非白名单可访问用户拦截！\"}")
@RequestMapping(path = "/api/queryUserInfo", method = RequestMethod.GET)
public UserInfo queryUserInfo(@RequestParam String userId) {
  logger.info("查询用户信息，userId：{}", userId);
  return new UserInfo("虫虫:" + userId, 19, "天津市东丽区万科赏溪苑14-0000");
}
```

1. @DoWhiteList 自定义注解配置在方法上，两个参数信息一个配置 userId，另外一个配置方法拦截后的返回信息 {\"code\":\"1111\",\"info\":\"非白名单可访问用户拦截！\"}

### **4. 测试结果**

**白名单用户访问**

**接口**：http://localhost:8081/api/queryUserInfo?userId=aaa

```
{
  "code": "0000",
  "info": "success",
  "name": "虫虫:aaa",
  "age": 19,
  "address": "天津市东丽区万科赏溪苑14-0000"
}
```



**普通用户访问**

**接口**：http://localhost:8081/api/queryUserInfo?userId=123

```
{
  "code": "1111",
  "info": "非白名单可访问用户拦截！",
  "name": null,
  "age": null,
  "address": null
}
```

**服务端日志**

```
2021-02-27 15:38:18.931 INFO 19653 --- [nio-8081-exec-1] o.s.web.servlet.DispatcherServlet    : Completed initialization in 7 ms
2021-02-27 15:38:18.984 INFO 19653 --- [nio-8081-exec-1] c.b.middleware.whitelist.DoJoinPoint   : middleware whitelist handler method：queryUserInfo value：123
2021-02-27 15:38:29.555 INFO 19653 --- [nio-8081-exec-2] c.b.middleware.whitelist.DoJoinPoint   : middleware whitelist handler method：queryUserInfo value：aaa
2021-02-27 15:38:29.563 INFO 19653 --- [nio-8081-exec-2] c.b.m.w.test.interfaces.UserController  : 查询用户信息，userId：aaa
2021-02-27 15:52:24.510 INFO 19653 --- [nio-8081-exec-4] c.b.middleware.whitelist.DoJoinPoint   : middleware whitelist handler method：queryUserInfo value：123
2021-02-27 16:01:25.852 INFO 19653 --- [extShutdownHook] o.s.s.concurrent.ThreadPoolTaskExecutor : Shutting down ExecutorService 'applicationTaskExecutor'
```

1. 通过测试结果我们可以看到，白名单中间件已经起到了拦截作用。通过不同用户ID的访问，返回是否拦截的结果信息。

## 五、开源项目
[源码地址](https://github.com/18194085604/whitelist-spring-boot-starter.git)
