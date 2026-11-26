# 第93节 涉及到钱的，千万不要用double，请用BigDecimal

# 1、金融系统不要用double，会有精度问题
```java
@Test
public void m1() {
    double a = 4.015, b = 100.00;
    System.out.println(a * b);  // 期望结果：401.5
    double c = 123.30, d = 100.00;
    System.out.println(c / d); //期望结果：1.233
}
```
运行输出如下
```
401.49999999999994
1.2329999999999999
```
和期望的结果不太一致。
# 2、原因
是由于计算机存储double类型数据的时候，会产生精度问题；float类型同样也有精度问题。
具体底层原理，大家可以查阅相关资料了解。
如何解决这个问题呢？
# 3、使用BigDecimal，可解决问题
java为我们提供了一个类：BigDecimal，可以用来解决double、float这种浮点数的精度问题。
代码如下
```java
@Test
public void m2() {
    BigDecimal a = new BigDecimal("4.015");
    BigDecimal b = new BigDecimal("100.00");
    System.out.println(a.multiply(b));
    BigDecimal c = new BigDecimal("123.30");
    BigDecimal d = new BigDecimal("100.00");
    System.out.println(c.divide(d));
}
```
运行输出
```java
401.50000
1.233
```
# 4、如何构造BigDecimal对象 ？
## 正确做法
**请使用字符串来构造BigDecimal对象，如下**
```java
BigDecimal bd = new BigDecimal("0.1");  
```
## 错误做法
下面这种，使用double类型的参数构造BigDecimal，会有精度问题，**不要使用**
```java
BigDecimal bd = new BigDecimal(0.1);  
```
# 5、BigDecimal对象如何比较大小？
需要用使用BigDecimal中的compareTo方法，如下，需传入另外一个BigDecimal对象，和当前对象比较大小
```java
public int compareTo(BigDecimal val);
```
返回值有3种情况
- -1：小于
- 0：相等
- 1：大于
案例
```java
@Test
public void m3() {
    System.out.println(new BigDecimal("0.1").compareTo(new BigDecimal("0.2")));
    System.out.println(new BigDecimal("0.2").compareTo(new BigDecimal("0.1")));
    System.out.println(new BigDecimal("0.123").compareTo(new BigDecimal("0.123000000")));
}
```
输出
```java
-1
1
0
```
# 6、BigDecimal保留到分，如何处理？
BigDecimal计算出的结果，小数位可能很长，此时就需要考虑保留几位小数，如何舍掉后面的位数。
金融系统中通常会将计算的结果采用四舍五入，保留到分，即2位小数，处理如下
```java
@Test
public void m4() {
    System.out.println(new BigDecimal("0.12345678").setScale(2, BigDecimal.ROUND_HALF_UP));
    System.out.println(new BigDecimal("0.45678910").setScale(2, BigDecimal.ROUND_HALF_UP));
}
```
输出
```java
0.12
0.46
```
# 7、数据库中对应的类型：decimal
BigDecimal中在db中也有对应的类型，MySQL中对应decimal类型，如下，保留2位小数，具体保留几位小数，大家可以根据业务来决定。
```java
decimal(18,2)
```
# 8、给大家提供一个BigDecimal工具类
下面这个类，是我在做金融系统的时候，写的一个，大家直接拿去用，包含了数据常见的各种方法。
```java
package com.itsoku.lesson093;
import java.math.BigDecimal;
import java.text.DecimalFormat;
/**
 * <b>description</b>实战
 * <b>time</b>：2024/9/10 23:21 <br>
 * <b>author</b>：gjy
 */
public class BigDecimalUtils {
    /**
     * 除法默认保留精度
     */
    private static final int DEF_DIV_SCALE = 10;
    /**
     * 默认舍入模式（ROUND_HALF_UP：四舍五入）
     */
    private static final int DEF_ROUNDING_MODE = BigDecimal.ROUND_HALF_UP;
    private static final String FORMAT_1 = "#.##";
    /**
     * 将字符串转换为 BigDecimal
     *
     * @param value
     * @return
     */
    public static BigDecimal of(String value) {
        return value == null ? null : new BigDecimal(value);
    }
    /**
     * v1 + v2
     *
     * @param v1 被加数
     * @param v2 加数
     * @return 两个参数的和
     */
    public static BigDecimal add(BigDecimal v1, BigDecimal v2) {
        return v1.add(v2);
    }
    /**
     * args[0] + args[1] + ... + args[n]
     *
     * @param args
     * @return
     */
    public static BigDecimal add(BigDecimal... args) {
        if (args == null || args.length <= 1) {
            throw new IllegalArgumentException("args Contains at least two parameters");
        }
        BigDecimal result = args[0];
        for (int i = 1; i < args.length; i++) {
            result = add(result, args[i]);
        }
        return result;
    }
    /**
     * v1 - v2
     *
     * @param v1 被加数
     * @param v2 加数
     * @return 两个参数的和
     */
    public static BigDecimal subtract(BigDecimal v1, BigDecimal v2) {
        return v1.subtract(v2);
    }
    /**
     * args[0] - args[1] - ... - args[n]
     *
     * @param args
     * @return
     */
    public static BigDecimal subtract(BigDecimal... args) {
        if (args == null || args.length <= 1) {
            throw new IllegalArgumentException("args Contains at least two parameters");
        }
        BigDecimal result = args[0];
        for (int i = 1; i < args.length; i++) {
            result = subtract(result, args[i]);
        }
        return result;
    }
    /**
     * v1 * v2
     *
     * @param v1 被乘数
     * @param v2 乘数
     * @return 两个参数的积
     */
    public static BigDecimal multiply(BigDecimal v1, BigDecimal v2) {
        return v1.multiply(v2);
    }
    /**
     * args[0] * args[1] * ... * args[n]
     *
     * @return 两个参数的积
     */
    public static BigDecimal multiply(BigDecimal... args) {
        if (args == null || args.length <= 1) {
            throw new IllegalArgumentException("args Contains at least two parameters");
        }
        BigDecimal result = args[0];
        for (int i = 1; i < args.length; i++) {
            result = multiply(result, args[i]);
        }
        return result;
    }
    /**
     * v1 / v2
     *
     * @param v1 被乘数
     * @param v2 乘数
     * @return 两个参数的积
     */
    public static BigDecimal divide(BigDecimal v1, BigDecimal v2) {
        return v1.divide(v2, DEF_DIV_SCALE, DEF_ROUNDING_MODE);
    }
    /**
     * args[0] / args[1] / ... / args[n]
     *
     * @return 两个参数的积
     */
    public static BigDecimal divide(BigDecimal... args) {
        if (args == null || args.length <= 1) {
            throw new IllegalArgumentException("args Contains at least two parameters");
        }
        BigDecimal result = args[0];
        for (int i = 1; i < args.length; i++) {
            result = divide(result, args[i]);
        }
        return result;
    }
    /**
     * 四舍五入，保留两位小数
     *
     * @param d
     * @return
     */
    public static BigDecimal round(BigDecimal d) {
        if (d == null) {
            return null;
        }
        return d.setScale(2, BigDecimal.ROUND_HALF_UP);
    }
    /**
     * v1>v2?
     *
     * @param v1
     * @param v2
     * @return
     */
    public static boolean gt(BigDecimal v1, BigDecimal v2) {
        return v1.compareTo(v2) > 0;
    }
    /**
     * v1 == v2
     *
     * @param v1
     * @param v2
     * @return
     */
    public static boolean eq(BigDecimal v1, BigDecimal v2) {
        return v1.compareTo(v2) == 0;
    }
    /**
     * 判断 values 是否等于 0？
     *
     * @param value
     * @return
     */
    public static boolean eq0(BigDecimal value) {
        return BigDecimal.ZERO.compareTo(value) == 0;
    }
    /**
     * v1>=v2?
     *
     * @param v1
     * @param v2
     * @return
     */
    public static boolean ge(BigDecimal v1, BigDecimal v2) {
        return v1.compareTo(v2) >= 0;
    }
    /**
     * v1<v2?
     *
     * @param v1
     * @param v2
     * @return
     */
    public static boolean lt(BigDecimal v1, BigDecimal v2) {
        return v1.compareTo(v2) < 0;
    }
    /**
     * 格式化，保留2为小数
     *
     * @param value
     * @return
     */
    public static String format(BigDecimal value) {
        if (value == null) {
            return null;
        }
        DecimalFormat df = new DecimalFormat(FORMAT_1);
        return df.format(value);
    }
    /**
     * 格式化
     *
     * @param value
     * @param pattern 模式字符串，如：#.##
     * @return
     */
    public static String format(BigDecimal value, String pattern) {
        if (value == null) {
            return null;
        }
        DecimalFormat df = new DecimalFormat(pattern);
        return df.format(value);
    }
}
```
案例代码
```java
@Test
public void m5() {
    //1、通过字符串构造 BigDecimal
    System.out.println(BigDecimalUtils.of("0.123"));
    //2、加法
    System.out.println(BigDecimalUtils.add(new BigDecimal("0.111"), new BigDecimal("0.123")));
    //3、减法
    System.out.println(BigDecimalUtils.subtract(new BigDecimal("0.111"), new BigDecimal("0.123")));
    //4、乘法
    System.out.println(BigDecimalUtils.multiply(new BigDecimal("0.111"), new BigDecimal("0.123")));
    //5、除法
    System.out.println(BigDecimalUtils.divide(new BigDecimal("0.111"), new BigDecimal("0.123")));
    //6、四舍五入，结果保留2位小数，金融系统中通常会将计算的结果保留到分，此时就可以用这个方法
    System.out.println(BigDecimalUtils.round(BigDecimalUtils.divide(new BigDecimal("0.111"), new BigDecimal("0.123"))));
    //7、判断 v1<v2?
    BigDecimal v1 = new BigDecimal("0.111");
    BigDecimal v2 = new BigDecimal("0.123");
    System.out.println(BigDecimalUtils.lt(v1, v2));
    //8、判断2个数是否相等 0.111 == 0.11100000000，相等
    System.out.println(BigDecimalUtils.eq(v1, new BigDecimal("0.11100000000"))); // true
    //9、判断是否等于0
    System.out.println(BigDecimalUtils.eq0(new BigDecimal("0")));  // true
    System.out.println(BigDecimalUtils.eq0(new BigDecimal("0.000"))); // ture
    System.out.println(BigDecimalUtils.eq0(new BigDecimal("0.001"))); // false
    //10、格式化
    System.out.println(BigDecimalUtils.format(BigDecimalUtils.of("123.45678"))); // 123.46
}
```
运行输出
```java
0.123
0.234
-0.012
0.013653
0.9024390244
0.90
true
true
true
true
false
123.46
```
# 9、其他知识点
## 1）接口中，资金直接使用BigDecimal类型
```java
@RequestMapping("/transfer")
public ResultDto<Boolean> transfer(@RequestBody TransferRequest request){
}
@Data
public class TransferRequest {
    //付款人账户id
    private String fromAccountId;
    //收款人账号id
    private String toAccountId;
    //转账金额
    private BigDecimal transferPrice;
}
```
## 2）PO中也使用BigDecimal类型
```sql
create table if not exists t_account
(
    id      varchar(32)    not null primary key comment '用户id',
    balance decimal(12, 2) not null comment '账户余额',
) comment '账户表';
```
对应的po如下，balance用的是BigDecimal类型
```java
@Data
public class AccountPO {
    //用户id
    private String id;
    //账户余额
    private BigDecimal balance;
}
```
