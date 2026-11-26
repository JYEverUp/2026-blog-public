#  使用AOP简化MyBatis分页功能
## 本文内容
- PageHelper实现MyBatis分页
- 使用AOP简化MyBatis分页
## 涉及到的技术
- SpringBoot 2.7.13
- MyBatis
- PageHelper：一个很好用的 MyBatis 分页工具
- AOP环绕通知
## 案例1：PageHelper实现Mybatis分页
### PageHelper是什么？
一个开源的mybatis分页工具，github地址：https://pagehelper.github.io/
### PageHelper原理
使用Mybatis的拦截器，对sql进行改写，进而实现分页功能。
### 如何使用？（3步）
引入对应的maven配置
```xml
<dependency>
    <groupId>com.github.pagehelper</groupId>
    <artifactId>pagehelper-spring-boot-starter</artifactId>
    <version>1.4.7</version>
</dependency>
```
application.yml中添加
> 每种数据库分页语法不一样，需要指定咱们使用是那种数据库
```properties
pagehelper:
  helper-dialect: mysql # 数据方言
```
分页查询
```java
//开启分页
PageHelper.startPage(pageNum, pageSize, true);
try {
    //Mapper接口中任意查询，返回List的方法
} finally {
    //清理分页信息
    PageHelper.clearPage();
}
```
### 案例代码
```java
com.itsoku.lesson025.service.UserService#selectPage
public PageResult<UserPO> selectPage(int pageNum, int pageSize) {
    //开启分页
    PageHelper.startPage(pageNum, pageSize, true);
    try {
        List<UserPO> users = this.userMapper.selectPage();
        return PageResult.of(users);
    } finally {
        //清理分页信息
        PageHelper.clearPage();
    }
}
```
### 测试用例
```java
http://localhost:8080/user/selectPage?pageNum=2&pageSize=10
```
### 存在问题
上面的案例有个问题，代码如下，就是每次写的时候，都需要PageHelper.startPage，结束的时候，需要PageHelper.clearPage。
```java
//开启分页
PageHelper.startPage(pageNum, pageSize, true);
try {
   	//调用mapper中的方法分页查询数据
} finally {
    //清理分页信息
    PageHelper.clearPage();
}
```
### 如何解决这个问题？
我们可以通过aop搞个环绕通知，将这部分公共的代码丢到aop中，这样，就可以大大简化这个操作。
下面的案例2，将实现这个套方案。
## 案例2：使用AOP简化案例1中的分页
### 先看效果，再说原理
java代码
```java
com.itsoku.lesson025.service.UserService#selectPageNew
```
测试用例地址
```http
http://localhost:8080/user/selectPageNew?pageNum=1&pageSize=10
```
### 如何实现的？
#### IPageQuery：分页顶层接口
我们定义了一个分页的顶层接口，如下，有3个方法，用于获取分页信息，当我们mapper中的方法中有这个类型的参数的时候，就会被aop统一处理，进行分页。
```java
public interface IPageQuery {
    /**
     * 页码
     *
     * @return
     */
    int getPageNum();
    /**
     * 每页大小
     *
     * @return
     */
    int getPageSize();
    /**
     * 是否需要分页
     *
     * @return
     */
    boolean count();
}
```
#### PageQuery：IPageQuery默认实现
```java
public class PageQuery implements IPageQuery {
    private int pageNum = 1;
    private int pageSize = 10;
    private boolean count = true;
    /**
     * 获取分页请求参数
     *
     * @param pageNum  页码
     * @param pageSize 每页大小
     * @param count    是否需要分页
     * @return
     */
    public static PageQuery of(int pageNum, int pageSize, boolean count) {
        return new PageQuery(pageNum, pageSize, count);
    }
}
```
#### IPageQuery这个接口如何使用呢？
咱们的Mapper接口中需要分页的方法，方法的参数中，有任意一个参数是 IPageQuery 类型，那么这个方便自动拥有了分页功能，这个是通过aop实现的，稍后会介绍这块aop的代码，比如下面这个方法，第一个参数是 IPageQuery 类型，那么这个方法就自动拥有了分页功能。
```java
@Select("select id,name from t_user_lesson025 order by id asc")
List<UserPO> selectPageNew(IPageQuery pageQuery);
```
#### 原理：通过AOP统一处理IPageQuery参数，进行分页
通过AOP统一处理IPageQuery参数，实现分页功能，如下我们搞了个环绕通知，会拦截Mapper中的所有方法，判断方法的参数是否有IPageQuery类型参数，如果有，则从 IPageQuery 中拿到分页的信息，然后调用 PageHelper.startPage 开启分页，方法执行完毕之后，然后调用 PageHelper.clearPage 清理分页。
```java
@Aspect
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class PageQueryAspect {
    /**
     * 拦截mapper中的素有方法
     *
     * @param pjp
     * @return
     * @throws Throwable
     */
    @Around("execution(* com.itsoku..*Mapper.*(..))")
    public Object around(ProceedingJoinPoint pjp) throws Throwable {
        boolean pageFlag = false;
        try {
            //遍历参数，参数中如果有 IPageQuery 类型的，则从 IPageQuery 取出分页信息，则使用 PageHelper 开启分页
            Object[] args = pjp.getArgs();
            for (Object arg : args) {
                if (arg instanceof IPageQuery) {
                    IPageQuery pageQuery = (IPageQuery) arg;
                    PageHelper.startPage(pageQuery.getPageNum(), pageQuery.getPageSize(), pageQuery.count());
                    pageFlag = true;
                    break;
                }
            }
            return pjp.proceed();
        } finally {
            if (pageFlag) {
                //清理分页信息
                PageHelper.clearPage();
            }
        }
    }
}
```
## 案例3：案例2拓展实战
分页查询用户信息，支持根据关键字模糊检索用户名。
```java
com.itsoku.lesson025.service.UserService#userPage
```
测试，检索用户名中包含路人的用户列表，浏览器中访问
```http
http://localhost:8080/user/userPage?pageNum=1&pageSize=10&keyword=路人
```
