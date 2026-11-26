## 整合redis

- springboot在现在的版本中操作Redis数据库用到了lettuce，而不是Jedis，他们各有各的特点。
- Jedis以Redis命令作为方法名称，学习成本低，简单实用。但是Jedis实例是线程不安全的，多线程环境下需要基于连接池来使用。
- Lettuce是基于Netty实现的，支持同步、异步和响应式编程方式，并且是线程安全的。支持Redis的哨兵模式、集群模式和管道模式。

SpringDataRedis相关的api

![image-20240924201415371](/blogs/_archive-2024-assets/200ce5f48e6201ef776d.webp)

### 1、引入依赖

```java
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
```

### 2、配置文件

```java
spring:
  redis:
    # Redis服务器地址
    host: 19.1.5.11
    # Redis服务器端口号
    port: 6379
    # 使用的数据库索引，默认是0
    database: 0
    # 连接超时时间
    timeout: 1800000
     # 设置密码
    password: "123456"
    lettuce:
      pool:
        # 最大阻塞等待时间，负数表示没有限制
        max-wait: -1
        # 连接池中的最大空闲连接
        max-idle: 5
        # 连接池中的最小空闲连接
        min-idle: 0
        # 连接池中最大连接数，负数表示没有限制
        max-active: 20
```

### 3、代码实践

```java
    @Autowired
    private RedisTemplate redisTemplate;
    @Test
    public void redis() {
        redisTemplate.opsForValue().set("name","卷心菜");
        String name = (String) redisTemplate.opsForValue().get("name");
        System.out.println(name); //卷心菜
    }
```

问题出现了：当我们使用Redis客户端查看刚刚存入[Redis数据库](https://so.csdn.net/so/search?q=Redis数据库&spm=1001.2101.3001.7020)的数据时，结果是这样的：

![image-20240924201353224](/blogs/_archive-2024-assets/a2ccf93a04c23a23228c.webp)

![image-20240924201402090](/blogs/_archive-2024-assets/2dfc0e3d3a15bfb1aee2.webp)

### 4、自定义序列化器

```java
@Configuration
public class RedisConfig {
    @Bean
    public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory redisConnectionFactory)
            throws UnknownHostException {
        // 创建模板
        RedisTemplate<String, Object> redisTemplate = new RedisTemplate<>();
        // 设置连接工厂
        redisTemplate.setConnectionFactory(redisConnectionFactory);
        // 设置序列化工具
        GenericJackson2JsonRedisSerializer jsonRedisSerializer =
                new GenericJackson2JsonRedisSerializer();
        // key和 hashKey采用 string序列化
        redisTemplate.setKeySerializer(RedisSerializer.string());
        redisTemplate.setHashKeySerializer(RedisSerializer.string());
        // value和 hashValue采用 JSON序列化
        redisTemplate.setValueSerializer(jsonRedisSerializer);
        redisTemplate.setHashValueSerializer(jsonRedisSerializer);
        return redisTemplate;
    }
}
```

当配置好配置类后，再次执行上文的代码就不会出现上述情况了，但是问题又来了，当我们的value是一个对象时：

![img](/blogs/_archive-2024-assets/85a03c6825faa800e0d3.png)

不仅仅是这个问题，由于我们的value是object类型。在反序列化的时候还经常会出现把long值转成int值导致泛型转化失败等场景。

这里推荐不需要**json序列化器**，直接用**string序列化器**

**用**spring的 **stringRedisTemplate，**要求只能存储String类型的key和value。

这样每次存取很麻烦，但是可以通过redisUtils工具类来屏蔽这层麻烦。

## RedisUtil使用

![image-20240924201335122](/blogs/_archive-2024-assets/c87b80a93ac10facb094.webp)

![image-20240924201322576](/blogs/_archive-2024-assets/d24c2773479cb256abfc.webp)

`stringRedisTemplate`是通过`@PostConstruct`在类初始化阶段从spring容器中拿到对象，设置进静态变量中。

这里还有个小设计

![image-20240924201313712](/blogs/_archive-2024-assets/438f91dfb26cb8c4729b.webp)

虽然我们用的是`stringRedisTemplate`但是工具类支持设置object的值，以及取出任意类型对象的值，工具类里封装了方法会对object的值转成json。

```java
public static void main(String[] args) {
    Long aLong = JSONUtil.toBean("1", Long.class);
    System.out.println(aLong);
}
```

有些序列化工具类不支持这样的反序列化，我选择用jackson。

## 引入redisson

分布式锁是我们经常需要用的，因此需要引入redisson。

### 1、引入依赖

```java
<dependency>
    <groupId>org.redisson</groupId>
    <artifactId>redisson-spring-boot-starter</artifactId>
</dependency>
```

### 2、配置类

对于单机redis的配置比较简单，就是配置一个redissonClinet对象，以后的使用也是注入这个对象来使用

```java
@Configuration
public class RedissonConfig {
    @Autowired
    private RedisProperties redisProperties;

    @Bean
    public RedissonClient redissonClient() {
        Config config = new Config();
        config.useSingleServer()
                .setAddress("redis://" + redisProperties.getHost() + ":" + redisProperties.getPort())
                .setPassword(redisProperties.getPassword())
                .setDatabase(redisProperties.getDatabase());
        return Redisson.create(config);
    }
}
```

### 3、代码实践

```plain
@Autowired
private RedissonClient redissonClient;

public <T> T executeWithLockThrows(String key, int waitTime, TimeUnit unit, SupplierThrow<T> supplier) throws Throwable {
    RLock lock = redissonClient.getLock(key);
    boolean lockSuccess = lock.tryLock(waitTime, unit);
    if (!lockSuccess) {
        throw new BusinessException(CommonErrorEnum.LOCK_LIMIT);
    }
    try {
        return supplier.get();//执行锁内的代码逻辑
    } finally {
        lock.unlock();
    }
}
```
