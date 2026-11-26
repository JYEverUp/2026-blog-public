# 第85节 CompletableFuture 实现异步任务编排，太好用了

# 1、实现一个需求
后端需要给前端提供一个接口：根据商品id查询商品详情的接口，里面需要包含：
- step1：商品基本信息
- step2：商品折扣信息
- step3：商品描述信息
这3个信息都需要调用不同的接口获取
- step2需要依赖step1
- step3和step1、step2之间没有依赖关系
关系图如下，我们可以使用线程池来并行执行，提升这个接口的性能
- step1和step3可以并行执行
- step2需要等待step1执行后才能执行
- 等到3个步骤都完成后，将结果返回
![image-20240904111045902](/blogs/_archive-2024-assets/ed932bb8a7ab6e5d2d9f.webp)
# 2、版本1：使用线程池+Future实现需求
```java
@Test
public void test1() throws ExecutionException, InterruptedException {
    long startTime = System.currentTimeMillis();
    ExecutorService executorService = Executors.newFixedThreadPool(10);
    //使用线程池异步执行step1
    Future<String> step1 = executorService.submit(() -> {
        sleep(500);
        return "获取商品基本信息";
    });
    //使用线程池异步执行step2
    Future<String> step2 = executorService.submit(() -> {
        //这里需要等到step1执行完毕
        step1.get();
        sleep(500);
        return "获取商品折扣信息";
    });
    //使用线程池异步执行step3
    Future<String> step3 = executorService.submit(() -> {
        sleep(500);
        return "获取商品描述信息";
    });
    //这里需要等到3个步骤都执行完成，这里可以不用写step1.get()，因为step2依赖于step1
    step2.get();
    step3.get();
    System.out.println("耗时(ms)：" + (System.currentTimeMillis() - startTime));
}
private static void sleep(long timeout) {
    try {
        TimeUnit.MILLISECONDS.sleep(timeout);
    } catch (InterruptedException e) {
        throw new RuntimeException(e);
    }
}
```
上面这种写法不是太优雅，step2对step1有依赖，需要在step2中调用step1.get()等到step1执行结束；如果任务之间的依赖关系非常复杂的时候，写法上就比较复杂了。
比如下面这个图，有6个任务，任务之间有并行关系，有依赖关系，使用线程池+Future实现，写法上就比较复杂了。
![image-20240904113158956](/blogs/_archive-2024-assets/f8a3c83a7ba7a96a0b66.webp)
更好的办法，使用`CompletableFuture `；CompletableFuture 可以解决异步任务任意编排的问题。
# 3、什么是异步任务编排？
异步任务编排就是让多个可以并行的任务按照预定的逻辑和顺序高效执行的过程。
说的更简单点：就是任务之间可以随意组合，按照任意的逻辑进行组合，重点在于逻辑二字，任务之间可以是：并行关系、依赖关系、AND关系、OR关系
CompletableFuture 就是异步任务编排的一种实现，非常好用，它实现了Future接口，所以Future可以干的事情，CompletableFuture 都可以干，且功能更强大。
下面使用`CompletableFuture+线程池`来实现本文需求。
# 4、版本2：线程池+CompletableFuture 实现需求
```java
@Test
public void test2() throws ExecutionException, InterruptedException {
    long startTime = System.currentTimeMillis();
    ExecutorService executorService = Executors.newFixedThreadPool(10);
    //使用线程池异步执行step1
    CompletableFuture<String> step1 = CompletableFuture.supplyAsync(() -> {
        sleep(500);
        return "获取商品基本信息";
    }, executorService);
    //使用线程池异步执行step2
    CompletableFuture<String> step2 = step1.thenApplyAsync((goodsInfo) -> {
        sleep(500);
        return "获取商品折扣信息";
    }, executorService);
    //使用线程池异步执行step3
    CompletableFuture<String> step3 = CompletableFuture.supplyAsync(() -> {
        sleep(500);
        return "获取商品描述信息";
    }, executorService);
    //这里需要等到3个步骤都执行完成，这里可以不用写step1，因为step2依赖于step1
    CompletableFuture.allOf(step2, step3).get();
    System.out.println("耗时(ms)：" + (System.currentTimeMillis() - startTime));
}
private static void sleep(long timeout) {
    try {
        TimeUnit.MILLISECONDS.sleep(timeout);
    } catch (InterruptedException e) {
        throw new RuntimeException(e);
    }
}
```
