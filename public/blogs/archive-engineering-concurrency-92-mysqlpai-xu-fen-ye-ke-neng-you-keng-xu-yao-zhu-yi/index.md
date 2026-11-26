# 第92节 MySQL排序分页，可能有坑，需要注意

# 1、问题演示
## 1）创建一个表`test1`
```sql
drop table if exists test1;
CREATE TABLE test1 (
	a INT auto_increment PRIMARY KEY,
	b INT
);
```
## 2）插入 8 条数据
```sql
insert into test1 (b) values (1),(2),(3),(4),(2),(2),(2),(2);
```
## 3）根据字段b排序，查询表中数据
执行下面sql
```sql
select * from test1 order by b asc;
```
结果如下
![image-20240911100825357](/blogs/_archive-2024-assets/a28ba478f4ed0f252f32.png)
大家先看下上面这个结果，然后思考下：假如我们按照b排序，每页5条，第1页应该是什么数据？
是不是应该是下面这样？
![image-20240911101025125](/blogs/_archive-2024-assets/c7f61f117d88ed5666db.png)
我们来实际测试下，看看是不是这样，执行下面sql
```sql
select * from test1 order by b asc limit 0,5;
```
结果如下，和上面我们期望的结果不一样啊，期望的是 a = 1、2、5、6、7 这5条记录，实际查出来的是 a = 1、2、8、7、5；说明顺序乱掉了
![image-20240911101110093](/blogs/_archive-2024-assets/f8cd6aac127fd46ff2af.png)
我们再来测试下，按照b排序，每页5条，第2页是什么数据，sql如下
```sql
select * from test1 order by b asc limit 5,5;
```
执行后，结果如下
![image-20240911101509063](/blogs/_archive-2024-assets/e055f9e1f30fd11a7e60.png)
将第1页和第2页的结果对比下，发现出现了重复的数据，如下，a = 8 这条记录，在第一页和第二页中都出现了，说明目前的排序分页有问题。
![image-20240911101722817](/blogs/_archive-2024-assets/1571760b1abc666d0309.webp)
# 2、原因
由于b字段存在相同的值，当排序过程中存在相同的值时，没有其他排序规则时，MySQL 懵了，不知道怎么排序了
所以，排序字段存在相同值的时候顺序可能会乱。
# 3、如何解决这个问题？
当排序字段存在相同的值时，需要再增加一些其他的排序规则，通过多个排序规则的组合，使排序结果不存在二义性。
比如上面这个问题，可以再加上a字段作为排序规则，由于a是主键，具有唯一性，可以解决这个问题。
sql如下，可以验证下
```sql
select * from test1 order by b asc, a asc;
select * from test1 order by b asc, a asc limit 0,5;
select * from test1 order by b asc, a asc limit 5,5;
```
