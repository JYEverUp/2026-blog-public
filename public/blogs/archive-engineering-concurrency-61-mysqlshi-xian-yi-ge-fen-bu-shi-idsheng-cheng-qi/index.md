# 使用MySQL，实现一个高性能，分布式id生成器

# 1、效果演示
```java
com.itsoku.lesson061.Lesson061ApplicationTest
```
# 2、原理
基于数据库号段模式，可以理解为从数据库批量的获取自增id，每次从数据库取出一个号段范围，例如 [1,100] 代表100个Id，然后将这100个id加载到内存，以供调用方慢慢使用，等这批id用完之后，再次向数据库申请100个。
需要用到一张表
```sql
CREATE TABLE if not exists `t_id_generator_lesson061`
(
    `code`      varchar(128) not null primary key COMMENT '业务编码（唯一）',
    `max_id` bigint       not null default 1 comment '当前最大id'
) COMMENT ='id生成器';
```
比如code是ORDER_ID，每次申请100个
那么首次申请的时候，会向此表插入一条记录
```sql
insert t_id_generator_lesson061 values ('ORDER_ID',100);
```
再次申请的时候，会执行下面sql进行更新，为了防止并发，条件中带上了`max_id`旧值，采用乐观锁更新，直到更新成功 
```sql
while(true){
	int updateCount = update t_id_generator_lesson061 set max_id = max_id + 100 where code = 'ORDER_ID' and max_id = #{旧值};
	if(updateCount==1){
		break;
	}
}
```
# 3、源码解析
```java
com.itsoku.lesson061.service.impl.IdGeneratorServiceImpl#getId
```
# 4、如何使用
## 参考测试用例
```java
com.itsoku.lesson061.Lesson061ApplicationTest
```
## 获取一个id
```
com.itsoku.lesson061.service.IdGeneratorService#getId
```
## 批量获取id
```java
com.itsoku.lesson061.service.IdGeneratorService#getIdList
``` 
