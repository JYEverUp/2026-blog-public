# 第96节 订单状态流转，代码优化，太优雅了

# 1、背景
电商系统中，订单属于比较核心的功能；
本文会带大家看下订单状态流转这块的功能是如何实现的
顺便会对其进行优化，学完后应该可以收获不少。
# 2、订单状态图
![image-20240913152302091](/blogs/_archive-2024-assets/a27f2458e7c749c08327.webp)
# 3、订单状态流转代码：第一个版本
```java
public class OrderService {
    /**
     * 订单支付
     *
     * @param orderModel
     */
    public void pay(OrderModel orderModel) {
        //验证订单状态，订单当前状态必须是待支付状态，即新创建的订单
        if (!Objects.equals(orderModel.getStatus(), OrderStatus.INIT.getStatus())) {
            throw new RuntimeException("订单状态不支持当前操作");
        }
        //将订单状态置为已支付状态
        OrderStatus toStatus = OrderStatus.PAID;
        orderModel.setStatus(toStatus.getStatus());
        //todo: 其他操作，比如将订单数据保存到db
    }
    /**
     * 卖家发货
     *
     * @param orderModel
     */
    public void ship(OrderModel orderModel) {
        //验证订单状态，订单当前状态必须是已支付状态
        if (!Objects.equals(orderModel.getStatus(), OrderStatus.PAID.getStatus())) {
            throw new RuntimeException("订单状态不支持当前操作");
        }
        //将订单状态置为已发货状态
        OrderStatus toStatus = OrderStatus.SHIPPED;
        orderModel.setStatus(toStatus.getStatus());
        //todo: 其他操作，比如将订单数据保存到db
    }
    /**
     * 买家确认收货
     *
     * @param orderModel
     */
    public void deliver(OrderModel orderModel) {
        //验证订单状态，订单当前状态必须是已支付状态
        if (!Objects.equals(orderModel.getStatus(), OrderStatus.PAID.getStatus())) {
            throw new RuntimeException("订单状态不支持当前操作");
        }
        //将订单状态置为已完成状态
        OrderStatus toStatus = OrderStatus.FINISHED;
        orderModel.setStatus(toStatus.getStatus());
        //todo: 其他操作，比如将订单数据保存到db
    }
}
```
每个方法里面，都有订单状态校验的代码，校验订单当前状态是否支持当前操作，如果不支持则抛出异常；验证通过后，将订单状态置为下一个状态。
这个代码大家感觉如何？
下面我们来看另外一个版本，优化后的。
# 4、优化后的版本
```java
public class OrderServiceNew {
    /**
     * 订单状态转换列表，相当于订单的状态图存储在这个列表中了，
     * 列表中每条记录对应状态图中一个流转步骤，（OrderStatusTransition：表述一个流转步骤，由（fromStatus、action、toStatus）组合而成）
     */
    public static List<OrderStatusTransition> orderStatusTransitionList = new ArrayList<>();
    static {
        //下面根据订单状态图，将订单流转步骤添加到 orderStatusTransitionList 中
        // 待支付 -- 支付 -->已支付
        orderStatusTransitionList.add(OrderStatusTransition.builder()
                .fromStatus(OrderStatus.INIT)
                .action(OrderStatusChangeAction.PAY)
                .toStatus(OrderStatus.PAID).build());
        // 已支付 -- 发货 -->已发货
        orderStatusTransitionList.add(OrderStatusTransition.builder()
                .fromStatus(OrderStatus.PAID)
                .action(OrderStatusChangeAction.SHIP)
                .toStatus(OrderStatus.SHIPPED).build());
        // 已发货 -- 买家收货 -->完成
        orderStatusTransitionList.add(OrderStatusTransition.builder()
                .fromStatus(OrderStatus.SHIPPED)
                .action(OrderStatusChangeAction.DELIVER)
                .toStatus(OrderStatus.FINISHED).build());
    }
    /**
     * 触发订单状态转换
     *
     * @param orderModel 订单
     * @param action     动作
     */
    private void statusTransition(OrderModel orderModel, OrderStatusChangeAction action) {
        //根据订单当前状态 & 动作，去 orderStatusTransitionList 中找，可以找到对应的记录，说明当前操作是允许的；否则抛出异常
        OrderStatus fromStatus = OrderStatus.get(orderModel.getStatus());
        Optional<OrderStatusTransition> first = orderStatusTransitionList.stream().
                filter(orderStatusTransition -> orderStatusTransition.getFromStatus().equals(fromStatus) && orderStatusTransition.getAction().equals(action))
                .findFirst();
        if (!first.isPresent()) {
            throw new RuntimeException("订单状态不支持当前操作");
        }
        OrderStatusTransition orderStatusTransition = first.get();
        //切换订单状态
        orderModel.setStatus(orderStatusTransition.getToStatus().getStatus());
    }
    /**
     * 订单支付
     *
     * @param orderModel
     */
    public void pay(OrderModel orderModel) {
        // 订单状态转换
        this.statusTransition(orderModel, OrderStatusChangeAction.PAY);
        //todo: 其他操作，比如将订单数据保存到db
    }
    /**
     * 卖家发货
     *
     * @param orderModel
     */
    public void ship(OrderModel orderModel) {
        // 订单状态转换
        this.statusTransition(orderModel, OrderStatusChangeAction.SHIP);
        //todo: 其他操作，比如将订单数据保存到db
    }
    /**
     * 买家确认收货
     *
     * @param orderModel
     */
    public void deliver(OrderModel orderModel) {
        // 订单状态转换
        this.statusTransition(orderModel, OrderStatusChangeAction.DELIVER);
        //todo: 其他操作，比如将订单数据保存到db
    }
}
```
这种写法将订单状态流转集中处理，方便管理和维护。
测试看下效果。
