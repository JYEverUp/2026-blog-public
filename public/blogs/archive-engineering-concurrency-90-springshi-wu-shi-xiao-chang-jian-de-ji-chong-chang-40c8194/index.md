# 第90节 Spring事务失效，常见的几种场景，带你精通Spring事务

# 1、本文主要3块内容
1. Spring事务失效常见的4种场景
2. 事务失效问题如何排查？
3. 如何精通Spring事务？
# 2、事务失效场景1：通过this调用自身@Transactional方法
## 案例代码
如下代码，外部调用m1方法，m1方法中调用m2方法，虽然m2方法上加了事务@Transactional注解，但是事务不会生效
```java
@Service
public class UserService {
    @Autowired
    private UserMapper userMapper;
    public void m1() {
        this.m2("1", "m1");
    }
    @Transactional
    public void m2(String id, String name) {
        //向用户表插入一条记录
        UserPO userPO = new UserPO();
        userPO.setId(id);
        userPO.setName(name);
        this.userMapper.insert(userPO);
        //抛出异常，看看事务是否会回滚
        throw new RuntimeException("故意失败，看下事务是否会回滚");
    }
}
```
运行看下效果，虽然报异常了，但是数据插入成功了。
![image-20240910141701865](/blogs/_archive-2024-assets/b47f71e7243f45a5b4fc.png)
## 原因
Spring中的@Transactional事务，是通过aop生成代理对象实现的，所以通过代理对象访问目标方法的时候，事务才会起效。
而上面的m1方法中通过this调用的m2方法，而this并不是代理对象，所以事务是无效的。
**解决方案，这里给大家介绍3种。**
## 解决方案1：注入了自己
```java
@Service
public class UserService {
    //注入自己，articleService就是被AOP包装后的代理对象
    @Autowired
    private UserService userService;
    public void m3() {
        //通过userService访问m2，事务会生效
        this.userService.m2("3", "m3");
    }
    @Transactional
    public void m2(String id, String name) {
        //向用户表插入一条记录
        UserPO userPO = new UserPO();
        userPO.setId(id);
        userPO.setName(name);
        this.userMapper.insert(userPO);
        //抛出异常，看看事务是否会回滚
        throw new RuntimeException("故意失败，看下事务是否会回滚");
    }
}
```
## 解决方案2：编程式事务
```java
@Service
public class UserService {
    @Autowired
    private TransactionTemplate transactionTemplate;
    public void m4() {
        this.transactionTemplate.executeWithoutResult(action -> {
            this.m2("4", "m4");
        });
    }
    @Transactional
    public void m2(String id, String name) {
        //向用户表插入一条记录
        UserPO userPO = new UserPO();
        userPO.setId(id);
        userPO.setName(name);
        this.userMapper.insert(userPO);
        //抛出异常，看看事务是否会回滚
        throw new RuntimeException("故意失败，看下事务是否会回滚");
    }
}
```
## 解决方案3：AopContext.currentProxy()
```java
@Service
public class UserService {
    public void m5() {
        //通过Spring提供的工具类AopContext.currentProxy()，可以获取当前代理对象，将类型强制转换为UserService，然后调用m2方法，事务也会生效
        UserService as = (UserService) AopContext.currentProxy();
        as.m2("5", "m5");
    }
    @Transactional
    public void m2(String id, String name) {
        //向用户表插入一条记录
        UserPO userPO = new UserPO();
        userPO.setId(id);
        userPO.setName(name);
        this.userMapper.insert(userPO);
        //抛出异常，看看事务是否会回滚
        throw new RuntimeException("故意失败，看下事务是否会回滚");
    }
}
```
# 3、事务失效场景2：异常类型不匹配
Spring事务回滚的机制：会拦截@Transactional标注的方法，当方法抛出指定的异常时，被Spring捕获到了，事务才会进行回滚。
那么问题来了，哪些异常spring会回滚事务呢？
并不是任何异常Spring都会回滚事务，默认情况下，RuntimeException和Error的情况下，spring事务才会回滚。
也可以通过@Transactional中的rollbackFor属性指定要回滚的异常类型：
```java
@Transactional(rollbackFor = {异常类型列表})
```
当方法抛出的异常是这些异常、或者是这些异常的子类的时候，事务才会回滚。
比如下面这个案例代码，rollbackFor指定的是 `RuntimeException`异常，而方法内部抛出的是 `Exception`异常，不符合上面的条件，所以事务不会回滚。
```java
@Transactional(rollbackFor = RuntimeException.class)
public void m6() throws Exception {
    //向用户表插入一条记录
    UserPO userPO = new UserPO();
    userPO.setId("6");
    userPO.setName("m6");
    this.userMapper.insert(userPO);
    //抛出一个Exception异常，看看事务是否会回滚
    throw new Exception("抛出Exception异常");
}
```
运行看下效果，确实没有回滚。
# 4、事务失效场景3：异常被吞了
当业务方法抛出异常，spring感知到异常的时候，才会做事务回滚的操作，若方法内部将异常给吞了，那么spring事务无法感知到异常了，事务就不会回滚了。
如下代码，发生了异常，但是被捕获了，spring无法感知到异常，此时事务并不会被回滚
```java
@Transactional(rollbackFor = Exception.class)
public void m7() throws Exception {
    try {
        //向用户表插入一条记录
        UserPO userPO = new UserPO();
        userPO.setId("7");
        userPO.setName("m7");
        this.userMapper.insert(userPO);
        //抛出一个Exception异常，
        throw new RuntimeException("抛出Exception异常");
    } catch (Exception e) {
        e.printStackTrace();
    }
}
```
# 5、事务失效场景4：不同的线程事务无法共享
```java
@Transactional
public void m1() {
	// 事务操作1....
    new Thread() {
        //事务操作2....
    }.start();
}
```
原因：@Transactional标注的方法，在进入到这个方法前，spring会获取一个数据库的连接，通过这个连接开启事务，这个连接会放在ThreadLocal中，然后才会被dao层的mybatis、jdbctemplate共享；
但是如果是不同的线程，他们用的不是同一个数据连接，无法共享事务。
# 6、事务失效问题如何排查？
@Transaction标注的方法，调用时，会被下面这个拦截器处理，咱们可以在此方法中设置一个断点，通过debug，可以排查问题
```java
org.springframework.transaction.interceptor.TransactionInterceptor#invoke
```
# 7、如何精通Spring事务？
Spring事务这块是非常重要的一个知识点，建议大家一定要吃透。
可以看我的Spring这个系列，里面包含了Spring事务深度讲解，地址：http://itsoku.com/course/5
![image-20240910135504001](/blogs/_archive-2024-assets/f9ca4194e8f8ea26ae11.webp)
