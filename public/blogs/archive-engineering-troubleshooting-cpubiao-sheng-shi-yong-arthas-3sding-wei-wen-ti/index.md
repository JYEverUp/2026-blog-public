## 1、Arthas

arthas:阿里开源的一款java问题诊断利器，详情见:https://arthas.aliyun,com/doc/quick-start.html

## 2、演示:使用Arthas，3秒定位cpu飙升的代码

### 2.1、问题代码

```
public class CpuLoadTest {
    public static void main(String[] args) {
       System.out.println("程序已启动");
       while (true) {
       }
    }
}
```

执行上面这段代码，会导致cpu飙升

```
javac CpuLoadTest.java
java CpuLoadTest
```

### 2.1、使用Arthas定位问题代码(5个步骤)

#### 下载arthas-boot.jar

```
curl -0 https://arthas.aliyun.com/arthas-boot.jar
```

#### 选择需要诊断的代码

```
[root@izuf6aaovalojwh3hg9pnxz soft]# java -jar arthas-boot .jar
*[1]:3219613 cpuLoadTest
```

#### 使用thread命令查看cpu占比最高的线程

![image-20241015153713062](/blogs/_archive-2024-assets/404636c68b54f617bf58.webp)

#### 使用thread 线程id查看线程堆栈，定位问题代码

```
[arthas@3219613]$ thread 1 
"main" Id=1 RUNNABLat 
	at cpuLoadTest.main(cpuLoadTest.java:4)
```
