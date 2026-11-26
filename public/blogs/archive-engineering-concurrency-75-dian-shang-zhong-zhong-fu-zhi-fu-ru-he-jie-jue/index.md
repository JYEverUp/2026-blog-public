# 第75节 电商中，重复支付如何解决？
本篇是一个场景题，工作中也可能会遇到，先收藏点赞，慢慢看。
# 1、什么是重复支付
同一笔订单，用户付了两次款，且两次都成功了
# 2、重复支付演示
美团外面APP，可以重现这个问题，流程如下：
1. 准备2部手机，手机1、手机2
2. 2部手机登录同一个美团账号
3. 手机1：随便找一个店铺，下一笔订单，将订单提交，先别支付，此时订单待支付
4. 手机1：对这笔订单，发起微信支付，此时会跳转到微信，先别支付
5. 手机2：也能看到这笔订单，对这笔订单发起支付宝支付，此时会跳转到支付宝，然后输入支付密码，支付成功
6. 回到手机1：输入微信支付密码，支付成功
此时就出现了同一笔订单，成功支付了2次，一次微信支付、一次支付宝支付；不过稍后会收到美团的一笔退款
# 3、出现重复支付，怎么处理？
支付，涉及到和第三方支付进行交互，里面涉及到网络问题，数据一致性的问题，单靠商户端很难避免重复支付，大部分app是允许重复支付发生的。
那我们只需要考虑，若出现了重复支付的问题，怎么解决就可以了。
比如去包子店买包子，用手机支付了2次，那么只需要和老板核对下，老板确认后，会将第二笔支付金额退还给我们。
同样，电商系统也可以借鉴这个思路，当订单出现重复支付的时，只保留第一笔成功的支付记录，其他支付成功的记录原路退回给用户就可以了。
# 4、代码应该如何落地？
## 4.1、需要2张表
一张订单表，一张订单支付记录表，他们是一对多的关系，一个订单可能有多条支付记录，下面来看下这2张表，这里只列出关键的一些字段。
## 4.2、订单表（t_order）
- id：订单
- price：订单金额
- status：0：待支付；100：已支付
用户下单的时候，会向这张表写入一条数据，状态为`待支付`
## 4.3、订单支付记录表（t_order_pay)
- id：支付记录
- order_id：订单id，指向（t_order表中的id）
- price：支付金额
- status：状态，0：支付中，100：支付成功，200：退款中，300：退款成功
当用户对某一笔订单进行支付的时候，会向该表插入一条记录，状态为`支付中`
## 4.4、支付流程
先带大家熟悉下支付流程，熟悉后，解决重复支付就很容易了。
![](/blogs/_archive-2024-assets/a3ca95f5cccf1fb19f62.webp)
## 4.5、处理支付回调：含重复支付处理
下面是支付回调的伪代码，里面包含了重复支付的处理，对于重复支付，只保留第一笔成功的支付记录，其他的成功支付记录将原路退款
```java
/**
 * outOrderNo：电商这边订单支付记录id
 * paySuccess：支付结果，true：支付成功，false：支付失败
 **/
public boolean payCallBack(String outOrderNo, boolean paySuccess) {
    //1、先根据outOrderNo找到支付记录
    OrderPay orderPay = select * from t_order_pay where id = #{outOrderNo} ;
    //2、若支付订单不是待支付，说明已处理过了
    if (orderPay != 待支付) {
        return true;
    }
    //3、为了避免并发问题，这里对同一笔订单加分布式锁，确保同一笔订单，并发收到多个通知时，排队执行
    String orderId = orderPay.orderId;
    distributeLock.lock("order-" + orderId);
    try {
        //4、支付失败
        if (!paySuccess) {
            //将支付订单改成支付失败状态
            update t_order_pay set status = 支付失败 where id = #{outOrderNo} ;
            return true;
        }
        /**
         *支付成功的逻辑，如下
         **/
        //5、根据订单id，查询成功的支付记录
        OrderPay successOrderPay = select * from t_order_pay where id = #{orderId} and status = 支付成功 limit 1;
        //6、不存在成功的记录，说明还未成功支付过
        if (successOrderPay == null) {
            //6.1、则将outOrderNo这笔支付记录置为支付成功
            update t_order_pay set status = 支付成功 where id = #{outOrderNo} ;
            //6.2、将关联的订单状态支付支付成功
            update t_order set status = 支付成功 where id = #{orderId} ;
            return true;
        }
        //7、若存在已支付成功的记录，且id和outOrderNo不一样，说明重复支付了，则要对outOrderNo这边支付记录发起退款
        if (!successOrderPay.id.equals(outOrderNo)) {
            //7.1、对outOrderNo这笔支付记录发起退款，状态置为：退款中
            update t_order_pay set status = 退款中 where id = #{outOrderNo} ;
            //7.2、调用微信支付发起退款，这里需要注意，退款结果可能是异步的
            发起微信退款，原路退款;
            //7.3、将outOrderNo这笔支付记录，状态置为：退款成功
            update t_order_pay set status = 退款成功 where id = #{outOrderNo} ;
            return ture;
        }
    } finally {
        //8、释放分布式锁
        distributeLock.unlock();
    }
    //返回成功
    return ture;
}
```
# 5、总结
重复支付，极端情况下，难以避免，推荐的做法是：出现这种问题后，将资金原路返回到用户的支付账户，就可以了
不管是依靠人工处理还是程序自动处理，都可以。
