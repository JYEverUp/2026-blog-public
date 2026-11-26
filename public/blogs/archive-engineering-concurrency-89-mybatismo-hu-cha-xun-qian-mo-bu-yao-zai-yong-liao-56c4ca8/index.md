# 第89节 MyBatis模糊查询，千万不要再用${}了，容易搞出大事故

# 1、来看个需求
我们这边有个博客表，如下，3个字段，目前有5条数据，用户1的数据有2条
- id：主键
- user_id：作者id
- title：博客标题
![image-20240910100248466](/blogs/_archive-2024-assets/7f66ba9695920fb4fc42.webp)
假如，我们要给前端提供一个接口，根据title模糊检索当前用户博客列表，这个需求怎么实现？
算是一个非常简单的需求吧。
# 2、版本1：MyBatis+${}实现
代码如下，大家应该比较熟悉这种写法吧。
```xml
<select id="findMyArticles1" resultType="com.itsoku.lesson089.po.ArticlePO">
    SELECT
        id,
        user_id AS userId,
        title
    FROM
        t_article_lesson089
    WHERE
        user_id = #{userId}
      AND title LIKE '%${keywords}%'
</select>
```
测试下效果，启动应用`com.itsoku.lesson089.Lesson089Application`
浏览器中访问：http://localhost:8080/findMyArticles1?myUserId=1&keywords=java
> 查询用户1，标题中带有java的，文章列表，查询结果如下，结果符合预期
```json
[
  {
    "id": 1,
    "userId": 1,
    "title": "Java 高并发"
  },
  {
    "id": 2,
    "userId": 1,
    "title": "Java 微服务"
  }
]
```
控制台sql输出如下，原本sql中的<font color='red' style='font-weight:bold'>title LIKE '%${keywords}%'</font> 被替换成了 <font color='red' style='font-weight:bold'>title LIKE '%java%'</font>，MyBatis中的`${}`在SQL 解析阶段会替换成变量原本的值。
```java
10:08:56 - ==>  Preparing: SELECT id, user_id AS userId, title FROM t_article_lesson089 WHERE user_id = ? AND title LIKE '%java%'
10:08:56 - ==> Parameters: 1(Long)
10:08:56 - <==      Total: 2
```
这种写法存在严重的问题，下面来给大家演示下。
# 3、版本1：${}问题演示
在浏览器中访问下面地址，重点看下keywords参数的值
```java
http://localhost:8080/findMyArticles1?myUserId=1&keywords=' or 1=1 or '
```
浏览器输出如下，将表中所有数据都撸出来了，不符合预期
```json
[
  {
    "id": 1,
    "userId": 1,
    "title": "Java 高并发"
  },
  {
    "id": 2,
    "userId": 1,
    "title": "Java 微服务"
  },
  {
    "id": 3,
    "userId": 2,
    "title": "Java 性能调优"
  },
  {
    "id": 4,
    "userId": 2,
    "title": "Java 从入门到精通"
  },
  {
    "id": 5,
    "userId": 3,
    "title": "Java Web开发"
  }
]
```
再看下控制台的sql，如下：
```java
10:14:30 - ==>  Preparing: SELECT id, user_id AS userId, title FROM t_article_lesson089 WHERE user_id = ? AND title LIKE '%' or 1=1 or '%'
10:14:30 - ==> Parameters: 1(Long)
10:14:30 - <==      Total: 5
```
整个表的数据都被撸出来了，产生了严重的事故
- 用户1查看到了不属于自己的数据，若这些是敏感数据，直接导致数据泄露
- 若表数据库非常大，直接导致数据库或业务系统崩溃
这也是常说的sql注入，mybatis中${}这种写法存在sql注入的风险。
如何解决呢？请看方案2。
# 3、方案2：使用#{}替换${}
新的写法如下，使用#{}替换${}， \#{ } 被解析为一个参数占位符 ，不存在sql注入
```xml
<select id="findMyArticles2" resultType="com.itsoku.lesson089.po.ArticlePO">
    SELECT
        id,
        user_id AS userId,
        title
    FROM
        t_article_lesson089
    WHERE
        user_id = #{userId}
      AND title LIKE #{keywords}
</select>
```
来看下效果，浏览器中访问
```java
http://localhost:8080/findMyArticles2?myUserId=1&keywords=java
```
浏览器输出如下，结果符合预期
```json
[
  {
    "id": 1,
    "userId": 1,
    "title": "Java 高并发"
  },
  {
    "id": 2,
    "userId": 1,
    "title": "Java 微服务"
  }
]
```
控制台sql如下，也没问题
```java
10:22:41 - ==>  Preparing: SELECT id, user_id AS userId, title FROM t_article_lesson089 WHERE user_id = ? AND title LIKE ?
10:22:41 - ==> Parameters: 1(Long), %java%(String)
10:22:41 - <==      Total: 2
```
浏览器中再访问下下面这个地址，看看会不会出问题
```
http://localhost:8080/findMyArticles2?myUserId=1&keywords=' or 1=1 or '
```
浏览器中输出如下，没有查询到任何数据，符合预期
```json
[]
```
再来看下控制台sql如下，也没问题
```java
10:24:00 - ==>  Preparing: SELECT id, user_id AS userId, title FROM t_article_lesson089 WHERE user_id = ? AND title LIKE ?
10:24:00 - ==> Parameters: 1(Long), %' or 1=1 or '%(String)
10:24:00 - <==      Total: 0
```
问题已解决。
# 4、总结
MyBatis中使用模糊查询的时候，千万不要使用`${}`这种写法了，请使用`#{}`这种写法。
