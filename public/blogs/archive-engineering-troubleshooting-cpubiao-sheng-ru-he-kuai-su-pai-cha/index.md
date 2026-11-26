## 1、问题代码

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

## 2、解决问题

### 1、使用top命令查出cpu飙升的进程

![image-20241015154113476](/blogs/_archive-2024-assets/1bd4ab56900cde441d8e.webp)

### 2:根据进程id找到导致cpu飙升的线程

```
ps H -eo pid,tid,%cpu | grep 进程id
```

### 3:将线程id转换为16进制

```
printf '0x%x\n' 线程id
```

### 4:根据线程定位问题代码

```
jstack 进程id | grep 16进制线程id -A 20
```

* jstack:jdk内置命令，用于查看某个Java进程所有线程快照，里面包含了线程详细的堆信息

* grep:linux中的用于内容查找的命令，可以从大量文本中快速找到某个关键字所在的行，一A参数后面的20，表示找到内容后，取内容所在行后面20行记录；
