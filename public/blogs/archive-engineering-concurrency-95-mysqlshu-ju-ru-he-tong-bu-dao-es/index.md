# 第95节 MySQL数据如何同步到ES？靠谱方案

# 1、背景
本文以博客系统为例，来介绍下，如何将mysql中的博客数据同步到ElasticSearch。
# 2、使用MQ实现
大概流程如下，主要有2个步骤。
![image-20240912170026783](/blogs/_archive-2024-assets/f3d6f22772545ec25eea.webp)
## step1：投递mq消息
博客发生增删改（insert、update、delete）操作的时候，投递一条MQ消息，消息体如下，只需要带上博客id就行了，这里不需要知道具体是什么类型的操作，具体原因，大家看了后面的消费逻辑就清楚了。
```json
{
	"articleId": "博客id"
}
```
> 最好采用事务消息，可以确保业务执行成功，消息一定投递成功，怎么投递事务消息？
>
> 可参考：[30.MQ专题：SpringBoot中，手把手教你实现事务消息.md](/blog/archive-engineering-concurrency-30-mqzhuan-ti-springbootzhong-shou-ba-shou-jiao-ni-shi-9994918)
## step2：消费消息，将博客数据写入ES
过程如下
```java
String articleId = 消息中获取博客id;
//为了避免并发问题，这里对同一条博客记录加分布式锁，确保同一个articleId，并发收到多个消息时，排队执行，这样可以确保同步到es的数据最终和mysql是一致的
distributeLock.lock("es:article:" + articleId);
try{
    // 从db中查询博客
    ArticlePO articlePo = select * from t_article where id = #{articleId};
    //从es中删除博客
    es.delete(articleId);
    //将博客写入es
    if(articlePo != null){
        es.insert(articlePo);
    }
}finally{
    //释放分布式锁
    distributeLock.unlock();
}
```
这里再给大家解释下，为什么要加分布式锁？
如果不加锁，用户短时间内，对同一个博客进行了2次修改
- 第1次将博客标题改成了：java
- 第2次将博客标题改成：java高并发
这2次修改会产生2条消息，2条消息按照下面逻辑消费，最终es的数据和db中数据不一致，db中是博客的标题是：java高并发，而es中是：java
| 时间点 | 消费者1                            | 消费者2                                  |
| ------ | ---------------------------------- | ---------------------------------------- |
| T1     | {"articleId":"1"}                  | {"articleId":"1"}                        |
| T2     | 从数据库读取博客内容，标题是：java | 从db中读取博客内容，标题是：java高并发   |
| T3     |                                    | 写入ES，此时es中博客的标题是：java高并发 |
| T4     | 写入ES，此时es中博客的标题是：java |                                          |
还有一点需要注意，如何确保消息一定消费成功呢？可以参考：[33.MQ专题：消息幂等消费 & 消费失败自动重试 通用方案](33.MQ专题：消息幂等消费 & 消费失败自动重试 通用方案)
