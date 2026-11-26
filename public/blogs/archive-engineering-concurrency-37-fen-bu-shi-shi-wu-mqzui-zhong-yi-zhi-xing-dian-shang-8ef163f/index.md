#  使用MQ最终一致性实现：电商平台账户余额提现到微信钱包
## 场景
假如咱们做个电商系统，商户可以在上面卖东西，卖东西会产生交易，交易产生的收入在平台账户的余额中，这就涉及到商户提现的操作
需支持：商户将平台上账户余额提现到微信钱包，这个功能如果交给我们，该如何实现？
本文将大家搞定这个问题，这个场景算是分布式事务中比较有代表性的一个案例，大家大概率会遇到类似的场景，望大家掌握。
## 方案
使用MQ最终一致性解决，大致的过程如下：
![image-20240515143018435](/blogs/_archive-2024-assets/65585370a45fc4e23427.webp)
代码我们已经实现了。
## 带大家看下效果
### 先准备2个表
账号表和提现记录表，账户表插入了一个用户，等会会模拟从这个账号中体现100到微信钱包。
```sql
-- 创建账户表
drop table if exists t_account_lesson037;
create table if not exists t_account_lesson037
(
    id      varchar(32)    not null primary key comment '用户id',
    name    varchar(50)    not null comment '用户名',
    balance decimal(12, 2) not null comment '账户余额'
) comment '账户表';
insert ignore into t_account_lesson037 value ('1','路人1','1000.00');
-- 提现记录表
drop table if exists t_cash_out_lesson037;
create table if not exists t_cash_out_lesson037
(
    id          varchar(32)    not null primary key comment '用户id',
    account_id  varchar(32)    not null comment '账号id',
    price       decimal(12, 2) not null comment '提现金额',
    status      smallint       not null comment '状态，0：待处理，100：提现成功',
    create_time datetime       not null comment '创建时间',
    update_time datetime comment '最后更新时间'
) comment '提现记录表';
```
### 提现接口
```java
com.itsoku.lesson037.controller.AccountController#cashOut
```
主要干了3件事情
1. 扣减账户余额
2. 创建提现记录，状态为0（处理中）
3. 发送提现消息（这块必须是事务消息，可以确保业务执行成功，消息一定会投递成功，不会丢失）
### 提现消息消费者
```java
com.itsoku.lesson037.consume.CashOutMsgConsumer#consume
```
主要干了2件事
1. 调用微信支付接口给个人钱包打款
   > 微信支付接口天然支幂等，如果也遇到了需要调用第三方接口的场景，也需要对方做幂等，这块可以参考微信支付接口或者支付宝接口
2. 将体现记录状态置为成功（status=100）
CashOutMsgConsumer 类继承了 com.itsoku.lesson037.mq.consumer.AbstractRetryConsumer，自动拥有了失败自动重试的功能。
### 启动应用
```java
com.itsoku.lesson037.Lesson037Application
```
### 先看db中账户余额
```sql
select * from t_account_lesson037;
```
![image-20240515142427374](/blogs/_archive-2024-assets/c15a8effc3b6bc141259.png)
### 执行测试用例
src/test/resources/AccountController.http
```http
### 平台账户余额提现到微信钱包
POST http://localhost:8080/account/cashOut
Accept: application/json
Content-Type: application/json
{
  "price": "10.00"
}
```
### 看db中账户余额
```sql
select * from t_account_lesson037;
```
![image-20240515141455305](/blogs/_archive-2024-assets/e3f5e14099e39a1d93b3.png)
