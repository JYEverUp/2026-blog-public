#  性能调优：线程死锁相关问题

# 1、什么是线程死锁？
两个或多个线程在执行过程中，因争夺共享资源而被阻塞，且无法继续执行下去的一种状态。
# 2、示例
比如下面这个案例，定义了两个线程：thread1和thread2
- thread1对resource1上锁，然后尝试获取resource2的锁；
- thread2对resource2上锁，然后尝试获取resource1的锁；
运行下，2个线程会相互等待，出现死锁
```java
public class DeadlockDemo {
    // 创建两个共享资源
    private static final String resource1 = new String();
    private static final Object resource2 = new Object();
    public static void main(String[] args) {
        /**
         * 两个线程
         * thread1对resource1上锁，然后尝试获取resource2的锁；
         * thread2对resource2上锁，然后尝试获取resource1的锁；
         * 2个线程会相互等待，出现死锁
         */
        Thread thread1 = new Thread(() -> {
            synchronized (resource1) {
                System.out.println("Thread 1: Locked resource 1");
                try {
                    Thread.sleep(100); // 假设这里有其他操作，需要一些时间
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                System.out.println("Thread 1: Attempting to lock resource 2");
                //尝试索取resource2的锁
                synchronized (resource2) {
                    System.out.println("Thread 1: Locked resource 2");
                }
            }
        }, "thread1");
        Thread thread2 = new Thread(() -> {
            synchronized (resource2) {
                System.out.println("Thread 2: Locked resource 2");
                try {
                    Thread.sleep(100); // 假设这里有其他操作，需要一些时间
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                //尝试索取resource1的锁
                System.out.println("Thread 2: Attempting to lock resource 1");
                synchronized (resource1) {
                    System.out.println("Thread 2: Locked resource 1");
                }
            }
        }, "thread2");
        // 启动线程
        thread1.start();
        thread2.start();
    }
}
```
# 3、死锁会导致什么问题？
线程阻塞，这个是最直接的影响
若有大量线程死锁，会导致线程被耗尽，最终将导致系统崩溃，无法对外提供服务
# 4、如何发现死锁？
需要依赖监控系统：监控系统可以定时使用jstack命令采集线程信息，jstack命令中可以查看到死锁的详细信息，进行告警，人工介入干预。
# 5、3种方法定位死锁代码
## 1）方案1：jps+jstack命令
- jps查找进程id
  > jdk自带工具，可以查看所有的java进程
  ```shell
  jsp
  ```
- jstack命令查看死锁信息
  > jdk自带的工具，可以查看某个java进程中所有的线程快照，可以看到死锁的相信信息
  ```shell
  jstack 进程id
  ```
## 2）方案2：jvisualvm
> jvisualvm工具：jdk自带的工具
cmd中运行：jvisualvm，即可打开这个工具
![image-20240702114921880](/blogs/_archive-2024-assets/2eac9301af4116a61e54.webp)
![image-20240702114947327](/blogs/_archive-2024-assets/6c2f98853343907d55de.webp)
## 3）方案3：arthas
> arthas：阿里提供的一个特好用的jvm线上问题诊断利器，详情见：https://arthas.aliyun.com/doc/quick-start.html
# 6、死锁常见的解决方案
为了解决Java中的线程死锁问题，可以采取以下几种策略：
1. **避免使用多个锁**：通过合理设计程序，尽量避免多个线程同时争用相同的资源
2. **保持锁的有序性**：当使用多个锁时，保持所有线程获取锁的顺序一致，以避免因顺序不一致而导致的死锁
3. **超时等待**：设置锁的超时时间，当等待超过一定时间后，放弃对锁的请求，进行其他的处理
4. **死锁检测和恢复**：使用工具来检测和恢复死锁，一旦检测到死锁，可以通过中断线程、释放资源等方式来恢复程序的执行
