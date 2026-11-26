#  MyBatisPlus 轻松实现多租户数据隔离

# 1、本文主要内容
使用MybatisPlus实现多租户数据隔离。
# 2、什么是多租户系统？
比如我们开发了一个 WEB 版的 CRM 系统，部署在网上，任何公司都可以使用，那么这个系统就相当于一个多租户系统，每个公司相当于一个租户，系统中每个租户的数据是需要隔离的。
# 3、多租户系统数据隔离有3种方案
1. 每个租户一个数据库
2. 所有租户共用同一个数据库，通过租户id隔离，也就是表里面需要有个租户id（tenant_id）字段，操作租户数据的时候，sql中都需要带上租户id
3. 上面2种方案的混合体，比如有1000个租户，每100个租户共用一个数据库，表里面也需要用租户id进行隔离
本文将采用第2种方案，也就是所有租户共用一个数据库，表中的数据通过租户id进行隔离。
# 4、使用MyBatis-plus实现数据隔离
MyBatis-plus 本身已经帮我们提供了多租户数据隔离的功能。
**这里简单说下原理**：当我们通过mybatisplus对数据库执行sql的时候，mybatisplus会拦截sql的执行，对sql进行改写，自动在sql上追加加上租户id，这样就实现了多租户数据隔离的功能。
# 5、效果演示
## 5.1、查询租户1所有用户
```http
### 获取租户 1 所有用户
GET http://localhost:8080/user/list
Content-Type: application/json
tenant_id: 1
```
## 5.2、创建用户，租户id是：1
```http
### 创建用户，租户id是：1
POST http://localhost:8080/user/insert
Content-Type: application/x-www-form-urlencoded
Content-Type: application/json
tenant_id: 1
userName=luren
```
# 6、源码解析
# 7、总结一下，主要就 3 个步骤
1. 请求头中传递租户id
2. 添加一个全局拦截器，将租户id读取出来，放到ThreadLocal中
3. 添加一个mybatisplus多租户的拦截器：TenantLineInnerInterceptor，这个拦截器需要用到一个 TenantLineHandler 对象：自定义一个类实现TenantLineHandler接口，实现getTenantId方法，从step2中的ThreadLocal中拿到租户id，作为这个方法的返回值
