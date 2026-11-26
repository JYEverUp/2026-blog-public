#  如何优雅的处理，线程池内异常？

# 完整代码
```java
package com.itsoku.lesson099;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.concurrent.*;
/**
 * 99、线程池中如何优雅处理异常？
 * <b>description</b>实战
 * <b>time</b>：2024/9/12 21:21 <br>
 * <b>author</b>：gjy
 */
public class ThreadTest {
    private static final Logger LOGGER = LoggerFactory.getLogger(ThreadTest.class);
    @Test
    public void test1() throws InterruptedException {
        Thread thread1 = new Thread(() -> {
            LOGGER.info("线程中抛出异常测试");
            throw new RuntimeException("异常啦");
        }, "thread1");
        thread1.start();
        thread1.join();
    }
    @Test
    public void test2() throws InterruptedException {
        Thread thread1 = new Thread(() -> {
            try {
                LOGGER.info("线程中抛出异常测试");
                throw new RuntimeException("异常啦");
            } catch (RuntimeException e) {
                LOGGER.error(e.getMessage(), e);
                throw new RuntimeException(e);
            }
        }, "thread1");
        thread1.start();
        thread1.join();
    }
    @Test
    public void test3() throws InterruptedException {
        Thread thread1 = new Thread(() -> {
            LOGGER.info("线程中抛出异常测试");
            throw new RuntimeException("异常啦");
        }, "thread1");
        thread1.setUncaughtExceptionHandler((Thread t, Throwable e) -> {
            LOGGER.info("线程thread1发生异常时，会进来");
            LOGGER.error(e.getMessage(), e);
        });
        thread1.start();
        thread1.join();
    }
    @Test
    public void test4() throws InterruptedException {
        ThreadFactory threadFactory = Executors.defaultThreadFactory();
        ThreadPoolExecutor threadPoolExecutor = new ThreadPoolExecutor(5,
                5,
                10,
                TimeUnit.MINUTES, new ArrayBlockingQueue<>(1000),
                new ThreadFactory() {
                    @Override
                    public Thread newThread(Runnable r) {
                        Thread thread = threadFactory.newThread(r);
                        thread.setUncaughtExceptionHandler((Thread t, Throwable e) -> {
                            LOGGER.error(e.getMessage(), e);
                        });
                        return thread;
                    }
                });
        threadPoolExecutor.execute(() -> {
            LOGGER.info("线程池执行任务，抛出异常测试");
            throw new RuntimeException("线程池执行任务，异常啦");
        });
        threadPoolExecutor.shutdown();
        threadPoolExecutor.awaitTermination(1, TimeUnit.MINUTES);
    }
}
```
