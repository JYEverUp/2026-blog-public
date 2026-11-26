# 接口报错，如何快速定位日志？
## 要解决的问题？
接口报错，如何快速定位问题？这个需要日志的辅助，一般错误日志中有详细的堆栈信息，具体是哪行代码报错，都可以看到。
要想快速定位问题，前提是要能够快速定位日志。
## 海量日志，如何定位呢？
日志量一般都是很大的，如何能够从大量日志中找到自己需要的日志呢？
## 解决方案
1、服务端入口处可以生成一个唯一的id，记做：traceId
2、日志中均需要输出traceId的值
3、接口返回值中，添加一个通用的字段：traceId，将上面的traceId作为这个字段的值
4、这样前端发现接口有问题的时候，直接将这个traceId提供给我们，我们便可以在日志中快速查询出对应的日志。
## 代码如何实现？（4步）
### 1、添加一个TraceFilter
> 拦截所有请求，入口生成一个唯一的traceId，放到ThreadLocal中
```java
@Order(Ordered.HIGHEST_PRECEDENCE)
@WebFilter(urlPatterns = "/**", filterName = "TraceFilter")
public class TraceFilter extends OncePerRequestFilter {
    public static Logger logger = LoggerFactory.getLogger(TraceFilter.class);
    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
        String traceID = IdUtil.fastSimpleUUID();
        TraceUtils.setTraceId(traceID);
        long st = System.currentTimeMillis();
        try {
            filterChain.doFilter(request, response);
        } finally {
            long et = System.currentTimeMillis();
            logger.info("请求地址:{},耗时(ms):{}", request.getRequestURL().toString(), (et - st));
            TraceUtils.removeTraceId();
        }
    }
}
```
### 2、日志中输出traceId
需要在MDC中设置一下traceId：MDC.put("traceId", traceId); 
MDC是logback为我们提供的一个扩展的入口，可以向里面放入一些键值对，然后在logback中的日志中就可以通过这个traceId获取到对应的值
如下，logback.xml中使用`%X{traceId}`可以获取到MDC中设置的traceId
![image-20240410145620307](/blogs/_archive-2024-assets/7793654eedcfe8ba3ed1.webp)
### 3、返回值中添加通用字段traceId
我们这里使用的是通用返回值Result，也就是所有接口的返回值均是Result类型，定义如下，我们在里面添加了一个traceId字段，这个值如何写入呢？看后面
![image-20240410153538758](/blogs/_archive-2024-assets/bd4887ced09ae8a7ca6c.webp)
### 4、通过aop将traceId写入响应结果的Result中
下面我们使用aop创建了一个环绕通知，会拦截controller的所有方法，以及全局异常处理器的方法，对Result类型的返回值进行统一处理，将traceId设置到Result中traceId字段中
```java
@Aspect
@Order(Ordered.LOWEST_PRECEDENCE)
public class ResultTraceIdAspect {
    @Pointcut("execution(* com.itsoku..*Controller.*(..)) ||execution(* com.itsoku.lesson017.web.GlobalExceptionHandler.*(..))")
    public void pointCut() {
    }
    @Around("pointCut()")
    public Object around(ProceedingJoinPoint pjp) throws Throwable {
        Object object = pjp.proceed();
        if (object instanceof Result) {
            ((Result<?>) object).setTraceId(TraceUtils.getTraceId());
        }
        return object;
    }
}
```
## 测试效果
访问接口`http://localhost:8080/`，输出
```json
{
  "success": true,
  "data": "欢迎和路人一起学习《
