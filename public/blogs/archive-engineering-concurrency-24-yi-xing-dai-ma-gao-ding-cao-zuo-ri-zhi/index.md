# 一行代码搞定系统操作日志
## 本文内容
通过aop统一记录系统操作日志，只需在接口方法上加个自定义的注解，不论接口成功还是失败，都可自动记录操作日志到db中。
操作日志包含的信息有
- 日志描述
- 状态，0：异常，1：正常
- 请求参数json格式
- 响应结果json格式
- 错误信息(状态=0时，记录异常堆栈信息)
- 接口耗时（毫秒）
- 操作ip地址
- 操作ip地址归属地
- 操作人用户名
- 操作时间
## 涉及到的技术
- SpringBoot 2.7.13
- MyBatis Plus
- MySQL
- ip2region：准确率99.9%的离线IP地址定位库，用于获取ip归属地
## 先带大家看下效果
- 测试用例代码：UserController.http
## 源码解析
### 操作日志表
```sql
create table if not exists t_oper_log_lesson024
(
    id              varchar(50) primary key comment 'id，主键',
    log             varchar(500) not null comment '操作日志',
    status          smallint     not null default 1 comment '状态，0：异常，1：正常',
    param_json      text comment '请求参数json',
    result_json     text comment '响应结果json',
    error_msg       text comment '错误信息(status=0时，记录错误信息)',
    cost_time       long comment '耗时（毫秒）',
    oper_ip         varchar(50) comment '操作ip地址',
    oper_ip_address varchar(50) comment '操作ip地址归属地',
    oper_user_name  varchar(50) comment '操作人用户名',
    oper_time       datetime comment '操作时间'
) comment '操作日志表';
```
### 自定义注解
用于标注在Controller中需要记录操作日志的方法上。
```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface OperLog {
    //日志内容
    String log();
}
```
### 记录日志切面类
> 使用环绕通知，会拦截所有controller中标注有@OperLog注解的方法，会对这些方法记录日志，不管方法是成功还是失败都会记录
```java
com.itsoku.lesson024.log.OperLogAspect
```
### 如何使用？
接口上标注@OprLog就可以了
```java
@PostMapping("/add")
@OperLog(log = "用户管理-新增用户")
public Result<String> add(@Validated @RequestBody UserAddRequest req) {
    return ResultUtils.success(this.userService.add(req));
}
```
## 其他一些技术点
### 操作日志中如何获取到操作人用户名的？
如下，咱们定义了一个接口，接口中有2个方法，一个用户设置用户名，一个用于获取用户名
```java
public interface IUserNameProvider {
    /**
     * 获取用户名
     *
     * @return
     */
    String getUserName();
    /**
     * 设置用户名
     *
     * @param userName
     */
    void setUserName(String userName);
}
```
这个接口有个默认实现，是将用户名放在ThreadLocal中，大家可以根据自己的项目情况，去自己实现一个IUserNameProvider
```java
@Component
public class ThreadLocalUserNameProvider implements IUserNameProvider {
    private ThreadLocal<String> userNameTl = new ThreadLocal<>();
    @Override
    public String getUserName() {
        return this.userNameTl.get();
    }
    @Override
    public void setUserName(String userName) {
        this.userNameTl.set(userName);
    }
}
```
那么这个用户名什么时候放进去的呢？代码如下，咱们搞了个拦截器，拦截请求，从请求中我们可以想办法拿到用户名，然后将其塞到IUserNameProvider中，这样记录操作日志的aop中，就可以通过IUserNameProvider获取到了。
```java
@Component
public class UserNameInterceptor implements HandlerInterceptor {
    @Autowired
    private IUserNameProvider userNameProvider;
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        //这里从请求中得到用户名，然后塞到userNameProvider中
        String userName = "路人";
        this.userNameProvider.setUserName(userName);
        return HandlerInterceptor.super.preHandle(request, response, handler);
    }
}
```
### ip地址如何获取的？
这里我们提供了一个工具类，可以通过请求拿到ip，具体代码在下面这个位置
```java
com.itsoku.lesson024.ip.IpUtils#getIpAddr()
```
### ip归属地如何获取的？
对应的方法在下面这个位置，传入ip，可以获取到ip对应的归属地。
```java
com.itsoku.lesson024.ip.IpAddressUtils#getRegion
```
这里使用了开源的一个工具：ip2region，准确率99.9%的离线IP地址定位库
项目地址：https://gitee.com/lionsoul/ip2region
![image-20240422160444704](/blogs/_archive-2024-assets/81099a540786bb9da2a8.webp)
## 案例源码
