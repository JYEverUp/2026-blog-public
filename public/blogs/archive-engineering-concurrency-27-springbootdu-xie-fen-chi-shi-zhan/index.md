#  SpringBoot读写分离实战
## 本文内容
- 通过一个注解搞定读写分离
- 支持查询强制路由到主库
## 涉及到的技术
- SpringBoot 2.7.13
- MyBatis
- 多数据源路由
- AOP环绕通知
## 背景
大多数系统都是读多写少，为了降低数据库的压力，可以对主库创建多个从库，从库自动从主库同步数据，程序中将写的操作发送到主库，将读的操作发送到从库去执行。
也可以强制读主库，这种可以解决，主从延迟的情况下，主库写入数据后立即查询从库，查询不到的问题。
## 实现思路
1. 可以定义一个读写分离的注解：@ReadWrite(value=路由策略)，路由策略主要有下面3种
   ```java
   public enum ReadWriteRoutingStrategy {
       MASTER, //路由到主库
       SLAVE, //路由到从库
       HIT_MASTER //强制路由到主库
   }
   ```
2. @ReadWrite注解用于标注在service层需要做读写分离的方法上，若没有该注解，则自动路由到主库
3. 通过Aop拦截@ReadWrite标注的方法，从@ReadWrite这个注解中取出读写策略，放到ThreadLocal中，如下
   ```java
   ThreadLocal<ReadWriteRoutingStrategy> readWriteRoutingStrategyThreadLocal = new ThreadLocal<>();
   //从@ReadWrite注解中取出读写策略，放到ThreadLocal中
   ReadWrite readWrite;
   readWriteRoutingStrategyThreadLocal.set(readWrite.value());
   ```
4. 需要一个有路由功能够的数据源，他里面需要有个targetDataSourcesMap，用于维护路由策略和真实数据源的映射关系，如下
   ```java
   //路由策略和数据源映射关系，放在一个map中（key：路由策略，value：对应的实际数据源）
   Map<Object, Object> targetDataSourcesMap = new HashMap<>();
   //主库路由配置
   targetDataSourcesMap.put(ReadWriteRoutingStrategy.MASTER, 主库数据源);
   //从库路由配置
   targetDataSourcesMap.put(ReadWriteRoutingStrategy.SLAVE, 从库数据源);
   //强制路由主库的配置
   targetDataSourcesMap.put(ReadWriteRoutingStrategy.HIT_MASTER, 从库数据源);
   ```
5. 操作数据库的时候，先从 readWriteRoutingStrategyThreadLocal.get() 中获取路由的策略，作为查找的key，然后从上面路由数据源的targetDataSourcesMap中找到实际的数据源，然后去执行db操作就可以了
## 先看下效果
### 创建主从库
下面准备2个数据库：javacode2018_master（主库）、javacode2018_slave（从库）
2个库中都创建一个t_user表，分别插入了一条用户数据，数据内容不一样，稍后用这个数据来验证走的是主库还是从库。
```sql
DROP DATABASE IF EXISTS javacode2018_master;
CREATE DATABASE IF NOT EXISTS javacode2018_master;
USE javacode2018_master;
DROP TABLE IF EXISTS t_user;
CREATE TABLE t_user (
  id   INT PRIMARY KEY       AUTO_INCREMENT,
  name VARCHAR(256) NOT NULL DEFAULT ''
  COMMENT '姓名'
);
INSERT INTO t_user (id, name) VALUE (1, 'master库');
DROP DATABASE IF EXISTS javacode2018_slave;
CREATE DATABASE IF NOT EXISTS javacode2018_slave;
USE javacode2018_slave;
DROP TABLE IF EXISTS t_user;
CREATE TABLE t_user (
  id   INT PRIMARY KEY       AUTO_INCREMENT,
  name VARCHAR(256) NOT NULL DEFAULT ''
  COMMENT '姓名'
);
INSERT INTO t_user (id, name) VALUE (1, 'slave库');
```
### 启动springboot应用
```java
com.itsoku.lesson027.Lesson027Application
```
### 测试用例
> 这个案例会演示4种情况
>
> 1. 没有标注@RreadWrite的方法，默认情况会走主库
> 2. 标注有@ReadWrite(Master)会走主库
> 3. 标注有@ReadWrite(Slave)会走从库
> 4. 标注有@ReadWrite(Slave)的方法，可以通过硬编码，强制将其路由到主库
```
com.itsoku.lesson027.controller.UserController#test
```
### 浏览器中访问
```http
http://localhost:8080/test
```
#### 输出
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "name": "master库"
    },
    "userFromMaster": {
      "id": 1,
      "name": "master库"
    },
    "userFromSlave": {
      "id": 1,
      "name": "slave库"
    },
    "userHitMaster": {
      "id": 1,
      "name": "master库"
    }
  },
  "msg": null,
  "code": null
}
```
## 源码解析
### @ReadWrite注解
标注在service上需要做读写分离的方法上
```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface ReadWrite {
    /**
     * 获取路由策略（主库、从库、还是强制路由到主库？）
     *
     * @return
     */
    ReadWriteRoutingStrategy value();
}
```
### ReadWriteRoutingStrategy：读写路由策略类（3个策略）
```java
public enum ReadWriteRoutingStrategy {
    MASTER, //路由到主库
    SLAVE, //路由到从库
    HIT_MASTER //强制路由到主库
}
```
### ReadWriteDataSource：读写分离的数据源
> 这是一个复合型的数据源，他继承了org.springframework.jdbc.datasource.lookup.AbstractRoutingDataSource
>
> 他里面会维护一个数据源的map，这个map的key就是路由的策略，value就是实际的数据源
>
> 里面还有个 determineCurrentLookupKey方法，如下 ，用于获取路由的策略，通过这个方法的返回值，就可以找到目标数据源。
```java
public class ReadWriteDataSource extends AbstractRoutingDataSource {
    @Override
    protected Object determineCurrentLookupKey() {
        //这里我们从ThreadLocal中获取路由的策略
        return ReadWriteRoutingStrategyHolder.getReadWriteRoutingStrategy();
    }
}
```
### ReadWriteRoutingStrategyHolder：使用ThreadLocal记录当前读写路由策略
```java
public class ReadWriteRoutingStrategyHolder {
    private static ThreadLocal<ReadWriteRoutingStrategy> readWriteRoutingStrategyThreadLocal = new ThreadLocal<>();
    public static void setReadWriteRoutingStrategy(ReadWriteRoutingStrategy readWriteRoutingStrategy) {
        readWriteRoutingStrategyThreadLocal.set(readWriteRoutingStrategy);
    }
    /**
     * 路由到主库
     */
    public static void master() {
        setReadWriteRoutingStrategy(ReadWriteRoutingStrategy.MASTER);
    }
    /**
     * 路由到从库
     */
    public static void slave() {
        setReadWriteRoutingStrategy(ReadWriteRoutingStrategy.SLAVE);
    }
    /**
     * 强制走主库执行 execute的代码
     *
     * @param execute
     * @param <T>
     * @return
     */
    public static <T> T hitMaster(Supplier<T> execute) {
        ReadWriteRoutingStrategy old = getReadWriteRoutingStrategy();
        try {
            setReadWriteRoutingStrategy(ReadWriteRoutingStrategy.HIT_MASTER);
            return execute.get();
        } finally {
            readWriteRoutingStrategyThreadLocal.set(old);
        }
    }
    /**
     * 获取读写策略
     *
     * @return
     */
    public static ReadWriteRoutingStrategy getReadWriteRoutingStrategy() {
        return readWriteRoutingStrategyThreadLocal.get();
    }
}
```
### ReadWriteAspect：AOP环绕通知
拦截所有标注有 @ReadWrite注解的方法，从这个注解中取出读写策略，将读写策略放到上面ReadWriteRoutingStrategyHolder中的readWriteRoutingStrategyThreadLocal中
```java
@Aspect
public class ReadWriteAspect {
    /**
     * 环绕通知，拦截所有方法上标注有 @ReadWrite注解的方法
     *
     * @param joinPoint
     * @param readWrite
     * @return
     * @throws Throwable
     */
    @Around("@annotation(readWrite)")
    public Object around(ProceedingJoinPoint joinPoint, ReadWrite readWrite) throws Throwable {
        //从ThreadLocal中获取读写策略
        ReadWriteRoutingStrategy readWriteRoutingStrategy = ReadWriteRoutingStrategyHolder.getReadWriteRoutingStrategy();
        // 若选择了强制路由到主库，则执行执行业务
        if (readWriteRoutingStrategy == ReadWriteRoutingStrategy.HIT_MASTER) {
            return joinPoint.proceed();
        }
        // 否则，从@ReadWrite注解中获取读写策略，放到ThreadLocal中，然后去执行业务
        ReadWriteRoutingStrategyHolder.setReadWriteRoutingStrategy(readWrite.value());
        return joinPoint.proceed();
    }
}
```
### ReadWriteConfiguration：读写分离Spring配置类
> 定义读写分离需要用到的bean，重点关注数据源的配置。
```java
com.itsoku.lesson027.ds.ReadWriteConfiguration
```
### 使用
如下，在需要做读写分离的方法上标注@ReadWrite注解，并通过其value属性指定路由策略，是走主库还是从库
```java
@Service
public class UserService {
    @Autowired
    private UserMapper userMapper;
    /**
     * 从主库获取用户
     *
     * @return
     */
    @ReadWrite(ReadWriteRoutingStrategy.MASTER)
    public UserPO getUserFromMaster() {
        return this.userMapper.getUser(1);
    }
    /**
     * 从库获取用户
     *
     * @return
     */
    @ReadWrite(ReadWriteRoutingStrategy.SLAVE)
    public UserPO getUserFromSlave() {
        return this.userMapper.getUser(1);
    }
}
```
## 其他问题
### 不加@ReadWrite注解会怎么样？
通过ReadWriteDataSource.setDefaultTargetDataSource方法设置兜底的数据源，如下，这里用主数据源进行兜底，也就是说没有路由策略或者根据路由策略找不到对应的数据源时，就会用setDefaultTargetDataSource指定的这个数据源进行兜底。
```java
//创建我们自定义的路由数据源
ReadWriteDataSource readWriteDataSource = new ReadWriteDataSource();
//设置默认兜底的数据源
readWriteDataSource.setDefaultTargetDataSource(this.masterDataSource());
```
### 强制走主库如何使用？
> 为什么需要强制走主库？
>
> 由于主从同步需要一个时间，数据写入主库后，立即去读从库，此时若数据还未同步到从库，会导致读取不到的问题，这个时候可以强制走主库查询解决这个问题。
使用下面这个方法，传入需要执行的查询逻辑，便可强制走主库查询
```java
com.itsoku.lesson027.ds.ReadWriteRoutingStrategyHolder#hitMaster(Supplier<T> execute)
```
