#  SpringBoot中，Redis如何实现排行榜？

# 1、本文内容
1. Redis 如何实现排行榜？
2. Redis中zset实现排行榜，分数相同时，按照时间降序，如何处理？
# 2、Redis 如何实现排行榜？
Redis 实现排行榜主要依赖于其有序集合zset（Sorted Set）数据结构。
zset中可以存储不重复的元素集合，并为每个元素关联一个浮点数分数（score），Redis 会根据这个分数自动对集合中的元素进行排序。
下面给大家演示下如何使用zset来实现排行榜的功能。
## 用户积分列表
下面表格是用户积分的数据，我们来演示如何将其添加到redis中，然后实现积分排行榜功能
| 用户id | 积分 |
| ------ | ---- |
| user1  | 100  |
| user2  | 200  |
| user3  | 150  |
## 使用有序集合-添加元素
可以使用 `ZADD` 命令来向有序集合中添加元素，将上面列表中：用户id作为元素、积分作为分数
```bash
192.168.216.128:6379> zadd user:ranking 100 user1
(integer) 1
192.168.216.128:6379> zadd user:ranking 200 user2
(integer) 1
192.168.216.128:6379> zadd user:ranking 150 user3
(integer) 1
```
> 上面命令中`user:ranking`是有序集合的名称，100、200、150 是每个用户的积分，user1、user2、user3 是用户的id
## 获取用户积分排行
使用 `ZREVRANGE` 命令（从高到低排序）或 `ZRANGE` 命令（从低到高排序）来获取排行榜的前几名
```bash
# 获取用户积分排行榜前3名（分数从高到低）  
192.168.216.128:6379> ZREVRANGE user:ranking 0 2 WITHSCORES
1) "user2"
2) "200"
3) "user3"
4) "150"
5) "user1"
6) "100"
```
# 3、积分相同时，如何处理？
如下表，当用户积分相同时，要求按最后更新时间升序
| 用户id | 积分 | 最后更新时间时间戳(毫秒) |
| ------ | ---- | ------------------------ |
| user1  | 100  | 1720663200002            |
| user2  | 100  | 1720663200001            |
| user3  | 150  | 1720663200000            |
按照：`积分 desc，最后更新时间 asc`，排名后，顺序应该是：user3、user2、user1，但是redis中的zset只能score进行排序，怎么解决呢？
# 4、积分相同时，按最后更新时间升序，解决思路
可以将zset中的score设置为一个浮点数，其中整数部分为积分，小数部分为最后更新时间时间戳，算法如下
## score = 积分 + 时间戳/10的13次方
> 这里为什么要除以10的13次方？由于时间戳的长度是13位，除以10的13次方，可以将其移到小数点的右边
对上面表格，处理之后，变成了下面这样
| 用户id | 积分 | 最后更新时间时间戳(毫秒) | score             |
| ------ | ---- | ------------------------ | ----------------- |
| user1  | 100  | 1720663200002            | 100.1720663200002 |
| user2  | 100  | 1720663200001            | 100.1720663200001 |
| user3  | 150  | 1720663200000            | 150.1720663200000 |
按score降序排序后，是：user3 (150.1720663200000)  > user1 (100.1720663200002)  > user2( 100.1720663200001)
和预期的不一样，user2的最后更新时间是小于user1的，user2应该排在user1之前，怎么办呢？
需要再做一次转换
## score = 积分 + (1 - 时间戳/10的13次方)
处理后，表格变成了下面这样
| 用户id | 积分 | 最后更新时间时间戳(毫秒) | score             |
| ------ | ---- | ------------------------ | ----------------- |
| user1  | 100  | 1720663200002            | 100.8279336799998 |
| user2  | 100  | 1720663200001            | 100.8279336799999 |
| user3  | 150  | 1720663200000            | 150.8279336800000 |
按降序排序后，是：user3 (150.8279336800000)  > user2 (100.8279336799999)  > user1(100.8279336799998)
这样就达到了预期的目的
# 5、SpringBoot代码实现
## 引入maven配置
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
```
## 提供：录入用户数据、查询排行榜接口
源码如下，有2个方法
- addUserPoint：批量将用户积分数据写入到redis的zset中
- userRankings：获取用户积分排行榜接口
```java
lesson065/src/main/java/com/itsoku/lesson065/controller/UserRankingController.java
package com.itsoku.lesson065.controller;
import com.itsoku.lesson065.dto.UserRanking;
import com.itsoku.lesson065.dto.UserPointsReq;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ZSetOperations;
import org.springframework.web.bind.annotation.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
/**
 * <b>description</b>实战
 * <b>time</b>：2024/7/18 20:23 <br>
 * <b>author</b>：gjy
 */
@RestController
public class UserRankingController {
    @Autowired
    private StringRedisTemplate stringRedisTemplate;
    /**
     * 用户积分批量插入到redis
     *
     * @param userPointsReqList
     * @return
     */
    @PostMapping("/addUserPoint")
    public boolean addUserPoint(@RequestBody List<UserPointsReq> userPointsReqList) {
        String key = "user:ranking";
        for (UserPointsReq userPointsReq : userPointsReqList) {
            String userId = userPointsReq.getUserId();
            //先按积分降序，积分相同时按照最后更新时间升序，score = 积分 + (1 - 时间戳/10的13次方)
            double score = userPointsReq.getPoints() + (1 - userPointsReq.getUpdateTime() / 1e13);
            this.stringRedisTemplate.opsForZSet().add(key, userId, score);
        }
        return true;
    }
    /**
     * 获取用户积分排行榜(倒序)
     *
     * @param topN 前多少名
     * @return
     */
    @GetMapping("/userRankings")
    public List<UserRanking> userRankings(@RequestParam("topN") int topN) {
        String key = "user:ranking";
        Set<ZSetOperations.TypedTuple<String>> typedTuples = this.stringRedisTemplate.opsForZSet().reverseRangeWithScores(key, 0, topN - 1);
        List<UserRanking> userRankingList = new ArrayList<>();
        for (ZSetOperations.TypedTuple<String> typedTuple : typedTuples) {
            UserRanking userRanking = new UserRanking();
            userRanking.setUserId(typedTuple.getValue());
            userRanking.setRedisScore(typedTuple.getScore());
            userRankingList.add(userRanking);
        }
        return userRankingList;
    }
}
```
```java
@Data
public class UserPointsReq {
    //用户id
    private String userId;
    //积分
    private Integer points;
    //最后更新时间（时间戳毫秒）
    private Long updateTime;
}
```
```java
@Data
public class UserRanking {
    private String userId;
    private double redisScore;
}
```
## 测试代码
lesson065/src/test/resources/UserRankingController.http
```http
### 1.批量将用户积分丢到redis中zset中
POST http://localhost:8080/addUserPoint
Accept: application/json
Content-Type: application/json
[
  {
    "userId": "user1",
    "points": 100,
    "updateTime": 1720663200002
  },
  {
    "userId": "user2",
    "points": 100,
    "updateTime": 1720663200001
  },
  {
    "userId": "user3",
    "points": 150,
    "updateTime": 1720763100000
  }
]
### 2.获取排名前3的用户列表，按积分倒序，积分相同时，按最后更新时间升序
GET http://localhost:8080/userRankings?topN=3
Accept: application/json
```
