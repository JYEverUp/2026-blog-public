# 第81节 评论系统如何设计，一次性给你讲清楚

# 1、前言
评论功能，属于非常常见的功能。
本文从评论功能的需求出发，来看下评论表如何设计，以及通过此表，如何实现评论中各种功能。
非常硬核，大家慢慢看。
# 2、先来了解需求
假如我们开发了一个短视频的网站，用户可以对视频进行评论，要实现二级评论的功能。
先来看下什么是一级评论和二级评论。
## 2.1、一级评论
对视频直接发表的评论，属于一级评论，如下图，下面这2条记录都是一级评论，评论列表默认只显示一级评论，支持分页
![image-20240827133300955](/blogs/_archive-2024-assets/0e05c913c620a0fc28b7.webp)
## 2.2、二级评论
一级评论下面挂的所有的评论属于二级评论，如下图
- 包含了对一级评论的回复
- 以及对一级评论下面回复的回复
![image-20240827134402710](/blogs/_archive-2024-assets/b984ad7626f04cecae77.webp)
# 3、评论表设计(t_comment)
| 字段                | 描述                                                         |
| ------------------- | ------------------------------------------------------------ |
| comment_id          | 评论记录id，主键                                             |
| video_id            | 被评论的视频id                                               |
| user_id             | 评论者用户id                                                 |
| root_comment_id     | 根评论id，如果是一级评论，则为0，如果是二级评论，则为一级评论的id |
| reply_to_comment_id | 指向被回复的评论id，如果是一级评论，则为0                    |
| reply_to_user_id    | 指向被回复的用户id，如果是一级评论，则为null；这个属于冗余字段，便于查询 |
| content             | 评论的内容                                                   |
| create_time         | 评论时间                                                     |
| count               | 一级评论下二级评论数量，当前记录是一级评论时，此值才有意义，当前记录是二级评论，此值为0 |
```sql
drop table if exists t_comment;
CREATE TABLE t_comment (
	comment_id BIGINT NOT NULL PRIMARY KEY COMMENT '评论id，主键',
	video_id BIGINT NOT NULL COMMENT '被评论的视频id',
	user_id varchar(32) NOT NULL COMMENT '评论者用户id',
	root_comment_id BIGINT NOT NULL DEFAULT 0 COMMENT '根评论id，如果是一级评论，则为0，如果是二级评论，则为一级评论的id',
	reply_to_comment_id BIGINT NOT NULL DEFAULT 0 COMMENT '指向被回复的评论id，如果是一级评论，则为0',
	reply_to_user_id varchar(32) COMMENT '指向被回复的用户id，如果是一级评论，则为null；这个属于冗余字段，便于查询',
	content TEXT NOT NULL COMMENT '评论的内容',
	create_time datetime NOT NULL COMMENT '评论时间',
	count BIGINT NOT NULL DEFAULT 0 COMMENT '一级评论下二级评论数量，当前记录是一级评论时，此值才有意义，当前记录是二级评论，此值为0'
);
```
下面我们来看演示下，通过这个表如何实现评论的各种功能。
# 4、功能演示：通过此表实现各种功能
假如视频id是1
## 功能1：对视频发表一级评论
### 入参
- user_id：用户id
- video_id：视频id
- content：评论内容
### sql脚本
假如：user_id = 用户a, video_id = 1, content = 很好看啊
sql脚本如下：
```sql
insert t_comment 
		(comment_id, video_id, user_id, root_comment_id, reply_to_comment_id, reply_to_user_id, content, create_time, count)
values
		(1, 1, '用户a', 0, 0, null, '很好看啊', NOW(), 0);
```
### 评论表当前数据
```sql
select * from t_comment;
```
![image-20240827143320539](/blogs/_archive-2024-assets/ad4f35715d333b0ce5a5.png)
## 功能2：分页查询一级评论列表
### 入参
- video_id：视频id
- page：第几页，从1开始，1表示第1页
- page_size：每页大小，默认为10
### 查询sql
假如：video_id = 1, page = 1, page_size = 10
```sql
SELECT
	*
FROM
	t_comment
WHERE
	video_id = 1
AND root_comment_id = 0
ORDER BY
	create_time DESC
LIMIT 0, 10
```
> 关键点：
>
> - root_comment_id = 0，表示查询的是一级评论
### 添加索引优化性能
目前表中没有添加索引，所以上面这个sql查询比较慢，我们可以添加一个组合索引，3个字段：(video_id, root_comment_id, create_time)
这样上面这个查询条件中的2个字段可以用到这个索引，且排序条件也可以用到这个索引进行排序，效率高
创建索引脚本如下
```sql
create index idx_video_id on t_comment (video_id, root_comment_id, create_time);
```
## 功能3：对一级评论进行回复
用户b需要对用户a下面这条1级评论进行回复，回复内容：剧情很精彩啊
![image-20240827143320539](/blogs/_archive-2024-assets/ad4f35715d333b0ce5a5.png)
sql脚本如下
```sql
-- 对一级评论进行回复
insert t_comment 
		(comment_id, video_id, user_id, root_comment_id, reply_to_comment_id, reply_to_user_id, content, create_time, count)
values
		(2, 1, '用户b', 1, 1, '用户a', '剧情很精彩啊', NOW(), 0);
-- 更新一级评论中二级评论的数量，count+1
update t_comment set count = count + 1 where comment_id = 1;
```
查看下评论表当前数据：`select * from t_comment;`
![image-20240827143358967](/blogs/_archive-2024-assets/52df52e6170d1d87f45d.png)
## 功能4：对二级评论进行回复
用户c，对刚才上面用户b发表的二级评论（comment_id=2）进行回复，回复内容：确实，演员的演技也都在线
sql脚本如下
```sql
-- 对二级评论进行回复
insert t_comment 
		(comment_id, video_id, user_id, root_comment_id, reply_to_comment_id, reply_to_user_id, content, create_time, count)
values
		(3, 1, '用户c', 1, 2, '用户b', '确实，演员的演技也都在线', NOW(), 0);
-- 更新一级评论中二级评论的数量，count+1
update t_comment set count = count + 1 where comment_id = 1;
```
查看下评论表当前数据：`select * from t_comment;`
![image-20240827143809891](/blogs/_archive-2024-assets/ffcb189a8b15b82af79c.webp)
## 功能5：分页查询二级评论列表
### 查询条件
- video_id：视频id
- root_comment_id：一级评论id
- page：当前页码，从1开始，1表示第1页
- page_size：每页大小，默认为10
### 查询sql
假如：video_id = 1, root_comment_id = 1,  page = 1,  page_size = 10
查询sql如下
```sql
SELECT
	*
FROM
	t_comment
WHERE
	video_id = 1
AND root_comment_id = 1
ORDER BY
	create_time DESC
LIMIT 0, 10
```
> 由于，评论表中有个组合索引：(video_id, root_comment_id, create_time)，所以这个查询会命中这个索引，会很快。
查询结果
![image-20240827144505400](/blogs/_archive-2024-assets/c3ed04bca8c5cadba7b9.png)
## 功能6：发表评论的接口
不管是发表一级评论，还是对一级评论进行回复，还是对二级评论进行回复，还是对回复进行回复，可以共用一个接口。
下面看下这个接口如何设计，伪代码如下
```java
/**
 * 发表评论或对评论进行回复
 * @param user_id 评论者id
 * @param content 评论内容
 * @param video_id 视频id
 * @param reply_to_comment_id 被回复的评论id，如果发表一级评论，则此参数为null，如果是二级评论，则此参数为被回复的评论id
 */
@Transactional(rollbackFor = Exception.class)
public void addComment(String user_id, String content,Long video_id, Long reply_to_comment_id){
    //1、评论id（可以通过分布式id生成工具生成);
    Long comment_id = 评论id;
    //2、若 reply_to_comment_id 为空，表示发表的是一级评论
    if(reply_to_comment_id==null){
        //2.1、插入评论
        insert t_comment
	        (comment_id, video_id, user_id, root_comment_id, reply_to_comment_id, reply_to_user_id, content, create_time, count)
        values
        	(#{comment_id}, #{video_id}, #{user_id}, 0, 0, null, #{content}, NOW(), 0);
    }else{
        //3、reply_to_comment_id 不为空，表示是对评论进行回复
        //3.1、根据 reply_to_comment_id 获取被回复的评论记录
        Comment comment = select * from t_comment where comment_id = #{reply_to_comment_id};
        //3.2、获取一级评论id
        Long root_comment_id = comment.root_comment_id;
        // 被回复的用户id
        String reply_to_user_id = comment.user_id;
        //3.3、插入评论
        insert t_comment
        	(comment_id, video_id, user_id, root_comment_id, reply_to_comment_id, reply_to_user_id, content, create_time, count)
        values
            (#{comment_id}, #{video_id}, #{user_id}, #{root_comment_id}, #{reply_to_comment_id}, #{reply_to_user_id}, #{content}, NOW(), 0);
        //3.4、更新一级评论的count = count + 1
        update t_comment set count = count + 1 where comment_id = #{root_comment_id};
    }
}
```
## 功能7：根据评论id，删除评论
```sql
delete from t_comment where comment_id = #{评论id}
```
这个sql根据主键删除记录，很快。
## 功能8：用户查询自己的评论列表
评论者可能需要查看自己的评论列表，可以通过下面这个sql实现
```sql
select * from t_comment where user_id = #{用户id} order by create_time desc
```
可以添加一个组合索引：(user_id, create_time)，来提升这个sql的查询性能。
```sql
create index idx_user_id on t_comment (user_id, create_time);
```
# 5、拓展：数据量大了怎么办？
## 5.1、导致查询缓慢
当评论表中的数据量太大，会导致下面2个查询比较慢
1. 用户查询某个视频下面的评论列表，主要检索条件：视频id
2. 用户查询自己发表的评论列表，主要检索条件：用户id
## 5.2、如何解决？分表
具体怎么分表呢？评论数据可以保存2份，2份采用不同的分表键，来解决上面2中查询慢的场景
1. 根据视频id进行分表，表名以t_comment_video开头，比如创建128张表，这个可以解决根据视频id查询评论列表缓慢的问题
2. 根据用户id进行分表，表名以t_comment_user开头，比如创建128张表，这个可以解决用户查询自己发表的评论列表慢的问题
## 5.3、分表后如何写入数据
此时发表评论会向2个表中写入数据：t_comment_video、t_comment_user
有2种方式
1. 方式1：同时写入2张表
2. 方式2：异步的方式，先写t_comment_video，然后通过mq异步写到t_comment_user表，更新或删除也是一样的，先操作t_comment_video，然后通过mq，同步到t_comment_user表；这种方式性能可能更高一些，复杂性上升了
# 
