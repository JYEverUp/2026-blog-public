#  cpu飙升，使用Arthas，3秒定位问题

# 1、Arthas
arthas：阿里开源的一款Java问题诊断利器，详情见：https://arthas.aliyun.com/doc/quick-start.html
# 2、演示：使用Arthas，3秒定位cpu飙升的代码
## 2.1、问题代码
```java
public class CpuLoadTest {
    public static void main(String[] args) {
        System.out.println("程序已启动");
        while (true){
            ;
        }
    }
}
```
执行上面这段代码，会导致cpu飙升
```shell
javac CpuLoadTest.java
java CpuLoadTest
```
## 2.1、使用Arthas定位问题代码（5个步骤）
### 下载`arthas-boot.jar`
```java
curl -O https://arthas.aliyun.com/arthas-boot.jar
```
### 然后用`java -jar`的方式启动`arthas`
```shell
java -jar arthas-boot.jar
```
### 选择需要诊断的java进程
```shell
[root@iZuf6aaova1ojwh3hg9pnxZ soft]# java -jar arthas-boot.jar
* [1]: 3219613 CpuLoadTest
```
### 使用thread命令查看cpu占比最高的线程
![image-20240703115644675](/blogs/_archive-2024-assets/38b1e27bfa28bd19054a.webp)
### 使用`thread 线程id`查看线程堆栈，定位问题代码
```shell
[arthas@3219613]$ thread 1
"main" Id=1 RUNNABLE
    at CpuLoadTest.main(CpuLoadTest.java:4)
```
