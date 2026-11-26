#  分库分表-如何平滑迁移数据？
非常实用的一节，内容有点多，先收藏点赞，慢慢看。
# 1、背景
假如我们做了一个电商系统，刚开始只有一个订单表，后面由于业务量暴增，单表数据量太多遇到性能瓶颈，需要对订单表进行分表来缓解压力
比如1个表扩容成32张表，扩容中需要考虑一个非常关键的问题：数据迁移
# 2、扩容：如何做数据迁移？
主要有3种方案
1. 停机迁移数据
2. 不停机+操作日志法，平滑迁移数据
3. 不停机+双写法，平滑迁移数据
下面对这3种方案进行详解。
# 3、方案1：停机-数据迁移
1. 发布停机升级公告
2. 开发数据迁移工具，将旧表数据迁移到新表
3. 开发数据校验工具，确保新表和旧表数据是一致的
4. 升级系统，所有业务逻辑使用新表
5. 升级完毕，对外提供服务
# 4、方案2：不停机+操作日志法，平滑迁移数据
## step1：升级代码，记录旧表操作日志，发布上线
对代码进行升级，需要创建一张操作日志表(t_order_log)，对旧表中任意记录的增删改（insert、delete、update）操作，都需要写一条记录到操作日志表，这个日志主要是记录旧表中哪些数据发生了变化
日志表主要有2个字段，如下，这里并不需要记录具体是什么操作，只需要知道哪条数据发生了变化就可以了
- log_id：主键id，自动增长
- order_id：当前操作的订单id
此时依旧是旧表对外提供服务
## step2：将旧表所有数据迁移到新表
开发一个数据迁移程序，将旧表的所有数据，迁移到新表，伪代码如下
```java
// 查询旧订单表：最小订单id
int minOrderId = select min(order_id) from t_order_old;
minOrderId = minOrderId - 1;
//循环将旧表订单数据，迁移到新表，按照订单号升序的方式，依次进行迁移
while(true){
	// 从旧表中获取一批订单，将其迁移到新表
	List<Order> oldOrderList = select * from 旧订单表 where order_id > #{minOrderId} limit 100 order by order_id asc;
    // 若没有数据，直接退出
    if(oldOrderList.isEmpty()){
        break;
    }
	//将 orderList 写入新表
	for(Order oldOrder in oldOrderList){
		//将旧表订单记录写入新表
		insert 新订单表 values (订单信息oldOrder);
	}
	// 将minOrderId设置为oldOrderList最后一条记录的订单id
	minOrderId = oldOrderList.get(oldOrderList.size() - 1).orderId;
}
```
## step3：新表中重放旧表操作日志
step2执行的过程中，系统依旧在运行，所有操作依旧是在旧的订单表上，这个过程中，旧表的数据会发生变化，所有发生变化的记录都会被记录在step1中的日志表中
此时只需在新表上重放所有操作日志就可以了，便可将发生变化的旧记录同步到新表中，处理逻辑如下
```java
// 查询日志表：最小操作日志
int minLogId = select min(log_id) from t_order_log;
minLogId = minLogId - 1;
// 将日志在新的订单表进行重放
while(true){
	// 从日志表拉取一批数据（按日志id升序拉取大于 minLogId 的100条记录），在新的订单表进行处理
	List<OrderLog> logList = select log_id as logId, order_id as orderId from 操作日志表t_order_log where log_id > #{minLogId} limit 100 order by log_id asc;
    // 若没有数据，可以休眠一会继续，休眠这个过程中，可能有新的日志进来了
    if(logList.isEmpty()){
        //比如：休眠1秒
		sleep(1000);
    }
	//将 logList 写入新表
	for(OrderLog log in logList){
		//根据日志记录中的订单id，去旧表查询订单记录
        Order oldOrder = select * from 旧订单表 where order_id = #{log.orderId};
        //旧表订单记录不存在，说明被删除了
        if(oldOrder==null){
            //将订单从新表删除
            delete from 新订单表 where order_id = #{log.orderId};
        }else{
        	//更新操作相当于 delete + insert
            //先将订单从新表删除
            delete from 新订单表 where order_id = #{log.orderId};
            //将订单记录重新写入新表
            insert 新订单表 values (订单信息oldOrder);
        }
		//将日志从日志表删除
        delete from t_order_log where log_id = #{log.logId};
	}
	// 将minLogId设置为logList最后一条记录的id
	minLogId = logList.get(logList.size() - 1).logId;
}
```
日志重放的过程中，线上业务一直在执行，又会产生新的操作日志，这样会出现一个问题，新表的数据永远无法和旧表完全一致，只能是无限接近；在某个时刻，日志全部被处理或者近乎处理完毕时，立即进入step4
## step4：禁止旧订单表写入数据（包括：insert、delete、update）
可以在程序中或者在db层，禁止旧的订单表写入数据（insert、delete、update）
然后将日志中的记录在新表重放完毕，此时新表和旧表数据完全一致，然后进入step5
## step5：通过开关将流量切到新表
step1中升级的代码中，要包含兼容新表的代码，但是在step1发布上线时，这个功能可以通过一个开关控制着，属于关闭状态
此时，两边数据一致了，将开关打开，会执行新的代码，所有订单请求将被路由到新表，完成迁移
# 5、方案3：不停机+双写，平滑迁移数据
## step1：升级程序，开启双写
对旧表任何写操作（包含insert、delete、update），同时也要在新表执行同样的操作
> insert 操作，2边都会成功
>
> delete操作，旧表成功，新表中数据有可能不存在，执行delete也没关系
>
> update操作，旧表更新成功，被更新的记录可能在新表不存在，也没关系
此时依旧是旧表对外提供服务。
## step2：将旧表所有数据迁移到新表
开发一个数据迁移程序，将旧表的所有数据，迁移到新表，伪代码如下
```java
// 旧订单表：最小订单id
int minOrderId = select min(order_id) from t_order_old;
minOrderId = minOrderId - 1;
//循环将旧表订单数据，迁移到新表，按照订单号升序的方式，依次进行迁移
while(true){
	// 从旧表中获取一批订单，将其迁移到新表
	List<Order> orderList = select * from 旧订单表 where order_id > #{minOrderId} limit 100 order by order_id asc;
    // 若没有数据，直接退出
    if(orderList.isEmpty()){
        break;
    }
	//将 orderList 写入新表
	for(Order order in orderList){
        开启事务;
        //从旧表读取订单记录，需要对旧的订单记录进行上锁，避免在同步当前记录的时候，旧数据被修改，导致同步到新表的数据和旧表不一致，这里使用for update对旧记录上锁，此时其他线程是无法修改当前旧的订单记录
        Order oldOrder = select * from 旧订单表 where order_id = #{order.orderId} for update;
        //订单记录可能在新表已经存在了，不管是否存在，都可以通过 delete + insert 解决
 		//先将订单从新表删除
        delete from 新订单表 where order_id = #{log.orderId};
        //将oldOrder写入新表
		insert 新的订单表 values (订单信息oldOrder);
        提交事务;
	}
	// 将minOrderId设置为orderList最后一条记录的id
	minOrderId = orderList.get(orderList.size() - 1).orderId;
}
```
这里面有个关键点，大伙需要注意，将某一条旧的订单记录同步到新的表，有2个步骤
1. 第1步查询旧的记录
2. 第2步将旧的记录插入新表
这个过程中容易出问题：假如刚好第1步执行后，第2步还未执行时，旧表的数据被某个请求修改了，那么此时同步到新表的数据和旧表数据会出现不一致，为了避免这个问题，上面从旧表查询数据的时候，使用了`for update`对旧的记录进行加锁，可确保事务提交前被加锁(for update)的记录是无法被其他线程修改。
## step3：校验两边数据一致性
需开发一套程序，对新表和旧表数据一致性进行校验，看下两边订单记录的数据是否是一致的，若不一致，则找到原因进行修复，重新同步。
若没有问题，进入step4
## step4：将流量切换到新表
可以在程序中通过开关控制，停止旧表对外提供服务，开启新表对外提供服务。
# 6、总结
本文给大家介绍了3种数据迁移的方案，大家可以根据业务需求进行选择。
