#  生产上，代码未生效，如何排查？

# 问题
我们的代码，由运维发布上线了，但是运行的结果和我们预期的不一样，怎么办？
# 怀疑：代码未生效
可能怀疑：运维没有发布成功，生产上运行的是老的代码
大家有没有遇到过这种情况？
# 如何解决？
让运维帮忙将生产上的代码拉下来，我们进行反编译，看下编译后的源码是不是最新的。
如果发现代码是最新，但是生产上跑的依旧是旧的代码，怎么办？
# 反编译正在运行的代码
能否进入正在运行的java程序中，反编译正在运行代码，获得其源码，便可解决问题。
arthas解决这个问题。
# arthas
arthas：阿里开源的一款Java问题诊断利器，详情见：https://arthas.aliyun.com/doc/quick-start.html
# arthas jad命令可以解决这个问题
arthas中的jad命令，可以进入正在运行的java程序，将程序中正在运行的类进行反编译，得到其源码。
# 如何使用？（4个步骤）
先运行下面这段代码，然后演示用arthas jad命令获取其源码。
```java
import java.util.concurrent.TimeUnit;
public class ArthasJadTest {
    public static void main(String[] args) throws InterruptedException {
        System.out.println("程序已启动");
        //防止程序退出，休眠1小时
        TimeUnit.HOURS.sleep(1);
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
[root@iZuf6aaova1ojwh3hg9pnxZ soft]# java -jar arthas-boot.jar
* [1]: 3219613 ArthasJadTest
```
### 4）使用jad命令获取类的源码
```java
jad 类的完整名称
```
如
```java
jad ArthasJadTest
```
