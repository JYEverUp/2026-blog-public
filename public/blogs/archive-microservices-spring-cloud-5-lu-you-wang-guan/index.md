## Zuul路由网关

### 什么是zuul

Zuul包含了对请求的路由和过滤两个最主要的功能:

>  其中路由功能负责将外部请求转发到具体的微服务实例上，是==实现外部访问统一入口的基础==， 而过滤器功能则负责对请求的处理过程进行干预，是实现请求校验，服务聚合等功能的基础。ZuuI和Eureka进行整合, 将Zuul自身注册为Eureka服务治理下的应用，同时从Eureka中获得其他微服务的消息，也即以后的访问微服务都是通过Zuul跳转后获得。

注意: Zuul服务最终还是会注册进Eureka

提供:代理+路由+过滤三大功能

一般网关也有另外一个名字`gateway`(直译)

### 起步

创建`study-zuul-9527`模块

配置pom依赖

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <parent>
        <artifactId>springcloud-study</artifactId>
        <groupId>com.ifyyf</groupId>
        <version>1.0-SNAPSHOT</version>
    </parent>
    <modelVersion>4.0.0</modelVersion>

    <artifactId>study-zuul-9527</artifactId>

    <dependencies>
        <!--  zuul依赖  -->
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-zuul</artifactId>
        </dependency>

        <!--    引入该模块的依赖，使得能够访问到该模块的包和类文件等    -->
        <dependency>
            <groupId>com.ifyyf</groupId>
            <artifactId>study-api</artifactId>
            <version>1.0-SNAPSHOT</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-netflix-eureka-server</artifactId>
            <!--  问题：json被解析成xml返回浏览器， 解决：客户端加入此排除jackson依赖  -->
            <exclusions>
                <exclusion>
                    <artifactId>jackson-dataformat-xml</artifactId>
                    <groupId>com.fasterxml.jackson.dataformat</groupId>
                </exclusion>
            </exclusions>
        </dependency>
        <dependency>
            <groupId>com.alibaba</groupId>
            <artifactId>fastjson</artifactId>
        </dependency>
        <!--  hystrix依赖  -->
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-hystrix</artifactId>
        </dependency>
        <!--  hystrix监控  -->
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-hystrix-dashboard</artifactId>
        </dependency>
    </dependencies>
</project>
```

yml配置文件，将网关注册到注册中心

```properties
server:
  port: 9527

spring:
  application:
    name: springcloud-zuul

# Eureka配置，服务注册到哪里
eureka:
  client:
    service-url:
      defaultZone: http://local2.ifyyf.com:7002/eureka/,http://local1.ifyyf.com:7001/eureka/,http://local3.ifyyf.com:7003/eureka/
  instance:
    instance-id: springcloud-zuul-9527 # 修改Eureka上的默认描述信息

# info配置
info:
  app.name: study-springcloud
  company.name: www.ifyyf.com

# 配置路由重定向，如果不加这个重定向路由的话需要根据服务名称调用服务
zuul:
  routes:
    mydept.serviceId: springcloud-provider-dept
    mydept.path: /mydept/**
    mydept2.serviceId: springcloud-consumer-dept-feign-80
    mydept2.path: /mydept2/**
  # 忽略服务名称调用服务，只能根据↑配置的path访问
#  ignored-services: springcloud-provider-dept
  ignored-services: "*"     # 有多个服务时，"*"可以隐藏所有的
#  prefix: /if   # 设置公共的前缀
```

启动类`ZuulApplication_9527`

```java
package com.ifyyf;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.netflix.zuul.EnableZuulProxy;

/**
 * @Author if
 * @Description: What is it
 * @Date 2021-08-30 下午 11:23
 */
@SpringBootApplication
@EnableZuulProxy
public class ZuulApplication_9527 {
    public static void main(String[] args) {
        SpringApplication.run(ZuulApplication_9527.class,args);
    }
}

```

然后可以访问`localhost:9527/springcloud-provider-dept/dept/get/1`来访问这个服务

但是如果==将服务名称暴露在url上是很不安全的==，所以需要配置路由

```properties
# 配置路由重定向，如果不加这个重定向路由的话需要根据服务名称调用服务
zuul:
  routes:
    mydept.serviceId: springcloud-provider-dept
    mydept.path: /mydept/**
    mydept2.serviceId: springcloud-consumer-dept-feign-80
    mydept2.path: /mydept2/**
  # 忽略服务名称调用服务，只能根据↑配置的path访问
#  ignored-services: springcloud-provider-dept
  ignored-services: "*"     # 有多个服务时，"*"可以隐藏所有的
#  prefix: /if   # 设置公共的前缀
```

routes下可以随意配置多个map，根据path替换服务名称调用

> 这里我将80端口的feign负载均衡客户端注册到了注册中心，所以zuul能访问并配置路由

通过`http://localhost:9527/mydept/dept/get/2`可以访问到配置好的服务端

也可以通过`http://localhost:9527/mydept2/consumer/dept/get/3`访问到客户端

*（原站配图缺失）*




## Config配置中心

### 分布式面临的问题

分布式微服务中，将应用拆分成了多个服务模块，而这每一个模块都有一个application.yml配置文件，成千上百的配置文件配置起来非常麻烦，所以我们需要一个统一配置文件的配置中心

### 什么是Config分布式配置中心

Spring Cloud Config为微服务架构中的微服务提供集中化的外部配置支持,配置服务器为各个不同微服务应用
的所有环节提供了一一个==中心化的外部配置==

Spring Cloud Config 分为==服务端==和==客户端==两部分

- 服务端也称为分布式配置中心，==**它是一个独立的微服务应用**==，用来连接配置服务器并为客户端提供获取配置信息,加密，解密信息等访问接口。
- 客户端则是通过指定的配置中心来管理应用资源，以及与业务相关的配置内容，并在启动的时候从配置中心获取和加载配置信息。
- 配置服务器默认采用git来存储配置信息，这样就有助于对环境配置进行版本管理。并且可以通过git客户端工具来方便的管理和访问配置内容。

**SpringCloud config分布式配置中心能干嘛**

==实现了代码和配置解耦==：运维只需要修改远程仓库的配置文件，而无需动开发人员的代码文件

集中管理配置文件

- 不同环境，不同配置，动态化的配置更新，分环境部署，比如/dev /test/ /prod /beta /release -
- 运行期间动态调整配置,不再需要在每个服务部署的机器上编写配置文件,服务会向配置中心统一 拉取配置自己的信息。
- 当配置发生变动时，服务不需要重启，即可感知到配置的变化，并应用新的配置
- 将配置信息以REST接口的形式暴露



**SpringCloud config分布式配置中心与github整合**

由于Spring Cloud Config默认使用Git来存储配置文件(也有其他方式， 比如支持SVN和本地文件)， 但是最推
荐的还是Git，而且使用的是http / https访问的形式



### 服务器连接git获取配置

首先gitee创建仓库`springcloud-config`，[这里我测试的仓库地址](https://gitee.com/ifyyf/springcloud-config)

clone到本地，创建application.yml文件

==注：需要配置多环境的话`---`千万别省略，不然会报错==

```properties
spring: 
  profiles: 
    active: dev  # 当前选择激活dev

---
spring: 
  profiles: dev
  application: 
    name: springcloud-config-dev

---
spring: 
  profiles: test
  application: 
    name: springcloud-config-test
```

add，commit ，push上去

**环境搭建完成**

接下来创建配蜘中心模块`study-config-server-3344`

导入依赖

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <parent>
        <artifactId>springcloud-study</artifactId>
        <groupId>com.ifyyf</groupId>
        <version>1.0-SNAPSHOT</version>
    </parent>
    <modelVersion>4.0.0</modelVersion>

    <artifactId>study-config-server-3344</artifactId>

    <dependencies>
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-config-server</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
    </dependencies>
</project>
```

配置yml文件

```properties
server:
  port: 3344
spring:
  application:
    name: springcloud-config-server-3344
  # 连接远程仓库（下面那个是uri，不是url ！！！）
  cloud:
    config:
      server:
        git:
          uri: https://gitee.com/ifyyf/springcloud-config.git   # git链接地址
#          username: xxxxxx  # 如果git仓库是私有，且出现身份验证错误，需要填写用户名和密码
#          password: xxxxxx  # 如果git仓库是私有，且出现身份验证错误，需要填写用户名和密码
#      label: master # 读取的分支


# Eureka配置
#eureka:
#  client:
#    service-url:  # 监控页面
#      defaultZone: http://local1.ifyyf.com:7001/eureka/,http://local2.ifyyf.com:7002/eureka/,http://local3.ifyyf.com:7003/eureka/
#    instance:
#      instance-id: springcloud-config-server-3344 # 修改Eureka上的默认描述信息
```

启动类

```java
package com.ifyyf;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.config.server.EnableConfigServer;

/**
 * @Author if
 * @Description: What is it
 * @Date 2021-08-31 下午 12:11
 */
@SpringBootApplication
//开启服务器连接git的配置中心
@EnableConfigServer
public class Config_server_3344 {
    public static void main(String[] args) {
        SpringApplication.run(Config_server_3344.class,args);
    }
}
```

启动项目，访问`http://localhost:3344/master/application-dev.yml`或者`http://localhost:3344/master/application-test.yml`都可以访问到

注：此处master可以省略，只是表面label分支而已

### 客户端连接服务端访问远程

`bootstrap.yml`是系统级别的配置文件，`application.yml`是用户级别的配置文件，所以前者级别更高

我们客户端模块要从云端拿数据，所以需要用到`bootstrap.yml`

创建`bootstrap.yml`

```properties
# 系统级别的配置，从云端拿数据需要用到本配置
# 3355为客户端，去连接3344配置中心服务端，然后服务器去gitee上获取配置文件
spring:
  cloud:
    config:
      uri: http://localhost:3344
      label: master # 仓库的分支
      name: config-client # 需要从git上读取的资源名称，不需要yml后缀
      profile: dev # 拿的版本
      # 以上3个配置相当于访问到了http://localhost:3344/config-client/test/master
```

创建`application.yml`

```properties
spring:
  application:
    name: springcloud-config-server-3355
```

创建controller，为了直观看到配置信息等

```java
package com.ifyyf.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * @Author if
 * @Description: What is it
 * @Date 2021-08-31 下午 01:03
 */
@RestController
public class ConfigClientController {

    @Value("${spring.application.name}")
    private String applicationName;

    @Value("${eureka.client.service-url.defaultZone}")
    private String eurekaServer;

    @Value("${server.port}")
    private String port;

    @RequestMapping("/config")
    public String config(){
        return "applicationName = "+applicationName
                + " eurekaServer = "+eurekaServer
                +" port = "+port;
    }

}

```

启动类

```java
package com.ifyyf;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * @Author if
 * @Description: What is it
 * @Date 2021-08-31 下午 01:01
 */
@SpringBootApplication
public class ConfigClient_3355 {
    public static void main(String[] args) {
        SpringApplication.run(ConfigClient_3355.class,args);
    }
}

```

启动客户端模块(**配置中心服务端不能关闭**)

git仓库里写的端口，dev是8081，test是8082，根据`bootstrap.yml`编写的版本访问对应的端口

这里以dev、8081端口为例，访问`http://localhost:8202/config`

出现以下文字证明获取成功

> applicationName = springcloud-provider-dept eurekaServer = http://local2.ifyyf.com:7002/eureka/,http://local1.ifyyf.com:7001/eureka/,http://local3.ifyyf.com:7003/eureka/ port = 8201

## 完结

所有工程原代码放在个人gitee上了，地址→[gitee仓库地址](https://gitee.com/ifyyf/springcloud-study)



在学习的过程中，父工程的pom依赖总是有改变的，最后呈上一份父工程的pom文件

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.ifyyf</groupId>
    <artifactId>springcloud-study</artifactId>
    <version>1.0-SNAPSHOT</version>
    <modules>
        <module>study-api</module>
        <module>study-provider-dept-8001</module>
        <module>study-consumer-dept-80</module>
        <module>study-eureka-7001</module>
        <module>study-eureka-7002</module>
        <module>study-eureka-7003</module>
        <module>study-provider-dept-8003</module>
        <module>study-provider-dept-8002</module>
        <module>study-consumer-dept-feign</module>
        <module>study-provider-dept-hystrix-8001</module>
        <module>study-consumer-hystrix-dashboard</module>
        <module>study-zuul-9527</module>
        <module>study-config-server-3344</module>
        <module>study-config-client-3355</module>
    </modules>

    <!--  打包方式pom  -->
    <packaging>pom</packaging>
<!--  版本号  -->
    <properties>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
        <junit.version>4.12</junit.version>
        <log4j.version>1.2.17</log4j.version>
        <druid.version>1.1.10</druid.version>
        <logback-core.version>1.2.3</logback-core.version>
        <fastjson.version>1.2.31</fastjson.version>
    </properties>
<!--  Management管理依赖  -->
    <dependencyManagement>
        <dependencies>
            <!--  springcloud依赖  -->
            <dependency>
                <groupId>org.springframework.cloud</groupId>
                <artifactId>spring-cloud-dependencies</artifactId>
                <version>Hoxton.SR9</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
            <!--  springboot依赖  -->
            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-dependencies</artifactId>
                <version>2.3.2.RELEASE</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
            <dependency>
                <groupId>mysql</groupId>
                <artifactId>mysql-connector-java</artifactId>
                <version>5.1.25</version>
            </dependency>
            <dependency>
                <groupId>com.alibaba</groupId>
                <artifactId>druid</artifactId>
                <version>${druid.version}</version>
            </dependency>
            <!--  springboot启动器  -->
            <dependency>
                <groupId>org.mybatis.spring.boot</groupId>
                <artifactId>mybatis-spring-boot-starter</artifactId>
                <version>2.1.3</version>
            </dependency>
            <dependency>
                <groupId>junit</groupId>
                <artifactId>junit</artifactId>
                <version>${junit.version}</version>
            </dependency>
            <dependency>
                <groupId>org.projectlombok</groupId>
                <artifactId>lombok</artifactId>
                <version>1.18.20</version>
            </dependency>
            <dependency>
                <groupId>log4j</groupId>
                <artifactId>log4j</artifactId>
                <version>${log4j.version}</version>
            </dependency>
            <dependency>
                <groupId>ch.qos.logback</groupId>
                <artifactId>logback-core</artifactId>
                <version>${logback-core.version}</version>
            </dependency>
            <dependency>
                <groupId>com.alibaba</groupId>
                <artifactId>fastjson</artifactId>
                <version>${fastjson.version}</version>
            </dependency>
            <dependency>
                <groupId>org.springframework.cloud</groupId>
                <artifactId>spring-cloud-starter-feign</artifactId>
                <version>1.4.6.RELEASE</version>
            </dependency>
            <dependency>
                <groupId>org.springframework.cloud</groupId>
                <artifactId>spring-cloud-starter-hystrix</artifactId>
                <version>1.4.6.RELEASE</version>
            </dependency>
            <dependency>
                <groupId>org.springframework.cloud</groupId>
                <artifactId>spring-cloud-starter-hystrix-dashboard</artifactId>
                <version>1.4.6.RELEASE</version>
            </dependency>
            <dependency>
                <groupId>org.springframework.cloud</groupId>
                <artifactId>spring-cloud-starter-zuul</artifactId>
                <version>1.4.6.RELEASE</version>
            </dependency>
            <dependency>
                <groupId>org.springframework.cloud</groupId>
                <artifactId>spring-cloud-config-server</artifactId>
                <version>2.1.1.RELEASE</version>
            </dependency>
            <dependency>
                <groupId>org.springframework.cloud</groupId>
                <artifactId>spring-cloud-starter-config</artifactId>
                <version>2.1.1.RELEASE</version>
            </dependency>
        </dependencies>
    </dependencyManagement>
</project>
```



*（原站配图缺失）*
*（原站配图缺失）*
