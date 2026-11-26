## 1、什么是线程死锁?

两个或多个线程在执行过程中，因争夺共享资源而被阻塞，且无法继续执行下去的一种状态。

## 2、示例

比如下面这个案例，定义了两个线程:thread1和thread2

* thread1对resource1上锁，然后尝试获取resource2的锁;
* thread2对resource2上锁，然后尝试获取resource1的锁:
* 运行下，2个线程会相互等待，出现死锁

```
public class DeadlockExample {

    private static final Object lock1 = new Object();
    private static final Object lock2 = new Object();

    public static void main(String[] args) {
        new Thread(() -> {
            synchronized (lock1) {
                System.out.println("Thread 1: Hold lock1 and waiting for lock2");
                try {
                    Thread.sleep(10);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                synchronized (lock2) {
                    System.out.println("Thread 1: Hold both lock1 and lock2");
                }
            }
        }).start();

        new Thread(() -> {
            synchronized (lock2) {
                System.out.println("Thread 2: Hold lock2 and waiting for lock1");
                try {
                    Thread.sleep(10);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                synchronized (lock1) {
                    System.out.println("Thread 2: Hold both lock1 and lock2");
                }
            }
        }).start();
    }
}
```

## 3、死锁会导致什么问题?

线程阻塞，这个是最直接的影响
若有大量线程死锁，会导致线程被耗尽，最终将导致系统崩溃，无法对外提供服务

## 4、如何发现死锁?

需要依赖监控系统:监控系统可以定时使用istack命令采集线程信息，jstack命令中可以查看到死锁的详细信息，进行告警，人工介入干预。

## 5、3种方法定位死锁代码

#### 1)方案1:jps+jstack命令

* jps查找进程id
  JDK自带工具，可以查看所有的java进程

  ```
  jps
  ```

* jstack命令查看死锁信息
  jdk自带的工具，可以查看某个java进程中所有的线程快照，可以看到死锁的相信信息

  ```
  jstack 进程id
  ```

![image-20241017233222978](/blogs/_archive-2024-assets/96e759cfb70206764c9a.webp)

![image-20241017233234675](/blogs/_archive-2024-assets/9e4bd6caa77417fd9c03.webp)

#### 2)方案2：jvisualvm

jvisualvm工具：jdk自带的工具

cmd运行：jvisualvm，即可打开这个工具

![image-20241017232524174](/blogs/_archive-2024-assets/5f252221ac62f965e59c.webp)

![image-20241017232836120](/blogs/_archive-2024-assets/cfca1ec5a4e61b103270.webp)

![image-20241017232854604](/blogs/_archive-2024-assets/2527068681dfa4465b5f.webp)

#### 3)方案3：arthas

![image-20241017233342671](/blogs/_archive-2024-assets/f3cc35eb0a065519ad51.webp)

打：jvm命令

![image-20241017233422611](/blogs/_archive-2024-assets/2e6f0ade1aaaf50480c6.webp)

![image-20241017233750623](/blogs/_archive-2024-assets/d1d7ec973fc32c5ca92c.webp)
