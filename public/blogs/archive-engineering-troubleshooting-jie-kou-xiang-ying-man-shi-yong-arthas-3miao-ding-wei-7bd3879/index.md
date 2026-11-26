## 1、使用Arthas定位分析

案例代码：

```
public class Testcontroller {
    public String test() {
        this.m1();
        this.m2();
        this.m3();
    }

    private void m3() {
        Thread.sleep(100);
        System.out.println("m3");
    }

    private void m2() {
        Thread.sleep(1000);
        System.out.println("m2");
    }

    private void m1() {
        Thread.sleep(1000);
        System.out.println("m1");
    }
}
```

## 2.1、使用Arthas快速定位慢接接口代码(5个步骤)

### 1)下载arthas-boot.jar

```
curl -O https://arthas.aliyun.com/arthas-boot.jar
```

### 2)启动arthas

```
java -jar arthas-boot.jar
```

### 3)选择需要诊断的iava进程

```
[root@iZuf6aaovalojwh3hg9pnxz ~]# java -jar arthas-boot.jar
*[1]:3221212 esson058-0.0.1-SNAPSHOT.jar
```

### 4)使用trace命令监控接口详细的耗时情况

* trace命令可以显示指定类和方法内部调用的详细路径，以及每个节点上的耗时情况。
* 这对于分析方法执行过程中的性能瓶颈非常有用，尤其是当方法调用链较长或涉及多个层级时

```
trace com.itsoku.lesson058.Testcontroller test -n 5 --skipJDKMethod false
```

idea可以安装插件，快速得出trace记录

![image-20241015155054292](/blogs/_archive-2024-assets/f8ade18513b72473d47d.webp)

![image-20241015155129390](/blogs/_archive-2024-assets/af1e67df10e113193ff0.webp)

![image-20241015154944212](/blogs/_archive-2024-assets/00afc6efedc1cc8d6956.webp)

### 5)访问接口，观察第4步trace命令的输出

```
curl http://localhost:8080/test
```
