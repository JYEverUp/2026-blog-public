### xml配置

springboot自带logback的依赖，不需要导入任何包。我们只需要在项目路径下创建文件`logback.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <!--日志路径 -->
  <property name="LOG_PATH" value="/data/logs/mallchat-custom-server"/>
  <property name="LOG_FILE" value="mallchat-custom-server"/>
  <!-- 格式化-->
  <property name="CONSOLE_LOG_PATTERN"
    value="|%level|%d{yyyy-MM-dd HH:mm:ss.SSS}|%thread|%X{tid}|uid=%X{uid}|%msg|%X{callChain}%n"/>

  <include resource="org/springframework/boot/logging/logback/defaults.xml"/>
  <include resource="org/springframework/boot/logging/logback/console-appender.xml"/>

  <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
    <encoder >
      <pattern>${CONSOLE_LOG_PATTERN}</pattern>
    </encoder>
  </appender>
  <!-- 全部日志的配置-->
  <appender name="fileAppender" class="ch.qos.logback.core.rolling.RollingFileAppender">
    <file>${LOG_PATH}/${LOG_FILE}.log</file>
    <append>true</append>
    <encoder >
      <pattern>${CONSOLE_LOG_PATTERN}</pattern>
    </encoder>
    <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
      <!-- 按天生成日志文件 -->
      <fileNamePattern>
        ${LOG_PATH}/archived/${LOG_FILE}.%d{dd-MM-yyyy}.log
      </fileNamePattern>
      <!--保留天数-->
      <maxHistory>30</maxHistory>
      <!--单个文件的大小-->
      <totalSizeCap>5GB</totalSizeCap>
    </rollingPolicy>

  </appender>
  <!-- error日志的配置-->
  <appender name="fileError" class="ch.qos.logback.core.rolling.RollingFileAppender">
    <filter class="ch.qos.logback.classic.filter.LevelFilter">
      <level>ERROR</level>
      <onMatch>ACCEPT</onMatch>
      <onMismatch>DENY</onMismatch>
    </filter>
    <file>${LOG_PATH}/${LOG_FILE}.error.log</file>
    <append>true</append>
    <encoder >
      <pattern>${CONSOLE_LOG_PATTERN}</pattern>
    </encoder>
    <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
      <fileNamePattern>
        ${LOG_PATH}/archived/${LOG_FILE}.%d{dd-MM-yyyy}.error.log
      </fileNamePattern>
      <maxHistory>30</maxHistory>
      <totalSizeCap>2GB</totalSizeCap>
    </rollingPolicy>
  </appender>

  <root level="info">
    <!--文件输出-->
    <appender-ref ref="fileAppender"/>
    <appender-ref ref="fileError"/>
    <!--制台输出-->
    <appender-ref ref="STDOUT"/>
  </root>

</configuration>
```

启动项目，就可以看到打印的日志格式了

![image-20240924201025847](/blogs/_archive-2024-assets/d24cc38be1a35da42a2d.webp)

### 日志格式化

仔细看我们日志的格式化中

```tsx
|%level|%d{yyyy-MM-dd HH:mm:ss.SSS}|%thread|%X{tid}|uid=%X{uid}|%msg|%X{callChain}%n
```

其中有两个自定义参数 `tid`和`uid`，需要将他们放入logback的`MDC`上下文中，这样日志在打印的时候就可以打印出来。

#### 链路追踪-tid

很多时候排查某个接口的问题，需要将接口内的所有日志查出来，看看哪一步出了问题。这时候就需要有个接口请求的唯一标识。在分布式项目下一般可以用`sleuth`或者`skywalking`。对于目前还是单体项目的抹茶来说，我们只需要在controller入口的时候，通过拦截器，设置一个uuid进去作为请求唯一标识即可。

**过滤器注入tid**

```tsx
@Slf4j
@WebFilter(urlPatterns = "/*")
public class HttpTraceIdFilter implements Filter {

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) throws IOException, ServletException {
        String tid = UUID.randomUUID().toString();
        MDC.put(MDCKey.TID, tid);
        chain.doFilter(request, response);
    }

}
```

其实很简单，MDC的底层就是个threadlocal，所以我们如果在请求中又开了异步，链路追踪就会失效。当然我们也可以在开启异步线程的时候把上下文带进去。

**日志排查**

只需要在服务器输入命令

```bash
grep "7eb0c96e-9296-4eec-8a9b-1d9ffc09949b" mallchat-custom-server.log 
```

就可以抓到某次请求的所有日志

![img](/blogs/_archive-2024-assets/666bcd8b5f76230dc4dc.webp)

#### uid

当然我们也有相应的需求想抓出某个用户的请求日志，所以日志中最好是也打印出uid。

uid也是在每次请求的拦截器中去校验，解析，注入。具体原理可参考[用户认证，鉴权，续期，我是怎么做的？](https://www.yuque.com/snab/mallcaht/sk1l1z8lu2gd2ioe)

![image-20240924201040827](/blogs/_archive-2024-assets/502ddf3ec63e36c6b7e6.webp)

有了uid，我们就可以通过日志查出某个用户的所有请求

```plain
grep "uid=10026" mallchat-custom-server.log
```

![img](/blogs/_archive-2024-assets/94a09c9cafbf00f58680.webp)
