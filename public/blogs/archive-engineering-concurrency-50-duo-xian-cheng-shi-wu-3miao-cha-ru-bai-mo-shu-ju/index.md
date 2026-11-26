#  多线程事务，3秒插入百万数据
# 1、本文内容
1. 多线程事务效果演示
2. 多线程事务原理详解
3. 手写了一个非常好用的多线程事务工具类，大家拿去用
# 2、演示：单线程插入50 万数据
```java
com.itsoku.lesson050.Lesson050ApplicationTest#singleThreadInsert
```
```sql
select count(*) from t_test_1;
select count(*) from t_test_2;
select count(*) from t_test_3;
select count(*) from t_test_4;
select count(*) from t_test_5;
```
平均耗时 6 秒左右。
# 3、演示：多线程插入50万数据
```java
com.itsoku.lesson050.Lesson050ApplicationTest#moreThreadInsert
```
```sql
select count(*) from t_test_1;
select count(*) from t_test_2;
select count(*) from t_test_3;
select count(*) from t_test_4;
select count(*) from t_test_5;
```
平均耗时 3 秒左右。
# 4、演示：多线程插入50万数据，其中一个失败，是否会全部回滚？
```java
com.itsoku.lesson050.Lesson050ApplicationTest#moreThreadInsertFail
```
```sql
select count(*) from t_test_1;
select count(*) from t_test_2;
select count(*) from t_test_3;
select count(*) from t_test_4;
select count(*) from t_test_5;
```
# 5、多线程事务原理
![image-20240615202320117](/blogs/_archive-2024-assets/69047dc2c7e411868ee1.webp)
# 6、非常好用的多线程工具类
```java
com.itsoku.lesson050.utils.MoreThreadTransactionUtils
```
