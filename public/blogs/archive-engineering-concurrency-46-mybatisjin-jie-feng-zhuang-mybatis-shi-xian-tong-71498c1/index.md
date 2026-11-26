#  封装MyBatis，实现通用无SQL版CRUD功能ORM框架
# 1、本文主要内容
对Mybatis进行封装，实现一个通用的无 SQL 版的 CRUD 功能 ORM 框架。
MyBatis-plus 大家应该都比较熟悉吧，本文实现的功能，类似与Mybatis-plus功能，实现的原理非常的简单，这样方便大家扩展。
不需要写一行sql，便可实现对数据库的 **增、删、改、查、分页、统计、乐观锁更新数据**等操作。
# 2、本框架涵盖的功能
## 2.1、插入
1. 插入记录：com.itsoku.orm.IService#insert
2. 批量插入：com.itsoku.orm.IService#insertBatch
## 2.2、删除
1. 根据主键删除记录：com.itsoku.orm.IService#deleteById
2. 根据主键批量删除记录：com.itsoku.orm.IService#deleteByIds
3. 根据条件删除记录：com.itsoku.orm.IService#delete
## 2.3、更新
1. 根据主键，更新一条记录：com.itsoku.orm.IService#update
2. 根据主键，更新一条记录，只更新非 null 字段：com.itsoku.orm.IService#updateNonNull
3. 根据主键，更新一条记录，只更新指定的字段：com.itsoku.orm.IService#updateWith
4. 根据主键+乐观锁，更新一条记录：com.itsoku.orm.IService#optimisticUpdate
5. 根据主键+乐观锁，更新一条记录，只更新非 null 字段：com.itsoku.orm.IService#optimisticUpdateNonNull
6. 根据主键+乐观锁，更新一条记录，只更新指定的字段：com.itsoku.orm.IService#optimisticUpdateWith
## 2.4、查询
1. 根据条件查询记录：com.itsoku.orm.IService#find
   > 基本上所有的查询条件都支持、支持查询部分列
2. 查询满足的条件的一条记录：com.itsoku.orm.IService#findOne
3. 根据主键查询记录：com.itsoku.orm.IService#findById
4. 根据主键列表查询多条记录：com.itsoku.orm.IService#findByIds
5. 根据主键列表查询记录，返回Map，key为主键，value为记录：com.itsoku.orm.IService#findMapByIds
## 2.5、数量统计
1. 查询满足条件的记录数：com.itsoku.orm.IService#count
## 2.6、分页查询
1. 通用分页查询方法：com.itsoku.orm.IService#findPage
# 3、效果演示
## 3.1、准备2张表
```sql
-- 创建用户表
drop table if exists t_user_lesson046;
create table t_user_lesson046
(
    id        bigint not null auto_increment primary key,
    user_name varchar(100),
    age       int
);
insert into t_user_lesson046 (user_name, age)
values ('路人1', 10),
       ('路人2', 11),
       ('路人3', 20),
       ('路人4', 21),
       ('路人5', 22),
       ('路人6', 23),
       ('路人7', 30),
       ('路人8', 31),
       ('路人9', 32);
-- 创建账户表
drop table if exists t_account_lesson046;
create table if not exists t_account_lesson046
(
    id      varchar(32)    not null primary key comment '用户id',
    name    varchar(50)    not null comment '用户名',
    balance decimal(12, 2) not null comment '账户余额',
    version bigint         not null default 0 comment '版本号，默认为0，每次更新+1'
) comment '账户表';
insert ignore into t_account_lesson046 value ('1', '路人1', '1000.00', 0);
```
- 这两张表有点区别，用户表的id是自动增长的，账户表的id是插入的时候调用方填充进来的
- 第二张表有version字段，可以用于演示乐观锁更新数据。
## 3.2、先演示对用户表的一些操作
需要先用户对应的 5 个类。
### 1）创建用户实体类
com.itsoku.lesson046.po.UserPO
### 2）创建用户Mapper接口
com.itsoku.lesson046.mapper.UserMapper
需要继承`com.itsoku.orm.BaseMapper`，然后就拥有了上面说的增删改查分页通用的功能
### 3）创建用户service接口
com.itsoku.lesson046.service.IUserService
需要继承`com.itsoku.orm.IService`，这个接口中定义了通用的增删改查分页通用的功能
### 4）创建用户service接口实现类
com.itsoku.lesson046.service.impl.UserServiceImpl
需要继承`com.itsoku.orm.ServiceImpl`，这个类中包含了通用的增删改查分页通用的功能
## 3.3、测试效果
| 查询用户所有记录           | com.itsoku.lesson046.Lesson046ApplicationTest#test001 |
| -------------------------- | ----------------------------------------------------- |
| 查询需要的字段（id，name） | com.itsoku.lesson046.Lesson046ApplicationTest#test002 |
| 复杂条件分页查询           | com.itsoku.lesson046.Lesson046ApplicationTest#test003 |
| 插入用户记录               | com.itsoku.lesson046.Lesson046ApplicationTest#test101 |
## 3.4、演示对账户表的一些操作
主要演示乐观锁更新数据：com.itsoku.lesson046.Lesson046ApplicationTest#test204
# 4、更多案例
下面所有案例均在`com.itsoku.lesson046.Lesson046ApplicationTest`类中
## 4.1、查询
| 测试方法 | 说明                                                |      |
| -------- | --------------------------------------------------- | ---- |
| test001  | 查询所有用户                                        |      |
| test002  | 要的字段(id、name)                                  |      |
| test003  | 复杂条件分页查询                                    |      |
| test004  | 根据id查询                                          |      |
| test005  | 根据id列表批量查询                                  |      |
| test006  | 根据主键列表查询记录，返回Map，key为主键，map为记录 |      |
| test007  | 查询满足条件的一条记录                              |      |
## 4.2、统计数量
| 测试方法 | 说明                   |
| -------- | ---------------------- |
| test020  | 查询满足条件的记录数量 |
## 4.3、分页查询
| 测试方法 | 说明               |
| -------- | ------------------ |
| test030  | 分页查询用户记录   |
| test031  | 按条件分页查询     |
| test032  | 分页查询带转换功能 |
## 4.4、插入单条记录
### 1）id是自动增长类型的
com.itsoku.lesson046.Lesson046ApplicationTest#test101
主键上需要标注`@TableId(type = IdType.AUTO)`，参考`com.itsoku.lesson046.po.UserPO`
### 2）id 手动填充
com.itsoku.lesson046.Lesson046ApplicationTest#test101
## 4.5、批量插入
com.itsoku.lesson046.Lesson046ApplicationTest#test104
## 4.6、更新记录-普通更新
| 测试方法 | 说明                                     |
| -------- | ---------------------------------------- |
| test201  | 按照主键更新一个对象                     |
| test202  | 按照主键更新一个对象，只更新非 null 字段 |
| test203  | 键更新一个对象，只更新指定的属性         |
## 4.7、更新记录-主键+乐观锁更新
对应的PO必须要有@Version标注的字段，字段类型只能是int、Integer、long、Long类型，参考AccountPO
| 测试方法 | 说明                                                  |
| -------- | ----------------------------------------------------- |
| test204  | 按照主键和version字段作为条件更新                     |
| test205  | 按照主键和version字段作为条件更新，只更新非 null 字段 |
| test206  | 按照主键和version字段作为条件更新，只更新指定的属性   |
## 4.8、删除记录
| 测试方法 | 说明                 |
| -------- | -------------------- |
| test301  | 根据主键删除记录     |
| test302  | 根据主键批量删除记录 |
| test303  | 根据条件删除记录     |
# 5、源码解析
## 5.1、核心源码：com.itsoku.orm.BaseMapper
原理是使用MyBatis中的动态sql生成功能实现的，比如插入的方法
```java
/**
 * 插入
 *
 * @param po
 * @return
 */
@InsertProvider(type = SqlProvider.class, method = "insert")
int _insert(@Param("po") T po);
```
这里用到了MyBatis提供的一个注解`@InsertProvider`，当执行上面这个插入方法的时候，会通过`SqlProvider#insert`方法获取需要执行的sql。
Mybatis还提供3个类似的注解，如下
- @UpdateProvider：动态生成更新的sql
- @DeleteProvider：动态生成删除的sql
- @SelectProvider：动态生成查询的sql
## 5.2、com.itsoku.orm.IService
里面定义的方法和 BaseMapper接口中定义的方法基本上一样。
## 5.3、com.itsoku.orm.ServiceImpl
IServcie接口的默认实现，我们的service需要继承这个类，便拥有了增、删、改、查、分页、统计所有功能。
# 6、其他使用注意事项
### @TableName 注解
用户标注在PO上面，value为表名，如
```java
@Table("t_user_lesson046")
public class UserPO {
    @TableId(type = IdType.AUTO)
    private Long id;
    @TableField("user_name")
    private String userName;
    private Integer age;
}
```
### @TableFiled注解
标注在字段上，value为字段名称。
表中字段的名称一般采用下划线分割多个单词，对应的java中属性的名称，会采用驼峰命名法。
比如字段的名称为 user_name，对应的java中属性名称为userName。
当字段满足上面这个规则的时候，@TableFiled字段可以省略，比如案例中的 UserPo中的@TableFiled可以省略。
### @TableId
实体类中，必须有主键，且上面必须加上 @TableId注解，标识这个字段是主键。
```java
@Documented
@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.FIELD})
public @interface TableId {
    IdType type() default IdType.NONE;
}
```
注解有个 type属性，值如下，当主键是自增的时候，type的值为 AUTO
```java
public enum IdType {
    /**
     * 数据库ID自增
     * <p>该类型请确保数据库设置了 ID自增 否则无效</p>
     */
    AUTO,
    /**
     * 该类型为未设置主键类型
     */
    NONE;
}
```
 
