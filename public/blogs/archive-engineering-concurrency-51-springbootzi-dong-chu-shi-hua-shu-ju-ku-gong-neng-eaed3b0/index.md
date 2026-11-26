#  SpringBoot中自动初始化数据库功能，太好用了
# 背景
大部分系统都会用到数据库，这就涉及系统发布前数据库初始化的一些操作。
通常的做法是：
1. 提申请让dba去执行数据库脚本
2. 数据库脚本执行完成后，由运维发布应用
# 有没有更简单的方法呢？
比如我们把数据库的初始化脚本写在程序中某个文件中，系统启动的时候去自动执行这个文件，是不是会方便很多？
SpringBoot已经帮我们提供了这个功能，来看下如何使用。
# 效果演示
# 详细使用步骤
## 1、配置数据源
- 在`application.yml`或`application.properties`文件中配置数据库连接信息，包括URL、用户名、密码等。
- 例如，在`application.yml`中：
  ```yaml
  spring:  
    datasource:  
      driver-class-name: com.mysql.cj.jdbc.Driver  
      url: jdbc:mysql://localhost:3306/your_database?useUnicode=true&characterEncoding=utf-8&useSSL=false&serverTimezone=UTC  
      username: your_username  
      password: your_password
  ```
## 2、配置SQL脚本位置
- 在配置文件中指定SQL脚本的位置，Spring Boot在启动时会自动执行这些脚本。
- 可以通过`schema-locations`和`data-locations`属性来指定模式脚本和数据脚本的位置。
- 例如：
  ```yaml
  spring:  
    sql:
      init:
        # 数据库ddl脚本位置
        schema-locations: classpath:db/schema.sql
        # 数据库dml脚本位置
        data-locations: classpath:db/data.sql
        # always：应用每次启动都执行，never：禁用
        mode: always
  ```
## 3、编写SQL脚本
在指定的位置（如`src/main/resources/db/`）下创建SQL脚本文件，如`schema.sql`里面写数据库的ddl脚本，`data.sql`中写dml脚本
## 4、启动Spring Boot应用
启动Spring Boot应用时，它会自动读取配置，连接到数据库，并执行指定的SQL脚本。
# 原理
SpringBoot自动装配功能实现的，源码在下面这个自动配置类中
```java
org.springframework.boot.autoconfigure.sql.init.SqlInitializationAutoConfiguration
```
最终执行脚本是由下面这个方法负责的
```java
org.springframework.boot.sql.init.AbstractScriptDatabaseInitializer#afterPropertiesSet
```
