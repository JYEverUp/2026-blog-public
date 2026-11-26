# ThreadLocal 遇到线程池有大坑 & 通用解决方案
## 本文内容
- 演示 ThreadLocal 遇到线程池出现的故障
- 演示 InheritableThreadLocal 遇到线程池出现的故障
- 通过自定义线程池解决这些问题，也是通用的一个方案，大家一定要掌握
## 涉及到的技术
- ThreadLocal：当前线程数据共享的一个工具类，java中自带的
- InheritableThreadLocal：父子线程数据共享的一个工具类，java中自带的
- 自定义线程池
上案例。
## 案例1：测试 ThreadLocal 遇到线程池会怎么样？
### 案例代码
```java
/**
 * 1、测试 ThreadLocal 遇到线程池会怎么样？
 *
 * @throws InterruptedException
 */
@Test
public void threadLocalTest() throws InterruptedException {
    //1、创建一个ThreadLocal，用来存放用户名
    ThreadLocal<String> userNameTl = new ThreadLocal<>();
    //2、当前线程，即主线程中，放入用户名:路人
    userNameTl.set("路人");
    //3、在当前线程中从ThreadLocal获取用户名
    this.log(userNameTl.get());
    //4、创建大小为2的线程池
    ExecutorService executorService = Executors.newFixedThreadPool(2);
    //5、循环5次，通过线程池去执行任务，任务中去从 userNameTl 获取用户名，看看是否可以获取到？
    for (int i = 0; i < 5; i++) {
        executorService.execute(() -> {
            String userName = userNameTl.get();
            this.log(userName);
        });
    }
    //关闭线程池，并等待结束
    executorService.shutdown();
    executorService.awaitTermination(1, TimeUnit.MINUTES);
}
private void log(String s) {
    System.out.println(Thread.currentThread().getName() + ":" + s);
}
```
### 运行输出
```
main:路人
pool-1-thread-1:null
pool-1-thread-2:null
pool-1-thread-2:null
pool-1-thread-2:null
pool-1-thread-2:null
```
### 结论
ThreadLocal 只能在当前线程共享数据， 在线程池中无法获取到外面线程中ThreadLocal中的数据。
### 疑问？
InheritableThreadLocal 可以实现父子线程共享数据，他能解决这个问题么？看案例2
## 案例2：测试 InheritableThreadLocal 遇到线程池会怎么样？
### 案例代码
```java
/**
 * 2、测试 InheritableThreadLocal 遇到线程池会怎么样？
 *
 * @throws InterruptedException
 */
@Test
public void InheritableThreadLocalTest() throws InterruptedException {
    //1、创建一个InheritableThreadLocal，用来存放用户名
    InheritableThreadLocal<String> userNameItl = new InheritableThreadLocal<>();
    //2、创建大小为2的线程池
    ExecutorService executorService = Executors.newFixedThreadPool(2);
    //3、循环5次，通过线程池去执行任务，执行任务之前会生成一个用户名放入 userNameItl，然后在线程池中的任务中，将用户再取出来，看看和外面丢进去的是不是一样的？
    for (int i = 0; i < 5; i++) {
        //主线程中用户名，丢到userNameItl中
        String mainThreadUserName = "路人-" + i;
        userNameItl.set(mainThreadUserName);
        executorService.execute(() -> {
            //线程池中获取用户名
            String threadPoolThreadUserName = userNameItl.get();
            this.log(String.format("mainThreadUserName:" + mainThreadUserName + ",threadPoolThreadUserName:" + threadPoolThreadUserName));
        });
        TimeUnit.SECONDS.sleep(1);
    }
    //关闭线程池，并等待结束
    executorService.shutdown();
    executorService.awaitTermination(1, TimeUnit.MINUTES);
}
```
### 运行输出
大家重点关注：mainThreadUserName的值和threadPoolThreadUserName的值是否一致，从输出中可以看出，前2行是一样的，后面3行不一样了。
```java
pool-1-thread-1:mainThreadUserName:路人-0,threadPoolThreadUserName:路人-0
pool-1-thread-2:mainThreadUserName:路人-1,threadPoolThreadUserName:路人-1
pool-1-thread-1:mainThreadUserName:路人-2,threadPoolThreadUserName:路人-0
pool-1-thread-2:mainThreadUserName:路人-3,threadPoolThreadUserName:路人-1
pool-1-thread-1:mainThreadUserName:路人-4,threadPoolThreadUserName:路人-0
```
## 原因
线程中的2个子线程是重复使用，他的父线程都是main线程，子线程创建的时候，会将父线程中InheritableThreadLocal中的数据复制到子线程中，后续父线程中InheritableThreadLocal的数据再变化的时候，对子线程是没有影响的，所以出现了上面的现象。
### 结论
InheritableThreadLocal 也无法解决外面线程和线程池中线程数据共享的问题。
## 如何解决这个难题？
我们可以通过自定义线程池解决，需要重写线程池的execute和submit方法，在线程池执行任务前，先将需要在线程池中共享的数据取出来，然后在执行任务的时候，再将这个数据塞到线程池执行任务的线程中就可以了。
案例3将对这个方案进行落地。
## 案例3：自定义线程池解决这个问题
### 案例代码
大家先不要取研究代码，我们先看效果，稍后给大家解释源码
```java
/**
 * 3、自定义线程池解决这个问题
 */
@Test
public void threadLocalTestNew() throws InterruptedException {
    //1、创建一个ThreadLocal，用来存放用户名
    ThreadLocal<String> userNameTl = new ThreadLocal<>();
    //2、创建大小为2的线程池，大家先不用过度关注这块代码，稍后会解释
    ExecutorService executorService = new MyThreadPoolExecutor(new MyThreadPoolExecutor.ThreadLocalContext<String>() {
        @Override
        public String getContext() {
            return userNameTl.get();
        }
        @Override
        public void setContext(String userName) {
            userNameTl.set(userName);
        }
    }, 2, 2, 5, TimeUnit.MINUTES, new LinkedBlockingQueue<>(100));
    //3、循环5次，通过线程池去执行任务，执行任务之前会生成一个用户名放入 userNameTl，然后在线程池中的任务中，将用户再取出来，看看和外面丢进去的是不是一样的？
    for (int i = 0; i < 5; i++) {
        //主线程中用户名，丢到userNameTl中
        String mainThreadUserName = "路人-" + i;
        userNameTl.set(mainThreadUserName);
        executorService.execute(() -> {
            //线程池中获取用户名
            String threadPoolThreadUserName = userNameTl.get();
            this.log(String.format("mainThreadUserName:" + mainThreadUserName + ",threadPoolThreadUserName:" + threadPoolThreadUserName));
        });
        TimeUnit.SECONDS.sleep(1);
    }
    //关闭线程池，并等待结束
    executorService.shutdown();
    executorService.awaitTermination(1, TimeUnit.MINUTES);
}
```
### 运行输出
可以看下，mainThreadUserName和threadPoolThreadUserName的值都是一致的，说明当前这个案例解决了线程池共享外部ThreadLocal数据的问题。
```java
pool-1-thread-1:mainThreadUserName:路人-0,threadPoolThreadUserName:路人-0
pool-1-thread-2:mainThreadUserName:路人-1,threadPoolThreadUserName:路人-1
pool-1-thread-1:mainThreadUserName:路人-2,threadPoolThreadUserName:路人-2
pool-1-thread-2:mainThreadUserName:路人-3,threadPoolThreadUserName:路人-3
pool-1-thread-1:mainThreadUserName:路人-4,threadPoolThreadUserName:路人-4
```
### 源码解析
重点在于下面这个自定义线程池。
```java
import java.util.concurrent.*;
/**
 * <b>description</b>实战
 * <b>time</b>：2024/4/24 13:27 <br>
 * <b>author</b>：gjy
 */
public class MyThreadPoolExecutor extends ThreadPoolExecutor {
    private ThreadLocalContext threadLocalContext;
    public MyThreadPoolExecutor(ThreadLocalContext context, int corePoolSize, int maximumPoolSize, long keepAliveTime, TimeUnit unit, BlockingQueue<Runnable> workQueue) {
        super(corePoolSize, maximumPoolSize, keepAliveTime, unit, workQueue);
        this.threadLocalContext = context;
    }
    public MyThreadPoolExecutor(ThreadLocalContext context, int corePoolSize, int maximumPoolSize, long keepAliveTime, TimeUnit unit, BlockingQueue<Runnable> workQueue,
                                ThreadFactory threadFactory,
                                RejectedExecutionHandler handler) {
        super(corePoolSize, maximumPoolSize, keepAliveTime, unit, workQueue, threadFactory, handler);
        this.threadLocalContext = context;
    }
    @Override
    public void execute(Runnable command) {
        super.execute(this.new RunnableWrap(command));
    }
    @Override
    public <T> Future<T> submit(Callable<T> task) {
        return super.submit(task);
    }
    /**
     * 线程本地变量上下文接口，用于解决线程池中共享外部线程ThreadLocal数据的问题
     *
     * @param <T>
     */
    public interface ThreadLocalContext<T> {
        /**
         * 获取线程池中需要共享的上下文对象，将任务交给线程时会被调用
         *
         * @return
         */
        T getContext();
        /**
         * 设置上下文，线程池中的线程执行任务的时候会调用
         *
         * @param context {@link #getContext()} 返回的对象
         */
        void setContext(T context);
    }
    private class CallableWrap<V> implements Callable<V> {
        private Callable<V> target;
        private Object context;
        public CallableWrap(Callable<V> target) {
            this.target = target;
            this.context = MyThreadPoolExecutor.this.threadLocalContext.getContext();
        }
        @Override
        public V call() throws Exception {
            MyThreadPoolExecutor.this.threadLocalContext.setContext(this.context);
            return this.target.call();
        }
    }
    private class RunnableWrap implements Runnable {
        private Runnable target;
        private Object context;
        public RunnableWrap(Runnable target) {
            this.target = target;
            this.context = MyThreadPoolExecutor.this.threadLocalContext.getContext();
        }
        @Override
        public void run() {
            MyThreadPoolExecutor.this.threadLocalContext.setContext(this.context);
            this.target.run();
        }
    }
}
```
## 扩展
SpringBoot中有个@Async注解，标注在方法上，可以让这个方法异步执行，如果刚好用到了ThreadLocal来共享数据，那么就可能碰到本文中的问题。
比如：调用@Async标注的方法之前，向ThreadLocal中放入了数据，然后在@Async标注的方法中，通过ThreadLocal却取不到数据，这个时候大家应该知道如何解决了吧。
