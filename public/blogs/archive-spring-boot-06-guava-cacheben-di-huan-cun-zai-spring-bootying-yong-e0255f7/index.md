## **概  述**

在如今高并发的互联网应用中，缓存的地位举足轻重，对提升程序性能帮助不小。而 3.x开始的 Spring也引入了对 Cache的支持，那对于如今发展得如火如荼的 Spring Boot来说自然也是支持缓存特性的。当然 Spring Boot默认使用的是 `SimpleCacheConfiguration`，即使用 `ConcurrentMapCacheManager` 来实现的缓存。但本文将讲述如何将 Guava Cache缓存应用到 Spring Boot应用中。

## **准备工作**

- 准备好数据库和数据表并插入相应实验数据（MySQL）

比如我这里准备了一张用户表，包含几条记录：

![image-20241228122524473](/blogs/_archive-2024-assets/5fbcc910a5eae2bb3698.webp)

我们将通过模拟数据库的存取操作来看看 Guava Cache缓存加入后的效果。

------

### **工程搭建：Spring Boot + MyBatis + MySQL + Guava Cache**

pom.xml 中添加如下依赖：

```
<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-test</artifactId>
        <scope>test</scope>
    </dependency>
    <!--for mybatis-->
    <dependency>
        <groupId>org.mybatis.spring.boot</groupId>
        <artifactId>mybatis-spring-boot-starter</artifactId>
        <version>1.3.2</version>
    </dependency>
    <!--for Mysql-->
    <dependency>
        <groupId>mysql</groupId>
        <artifactId>mysql-connector-java</artifactId>
        <scope>runtime</scope>
    </dependency>
    <!-- Spring boot Cache-->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-cache</artifactId>
    </dependency>
    <!--for guava cache-->
    <dependency>
        <groupId>com.google.guava</groupId>
        <artifactId>guava</artifactId>
        <version>27.0.1-jre</version>
    </dependency>
</dependencies>
```

------

### **引入Guava Cache配置**

引入 Guava Cache的配置文件 `GuavaCacheConfig`

```
@Configuration
@EnableCaching
public class GuavaCacheConfig {
    @Bean
    public CacheManager cacheManager() {
        GuavaCacheManager cacheManager = new GuavaCacheManager();
        cacheManager.setCacheBuilder(
            CacheBuilder.newBuilder()
                .expireAfterWrite(10, TimeUnit.SECONDS)
                .maximumSize(1000)
        );
        return cacheManager;
    }
}
```

Guava Cache配置十分简洁，比如上面的代码配置缓存存活时间为 10 秒，缓存最大数目为 1000 个

------

### **配置 application.properties**

```
server.port=82

# Mysql 数据源配置
spring.datasource.url=jdbc:mysql://121.116.23.145:3306/demo?useUnicode=true&characterEncoding=utf-8&useSSL=false
spring.datasource.username=root
spring.datasource.password=xxxxxx
spring.datasource.driver-class-name=com.mysql.jdbc.Driver

# mybatis配置
mybatis.type-aliases-package=cn.codesheep.springbt_guava_cache.entity
mybatis.mapper-locations=classpath:mapper/*.xml
mybatis.configuration.map-underscore-to-camel-case=true
```

------

## 写数据库操作

### **编写业务代码**

- **编写 entity**

```
public class User {
    private Long userId;
    private String userName;
    private Integer userAge;

    public Long getUserId() {
        return userId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public String getUserName() {
        return userName;
    }

    public void setUserName(String userName) {
        this.userName = userName;
    }

    public Integer getUserAge() {
        return userAge;
    }

    public void setUserAge(Integer userAge) {
        this.userAge = userAge;
    }
}
```

- **编写 mapper**

```
public interface UserMapper {
    List<User> getUsers();
    int addUser(User user);
    List<User> getUsersByName(String userName);
}
```

- **编写 service**

```
@Service
public class UserService {
    @Autowired
    private UserMapper userMapper;

    public List<User> getUsers() {
        return userMapper.getUsers();
    }

    public int addUser(User user) {
        return userMapper.addUser(user);
    }

    @Cacheable(value = "user", key = "#userName")
    public List<User> getUsersByName(String userName) {
        List<User> users = userMapper.getUsersByName(userName);
        System.out.println("从数据库读取，而非读取缓存！");
        return users;
    }
}
```

看得很明白了，我们在 `getUsersByName`接口上添加了注解： `@Cacheable`。这是 缓存的使用注解之一，除此之外常用的还有 `@CachePut`和 `@CacheEvit`，分别简单介绍一下：

1. `@Cacheable`：配置在 `getUsersByName`方法上表示其返回值将被加入缓存。同时在查询时，会先从缓存中获取，若不存在才再发起对数据库的访问
2. `@CachePut`：配置于方法上时，能够根据参数定义条件来进行缓存，其与 `@Cacheable`不同的是使用 `@CachePut`标注的方法在执行前不会去检查缓存中是否存在之前执行过的结果，而是每次都会执行该方法，并将执行结果以键值对的形式存入指定的缓存中，所以主要用于数据新增和修改操作上
3. `@CacheEvict`：配置于方法上时，表示从缓存中移除相应数据。

- **编写 controller**

```
@RestController
public class UserController {
    @Autowired
    private UserService userService;
    @Autowired
    CacheManager cacheManager;

    @RequestMapping(value = "/getusersbyname", method = RequestMethod.POST)
    public List<User> geUsersByName(@RequestBody User user) {
        System.out.println("-------------------------------------------");
        System.out.println("call /getusersbyname");
        System.out.println(cacheManager.toString());
        List<User> users = userService.getUsersByName(user.getUserName());
        return users;
    }
}
```

------

## **改造 Spring Boot应用主类**

主要是在启动类上通过 @EnableCaching注解来显式地开启缓存功能

```
@SpringBootApplication
@MapperScan("cn.codesheep.springbt_guava_cache")
@EnableCaching
public class SpringbtGuavaCacheApplication {
    public static void main(String[] args) {
        SpringApplication.run(SpringbtGuavaCacheApplication.class, args);
    }
}
```

最终完工的整个工程的结构如下：

![image-20241228122541663](/blogs/_archive-2024-assets/c7780d3d692526b98dcc.webp)

------

### **实际实验**

通过多次向接口 `localhost:82/getusersbyname` POST数据来观察效果：

![image-20241228122551720](/blogs/_archive-2024-assets/5613beebc666bf8746ed.webp)

可以看到缓存的启用和失效时的效果如下所示（上文 Guava Cache的配置文件中设置了缓存 user的实效时间为 10s）：

怎么样，缓存的作用还是很明显的吧！
