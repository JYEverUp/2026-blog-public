#  电商系统-资金账户表设计 及 应用实战
# 1、本文主要内容
- 电商系统资金账户相关表设计及代码落地
- 案例：电商平台余额提现到微信钱包
# 2、看一个需求
比如咱们需要开发一个电商系统，电商系统中每个用户都有一个资金账户，相当于我们在电商系统中给用户开了一张银行卡一样，这个账户需要支持以下功能
1. 支持通过第三方支付进行充值
2. 支持将余额提现到微信钱包
3. 支持通过账户余额购买商品
# 3、资金账户表如何设计？
可以使用3张表来搞定这个需求
## 3.1、账户资金表：t_account_funds_lesson048
每个用户会有一条记录
```sql
CREATE TABLE `t_account_funds_lesson048`
(
    `account_id`  bigint         NOT NULL COMMENT '账户id',
    `balance`     decimal(10, 2) NOT NULL DEFAULT '0.00' COMMENT '余额',
    `frozen`      decimal(10, 2) NOT NULL DEFAULT '0.00' COMMENT '冻结金额',
    `version`     bigint                  DEFAULT '0' COMMENT '版本号，默认为0，每次+1',
    `create_time` datetime(6)             DEFAULT NULL COMMENT '创建时间',
    `update_time` datetime(6)             DEFAULT NULL COMMENT '最后修改时间',
    PRIMARY KEY (`account_id`)
) COMMENT ='账户资金表';
```
## 3.2、账户资金流水表：t_account_funds_data_lesson048
> 记录账户资金的变化，余额和冻结金额发生任何变化，此表都会产生记录
```sql
CREATE TABLE `t_account_funds_data_lesson048`
(
    `id`                               bigint         NOT NULL auto_increment COMMENT '主键',
    `account_id`                       bigint         NOT NULL COMMENT '账号id,t_account_funds.account_id',
    `price`                            decimal(10, 2) NOT NULL DEFAULT '0.00' COMMENT '交易金额',
    `income`                           tinyint        NOT NULL DEFAULT '0' COMMENT '进出标志位，0：账户总金额余额不变，1：账户总金额增加，-1：账户总余额减少 （总金额 = account_funds.balance + account_funds.frozen）',
    `bus_type`                         smallint       NOT NULL COMMENT '交易关联的业务类型',
    `bus_id`                           bigint         NOT NULL COMMENT '交易关联的业务id',
    `before_account_funds_snapshot_id` bigint         NOT NULL COMMENT '本交易前资金快照id，快照是指交易时将（account_funds）当时的记录备份一份',
    `after_account_funds_snapshot_id`  bigint         NOT NULL COMMENT '本交易后资金快照id，快照是指交易后将（account_funds）当时的记录备份一份',
    `create_time`                      datetime(6)             DEFAULT NULL COMMENT '创建时间',
    PRIMARY KEY (`id`)
) COMMENT ='账户资金流水表'
```
## 3.3、账户资金快照表：t_account_funds_snapshot_lesson048
> 这个表是第1个表的一个快照，每条资金流水，这个表会产生2条记录
>
> - 交易前账户资金的快照
> - 交易后账户资金的快照
```sql
CREATE TABLE `t_account_funds_snapshot_lesson048`
(
    `id`          bigint         NOT NULL auto_increment COMMENT '主键',
    `account_id`  bigint         NOT NULL COMMENT '账号id,t_account_funds.account_id',
    `balance`     decimal(10, 2) NOT NULL DEFAULT '0.00' COMMENT '余额',
    `frozen`      decimal(10, 2) NOT NULL DEFAULT '0.00' COMMENT '冻结金额',
    `create_time` datetime(6)             DEFAULT NULL COMMENT '创建时间',
    PRIMARY KEY (`id`)
) COMMENT ='账户资金快照表'
```
# 4、举例说明这3张表如何使用
给用户充值100元，来看下 3 张表数据的变化。
![image-20240614110203385](/blogs/_archive-2024-assets/2eaf8ad3133557175695.webp)
# 5、资金相关操作+代码
## 5.1、资金表相关的操作主要有6个
1. 余额增加 + 生成快照 + 记录流水
   > 总金额（balance+frozen）增加
2. 余额减少 + 生成快照 + 记录流水
   > 总金额（balance+frozen）减少
3. 资金冻结（余额减少、冻结金额增加） + 生成快照 + 记录流水
   > 资金会从余额流向冻结金额中，总金额（balance+frozen）不变
4. 资金解冻（冻结金额减少、余额增加） + 生成快照 + 记录流水
   > 资金会从冻结金额流向余额，总金额（balance+frozen）不变
5. 冻结金额增加 + 生成快照 + 记录流水
   > 总金额（balance+frozen）增加
6. 冻结金额减少 + 生成快照 + 记录流水
   > 总金额（balance+frozen）减少
这几个操作基本可以支撑所有的业务场景。
## 5.2、对应的代码
```java
com.itsoku.lesson048.service.IAccountFundsService
com.itsoku.lesson048.service.impl.AccountFundsServiceImpl
```
如何使用呢？请看下面案例。
# 6、案例演示：余额提现到微信钱包
## 6.1、需要一个提现记录表
```sql
create table if not exists t_cash_out_lesson048
(
    `id`        bigint         NOT NULL auto_increment COMMENT '提现记录id',
    account_id  varchar(32)    not null comment '账号id',
    price       decimal(12, 2) not null comment '提现金额',
    status      smallint       not null comment '状态，0：处理中，1：提现成功，2：提现失败',
    fail_msg    varchar(1000) comment '提现失败原因',
    create_time datetime       not null comment '创建时间',
    update_time datetime comment '最后更新时间',
    PRIMARY KEY (`id`)
) comment '提现记录表';
```
## 6.1、提现到微信钱包-时序图
![](/blogs/_archive-2024-assets/719992e8d07347b89210.webp)
## 6.2、提现案例代码
```
com.itsoku.lesson048.controller.CashOutController
```
主要有2个接口
- 用户发起提现到微信钱包的接口：com.itsoku.lesson048.controller.CashOutController#cashOut
- 给微信提供的回调接口：com.itsoku.lesson048.controller.CashOutController#cashOutCallback
## 6.3、效果演示
### 1）模拟提现成功的场景
#### 用户发起提现10元
```http
### 1、用户发起提现10元
POST http://localhost:8080/cashOut
Accept: application/json
Content-Type: application/json
{
  "accountId": 1,
  "price": "10.00"
}
```
#### 查看表中数据的变化
```sql
-- 提现记录表
select * from t_cash_out_lesson048;
-- 账户资金表
select * from t_account_funds_lesson048;
-- 账户资金流水表
select * from t_account_funds_data_lesson048;
-- 账户资金快照表
select * from t_account_funds_snapshot_lesson048;
```
#### 模拟微信支付-提现成功回调
```http
### 2、模拟微信支付-提现成功回调
POST http://localhost:8080/cashOutCallback
Accept: application/json
Content-Type: application/json
{
  "cashOutId": 1,
  "success": true
}
```
#### 查看表中数据的变化
```sql
-- 提现记录表
select * from t_cash_out_lesson048;
-- 账户资金表
select * from t_account_funds_lesson048;
-- 账户资金流水表
select * from t_account_funds_data_lesson048;
-- 账户资金快照表
select * from t_account_funds_snapshot_lesson048;
```
### 2）模拟提现失败的场景
#### 用户发起提现10元
```http
### 1、用户发起提现10元
POST http://localhost:8080/cashOut
Accept: application/json
Content-Type: application/json
{
  "accountId": 1,
  "price": "10.00"
}
```
#### 查看表中数据的变化
```sql
-- 提现记录表
select * from t_cash_out_lesson048;
-- 账户资金表
select * from t_account_funds_lesson048;
-- 账户资金流水表
select * from t_account_funds_data_lesson048;
-- 账户资金快照表
select * from t_account_funds_snapshot_lesson048;
```
#### 模拟微信支付-提现成功回调
```http
### 3、模拟第三方支付-提现失败回调
POST http://localhost:8080/cashOutCallback
Accept: application/json
Content-Type: application/json
{
  "cashOutId": 2,
  "success": false,
  "failMsg": "账户余额不足"
}
```
#### 查看表中数据的变化
```sql
-- 提现记录表
select * from t_cash_out_lesson048;
-- 账户资金表
select * from t_account_funds_lesson048;
-- 账户资金流水表
select * from t_account_funds_data_lesson048;
-- 账户资金快照表
select * from t_account_funds_snapshot_lesson048;
```
# 7、注意事项
## 7.1、防止余额和冻结金额更新为负数
本案例中，我们使用的是乐观锁解决这个问题的，账户资金表有个version字段。
关键代码
```java
com.itsoku.lesson048.service.impl.AccountFundsServiceImpl#updateFunds
```
