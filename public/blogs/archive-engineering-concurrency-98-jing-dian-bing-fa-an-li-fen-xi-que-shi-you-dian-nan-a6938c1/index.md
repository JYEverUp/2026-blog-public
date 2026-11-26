#  经典并发案例分析，确实有点难，一起来挑战下
本文如果你能看懂，说明你解决并发问题的能力已经相当高了，先收藏点赞，慢慢看。
# 1、先来了解下业务
如下图，我们有个视频网站，视频下方允许用户发表评论，用户还可以对别人的评论进行回复。
![image-20240914200710601](/blogs/_archive-2024-assets/69a9a532fde616bf0ff2.webp)
评论表如下(t_comment)，比较简单
| 字段                | 描述               |
| ------------------- | ------------------ |
| comment_id          | 评论记录id，主键   |
| video_id            | 被评论的视频id     |
| user_id             | 评论者用户id       |
| reply_to_comment_id | 指向被回复的评论id |
| content             | 评论的内容         |
| create_time         | 评论时间           |
# 2、产品提了2个需求，看下怎么实现？
1. 用户删除评论的时候，需要删掉其所有子评论（也就是其下的回复）
2. 用户对某个评论回复的时候，需要校验被回复的评论必须存在，不存在，则给个错误提示
# 3、方案1：第1个版本代码
## 删除评论的代码
```java
/**
 * 删除评论，顺便会删除所有的子评论
 * @param commentId 评论id
 */
@Transactional
public void deleteComment(String commentId){
	//删除主评论
	delete from t_comment where id = #{commentId};
	//删除子评论列表
	delete from t_comment where repay_to_comment_id = #{commentId};
}
```
## 评论回复的代码
```java
/**
 * 对评论进行回复
 * @param videoId 视频id
 * @param userId 用户id
 * @param content 评论内容
 * @param repayToCommentId 被回复的评论id
 */
@Transactional
public void repay(String videoId, String userId, String content, String repayToCommentId){
    //查看主评论是否存在
    CommentPO repayToCommentPO = select * from t_comment where commentId = #{reapyToCommentId};
    //主评论不存在
    if(repayToCommentPO == null){
        throw new RuntimeException("评论不存在");
    }
    //插入评论
    insert t_comment (video_id, user_id, content, repay_to_comment_id)
    values (#{videoId}, #{userId}, #{content}, #{repayToCommentId});
}
```
## 使用并发对代码进行验证
| 时间点 | 请求1：对评论1进行回复 | 请求2：删除评论1                    |
| ------ | ---------------------- | ----------------------------------- |
| T1     | 开启事务               | 开启事务                            |
| T2     | 查询主评论1，存在      |                                     |
| T3     |                        | 调用删除评论的方法，主评论1会被删掉 |
| T4     |                        | 删除评论1下面的所有子评论           |
| T5     |                        | 提交事务                            |
| T6     | 插入子评论，插入成功   |                                     |
| T7     | 提交事务               |                                     |
按照上面这个并发过程，最终的结果就是，评论1被删掉了，但是子评论却插入成功了。
产品要求，主评论删除的时候，所有的子评论都需要删掉，上面这种方案并没有满足产品需求。
怎么解决？见方案2
# 4、方案2：加互斥锁，让2个操作排队执行
## 方法如下
- 删除评论和对评论进行回复的这两个方法，都会用到主评论id，可以对主评论记录加互斥锁，从而保证2个方法在并发情况下，操作同一个主评论的时候排队执行，便可以解决上面的问题
- 目前删除评论的时候，主评论已经加锁了（`delete from t_comment where comment_id = #{commentId}`，数据库中对某一条记录执行delete、update、for update的时候会加互斥锁）
- 调整下评论回复的代码，查询主评论是否存在的时候，采用`for update`的方式对主评论加互斥锁：`select * from t_comment where commentId = #{reapyToCommentId} for update`
评论回复的代码，调整后如下，这样，在同一条主评论上面加了互斥锁，确保2个方法排队执行，就解决了上面的问题。
```java
/**
 * 对评论进行回复
 * @param videoId 视频id
 * @param userId 用户id
 * @param content 评论内容
 * @param repayToCommentId 被回复的评论id
 */
@Transactional
public void repay(String videoId, String userId, String content, String repayToCommentId){
    //查看主评论是否存在，通过for update 对主评论加互斥锁，加互斥锁之后，这条记录执行修改、删除、
    CommentPO repayToCommentPO = select * from t_comment where commentId = #{reapyToCommentId} for update;
    // 剩下的代码。。。和方案1中是一样的
}
```
## 使用并发对代码进行验证
| 时间点 | 请求1：对评论1进行回复                                       | 请求2：删除评论1                                             |
| ------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| T1     | 开启事务                                                     |                                                              |
| T2     | 查询主评论1：select * from t_comment where commentId = 1 for update，会对这条评论加互斥锁 | 开启事务                                                     |
| T3     |                                                              | 删除评论1：delete from t_comment where comment_id = 1；<br />由于请求1中对这条记录添加了互斥锁，这里会被阻塞，直到请求1事务结束 |
| T4     | 插入评论，评论插入成功                                       | 阻塞中                                                       |
| T5     | 提交事务                                                     | 阻塞中                                                       |
| T6     |                                                              | 恢复了，删除子评论，此时请求1刚才发表的评论也会被删掉        |
| T7     |                                                              | 提交事务                                                     |
大家好好看看这个过程，此时问题解决了。
## 又带来了新的问题，来看下
![image-20240914205448529](/blogs/_archive-2024-assets/66c977f16cf3520e2759.webp)
对同一条评论进行回复，变成串行了，有点追求的我们，肯定是无法接受的。
我们期望，对于同一条评论记录，上面2个方法并发的时候排队执行，但是如果当前只有repay方法发生并发，要支持并行执行，不要排队。
如何解决？见方案3
# 5、方案3：将repay方法中的互斥锁改成共享锁
## MySQL互斥锁和共享锁
这里给大家普及一个知识点，mysql中有2种很重要的锁：互斥锁和共享锁。
- 互斥锁：对记录执行update、delete、或者执行select ... for update的时候，会加互斥锁
- 共享锁：加锁语法：`select * from 表名 where 查询条件 lock in share mode;` 
看下下面这个表格，互斥锁和互斥锁不能共存，互斥锁和共享锁不能共存，共享锁和共享锁可以共存
|        | 互斥锁   | 共享锁   |
| ------ | -------- | -------- |
| 互斥锁 | 不能共存 | 不能共存 |
| 共享锁 | 不能共存 | 可共存   |
大家可以理解是什么意思么？给大家举个例子吧
- 请求1对记录1添加了互斥锁，请求2此时如果想对记录1添加互斥锁、或者共享锁，就需要等待，直到请求1释放锁
- 请求1对记录1添加了共享锁，请求2此时也可以对请求1添加共享锁；但是请求2此时如果想对记录1添加互斥锁，就需要等待，直到请求1释放锁
可能大家还是无法理解，带大家看下效果
## 效果1：验证互斥锁和互斥锁不能共存
准备数据
```sql
drop table if exists t_user;
create table t_user (id int primary key, name varchar(20));
insert into t_user values (1,'路人');
```
| 窗口1                                                        | 窗口2                                                        |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| start transaction;                                           |                                                              |
| delete from t_user where id = 1; -- 对id=1这条记录添加互斥锁 |                                                              |
|                                                              | start transaction;                                           |
|                                                              | delete from t_user where id = 1; --这里会被阻塞（原因：窗口1中对id=1这条记录添加了互斥锁） |
|                                                              | 阻塞中                                                       |
| rollback; -- 结束事务(commit或者rollback)                    | 唤醒了（原因：窗口1事务结束了，释放了互斥锁）                |
|                                                              | rollback; -- 结束事务(commit或者rollback)                    |
## 效果2：验证互斥锁和共享锁不能共存
| 窗口1                                                        | 窗口2                                                        |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| start transaction;                                           |                                                              |
| delete from t_user where id = 1; -- 对id=1这条记录添加互斥锁 |                                                              |
|                                                              | start transaction;                                           |
|                                                              | select * from t_user where id = 1 lock in share mode;  --这里会被阻塞（原因：窗口1中对id=1这条记录添加了互斥锁） |
|                                                              | 阻塞中                                                       |
| rollback; -- 结束事务(commit或者rollback)                    | 唤醒了（原因：窗口1事务结束了，释放了互斥锁）                |
|                                                              | rollback; -- 结束事务(commit或者rollback)                    |
## 效果3：验证共享锁和共享锁可以共存
| 窗口1                                                        | 窗口2                                                        |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| start transaction;                                           | start transaction;                                           |
| select * from t_user where id = 1 lock in share mode; --对id=1这条记录添加了共享锁 |                                                              |
|                                                              | select * from t_user where id = 1 lock in share mode; --对id=1这条记录添加了共享锁，共享锁可以共存，所以这里不会被阻塞 |
| rollback; -- 结束事务(commit或者rollback)                    | rollback; -- 结束事务(commit或者rollback)                    |
理解了这些之后，我们对repay方法进行调整，将互斥锁(for update) 调整成共享锁（lock in share model）就可以了。
## 方案3，代码如下
![image-20240914212320389](/blogs/_archive-2024-assets/9fdbbbdf0e0016314d9f.webp)
# 6、总结
本文内容稍微有点多，大家多看两遍，好好消化下。
