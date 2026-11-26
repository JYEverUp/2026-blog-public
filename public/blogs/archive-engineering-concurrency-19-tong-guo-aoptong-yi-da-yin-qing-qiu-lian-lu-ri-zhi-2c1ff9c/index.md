# 通过AOP统一打印请求链路日志，排错效率飞升
看过本文并实施之后，解决问题的效率将大幅提升。
## 思考一个问题：当一个接口报错的时候，如何能够快速定位问题？
如果能够满足下面这些条件，咱们就可以快速定位错误
1. 能够快速找到接口的详细调用日志
2. 日志中最好知道出错的是哪个接口的哪个方法，即哪个controller的哪个方法
3. 日志中最好有接口的入参、返参
4. 日志中含有异常的详细堆栈信息（即：哪行代码报的错）
有了这些信息之后，解决问题的效率将大幅提升。
本文就是帮你解决这些问题。
## 下面，先带大家看效果，再看代码如何实现
### 启动案例
```java
com.itsoku.lesson019.Lesson019Application
```
### 访问一个正常的接口
```http
http://localhost:8080/userAdd?userName=路人&age=35&password=123456
```
### 先看下接口的返回值，里面有个traceId
```json
{
  "success": true,
  "data": true,
  "msg": null,
  "code": null,
  "traceId": "b910649f02514cae8b015a862c7f6dca"
}
```
### 拿着这个traceId的值，可以找到这个请求完整的日志
看后端控制台，通过traceId的值去检索，如下，可以看到接口的详细执行日志，包含（接口url、开始时间、结束时间、及处理这个请求的controller和方法、还有方法的入参、返回值，都输出了），前端给我们这个traceId，我们便可以快速定位到这个请求的完整调用日志。
![image-20240414160934535](/blogs/_archive-2024-assets/e04992c67364593057ea.webp)
### 再来看请求一个异常的接口，浏览器中打开下面地址
```http
http://localhost:8080/login?name=张三
```
### 浏览器中显示如下，可以看出接口报错了
```json
{
  "success": false,
  "data": null,
  "msg": "用户名无效",
  "code": null,
  "traceId": "a3b2d88c85134e5dad4d3d7ccd8cd892"
}
```
### 我们可以拿着上面的traceId的值，去后端控制台找对应的日志，看到的结果如下
![image-20240414161520911](/blogs/_archive-2024-assets/a9cae2aa6ffb2ac6bd6a.webp)
## 源码解析
### ControllerLogAspect：打印接口的详细日志
### TraceFilter：生成唯一的traceId，日志中会输出这个tracId
### ResultTraceIdAspect：将traceId统一丢到响应结果Result类的traceId字段中
