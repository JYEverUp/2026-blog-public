# 第80节 逻辑删除与唯一约束冲突，如何解决？

# 1、先来看一个需求
假如系统中有个用户表(t_user)，产品要求用户信息，需要满足下面几个条件
1. 用户名必须唯一
2. 用户数据不要物理删除，需要留痕，删除的时候可以对这条记录打个删除标记，标记这条记录被删除了
这个表应该如何设计呢？
先来看此表的第一个版本
# 2、用户表：第1个版本
## 2.1、表结构
| 字段      | 说明                                                   |
| --------- | ------------------------------------------------------ |
| id        | 用户id，主键                                           |
| user_name | 用户名，需添加唯一索引，确保用户名唯一                 |
| is_delete | 逻辑删除标记，用于标记当前记录是否已删除，0：否，1：是 |
> 什么是逻辑删除？
>
> 执行删除时，物理上不删除数据，只是在数据上打个标记，标记该记录已删除，比如将 is_delete 字段的值置为 1，表示该记录已删除，实际上记录并不会从表中真实删掉，如果有查询操作，需要在查询条件上加上is_delete=0，过滤出未被删除的数据。
## 2.2、建表脚本
```sql
DROP TABLE IF EXISTS `t_user`;
-- 创建用户表：t_user
CREATE TABLE IF NOT EXISTS `t_user` (
	`id` VARCHAR (32) NOT NULL PRIMARY KEY COMMENT '用户id',
	`user_name` VARCHAR (64) NOT NULL COMMENT '用户名，唯一',
	`is_delete` SMALLINT NOT NULL DEFAULT 0 COMMENT '逻辑删除标记，用于标记当前记录是否已删除，0：否，1：是',
	UNIQUE KEY `uq_user_name` (`user_name`)
) COMMENT = '用户表';
```
## 2.3、验证是否可以满足需求
执行下面脚本，如果都能执行成功，说明可以满足需求。
```sql
-- 插入一条记录，id为1，用户名：路人
insert into t_user (id, user_name) values ('1','路人');
-- 将路人这条记录逻辑删除：is_delete 设置为 1
update t_user set is_delete = 1 where id = 1;
-- 再次插入用户名：路人，看下是否可以插入成功
insert into t_user (id, user_name) values ('2','路人');
```
## 2.3、执行结果
```sql
[SQL] -- 插入一条记录，id为1，用户名：路人
insert into t_user (id, user_name) values ('1','路人');
受影响的行: 1
时间: 0.003s
[SQL] 
-- 将路人这条记录逻辑删除：is_delete 设置为 1
update t_user set is_delete = 1 where id = 1;
受影响的行: 1
时间: 0.002s
[SQL] 
-- 再次插入用户名：路人，看下是否可以插入成功
insert into t_user (id, user_name) values ('2','路人');
[Err] 1062 - Duplicate entry '路人' for key 'uq_user_name'
```
## 2.4、结果分析
从结果中可以看到，刚开始插入了`('1','路人')` 这条记录，稍后逻辑删除了，然后又插入了一条叫`路人`的记录，但是报错了，如下，违法了唯一约束
```java
[Err] 1062 - Duplicate entry '路人' for key 'uq_user_name'
```
业务上看用户id为1这条`路人`已经被删除了，此时再次插入id为2用户名为`路人`的记录，按说应该成功，是不是？但是却没有成功
此时就出现了：**逻辑删除和唯一约束冲突了**，当前这种设计无法满足需求。
下面来看下如何解决。
# 3、解决方案
## 3.1、设计上需调整，主要2点
1. 添加一个字段：delete_time，用来记录当前记录被逻辑删除的时间，默认值为0，当记录被逻辑删除的时候，即is_delete被设置为1的时候，将delete_time设置为当前时间戳
2. 需要用到组合唯一索引，在 (user_name,  delete_time) 这两个字段上添加唯一索引
这样便可解决问题，下面一起来验证下。
## 3.2、建表脚本
```sql
DROP TABLE IF EXISTS `t_user`;
-- 创建用户表：t_user
CREATE TABLE IF NOT EXISTS `t_user` (
	`id` VARCHAR (32) NOT NULL PRIMARY KEY COMMENT '用户id',
	`user_name` VARCHAR (64) NOT NULL COMMENT '用户名，唯一',
	`is_delete` SMALLINT NOT NULL DEFAULT 0 COMMENT '逻辑删除标记，用于标记当前记录是否已删除，0：否，1：是',
	`delete_time` BIGINT NOT NULL DEFAULT 0 COMMENT '逻辑删除时间，默认为0，当is_delete被置为1的时候，将此字段设置为当前时间戳',
	UNIQUE KEY `uq_user_name_delete_time` (`user_name`, `delete_time`)
) COMMENT = '用户表';
```
## 3.2、验证是否可以满足需求
执行下面脚本
```sql
-- 插入一条记录，id为1，用户名：路人
insert into t_user (id, user_name) values ('1','路人');
-- 将路人这条记录逻辑删除：is_delete 设置为 1, delete_time 设置为当前时间时间戳秒
update t_user set is_delete = 1, delete_time = UNIX_TIMESTAMP(now()) where id = 1;
-- 再次插入用户名：路人，插入成功
insert into t_user (id, user_name) values ('2','路人');
-- 再次插入用户名：路人，插入失败
insert into t_user (id, user_name) values ('3','路人');
```
## 3.2、执行结果
```sql
[SQL] -- 插入一条记录，id为1，用户名：路人
insert into t_user (id, user_name) values ('1','路人');
受影响的行: 1
时间: 0.003s
[SQL] 
-- 将路人这条记录逻辑删除：is_delete 设置为 1, delete_time 设置为当前时间时间戳秒
update t_user set is_delete = 1, delete_time = UNIX_TIMESTAMP(now()) where id = 1;
受影响的行: 1
时间: 0.002s
[SQL] 
-- 再次插入用户名：路人，插入成功
insert into t_user (id, user_name) values ('2','路人');
受影响的行: 1
时间: 0.002s
[SQL] 
-- 再次插入用户名：路人，插入失败
insert into t_user (id, user_name) values ('3','路人');
[Err] 1062 - Duplicate entry '路人-0' for key 'uq_user_name_delete_time'
```
此时表中数据如下
```java
mysql> select * from t_user;
+----+-----------+-----------+-------------+
| id | user_name | is_delete | delete_time |
+----+-----------+-----------+-------------+
| 1  | 路人      |         1 |  1724642691 |
| 2  | 路人      |         0 |           0 |
+----+-----------+-----------+-------------+
```
## 3.3、结果分析
从上面看，这样设计已满足需求。
# 4、总结
当逻辑删除遇到唯一约束的时候，解决方案如下
1. 添加is_delete字段，逻辑删除标记，0：未删除，1：已删除，默认值为0
2. 添加delete_time字段，用于记录数据被逻辑删除的时间，默认值为0
3. 需要添加组合字段唯一索引：( `业务上需要确保唯一的业务字段`,` delete_time` )
4. 数据删除逻辑，如下：将 is_delete 置为 1， delete_time 置为当前时间戳，便可解决问题
   ```sql
   update t_user set is_delete = 1, delete_time = UNIX_TIMESTAMP(now()) where id = 1;
   ```
# 
