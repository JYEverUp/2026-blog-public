#  分享一个特别好用的Redis分布式锁工具类
## 本文主要内容
分享一个特别好用redis分布式锁工具类，使用Redisson实现的，对其进行了封装，用起来特别优雅，方便。
## 核心代码
```java
com.itsoku.lesson040.lock.DistributeLock
com.itsoku.lesson040.lock.RedisDistributeLock
```
工具里面的方法都包含了获取锁的过程、执行业务、释放锁的过程，使用者不用关注锁的获取和释放了，这样使用起来特别方便。
## 测试类
跑3个测试用例带大家看看效果。
### 1. 测试用例1：无阻塞式获取锁
```
com.itsoku.lesson040.TestController#tryLockRun
```
测试地址：http://localhost:8080/tryLockRun
### 2. 测试用例2：获取锁有超时时间
```
com.itsoku.lesson040.TestController#tryLockRunWaitTime
```
测试地址：http://localhost:8080/tryLockRunWaitTime
### 3. 测试用例3：获取锁会阻塞，直到成功获取锁
```java
com.itsoku.lesson040.TestController#lockRun
```
测试地址：http://localhost:8080/lockRun
## 如何使用？
### 1. 引入redisson配置
```xml
<!-- redisson -->
<dependency>
    <groupId>org.redisson</groupId>
    <artifactId>redisson-spring-boot-starter</artifactId>
    <version>3.20.1</version>
    <exclusions>
        <exclusion>
            <groupId>org.redisson</groupId>
            <artifactId>redisson-spring-data-30</artifactId>
        </exclusion>
    </exclusions>
</dependency>
<dependency>
    <groupId>org.redisson</groupId>
    <artifactId>redisson-spring-data-24</artifactId>
    <version>3.20.1</version>
</dependency>
<!-- redisson -->
```
### 2. application.yml中配置锁的前置
锁设置前缀，一个为了避免和其他系统命名冲突，另外一点是方便知道这个key是来自于哪个服务，可以采用下面的方式命令。
```yaml
distribute:
  lock:
    prefix: '${spring.application.name}:lock:'
```
### 3. 业务中注入 DistributeLock
```java
@Autowired
private DistributeLock distributeLock;
```
### 4. 使用 DistributeLock 接口中的方法加锁执行业务
```java
// 无阻塞的方式获取锁，然后执行业务，释放锁，返回true
boolean lockResult = this.distributeLock.tryLockRun("lock1", () -> {
            log.info("获取锁成功，执行业务");
        });
// 尝试获取锁，最多等待5秒，获取锁成功则执行业务，释放锁，返回true；5秒还未获取到锁，则返回false
boolean lockResult = this.distributeLock.tryLockRun("lock1", () -> {
            log.info("获取锁成功，执行业务");
        }, 5, TimeUnit.SECONDS);
// 获取锁的过程会阻塞，直到获取锁成功，然后执行业务，释放锁
this.distributeLock.lockRun("lock1", () -> {
            log.info("获取锁成功，执行业务");
        });
```
