#  cpu飙升，如何快速排查？

# 1、问题代码
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
# 2、定位cpu飙升：4个步骤
## 步骤1：使用top命令找到cpu飙升进程id
![image-20240703105255043](/blogs/_archive-2024-assets/16dd52bc3fb90d1a70cb.webp)
## 步骤2：根据进程id找到导致cpu飙升的线程
```shell
ps H -eo pid,tid,%cpu | grep 进程id
```
## 步骤3：将线程id转换为16进制
```shell
printf '0x%x\n' 线程id
```
## 步骤4：根据线程定位问题代码
```shell
jstack 进程id | grep 16进制线程id -A 20
```
> - jstack：jdk内置命令，用于查看某个java进程所有线程快照，里面包含了线程详细的堆栈信息
> - grep：linux中的用于内容查找的命令，可以从大量文本中快速找到某个关键字所在的行，-A参数后面的20，表示找到内容后，取内容所在行后面20行记录
# 
