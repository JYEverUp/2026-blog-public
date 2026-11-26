## Hystrix：服务熔断、服务降级与服务监控

### 分布式面临的问题

> 复杂分布式体系结构中的应用程序有数-十个依赖关系，每个依赖关系在某些时候将不可避免的失败!

### Hystrix是什么

> 在分布式环境中，许多服务依赖项中的一些必然会失败。Hystrix是一个库，通过添加延迟容忍和容错逻辑，帮助你控制这些分布式服务之间的交互。Hystrix通过隔离服务之间的访问点、停止级联失败和提供回退选项来实现这一点，所有这些都可以提高系统的整体弹性 
>
> “断路器”本身是一种开关装置， 当某个服务单元发生故障之后，通过断路器的故障监控(类似熔断保险丝)，向
> 调用方返回一个服务预期的，可处理的备选响应(FalBack) ,而不是长时间的等待或者抛出调用方法无法处理
> 的异常,这样就可以保证了服务调用方的线程不会被长时间，不必要的占用，从而避免了故障在分布式系统中的蔓延,乃至雪崩

Hystrix被设计的目标是：

1. 对通过第三方客户端库访问的依赖项（通常是通过网络）的延迟和故障进行保护和控制。
2. 在复杂的分布式系统中阻止级联故障。
3. 快速失败，快速恢复。
4. 回退，尽可能优雅地降级。
5. 启用近实时监控、警报和操作控制。

### 什么是服务熔断

**熔断机制是对应雪崩效应的一种微服务链路保护机制。**

> 当扇出链路的某个微服务不可用或者响应时间太长时，会进行服务的降级,==进而熔断该节点微服务的调用，快速返回错误的响应信息==。
>
> 当检测到该节点微服务调用响应正常后恢复调用链路。
>
> 在SpringCloud框架里熔断机制通过Hystrix实现。Hystrix会监控微服务间调用的状况，当失败的调用到一定阈值，缺省是5秒内20次调用失败就会启动熔断机制。
>
> 熔断机制的注解是@HystrixCommand.

#### 起步

新建`study-provider-dept-hystrix-8001`作为hystrix的的服务端

controller层的接口==添加@HystrixCommand注解==，指定当前方法熔断的解决方法名称

这样在服务出现异常问题时，会自动执行到注解标识的名称的方法（下列代码中的异常为手动模拟）

```java
package com.ifyyf.controller;

import com.ifyyf.pojo.Dept;
import com.ifyyf.service.DeptService;
import com.netflix.hystrix.contrib.javanica.annotation.HystrixCommand;
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
    //指定当前方法熔断的解决方法名称
    @HystrixCommand(fallbackMethod = "hystrixGet")
    public Dept get(@PathVariable("deptno") Long deptno){
        Dept dept = deptService.getById(deptno);
        if(dept==null){
            //手动模拟异常情况
            throw new NullPointerException("不存在id为 "+deptno+" 的数据");
        }
        return dept;
    }
    
    public Dept hystrixGet(Long deptno){
        return new Dept()
                .setDeptno(deptno)
                .setDname("不存在id为 "+deptno+" 的数据")
                .setSource("no this database in mysql");
    }
    
}
```

启动类使用==@EnableHystrix==注解开启hystrix服务熔断机制

>  注：旧版本是@EnableCircuitBreaker，新版本是@EnableHystrix

*（原站配图缺失）*


疑问：那我为什么不try-catch或者统一异常处理呢，这不是更方便嘛？

### 什么是服务降级

> 当服务器压力剧增的情况下，根据实际业务情况及流量，对一些服务和页面有策略的不处理或换种简单的方式处理，从而释放服务器资源以保证核心交易正常运作或高效运作
>
> “临时性地拆东墙补西墙” 

服务降级这个问题，如果从整体来操作，

1. 一定是先降级优先级低的接口，两权相害取其轻
2. 如果服务链路整体没有性能特别差的点，比如就是外部流量突然激增，那么就从外到内开始降级
3. 如果某个服务能检测到自身负载上升，那么可以从这个服务自身做降级



- 服务降级用在客户端，从整体网站负荷考虑，拆东墙补西墙，访问降级的服务时，切换到配置类中重写的方法
- 服务熔断用在服务端，单个服务异常时，切换到备用方法

#### 起步

**步骤**

1. 创建`DeptClientServiceFallbackFactory`服务降级配置类继承`FallbackFactory`接口

   ```java
   package com.ifyyf.service;
   
   import com.ifyyf.pojo.Dept;
   import feign.hystrix.FallbackFactory;
   import org.springframework.stereotype.Component;
   
   import java.util.List;
   
   /**
    * @Author if
    * @Description: 服务降级
    * @Date 2021-08-26 下午 03:18
    */
   @Component
   public class DeptClientServiceFallbackFactory implements FallbackFactory {
       @Override
       public DeptClintService create(Throwable throwable) {
           return new DeptClintService() {
               @Override
               public List<Dept> queryAll() {
                   return null;
               }
               @Override
               public Dept queryById(Long deptno) {
                   return new Dept()
                           .setDeptno(deptno)
                           .setDname("无法查询id为"+deptno+"的数据，为了分担其他服务的压力，该服务现已被关闭")
                           .setSource("服务关闭，无法查询");
               }
           };
       }
   }
   ```

2. 重写`DeptClintService`api接口中的方法

3. `@FeignClient`注解配置`fallbackFactory`属性，指定服务降级配置类的class

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
   //指定负载均衡的服务名称，并添加服务降级配置类的class
   @FeignClient(value = "SPRINGCLOUD-PROVIDER-DEPT",fallbackFactory = DeptClientServiceFallbackFactory.class)
   @Component
   public interface DeptClintService {
   
       @GetMapping("/dept/getAll")
       List<Dept> queryAll();
   
       @GetMapping("/dept/get/{deptno}")
       Dept queryById(@PathVariable("deptno")Long deptno);
   }
   ```

4. 客户端开启feign.hystrix服务降级

   ```properties
   # 客户端80端口模块study-consumer-dept-feign中的yml配置文件
   
   
   # 开启feign.hystrix服务降级
   feign:
     hystrix:
       enabled: true
   ```

5. 正常访问时，数据正常，当服务断开时，返回配置类中配置的信息

#### 结果

正常访问

*（原站配图缺失）*


服务断开后

*（原站配图缺失）*


### 服务监控

hystrix dashboard仪表盘可以帮助开发者可视化的看见服务被请求的情况

首先创建模块`study-consumer-hystrix-dashboard`

xml导入依赖

```xml
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
```

配置yml

```yml
server:
  port: 9001
```

启动类

```java
package com.ifyyf;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.netflix.hystrix.dashboard.EnableHystrixDashboard;

/**
 * @Author if
 * @Description: What is it
 * @Date 2021-08-26 下午 04:19
 */
@SpringBootApplication
//开启hystrix监控
@EnableHystrixDashboard
public class DeptConsumerDashboard_9001 {
    public static void main(String[] args) {
        SpringApplication.run(DeptConsumerDashboard_9001.class,args);
    }
}

```

被监控的服务端`study-provider-dept-hystrix-8001`

导入依赖

```xml
<!--    actuator完善hystrix的监控信息(必须)    -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>
```

启动类添加

```java
@Bean
    public ServletRegistrationBean getServlet() {
        HystrixMetricsStreamServlet streamServlet = new HystrixMetricsStreamServlet();
        ServletRegistrationBean registrationBean = new ServletRegistrationBean(streamServlet);
        registrationBean.setLoadOnStartup(1);
        registrationBean.addUrlMappings("/actuator/hystrix.stream");
        registrationBean.setName("HystrixMetricsStreamServlet");
        return registrationBean;
    }
```

访问`http://localhost:9001/hystrix`并输入`http://192.168.80.1:8001/actuator/hystrix.stream`等信息进入监控仪表盘
