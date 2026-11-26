# 接口通用返回值设计与实现
## 前言
目前大部分系统都是前后端分离，后端提供接口，返回json数据，前端拿到数据进行处理。
后端接口返回值，可以采用固定的格式，这样前后端配合起来会更顺畅一些，也会节约很多时间。
这节课代码在 lesson013 模块中。
## 后端接口返回值通用格式
代码如下，通常会有4个字段
```java
public class Result<T> {
    /**
     * 请求是否处理成功？
     */
    private boolean success;
    /**
     * 数据，泛型类型，后端需要返回给前端的业务数据可以放到这个里面
     */
    public T data;
    /**
     * 提示消息，如success为false的时给用户的提示信息
     */
    private String msg;
    /**
     * 错误编码，某些情况下，后端可以给前端提供详细的错误编码，前端可以根据不同的编码做一些不同的操作
     */
    private String code;
}
```
对应的接口示例代码如下，返回值为Result类型
```java
@RestController
public class TestController {
    @GetMapping("/hello")
    public Result<String> hello() {
        return ResultUtils.success("欢迎大家学习《高并发 & 微服务 & 性能调优实战案例 100 讲》");
    }
}
```
前端调用此接口，看到的结果如下
```java
{
  "success": true,
  "data": "欢迎大家学习《高并发 & 微服务 & 性能调优实战案例 100 讲》",
  "msg": null,
  "code": null
}
```
## 异常情况处理
后端的接口中，通常，都是有一些校验功能的，比如登录接口中，需要验证用户名或密码是否正确，如果不正确需要提示前端：用户名或密码不正确，给前端返回下面的数据
```json
{
  "success": false,
  "data": null,
  "msg": "1001",
  "code": "用户名或密码错误"
}
```
代码中我们可以怎么写呢？后端校验不通过的时候，可以抛出一个业务异常，然后在全局异常处理中去处理这个异常，返回通用格式的结果。
## 具体怎么做呢？
### 自定义一个业务异常类
```java
public class BusinessException extends RuntimeException {
    private String code;
    /**
     * @param code    错误编码
     * @param message 错误提示
     */
    public BusinessException(String code, String message) {
        super(message);
        this.code = code;
    }
    public BusinessException(String code, String message, Throwable cause) {
        super(message, cause);
        this.code = code;
    }
    public String getCode() {
        return code;
    }
    public void setCode(String code) {
        this.code = code;
    }
}
```
### 接口中抛出业务异常
登录接口可以用下面这种写法了，用户名不对的时候，抛出一个业务异常BusinessException
```java
@GetMapping("/login")
public Result<String> login(String name) {
    if (!"路人".equals(name)) {
        throw new BusinessException("1001", "用户名错误");
    } else {
        return ResultUtils.success("登录成功");
    }
}
```
## 全局异常中对BusinessException异常进行统一处理
BusinessException这个异常可以使用springboot中的全局异常处理器去处理。
我们需要定义一个全局异常处理器，代码如下
- 类上使用 @RestControllerAdvice 注解标注
- 注意看handleBusinessException方法，这个方法上有个 @ExceptionHandler(BusinessException.class) 注解，这个注解的值是 BusinessException，表示接口中抛出这个异常的时候，会进入到 handleBusinessException 方法中去处理，这个方法最后返回的也是通用的结果Result类型
```java
@RestControllerAdvice
public class GlobalExceptionHandler {
    private Logger logger = LoggerFactory.getLogger(GlobalExceptionHandler.class);
    /**
     * 处理业务异常
     *
     * @param e
     * @param request
     * @return
     */
    @ExceptionHandler(BusinessException.class)
    public Result handleBusinessException(BusinessException e, HttpServletRequest request) {
        logger.info("请求：{}，发生异常：{}", request.getRequestURL(), e.getMessage(), e);
        return ResultUtils.error(e.getCode(), e.getMessage());
    }
}
```
> SpringBoot全局异常处理，如果有不理解的，可以去看看我的这篇文章：http://itsoku.com/course/6/224
此时我们验证下上面这个登录接口
访问：http://localhost:8080/login?name=路人，用户名正确，返回结果如下
```json
{
  "success": true,
  "data": "登录成功",
  "msg": null,
  "code": null
}
```
再来看用户名错误的情况
访问：http://localhost:8080/login?name=张三，用户名不匹配，此时登录接口会抛出BusinessException异常，然后被全局异常中的`GlobalExceptionHandler#handleBusinessException`方法处理，前端看到的返回结果如下：
```json
{
  "success": false,
  "data": null,
  "msg": "用户名或密码错误",
  "code": "1001"
}
```
## 案例：SpringBoot自带的参数校验功能异常处理
SpringBoot为我们提供了参数自动校验功能，很好用，看下面案例。
用户注册接口
```java
com.itsoku.lesson013.controller.TestController#register
@PostMapping("/userRegister")
public Result<Void> userRegister(@Validated @RequestBody UserRegisterRequest req) {
    return ResultUtils.success();
}
```
当参数校验不通过的时候，会自动抛出一个org.springframework.validation.BindException异常
对应的全局异常处理方法
```java
@ExceptionHandler(BindException.class)
public Result handleBindException(BindException e, HttpServletRequest request) {
    logger.info("请求：{}，发生异常：{}", request.getRequestURL(), e.getMessage(), e);
    String message = e.getAllErrors().get(0).getDefaultMessage();
    return ResultUtils.error(message);
}
```
## 全局其他异常处理
当上面的异常处理方法都无法匹配接口中的异常的时候，将走下面这个方法去处理异常，这个是用来对异常处理进行兜底的。
```java
/**
 * 处理其他异常
 *
 * @param e
 * @param request
 * @return
 */
@ExceptionHandler(Exception.class)
public Result handleException(Exception e, HttpServletRequest request) {
    logger.info("请求：{}，发生异常：{}", request.getRequestURL(), e.getMessage(), e);
    //会返回code为500的一个异常
    return ResultUtils.error(ErrorCode.SERVER_ERROR,"系统异常，请稍后重试");
}
```
## 提供的几个工具类
- com.itsoku.lesson013.common.ResultUtils：提供了创建Result对象的一些静态方法
- com.itsoku.lesson013.common.BusinessExceptionUtils：提供了创建BusinessException的一些静态方法
- com.itsoku.lesson013.common.ErrorCode：将系统中所有的错误编码可以放到这个类中集中化管理
