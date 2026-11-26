#  方法执行异常，使用arthas，快速定位问题

# 先来看一个问题
当生产上某个方法的执行结果和我们期望的结果不一致时，咱们怎么办？
# 常见的做法
- 修改代码，添加一些日志，在日志中输出方法的入参和返参
- 然后发布上线，拿到入参、返参
- 在本地进行重现，定位问题
# 是否有更简单的方法呢？
可以使用阿里的arthas工具，在不调整代码的情况下，拿到任意一个方法的入参、返参值，帮助我们更快的定位问题。
# arthas
arthas：阿里开源的一款Java问题诊断利器，详情见：https://arthas.aliyun.com/doc/quick-start.html
# arthas watch命令
watch命令可以用来观察某个方法的调用情况，具体点说，可以用来观察任意一个方法，方法被调用的时候，可以拿到这个方法的入参、方法的返回值、方法抛出的异常等信息。
# 如何使用？（4个步骤）
先运行下面这段代码，然后演示用arthas watch命令获取add方法的入参和返回值。
```java
import java.util.concurrent.TimeUnit;
public class WatchTest {
    public static void main(String[] args) throws InterruptedException {
        System.out.println("程序已启动");
        for (int i = 1; i < 1000000; i++) {
            add(i, i + 1);
            TimeUnit.SECONDS.sleep(1);
        }
    }
    public static int add(int a, int b) {
        return a + b;
    }
}
```
### 1）下载arthas
```java
curl -O https://arthas.aliyun.com/arthas-boot.jar
```
### 2）启动arthas
```shell
java -jar arthas-boot.jar
```
### 3）选择需要诊断的java进程
```shell
[root@iZuf6aaova1ojwh3hg9pnxZ test]# java -jar arthas-boot.jar
* [1]: 4047112 WatchTest
```
### 4）使用watch查看add方法的入参和返回值
```java
watch WatchTest add "{params,returnObj}" -x 2
```
> 这个命令会观察`WatchTest`类中的`add`方法，每次该方法被调用时，都会输出其参数和返回值。
![image-20240717162504494](/blogs/_archive-2024-assets/d5a373cf5a7c25bb0534.webp)
# 更详细的教程
更多用法见：https://arthas.aliyun.com/doc/watch.html
