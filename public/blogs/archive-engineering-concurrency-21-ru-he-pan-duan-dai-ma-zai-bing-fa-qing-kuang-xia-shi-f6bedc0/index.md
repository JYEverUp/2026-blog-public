# 如何判断代码在并发情况下会否安全？
## 背景
1、比如我们写了个扣库存的方法，怎么知道此方法在并发情况下，是否会超卖？
2、或者其他一些类似的业务操作，怎么知道他们在并发的情况下，有没有问题？
**这种问题统称为：在并发情况下，如何确定咱们的代码是否和预期的一致**
常用的方法，并发压测，但是有些情况可能不一定好测试，那么我们没有更简单的方法可以验证呢？
本文给大家介绍一种我自己用过的，感觉还不错。
下面通过2个案例，让大家看下这种方法怎么使用。
## 案例1：下面来看一个减库存的操作
### 商品表（t_goods）
| 字段    | 类型 | 说明   |
| ------- | ---- | ------ |
| goodsId | int  | 商品id |
| stock   | int  | 库存   |
### 扣减库存代码
```java
public class Goods{
	//商品id
	String goodsId;
	//库存
	Integer stock;
}
/**
 * 扣减库存
 * @param goodsId 商品id
 * @param num 扣减的数量
 */
@Transaction(rollback=Exception.class)
public void reduceStock(String goodsId,int num){
	//step1:根据商品id查询出商品信息
	Goods goods = select goodsId, stock where t_goods where goodsId = #{goodsId};
	//step2:扣减库存
	goods.stock = goods.stock - num;
	//step3:将商品信息保存到db
	update t_goods set stock = #{goods.stock} where goodsId = #{goodsId};
}
```
### 验证
假设goodsId=1的商品库存是10，下面模拟2个线程同时对这个商品下单，购买的数量都是10
| 时间点 | 步骤  | thread1                                         | thread2                                         |
| ------ | ----- | ----------------------------------------------- | ----------------------------------------------- |
| T1     |       | 入参：（goodsId：1，num：10）                   | 入参：（goodsId：1，num：10）                   |
| T2     | step1 | goodsId：1，stock：10                           | goodsId：1，stock：10                           |
| T3     | step2 | goods.stock = 10-10 = 0                         | goods.stock = 10-10 = 0                         |
| T4     | step3 | update t_goods set stock = 0 where goodsId = 1; | update t_goods set stock = 0 where goodsId = 1; |
| T5     |       | 更新成功，库存变成0了                           | 更新成功，库存变成0了                           |
这样最后两个线程都下单成功了，原本库存是10，但是2个线程共买了20件商品，超卖了。
## 案例2：调整扣减库存的代码
```java
/**
 * 扣减库存
 * @param goodsId 商品id
 * @param num 扣减的数量
 */
@Transaction(rollback=Exception.class)
public void reduceStock(String goodsId,int num){
	//step1:通过sql扣减库存，where中加了个条件 stock-#{num}>=0
	int upCount = (update t_goods 
                   		set stock = stock - #{num}
                   		where 
                   			goodsId = #{goodsId} 
                   			and stock-#{num}>=0);
    //step2
    if(upCount==1){
        //扣减库存成功，执行后续业务代码
    }else{
        //扣减库存失败，抛出异常，让事务回滚
        throw new RuntimeException("库存不足，下单失败");
    }
}
```
### 验证
同样，也是模拟2个线程对商品1同时下单，购买数量都是10
| 时间点 | 步骤  | thread1                                                      | thread2                                                      |
| ------ | ----- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| T1     |       | 入参：（goodsId：1，num：10）                                | 入参：（goodsId：1，num：10）                                |
| T2     |       | spring开启db事务                                             | spring开启db事务                                             |
| T3     | step1 | int upCount = (update t_goods <br/>                   		set stock = stock - 10<br/>                   		where <br/>                   			goodsId = 1 <br/>                   			and stock-10>=0) | int upCount = (update t_goods <br/>                   		set stock = stock - 10<br/>                   		where <br/>                   			goodsId = 1 <br/>                   			and stock-10>=0) |
| T4     | step2 | upCount = 1<br />扣减库存成功                                | upCount = 0<br />throw new RuntimeException("库存不足，下单失败"); |
| T5     |       | spring提交事务                                               | spring回滚事务                                               |
验证通过，和预期一样，没有超卖。
## 总结
上面通过2个案例，介绍了下如何验证代码的并发安全性，有些更复杂的场景可能2个线程还无法验证出来，此时可以横线再加入一些线程来验证。
或者使用第2节介绍的任务批处理工具并行测试下。
# 
