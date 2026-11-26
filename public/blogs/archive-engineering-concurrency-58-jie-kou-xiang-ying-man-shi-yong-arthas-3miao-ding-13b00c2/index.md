#  接口响应慢，使用Arthas，3秒定位问题代码

# 1、Arthas
arthas：阿里开源的一款Java问题诊断利器，详情见：https://arthas.aliyun.com/doc/quick-start.html
# 2、演示：使用Arthas，快速定位接口慢的代码
## 2.1、案例代码
```java
package com.itsoku.lesson058;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.concurrent.TimeUnit;
/**
 * <b>description</b>实战
 * <b>time</b>：2024/7/3 19:15 <br>
 * <b>author</b>：gjy
 */
@RestController
@Slf4j
public class TestController {
    @GetMapping("/test")
    public String test() throws InterruptedException {
        log.info("start");
        this.m1();
        this.m2();
        this.m3();
        log.info("end");
        return "ok";
    }
    private void m1() throws InterruptedException {
        //休眠100毫秒
        TimeUnit.MILLISECONDS.sleep(100);
        log.info("m1");
    }
    private void m2() throws InterruptedException {
        //休眠100毫秒
        TimeUnit.MILLISECONDS.sleep(100);
        log.info("m1");
    }
    private void m3() throws InterruptedException {
        //休眠1秒
        TimeUnit.MILLISECONDS.sleep(1000);
        log.info("m1");
    }
}
```
## 2.1、使用Arthas快速定位慢接口代码（5个步骤）
### 1）下载`arthas-boot.jar`
```java
curl -O https://arthas.aliyun.com/arthas-boot.jar
```
### 2）启动`arthas`
```shell
java -jar arthas-boot.jar
```
### 3）选择需要诊断的java进程
```java
[root@iZuf6aaova1ojwh3hg9pnxZ ~]# java -jar arthas-boot.jar
* [1]: 3221212 lesson058-0.0.1-SNAPSHOT.jar
```
> 编号1是咱们需要监控的进程，输入1 便可让arthas监控这个进程
### 4）使用trace命令监控接口详细的耗时情况
> trace命令可以显示指定类和方法内部调用的详细路径，以及每个节点上的耗时情况。
>
> 这对于分析方法执行过程中的性能瓶颈非常有用，尤其是当方法调用链较长或涉及多个层级时
```shell
trace com.itsoku.lesson058.TestController test  -n 5 --skipJDKMethod false 
```
![image-20240703123847464](/blogs/_archive-2024-assets/cba211c130ab91c94576.webp)
### 5）访问接口，观察第4步trace命令的输出
```http
curl http://localhost:8080/test
```
 
