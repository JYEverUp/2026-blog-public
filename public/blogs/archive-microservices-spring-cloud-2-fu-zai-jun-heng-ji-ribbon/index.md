## Ribbon：负载均衡及Ribbon

### 什么是Ribbon

Spring Cloud Ribbon是基于Netflix Ribbon实现的一套==客户端负载均衡==的工具。

> 简单的说，Ribbon是Netflix发布的开源项目 ,主要功能是提供客户端的软件负载均衡算法，将NetFlix的中间层服务连接在一起。
>
> Ribbon的客户端组件提供-系列完整的配置项如:连接超时、重试等等。
>
> 简单的说，就是在配置文件中列出LoadBalancer (==简称LB:负载均衡==)后面所有的机器，Ribbon会自动的帮助你基于某种规则(如简单轮询,随机连接等等)去连接这些机器。
>
> 我们也很容易使用Ribbon实现自定义的负载均衡算法!

### Ribbon能干嘛

- LB，负载均衡，在微服务或分布式集群中经常用的一种应用
- 负载均衡简单的说就是将用户的请求平摊的分配到多个服务上,从而达到系统的HA (高可用)
- 常见的负载均衡的软件有Ngnix，Lvs等
- dubbo、SpringCloud中均给我们提供了负载均衡, SpringCloud的负载均衡算法可以==自定义==
- 负载均衡简单分类
  - 集中式LB
    - 即在服务的消费方和提供方之间使用独立的L B设施，如Nginx: 反向代理服务器 ,由该设施负责把
      访问请求通过某种策略转发至服务的提供方
  - 进程式LB
    - 将LB逻辑集成到消费方(客户端)，消费方从服务注册中心获知有哪些地址可用,然后自己再从这些地址中选出一个合适的服务器（从Eureka中拿出所有服务，根据算法选出合适的）
    - Ribbon就属于进程内LB，它只是一个类库，集成于消费方进程,消费方通过它来获取到服务提供方
      的地址

### 使用Ribbon实现轮询负载均衡

*（原站配图缺失）*


首先创建3个内容相同的数据库

以`study-db01`、`study-db02`、`study-db03`为例，均含有dept表，但是表中有一个字段不同

source字段代表当前数据库名称(等会负载均衡时方便区分)

*（原站配图缺失）*


创建另外两个服务`study-provider-dept-8002`与`study-provider-dept-8003`，并配置好不同的数据库

在客户端使用`@LoadBalanced注解`开启Ribbon负载均衡实现RestTemplate，仅仅只是多了一个注解而已

```java
/**
     * @LoadBalanced注解配置负载均衡实现RestTemplate
     * @return
     */
    @LoadBalanced   //Ribbon
    @Bean
    public RestTemplate getRestTemplate(){
        return new RestTemplate();
    }
```



启动eureka集群，再启动3个服务，最后开启客户端进行访问

访问80端口的用户端，多刷新几次，可以看到返回的数据中source字段分别为`study-db01 `、`study-db02`、

 `study-db03 `

证明客户端访问到注册中心的服务时采用了Ribbon的负载均衡，==轮询==均摊到了各个服务中去，才会使得每次访问的结果不同

### 自定义Ribbon负载均衡算法

在客户端启动类中使用==Ribbon自定义负载均衡策略配置注解==

`@RibbonClient(name="SPRINGCLOUD-PROVIDER-DEPT",configuration = MyRule.class)`

- name是针对的某个服务的名称进行自定义负载均衡
- configuration是负载均衡算法类的class

> ==注==：这个自定义的类不能放在@ComponentScan所扫描的当前包以及子包下，否则我们自定义的这个配置类就会被所有的Ribbon客户端所共享，也就是我们达不到特殊化指定的目的了。 

## Feign负载均衡

### 什么是Feign

> feign是声明式的web service客户端，它让微服务之间的调用变得更简单了，类似controller调用service。 SpringCloud集成了Ribbon和Eureka,可在使用Feign时提供负载均衡的http客户端。
> 只需要创建一个接口， 然后添加注解即可!

ribbon是面向**微服务名字**进行访问，而feign是面向**接口和注解**进行访问

不需要像ribbon一样，根据服务名称进行配置，而是在微服务接口上添加一个feign注解，即可（与Dao接口上添加@Mapper注解差不多的感觉）

==Feign集成了Ribbon==，比ribbon更方便，但是加了一层之后性能会降低一点

### 起步

在api模块中创建interface接口类`DeptClintService`，用于Feign的配置

```java
package com.ifyyf.service;

import com.ifyyf.pojo.Dept;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import java.util.List;

/**
 * @Author if
 * @Description: mapping注解的url是指向对应服务的接口url
 * @Date 2021-08-25 下午 10:30
 */
//指定负载均衡的服务名称
@FeignClient(value = "SPRINGCLOUD-PROVIDER-DEPT")
@Component
public interface DeptClintService {

    @GetMapping("/dept/getAll")
    List<Dept> queryAll();

    @GetMapping("/dept/get/{deptno}")
    Dept queryById(@PathVariable("deptno")Long deptno);
}

```

因为之前的`study-consumer-dept-80`是配置了Ribbon，所以再创建一个新的客户端模块`study-consumer-dept-feign`用于配置Feign

==这俩选其一即可，都是80端口的客户端，所以yml等文件都是完全相同的==

`DeptConsumerController`客户端接口中注册刚刚写的`DeptClintService`feign配置接口

==**具体的访问流程在注释里**==

> 总结：用户=>客户端Controller=>Feign负载均衡=>注册中心集群=>服务端Controller=>mysql数据库集群

```java
package com.ifyyf.controller;

import com.ifyyf.pojo.Dept;
import com.ifyyf.service.DeptClintService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.List;

/**
 * @Author if
 * @Description: 消费者客户端
 * 用户应该访问的是本接口ip:80/consumer/dept/getAll
 * 然后代理到了Feign负载均衡接口类，由Feign的接口类根据算法(轮询)打向配置好了的并注册到了注册中心的服务接口去
 * 打向的主机地址由@FeignClient(value = "SPRINGCLOUD-PROVIDER-DEPT")注解接管
 * 具体的接口地址由方法上的@GetMapping("/dept/getAll")接管
 * 总结：用户=>客户端Controller=>Feign负载均衡=>注册中心集群=>服务端Controller=>mysql数据库集群
 * @Date 2021-08-24 下午 01:03
 */
@RestController
@CrossOrigin
@RequestMapping("/consumer/dept")
public class DeptConsumerController {

    @Autowired
    private DeptClintService deptClintService=null;
    /**
     * RestFul风格
     * @param deptno
     * @return
     */
    @GetMapping("/get/{deptno}")
    public Dept get(@PathVariable("deptno") Long deptno){
        return deptClintService.queryById(deptno);
    }

    /**
     * list返回值就给List.class
     * @return
     */
    @GetMapping("/getAll")
    public List<Dept> getAll(){
        return deptClintService.queryAll();
    }
}
```

最后开启注册中心，服务端，最后开启客户端并访问接口，可以看到成功访问，刷新后拿到不同结果，负载均衡成功实现
