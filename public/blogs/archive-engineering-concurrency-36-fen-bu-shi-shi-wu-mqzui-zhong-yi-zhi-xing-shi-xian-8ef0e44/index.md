#  使用MQ最终一致性实现跨库转账
本文将通过跨库转账这个案例，带大家掌握MQ最终一致性解决分布式事务问题。
案例中，通用的代码我都给大家写好了，大家拿这个方案去解决分布式事务，只需要写你们的业务代码就可以了，这样大家遇到分布式事务问题，可以快速搞定。
## 前言
接下来三四节，属于分布式事务专题，会带来：分布式事务相关的一些解决方案+案例+代码落地，基本上可以解决工作中碰到的分布式事务问题
主要会给大家介绍2种方案
- MQ最终一致性解决分布式事务
- TCC 的方式解决分布式事务
都会配代码+案例+文档。
## MQ解决分布式事务问题
会提供2个案例，这两个案例是比较有代表性的，掌握后，基本上可以完全掌握MQ解决分布式事务的套路。
1. 跨库转账
2. 平台账户-提现到微信钱包
## 前置知识
- 分布式事务相关的一些概念知识
  - 什么是分布式事务：http://itsoku.com/course/7/160
  - CAP原则：http://itsoku.com/course/7/161
  - BASE理论：http://itsoku.com/course/7/162
- 本课程 第12节 幂等性 4 种方案
- 本课程 第 28 - 35 节 MQ专题相关
## 案例：使用MQ解决跨库转账
![image-20240515111636335](/blogs/_archive-2024-assets/ecf15d9a168d490b53e9.webp)
上面整个过程中，开发者只需要写业务代码，其他的事情框架中都帮忙干了。
- 上游我们只需要写扣减余额和投递消息的代码
- 下游只需要写给收款方加钱的代码
## 先带大家看下效果
### 先准备一个表
```sql
drop table if exists t_account_lesson036;
create table if not exists t_account_lesson036
(
    id      varchar(32)    not null primary key comment '用户id',
    name    varchar(50)    not null comment '用户名',
    balance decimal(12, 2) not null comment '账户余额'
) comment '账户表';
insert ignore into t_account_lesson036 value ('1','路人1','1000.00');
insert ignore into t_account_lesson036 value ('2','路人2','0.00');
```
跨库转账这个案例中，为了方便，我们将付款方和收款方，用的是同一个库中的同一个账户表，但是在应用层面，我们用的是分布式事务解决的。
### 跨库转账接口
```java
com.itsoku.lesson036.controller.AccountController#transfer
```
这个方法中主要对应付款方的代码，干了2件事情：
1. 付款方扣减余额
2. 投递一条转账消息到MQ（这里投递的是事务消息，可以去报扣减余额成功，消息一定会投递成功）
### 下游：消费转账消息，给收款方加钱
```java
com.itsoku.lesson036.consume.TransferMsgConsumer#idempotentConsume
```
在这个方法中，只需要给收款方加钱就可以了
下面是这个类的一个类图，他上面有2个父类，父类中是通用的代码，分别帮我们实现了失败自动重试、消费幂等性的工作，所以我们只需要写业务代码就行了，大大节省了我们的工作量。
![image-20240515113349164](/blogs/_archive-2024-assets/a6c0689fd2cb2d281867.webp)
### 启动应用
```java
com.itsoku.lesson036.Lesson036Application
```
### 先看db中账户余额
```sql
select * from t_account_lesson036;
```
![image-20240515124133940](/blogs/_archive-2024-assets/d6972ecdbca1df5600b9.png)
### 执行测试用例
src/test/resources/AccountController.http
```http
### 跨库转账
POST http://localhost:8080/account/transfer
Accept: application/json
Content-Type: application/json
{
  "fromAccountId": "1",
  "toAccountId": "2",
  "transferPrice": "10.00"
}
```
### 查看db中2个账户的余额
```sql
select * from t_account_lesson036;
```
![image-20240515124207064](/blogs/_archive-2024-assets/7050920f40823aa64479.png)
## MQ最终一致性适用的场景
适合分布式事务中有2个事务参与者，且后面一个一定会成功的场景，这种比较适合采用MQ最终一致性来解决。
- 第一个参与者：执行本地业务+投递事务消息
- 第二个参与者：幂等消费消息+消费失败衰减式重试+重试达到上线人工干预
