# 第76节 千万级数据，全表update的正确姿势
千万数据全表更新，可能会导致严重的生产事故，本文将带大家分析下，千万级数据更新存在的问题，以及如何解决。
先收藏点赞，慢慢看。
# 1、准备千万数据
## 1）创建测试表
```sql
create table t_demo (
	id bigint auto_increment PRIMARY key,
	c1 bigint
);
```
## 2）插入千万数据
下面对代码会向t_demo表插入1000万数据，可能需要稍等会。
```java
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.SQLException;
public class BatchInsertExample {
    public static void main(String[] args) throws SQLException {
        String jdbcUrl = "jdbc:mysql://localhost:3306/luren?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=true&serverTimezone=GMT%2B8";
        String username = "root";
        String password = "root123";
        Connection connection = null;
        PreparedStatement preparedStatement = null;
        try {
            // 建立数据库连接
            connection = DriverManager.getConnection(jdbcUrl, username, password);
            // SQL插入语句，使用占位符来防止SQL注入
            String sql = "INSERT INTO t_demo(c1) VALUES (?)";
            // 创建PreparedStatement对象，并设置为批处理模式
            preparedStatement = connection.prepareStatement(sql);
            for (int j = 0; j < 2000; j++) {
                connection.setAutoCommit(false); // 设置为手动提交
                long c1 = System.currentTimeMillis();
                // 循环添加多个批处理操作
                for (int i = 0; i < 5000; i++) {
                    // 设置占位符的值
                    preparedStatement.setLong(1, c1 + 1);
                    // 添加到批处理中
                    preparedStatement.addBatch();
                }
                // 执行批处理
                int[] batchResults = preparedStatement.executeBatch();
                System.out.println(batchResults.length);
                // 手动提交事务
                connection.commit();
            }
        } catch (SQLException e) {
            e.printStackTrace();
            // 发生异常时回滚事务
            if (connection != null) {
                connection.rollback();
            }
        } finally {
            // 关闭PreparedStatement和Connection
            if (preparedStatement != null) {
                preparedStatement.close();
            }
            if (connection != null) {
                connection.close();
            }
        }
    }
}
```
## 3）千万数据准备完毕
```java
mysql> select count(*) from t_demo;
+----------+
| count(*) |
+----------+
| 10075001 |
+----------+
1 row in set (1.92 sec)
```
# 2、千万数据全表更新存在的问题
## 1）影响系统性能
- **执行时间长**：全表更新是一个极其耗时的操作，因为数据库需要遍历表中的每一条记录并进行更新，对于千万级的数据表，这个过程可能需要数小时甚至更长时间
- **资源消耗大**：全表更新会大量消耗数据库服务器的CPU、内存和I/O资源，导致服务器性能下降，可能影响其他数据库操作的响应时间和吞吐量
- **锁表问题**：在更新过程中，数据库可能会对表进行锁定，以防止数据不一致，这会导致其他用户或进程无法访问该表，从而影响业务的正常运行
## 2）导致主从同步延迟严重
全表更新会一次性在主库上产生大量binlog日志，而主从同步是依靠binlog来完成的，此时就会导致主从同步延迟特别严重。
比如系统采用了读写分离，某个用户在界面上更新了一个数据，操作完成后，去另外一个页面查看操作结果，而这个页面的数据是从从库获取的，由于主从延迟严重，用户此时看到的结果和期望的不一致，会感觉莫名其妙。
## 3）可能导致系统崩溃
更新过程中会导致锁表，此时如果有大量其他请求也去更新此表的数据，都会被阻塞，进而可能会耗光tomcat的线程，导致系统无法继续对外提供服务，引起连锁反应，导致整个系统崩溃。
# 4、演示下全表更新：会锁表，耗时特别久
### 窗口1中
全表更新千万数据，此操作执行过程中，会对整个表的数据上锁
```sql
update t_demo set c1 = c1 + 1;
```
### 窗口2中
按主键更新1条数据，由于窗口1中对全表上锁了，窗口2中这个操作会被阻塞
```sql
update t_demo set c1 = c1+1 where id = 1;
```
![image-20240820111023625](/blogs/_archive-2024-assets/c61b571ff5b4c3d7775e.webp)
# 5、正确的更新姿势
```java
//获取表中最小的id
long minId = select min(id) from t_demo;
//循环批量更新数据
while(true){
	//查询出1000条需要更新的记录的id，注意查询条件(id>=#{minId})，这个查询会走主键索引，查询会特别快，毫秒级别
	List<Long> idList = select id from t_demo where id>=#{minId} limit 1000;
	//如果数据为空，说明没有需要更新的数据了，跳出循环
	if(idList为空){
		break;
	}
	//根据id批量更新数据,这里更新1000条数据，也会非常快，事务也很小，也是毫秒级别
	update t_demo set 更新的字段 where id in (#{idList[0]},#{idList[1]},...,#{idList[n]});
	//minId = idList最后一条记录的id
	minId = idList.get(idList.size()-1);
}
```
