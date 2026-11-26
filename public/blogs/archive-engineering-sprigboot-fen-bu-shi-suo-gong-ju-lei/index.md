## Redis分布式锁工具类

### 核心代码

![image-20241020094820911](/blogs/_archive-2024-assets/3e702e8a053c40d0d6fd.webp)

#### 测试类

#### 1.测试用例1:无阻寒式获取锁

```
  @GetMapping("/tryLockRun")
    public String tryLockRun() {
        Long startTime = System.currentTimeMillis();
        log.info("tryLockRun start");

        // 获取锁的过程不会阻塞，成功获取锁后将执行业务，业务执行完成后自动释放锁，并返回true；
        // 若无法获取锁，则会立即返回false
        boolean lockResult = this.distributeLock.tryLockRun("lock1", () -> {
            log.info("获取锁成功，执行业务");
            try {
                TimeUnit.SECONDS.sleep(5); // 控制业务执行的时间
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
        });

        log.info("耗时:{}, {}", (System.currentTimeMillis() - startTime),
            lockResult ? "获取锁成功" : "获取锁失败");

        return lockResult ? "获取锁成功" : "获取锁失败";
    }

```

#### 2.测试用例2:获取锁有超时时间

```
@GetMapping("/tryLockRunWaitTime")
    public String tryLockRunWaitTime() {
        long startTime = System.currentTimeMillis();
        log.info("tryLockRunWaitTime start");

        // 尝试获取锁，最多等待1秒，成功获取锁后将执行业务，业务执行完成后自动释放锁，并返回true；
        // 若1秒无法获取锁，则返回false
        boolean lockResult = this.distributeLock.tryLockRun("lock1", () -> {
            log.info("获取锁成功，执行业务");
            try {
                TimeUnit.SECONDS.sleep(5); // 控制业务执行的时间
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
        }, 1, TimeUnit.SECONDS);

        log.info("耗时:{}, {}", (System.currentTimeMillis() - startTime),
                lockResult ? "获取锁成功" : "获取锁失败");

        return lockResult ? "获取锁成功" : "获取锁失败";
    }

```



#### 3.测试用例3:获取锁会阻塞，直到成功获取锁

```
@GetMapping("/lockRun")
    public String lockRun() {
        long startTime = System.currentTimeMillis();
        log.info("lockRun start");

        // 获取锁的过程会阻塞，直到成功获取锁，成功获取锁后将执行业务，业务执行完成后自动释放锁
        this.distributeLock.lockRun("lock1", () -> {
            log.info("获取锁成功，执行业务");
            try {
                TimeUnit.SECONDS.sleep(5); // 控制业务执行的时间
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
        });

        log.info("获取锁成功, 耗时: {}", (System.currentTimeMillis() - startTime));
        return "获取锁成功";
    }
```



### 如何使用?

#### 1.引|入redisson配置

```
    @Bean
    public RedissonClient redisson() {
        Config config = new Config();
        config.useSingleServer().setAddress("redis://127.0.0.1:6379");
        return Redisson.create(config);
    }
```

#### 2.application.yml中配置锁的前置

![image-20241020094835983](/blogs/_archive-2024-assets/97804658ad88648b81bb.webp)

#### 3.业务中注入 DistributeLock

#### 4.使用 DistributeLock接口中的方法加锁执行业务源码获取

## 源码获取方式

[源码获取]( https://github.com/18194085604/redisUtils.git)
