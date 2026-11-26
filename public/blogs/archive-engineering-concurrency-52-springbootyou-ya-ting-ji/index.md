#  SpringBoot 优雅停机
# 1、SpringBoot优雅停机是什么意思？
Spring优雅停机，通俗点说就是如何优雅的停止SpringBoot应用，
优雅停机，应满足下面3点：
1. SpringBoot应用不再接收新的请求
2. SpringBoot应用将已经进来的请求处理完成
3. 然后关闭SpringBoot应用
> 注意：这里说的停机，并不是停止我们的机器，而是停止我们的SpringBoot应用。
# 2、什么是立即停机？
直接把springboot应用强制关掉，比如linux中的：`kill -9 进程id`，这个命令就会触发强制关闭进程，相当于突然断电一样。
这种可能导致严重的问题
1. 用户体验差，用户请求还在处理中，springboot突然下线，会导致用户收到错误响应
2. 可能会引起系统中数据不一致
# 3、举例：餐馆营业
假如咱们开了一个餐馆，现在不想营业了，有2种方案
## 方案1：优雅关门
1. 门口挂个牌：已打样，这样顾客看到后，就不会进来了
2. 将店内已经在就餐的顾客服务完毕
3. 关门
## 方案2：暴力关门
1. 将餐馆内还在就餐的顾客直接轰出去
2. 关门
大家，感觉那种方案好？
# 4、SpringBoot优雅停机步骤
SpringBoot中已内置了优雅停机的方案，只需做一些简单的配置就可以了，具体步骤如下。
## 1）applicaiton.yml中添加配置
```yaml
server:
  # 停机方式，immediate：立即停机，默认值；graceful：优雅停机
  shutdown: graceful
```
## 2）触发停机常见的方式
### linux中：kill 进程pid
先通过jps命令找到进程id
```shell
jps
```
kill 进程id，触发优雅停机
```shell
kill 进程id
```
> 注意，`kill -9 进程id`是强制结束进程，不会触发优雅停机，相当于直接断电一样。
### 命令窗口中：ctrl+c
![image-20240627144355366](/blogs/_archive-2024-assets/9ae2b2916a8e99588e07.webp)
## idea中
![image-20240627144154406](/blogs/_archive-2024-assets/8e0f7d7c653c55162e47.webp)
# 5、效果演示：立即停机
# 6、效果演示：优雅停机
# 7、原理：JVM退出钩子
JVM退出钩子是指在JVM关闭时会被调用的回调方法。
在JVM关闭时，会执行所有的`shutdown hooks`。
可以使用`Runtime.getRuntime().addShutdownHook()`方法来注册一个退出钩子。
以下是一个简单的Java示例，演示了如何注册和使用JVM退出钩子：
```java
public class ShutdownHookDemo {
    public static void main(String[] args) {
        Runtime.getRuntime().addShutdownHook(new Thread() {
            @Override
            public void run() {
                System.out.println("优雅停机测试1....");
            }
        });
        Runtime.getRuntime().addShutdownHook(new Thread() {
            @Override
            public void run() {
                System.out.println("优雅停机测试2....");
            }
        });
    }
}
```
执行输出：
```java
优雅停机测试2....
优雅停机测试1....
```
# 8、SpringBoot优雅退出原理：通过jvm钩子实现的
源码位置：
```java
org.springframework.boot.SpringApplicationShutdownHook#addRuntimeShutdownHook
```
在jvm退出的时候会干一些事情，主要的事情：
1. 让web服务器（如Tomcat、Undertow、Jetty）不在接收新的请求
2. 将已经进来的请求处理完成
3. 销毁spring容器中的bean
4. 退出jvm
# 9、拓展：SpringCloud优雅停机步骤
## 1）将服务从服务注册中心下线
SpringCloud 涉及到服务注册中心，若服务下线前，没有提前告诉注册中心，而直接把服务下线了，而注册中心、以及其他服务消费者以为这个服务还活着，则还会有请求过来，会导致请求报错。
所以下线前需要先从注册中心中将服务摘除，然后需要等到注册中心最新的数据同步到其他服务消费者后，才可以将服务优雅停机。
常用的注册中心有eureka，nacos，他们都有服务下线的相关api，可以先调用这些api让服务从注册中心下线
> 具体的api，大家可以查询相关文档，或者咨询AI
## 2）休眠一段时间：等待注册中心数据同步给其他服务消费者
当我们的服务从注册中心摘除后，其他服务可能并不知道
而其他服务会定期从注册中心中拉取数据，所以需要等待一段时间，等到其他服务从注册中心获取到最新的服务列表后，才能对要停机的服务执行优雅停机。
比如微服务从服务注册中心同步的频率是 5 秒
则建议在这个步骤中，休眠 10 秒以确保所有服务都拉取了注册中心最新的数据。
## 3）对需要下线的服务执行优雅停机
```java
1、通过ps命令查询到进程id
2、执行：kill 进程id，触发优雅停机
```
## 4）轮询进程状态 + 超时强制结束
有些情况，执行了`kill 进程id`进程是无法正常结束的，可以通过linux命令去轮询，看下刚才kill的进程是否已结束。
可以设置一个超时时间，比如轮询60秒之后，进程还是会无法结束，那么可以执行`kill -9 进程id`强制结束进程
这样，SpringCloud中的服务就可以优雅下线了。
