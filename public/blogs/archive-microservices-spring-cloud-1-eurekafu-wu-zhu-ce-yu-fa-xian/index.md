# SpringCloud笔记
## 前言
微服务架构的几个核心问题

1. 服务很多，客户端该怎么访问？
2. 这么多服务之间怎么进行通信
3. 这么多服务怎么治理
4. 如果其中一个服务挂了怎么办

解决方案：

springcloud并不是一个技术框架，而是一个生态

技术选型

1. springcloud Netflix	一站式解决方案，现已停止维护

   > api网关，zuul组件
   >
   > Feign——HttpClinet——Http通信方式，同步，阻塞
   >
   > 服务注册发现：Euraka
   >
   > 熔断机制：Hystrix
   >
   > 。。。

   . Apache dubbo zookeeper 	半自动，专注于通信，其余需要整合别人的

   > api：没有，找第三方组件
   >
   > Dubbo：基于java开源的RPC的通信框架
   >
   > zookeeper：分布式应用程序协调服务
   >
   > 没有熔断机制，借助Hystrix
   >
   > 这个方案并不完善。。。

   springcloud alibaba	一站式解决方案，更简单

万变不离其宗：

1. API网关——路由
2. HTTP,RPC——通信
3. 注册和发现——高可用
4. 熔断机制——服务降级



### 微服务概述

什么是微服务？

目前而言，业界并没有一个统一的标准定义

微服务提倡将单一的一个程序分成一组小的服务，每个服务运行在自己的进程内，服务之间相互协调，互相配置，为用户提供价值

> 但通常而言，微服务架构是一种架构模式， 或者说是一种架构风格，它提倡将单一 的应用程序划分成一 组小的服务，每个服务运行在其独立的自己的进程内，服务之间互相协调，互相配置，为用户提供最终价值。
>
> 服务之间采用轻量级的通信机制互相沟通，每个服务都围绕着具体的业务进行构建，并且能够被独立的部署到生产环境中
>
> 另外，应尽量避免统一的， 集中式的服务管理机制，对具体的一个服务而言，应根据业务上下文，选择合适的语言，工具对其进行构建，可以有一个非常轻量级的集中式管理来协调这些服务，可以使用不同的语言来编写服务，也可以使用不同的数据存储



>微服务化的核心就是将传统的一站式应用，根据业务拆分成一个个的服务彻底地去耦合，每个微服务提
>供单个业务功能的服务，一个服务做-件事情，从技术角度看就是一种小而独立的处理过程， 类似进程的概
>念，能够自行单独启动或销毁，拥有自己独立的数据库。

### springcloud概述
*（原站配图缺失）*
>SpringCloud,基于SpringBoot提供了一套微服务解决方案， 包括服务注册与发现，配置中心，全链路监控,服务网关，负载均衡，熔断器等组件,除了基于NetFlix的开源组件做高度抽象封装之外，还有一些选型中立的开源组件。
>SpringCloud利用SpringBoot的开发便利性，巧妙地简化了分布式系统基础设施的开发，SpringCloud为开发人员 .提供了快速构建分布式系统的一些工具,包括配置管理，服务发现，断路器，路由，微代理，事件总线，全局锁,决策竞选，分布式会话等等,他们都可以用SpringBoot的开发风格做到一键启动和部署。
>SpringBoot并没有重复造轮子，它只是将目前各家公司开发的比较成熟，经得起实际考研的服务框架组合起来,
>通过SpringBoot风格进行再封装,屏蔽掉了复杂的配置和实现原理，最终给开发者留出了一套简单易懂，易部署和易维护的分布式系统开发工具包
>SpringCloud是分布式微服务架构下的一站式解决方案, 是各个微服务架构落地技术的集合体,俗称微服务全家
>桶。

应用服务拆分+消息中间件
*（原站配图缺失）*

dubbo和springcloud区别

*（原站配图缺失）*


**最大区别**：springcloud抛弃了dubbo的RPC通信，采取了基于HTTP的REST方式

一纸契约，只利用api调用，不存在代码级别的强依赖，后者虽然牺牲了服务调用的性能，但是更适合如今的微服务环境

dubbo相当于品牌NUC，而springcloud相当于一台组装机

**因为Dubbo定义是一款RPC框架，而springcloud是微服务架构下的一站式解决方案**

### 版本对比

依赖版本

| Spring Cloud Version        | Spring Cloud Alibaba Version      | Spring Boot Version |
| --------------------------- | --------------------------------- | ------------------- |
| Spring Cloud 2020.0.1       | 2021.1                            | 2.4.2               |
| Spring Cloud Hoxton.SR9     | 2.2.6.RELEASE                     | 2.3.2.RELEASE       |
| Spring Cloud Greenwich.SR6  | 2.1.4.RELEASE                     | 2.1.13.RELEASE      |
| Spring Cloud Hoxton.SR3     | 2.2.1.RELEASE                     | 2.2.5.RELEASE       |
| Spring Cloud Hoxton.RELEASE | 2.2.0.RELEASE                     | 2.2.X.RELEASE       |
| Spring Cloud Greenwich      | 2.1.2.RELEASE                     | 2.1.X.RELEASE       |
| Spring Cloud Finchley       | 2.0.4.RELEASE(停止维护，建议升级) | 2.0.X.RELEASE       |
| Spring Cloud Edgware        | 1.5.1.RELEASE(停止维护，建议升级) | 1.5.X.RELEASE       |

组件版本

| Spring Cloud Alibaba Version                              | Sentinel Version | Nacos Version | RocketMQ Version | Dubbo Version | Seata Version |
| --------------------------------------------------------- | ---------------- | ------------- | ---------------- | ------------- | ------------- |
| 2.2.6.RELEASE                                             | 1.8.1            | 1.4.2         | 4.4.0            | 2.7.8         | 1.3.0         |
| 2021.1 or 2.2.5.RELEASE or 2.1.4.RELEASE or 2.0.4.RELEASE | 1.8.0            | 1.4.1         | 4.4.0            | 2.7.8         | 1.3.0         |
| 2.2.3.RELEASE or 2.1.3.RELEASE or 2.0.3.RELEASE           | 1.8.0            | 1.3.3         | 4.4.0            | 2.7.8         | 1.3.0         |
| 2.2.1.RELEASE or 2.1.2.RELEASE or 2.0.2.RELEASE           | 1.7.1            | 1.2.1         | 4.4.0            | 2.7.6         | 1.2.0         |
| 2.2.0.RELEASE                                             | 1.7.1            | 1.1.4         | 4.4.0            | 2.7.4.1       | 1.0.0         |
| 2.1.1.RELEASE or 2.0.1.RELEASE or 1.5.1.RELEASE           | 1.7.0            | 1.1.4         | 4.4.0            | 2.7.3         | 0.9.0         |
| 2.1.0.RELEASE or 2.0.0.RELEASE or 1.5.0.RELEASE           | 1.6.3            | 1.1.1         | 4.4.0            | 2.7.3         | 0.7.1         |

### 快速开始

[springcloud中文网](https://www.springcloud.cc/spring-cloud-greenwich.html)

建立一个maven项目，删除src文件夹，配置依赖

此时这个项目相当于父项目，在此项目中创建子模块(module)，子模块虽然pom文件是空的，但是其所导入的maven依赖如果存在于父模块中，则与父项目的pom依赖版本保持一致

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
        <module>study-consumer-detp-80</module>
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
        </dependencies>
    </dependencyManagement>
</project>
```

可以看见子模块添加的lombok与父模块定义的版本一致

*（原站配图缺失）*


创建子模块并配置pom依赖（直接从父类引入，版本与父类一致）

消费者模块：`study-consumer-detp-80`

生产者模块：`study-provider-dept-8001`

因为分模块部署到不同的服务器上，所以需要接口调用接口，在本demo中是以消费者调用生产者的接口

所以生产者需要有完整一套接口服务mybatis-dao-service-serviceImpl-controller

*（原站配图缺失）*


而消费者不应该有service，所以需要将RestTemplate,注册到spring中调用

`RestTemplate`：提供多种便捷访问远程http服务的方法类，简单的restFul服务模板



生产者的controller代码

```java
package com.ifyyf.controller;

import com.ifyyf.pojo.Dept;
import com.ifyyf.service.DeptService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * @Author if
 * @Description: What is it
 * @Date 2021-08-24 下午 12:13
 */
@RestController
@RequestMapping("/dept")
public class DeptController {
    @Autowired
    private DeptService deptService;

    @GetMapping("/get/{deptno}")
    public Dept get(@PathVariable("deptno") Long deptno){
        return deptService.getById(deptno);
    }

    @GetMapping("/getAll")
    public List<Dept> getAll(){
        return deptService.getAll();
    }
}

```

消费者的ConfigBean和Controller代码如下：

```java
package com.ifyyf.config;

import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

/**
 * @Author if
 * @Description: @Configuration的类相当于spring的applicationContext.xml
 * @Date 2021-08-24 下午 01:05
 */
@Configuration
public class ConfigBean {
    @Bean
    public RestTemplate getRestTemplate(){
        return new RestTemplate();
    }
}
```

```java
package com.ifyyf.controller;

import com.ifyyf.pojo.Dept;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.List;

/**
 * @Author if
 * @Description: What is it
 * @Date 2021-08-24 下午 01:03
 */
@RestController
@CrossOrigin
@RequestMapping("/consumer/dept")
public class DeptConsumerController {
    /**
     * 消费者不应该有service
     * 因为分模块部署到不同的服务器上，所以需要接口调用接口
     * RestTemplate,注册到spring中直接调用
     * getForObject(URI url, Class<T> responseType)、
     * url是网络接口地址，responseType是本类中返回值的类型的class
     *
     * postForObject(URI url, @Nullable Object request, Class<T> responseType)
     * url是网络接口地址，request是参数，responseType是本类中返回值的类型的class
     */

    //提供多种便捷访问远程http服务的方法类，简单的restFul服务模板
    @Autowired
    private RestTemplate restTemplate;
    //远程接口主机地址
    private static String HOST="http://localhost:8001";

    /**
     * RestFul风格
     * @param deptno
     * @return
     */
    @GetMapping("/get/{deptno}")
    public Dept get(@PathVariable("deptno") Long deptno){
        return restTemplate.getForObject(HOST+"/dept/get/"+deptno,Dept.class);
    }

    /**
     * list返回值就给List.class
     * @return
     */
    @GetMapping("/getAll")
    public List<Dept> getAll(){
        return restTemplate.getForObject(HOST+"/dept/getAll",List.class);
    }
}

```

小结：

> 不管是访问了http://localhost:8001/dept/getAll，还是http://localhost/consumer/dept/getAll
>
> 都能正常调用到数据库拿到结果

## Eureka服务注册与发现

### 什么是Eureka

Eureka是Netflix的一个子模块，也是核心模块之一。Eureka是一个基于REST的服务，用于定位服务，以实现
云端中间层服务发现和故障转移,服务注册与发现对于微服务来说是非常重要的，有了服务发现与注册，只需
要使用服务的标识符，就可以访问到服务，而不需要修改服务调用的配置文件了，功能类似于Dubbo的注册
中心，比如Zookeeper

### Eureka的基本结构

- SpringCloud封装了NetFlix公司开发的Eureka模块来实现服务注册和发现(对比Zookeeper)

- Eureka采用了C-S的架构设计，EurekaServer 作为服务注册功能的服务器，他是服务注册中心

- 而系统中的其他微服务。使用Eureka的客户端连接到EurekaServer并维持心跳连接。 这样系统的维护人员就可以通过EurekaServer来监控系统中各个微服务是否正常运行，SpringCloud的一 些其他模块(比如Zuul)就可以通过EurekaServer来发现系统中的其他微服务,并执行相关的逻辑;

- > 心跳连接：搁一小段时间发送一下请求，如果没有响应则认为对方已经死亡

- 与Dubbo的区别

  - Eureka包含两个组件: Eureka Server和Eureka Client。
  - Eureka Server提供服务注册服务,各个节点启动后，会在EurekaServer中进行注册，这样Eureka Server
    中的服务注册表中将会村粗所有可用服务节点的信息，服务节点的信息可以在界面中直观的看到。
  - 心跳机制：Eureka Client是一个Java客户端， 用于简化EurekaServer的交互，客户端同时也具备-个内置的,使用轮询负载算法的负载均衡器。在应用启动后,将会向EurekaServer发送心跳(默认周期为30秒)。如果Eureka Server在多个心跳周期内没有接收到某个节点的心跳，EurekaServer将 会从服务注册表中把这个服务节点移除掉(默认周期为90秒) 

- 三大角色

  - 客户端Eureka Server: 提供服务的注册于发现。
  - 提供者Service Provider: 将自身服务注册到Eureka中，从而使消费方能够找到
  - 消费者Service Consumer: 服务消费方从Eureka中获取注册服务列表,从而找到消费服务

### 起步

springcloud项目创建子模块`study-eureka-7001`

pom依赖导入新版的netflix的

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

    <artifactId>study-eureka-7001</artifactId>
<!--  导入eureka的依赖，因为父项目指定了springcloud的版本，所以组件版本也固定了  -->
    <dependencies>
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-netflix-eureka-server</artifactId>
        </dependency>
    </dependencies>
</project>
```

配置yml文件

```properties
server:
  port: 7001

# Eureka配置
eureka:
  instance:
    hostname: localhost # 服务端的实例名称
  client:
    register-with-eureka: false # 是否想eureka注册中心注册自己本身
    fetch-registry: false # fetch-registry为false表示自己是注册中心
    service-url:  # 监控页面
      defaultZone: http://${eureka.instance.hostname}:${server.port}/eureka/
```

配置注册中心的启动类

```java
package com.ifyyf;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.netflix.eureka.server.EnableEurekaServer;

/**
 * @Author if
 * @Description: Eureka注册中心
 * @Date 2021-08-24 下午 06:48
 */
/**
 * Eureka服务端的启动类，可以接收别的服务注册进来
 * 访问直接访问localhost:7001根目录即可
 */
@EnableEurekaServer
@SpringBootApplication
public class EurekaServer_7001 {
    public static void main(String[] args) {
        SpringApplication.run(EurekaServer_7001.class,args);
    }
}
```

访问`http://localhost:7001/`得到下图页面
*（原站配图缺失）*


### 自我保护机制

一句话总结:`某时刻某一个微服务不可以用了，eureka不会立刻清理，依旧会对该微服务的信息进行保存!`

- 默认情况下，如果EurekaServer在一 定时间内没有接收到某个微服务实例的心跳，EurekaServer将 会注销该实例(默认90秒)。但是当网络分区故障发生时，微服务与Eureka之间无法正常通行，以上行为可能变得非常危险了——因为微服务本身其实是健康的，**此时本不应该注销这个服务**。Eureka通过**自我保护机制**来解决这个问题——当EurekaServer节点在短时间内丢失过多客户端时(可能发生了网络分区故障)，那么这个节点就会进入自我保护模式。一旦进入该模式，EurekaServer就会保护服务注册表中的信息 ，不再删除服务注册表中的数据(也就是不会注销任何微服务)。当网络故障恢复后,该EurekaServer节 点会自动退出自我保护模式。
- 在自我保护模式中，EurekaServer会保护服务注册表中的信息， 不再注销任何服务实例。当它收到的心跳数重新恢复到阈值以上时，该EurekaServer 节点就会自动退出自我保护模式。它的设计哲学就是宁可保留错误的服务注册信息，也不盲目注销任何可能健康的服务实例。-句话:好死不如赖活着
- 综上，自我保护模式是一-种应对网络异常的安全保护措施。它的架构哲学是宁可同时保留所有微服务(健康的微服务和不健康的微服务都会保留)，也不盲目注销任何健康的微服务。使用自我保护模式，可以让Eureka集群更加的健壮和稳定
- 在SpringCloud中，可以使用`eureka.server.enable-self-preservation = false`禁用自我保护模式
  - [不推荐关闭自我保护机制]

### 注册服务

`study-provider-dept-8001`添加Eureka依赖

```pom
<dependency>
    <groupId>org.springframework.cloud</groupId>
	<artifactId>spring-cloud-starter-netflix-eureka-server</artifactId>
</dependency>
```

启动类添加注解

```java
package com.ifyyf;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.netflix.eureka.EnableEurekaClient;

/**
 * @Author if
 * @Description:
 * 疑问@EnableEurekaClient和@EnableDiscoveryClient共同点与区别是什么？
 * 共同点：都是能够让注册中心能够发现，扫描到改服务
 * 区别：@EnableEurekaClient只适用于Eureka作为注册中心，@EnableDiscoveryClient可以是其他注册中心
 * @Date 2021-08-24 下午 12:42
 */
@SpringBootApplication
/**
 * 开启Eureka的客户端，会自动根据配置类的地址自动注册到Eureka中
 */
@EnableEurekaClient
//使之能够被注册中心发现，不仅仅是eureka
@EnableDiscoveryClient
public class DeptProvider_8001 {
    public static void main(String[] args) {
        SpringApplication.run(DeptProvider_8001.class,args);
    }
}
```

yml配置

```properties
# Eureka配置，服务注册到哪里
eureka:
  client:
    service-url:
      defaultZone: http://localhost:7001/eureka/
  instance:
    instance-id: springcloud-provider-dept8001  # 修改Eureka上的默认描述信息

# info配置
info:
  app.name: study-springcloud
  company.name: www.ifyyf.com
```

然后先重启注册中心，再启动微服务，访问注册中心

图示左边是微服务的id名称，右边链接是服务的相关info(在yml的info配置)

*（原站配图缺失）*


### 访问所有/单个微服务的信息

在服务中可以访问到其他微服务的信息

例如在`study-provider-dept-8001`服务的controller层导入DiscoveryClient类

```java
	/**
     * 导入这个包org.springframework.cloud.client.discovery.DiscoveryClient
     */
    @Autowired
    private DiscoveryClient client;

	/**
     * 根据DiscoveryClient类可以获取注册中心注册的微服务的一些信息
     * @return
     */
    @GetMapping("/discovery")
    public Object discovery(){
        //获取微服务列表清单
        List<String> services = client.getServices();
        System.out.println("discovery =>services: "+services);
        //根据具体的微服务id(ApplicationName)，获取实例对象
        List<ServiceInstance> instances = client.getInstances("SPRINGCLOUD-PROVIDER-DEPT");
        for (ServiceInstance instance : instances) {
            System.out.println("--------------------");
            System.out.println("instance.getHost() = "+instance.getHost());
            System.out.println("instance.getPort() = "+instance.getPort());
            System.out.println("instance.getUri() = "+instance.getUri());
            System.out.println("instance.getServiceId() = "+instance.getServiceId());
        }
        return this.client;
    }
```

输出结果

```shell
discovery =>services: [springcloud-provider-dept]
--------------------
instance.getHost() = 192.168.80.1
instance.getPort() = 8001
instance.getUri() = http://192.168.80.1:8001
instance.getServiceId() = SPRINGCLOUD-PROVIDER-DEPT
```

### 集群环境搭建

**为什么要用eureka集群？**

> 之所以进行eureka集群的搭建，在于我们平时的生产环境中，很难保证单节点的eureka服务能提供百分百不间断的服务，如果eureka无响应了，整个项目应用都会出现问题
>
> 因此要保证eureka随时都能提供服务的情况下，最好的方式就是采用eureka的集群模式，也就是搭建eureka的高可用，在eureka的集群模式下，多个eureka server之间可以同步注册服务
>
> 因此，在一个eureka宕掉的情况下，仍然可以提供服务注册和服务发现的能力，从而达到注册中心的高可用

**如何搭建eureka集群**

假设我们需要3台eureka服务配置集群，则需要在每个服务的yml配置文件中挂载到另外两个的url上

以`study-eureka-7001`为例，`study-eureka-7002`与`study-eureka-7003`同理

```properties
server:
  port: 7001

# Eureka配置
eureka:
  instance:
    hostname: local1.ifyyf.com # 服务端的实例名称
  client:
    register-with-eureka: false # 是否想eureka注册中心注册自己本身
    fetch-registry: false # fetch-registry为false表示自己是注册中心
    service-url:  # 监控页面
      # 单机配置
      # defaultZone: http://${eureka.instance.hostname}:${server.port}/eureka/

      # 集群配置(关联挂载别的集群地址)
      defaultZone: http://local2.ifyyf.com:7002/eureka/,http://local3.ifyyf.com:7003/eureka/
```

注：此处的主机地址是通过修改`C:\Windows\System32\drivers\etc`目录下的hosts文件实现的，实际上都是指向了本机的`192.168.80.1`，为了区分以及集群配置

此时eureka集群搭建完成，`study-provider-dept-8001`服务端需要同时注册到所有注册中心中去

也就是将原来yml配置的注册中心的单个url修改成多个url，以逗号分割

```properties
eureka:
  client:
    service-url:
      defaultZone: http://local2.ifyyf.com:7002/eureka/,http://local1.ifyyf.com:7001/eureka/,http://local3.ifyyf.com:7003/eureka/

```

**结果**

此时启动注册中心，再启动服务，可以看见3台注册中心都成功注册了服务，且如果其中有某一两台eureka注册中心断线宕机，剩下的注册中心依旧存在，达到了注册中心的高可用性

*（原站配图缺失）*


### CAP原则及对比Zookeeper

CAP原则又称CAP定理，指的是在一个分布式系统中

**一致性**（Consistency）

> 在分布式系统中的所有数据备份，在同一时刻是否同样的值，**即写操作之后的读操作，必须返回该值**。（分为弱一致性、强一致性和最终一致性） 

**可用性**（Availability）

> 在集群中一部分节点故障后，集群整体是否还能响应客户端的读写请求。（对数据更新具备高可用性） 

**分区容错性**（Partition tolerance） 

> 以实际效果而言，分区相当于对通信的时限要求。系统如果不能在时限内达成数据一致性，就意味着发生了分区的情况，必须就当前操作在C和A之间做出选择 

CAP原则的精髓就是要么AP，要么CP，要么AC，但是不存在CAP ，因为无法同时满足3个要求

#### 取舍策略

CAP三个特性只能满足其中两个，那么取舍的策略就共有三种 ：

**CA：**单点集群，满足-致性，可用性的系统，通常可扩展性较差

>  如果不要求P（不允许分区），则C（强一致性）和A（可用性）是可以保证的。但放弃P的同时也就意味着放弃了系统的扩展性，也就是分布式节点受限，没办法部署子节点，这是违背分布式系统设计的初衷的。传统的关系型数据库RDBMS：Oracle、MySQL就是CA。 

**CP：**满足一致性,分区容错性的系统，通常性能不是特别高

>  如果不要求A（可用），相当于每个请求都需要在服务器之间保持强一致，而P（分区）会导致同步时间无限延长(也就是等待数据同步完才能正常访问服务)，一旦发生网络故障或者消息丢失等情况，就要牺牲用户的体验，等待所有数据全部一致了之后再让用户访问系统。设计成CP的系统其实不少，最典型的就是分布式数据库，如Redis、HBase等。对于这些分布式数据库来说，数据的一致性是最基本的要求，因为如果连这个标准都达不到，那么直接采用关系型数据库就好，没必要再浪费资源来部署分布式数据库。

**AP：**满足可用性,分区容错性的系统，通常可能对一致性要求低一些

>  要高可用并允许分区，则需放弃一致性。一旦分区发生，节点之间可能会失去联系，为了高可用，每个节点只能用本地数据提供服务，而这样会导致全局数据的不一致性。典型的应用就如某米的抢购手机场景，可能前几秒你浏览商品的时候页面提示是有库存的，当你选择完商品准备下单的时候，系统提示你下单失败，商品已售完。这其实就是先在 A（可用性）方面保证系统可以正常的服务，然后在数据的一致性方面做了些牺牲，虽然多少会影响一些用户体验，但也不至于造成用户购物流程的严重阻塞。

#### Eureka比Zookeeper好在哪

一个分布式系统不能同时满足CAP

由于分布式系统必须要满足`分区容错性P`，所以只能在`可用性A`与`一致性C`之间权衡

- Zookeeper保证的是CP

  > 当向注册中心查询服务列表时,我们可以容忍注册中心返回的是几分钟以前的注册信息，但不能接受服务直接down掉不可用。也就是说，服务注册功能对一致性的要求要高于可用性。
  >
  > 但是zk会出现这样一种情况， 当master节点因为网络故障与其他节点失去联系时，剩余节点会重新进行leader选举。
  >
  > 问题在于，选举leader的时间太长，30~120s，且选举期间整个zk集群都是不可用的，这就导致在选举期间注册服务瘫痪。
  >
  > 在云部署的环境下，因为网络问题使得zk集群失去master节点是较大概率会发生的事件，虽然服务最终能够恢复，但是漫长的选举时间导致的注册长期不可用是不能容忍的。

- Eureka保证的是AP

  > Eureka看明白了这一-点， 因此在设计时就优先保证可用性。Eureka各个节 点都是平等的，几个节点挂掉不会影响正常节点的工作,剩余的节点依然可以提供注册和查询服务。
  >
  > 而Eureka的客户端在向某个Eureka注册时，如果发现连接失败，则会自动切换至其他节点，只要有一-台Eureka还在，就能保住注册服务的可用性，只不过查到的信息可能不是最新的，
  >
  > 除此之外，Eureka还有一 -种自我保护机制， 如果在15分钟内超过85%的节点都没有正常的心跳，那么Eureka就认为客户端与注册中心出现了网络故障，此时会出现以下几种情况:
  >
  > 1. Eureka不再从注册列表中移除因为长时间没收到心跳而应该过期的服务
  > 2. Eureka仍然能够接受新服务的注册和查询请求，但是不会被同步到其他节点上(即保证当前节点依然可用)
  > 3. 当网络稳定时，当前实例新的注册信息会被同步到其他节点中

**因此，Eureka可以很好地应对因为网络故障等原因导致的部分节点失去联系的情况，而不会像zookeeper那样整个服务瘫痪**

### json被解析成了xml？

如果发现本该返回json数据的接口，返回时变成了xml格式，那可能是eureka中自带的`jackson-dataformat-xml`将json数据解析成了xml，只需要在**客户端**的xml文件中的eureka依赖下排除这个依赖即可

```xml
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
```
