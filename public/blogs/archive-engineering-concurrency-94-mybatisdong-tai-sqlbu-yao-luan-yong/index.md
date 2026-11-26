# 第94节 MyBatis动态SQL不要乱用，容易搞出大事故

# 1、来看一个案例
## 代码如下
MyBatis写的一个更新用户信息的接口，字段可以动态更新：即用户传入的字段不为空的时候，才会被更新
```xml
<!-- 更新用户信息 -->
<update id="update" parameterType="com.xxx.model.UserModel">
    <![CDATA[ UPDATE `t_user` ]]>
    <set>
        <if test="username != null and username.toString() != ''">
            <![CDATA[ `username` = #{username}, ]]>
        </if>
        <if test="email != null and email.toString() != ''">
            <![CDATA[ `email` = #{email}, ]]>
        </if>
    </set>
    <where>
        <if test="user_id != null">
            <![CDATA[ AND `user_id` = #{user_id} ]]>
        </if>
    </where>
</update>
```
对这段代码解释下：
- 传入的参数是用户对象UserModel
- set部分采用的是动态sql，字段不为空的时候，才会去更新，这块没问题，设计的很好
- 条件部分，用的是动态sql，这部分大家好好看看，存在很大的风险，当user_id不传入的时候，会导致全表数据被更新，产生大事故
## 如何解决这个问题？
更新的功能，条件部分不要用动态sql，调整后代码如下，更新的时候必须传入用户id，否则报错就可以了
```xml
<!-- 更新用户信息 -->
<update id="update" parameterType="com.itsoku.model.UserModel">
    <![CDATA[ UPDATE `t_user` ]]>
    <set>
        <if test="username != null and username.toString() != ''">
            <![CDATA[ `username` = #{username}, ]]>
        </if>
        <if test="email != null and email.toString() != ''">
            <![CDATA[ `email` = #{email}, ]]>
        </if>
    </set>
    where user_id = #{user_id}
</update>
```
# 2、再来看另外一个案例
代码如下，用于删除用户记录，入参是Map对象，条件部分是动态sql
这么设计的初衷是：这种设计可以满足各种删除操作，比如需要根据其他条件删除，只需要在where部分添加一些动态条件就可以了。
```xml
<!-- 删除数据 -->
<delete id="delete" parameterType="map">
    <![CDATA[
        DELETE FROM `t_user`
    ]]>
    <where>
        <if test="user_id!=null">
            <![CDATA[ AND `user_id` = #{user_id} ]]>
        </if>
    </where>
</delete>
```
**这段代码存在极大的风险**：如果传入的map是空，把整个表的数据都给清空了，可能就要拎包走人了。
这就是大而全接口的危害，希望一个接口能够满足所有操作。
## 如何解决这个问题呢？
不要提供这种大而全的接口，可以将其调整成一个个小而明确的接口，比如需要根据用户id删除用户，可以写成下面这样，条件部分不要用动态sql
```xml
<!-- 根据用户id删除用户 -->
<delete id="deleteByUserId">
    <![CDATA[
        DELETE FROM `t_user` where `user_id` = #{user_id}
    ]]>
</delete>
```
# 3、总结
1. MyBatis中更新和删除操作，不要在条件中使用动态SQL，一不小心全表数据都被操作了
2. 对于查询功能，条件部分是可以用动态SQL
3. 尽量不要设计大而全的接口，想用一个接口满足所有功能，这种设计存在很大风险，且难以理解和维护，尽量杜绝
