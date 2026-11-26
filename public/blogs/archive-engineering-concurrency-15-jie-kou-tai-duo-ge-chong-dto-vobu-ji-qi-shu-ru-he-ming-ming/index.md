#  解决DTO、VO泛滥，命名困难的问题
## 痛点
有些项目接口很多，而接口入参一般我们使用XxxDTO这种类型参数，返回值通常使用XxxVO这种类型，很多开发按照自己项目搞事情，时间久了，导致系统中充斥着大量的dto、vo命名的类，各种命名千奇百怪。
问题来了，然后我们再添加新的接口的时候，入参和返回值不知道如何命名了，大家有没有这种经历？
## 如何解决？
当我们遇到问题的时候，别人肯定也会遇到这种问题。
那我们就去看高手遇到这种问题的时候，是如何解决的？
elasticsearch，这个框架框架大家应该比较熟悉吧，非常出名的一个搜索引擎解决方案，他通过restfull接口对外提供搜索服务。
我们来看一下他在SpringBoot中的源码，需要在SpringBoot中引入下面配置，然后可看到的他的源码。
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-elasticsearch</artifactId>
</dependency>
```
看下面这个类，这个就是elasticsearch为springboot端提供的一个用于调用elasticsearch服务端接口的工具类
```java
co.elastic.clients.elasticsearch.ElasticsearchClient
```
下面是一些方法的定义，大家先看下
```java
IndexResponse index(IndexRequest request)
ReindexResponse reindex(ReindexRequest request)
DeleteResponse delete(DeleteRequest request)
DeleteByQueryResponse deleteByQuery(DeleteByQueryRequest request)
DeleteScriptResponse deleteScript(DeleteScriptRequest request) 
```
不知道大家有没有发现规律，可能有些朋友已经看出来了，上面方法的特点
- 入参的类型是：方法名称+Request
- 返回值的类型是：方法名称+Response
大家觉得这种怎么样？本人觉得这种方式挺好的，最少解决了我们命名的痛点
## 案例
再来给大家看一下我写的接口的命名，和上面es的也类似，大家也可以看下。![image-20240410131448057](/blogs/_archive-2024-assets/1656f55e5800e2d181f0.webp)
## 大家有什么更好的方法呢？
这个问题本身缺少规范导致的问题，如果规范中能够指引大家很容易的解决这个问题，那就没有这个痛点了。
大家在项目中有没有碰到这个问题呢？你们是如何解决的？可以留言一起交流
