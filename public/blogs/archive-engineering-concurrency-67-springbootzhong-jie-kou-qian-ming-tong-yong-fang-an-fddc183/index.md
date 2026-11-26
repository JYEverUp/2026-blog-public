# SpringBoot中，接口签名，通用方案，一次性搞懂

# 1、本文内容
1. 接口为什么要签名？
2. 如何签名？
3. 什么是请求重放？
4. 如何避免请求重放？
5. 接口签名使用场景
6. SpringBoot实现接口签名实战
# 2、先来看一个接口：转账接口
假如咱们开发了一个转账接口，如下，用于从一个账户转账到另外一个账户
```java
@RequestMapping("/account/transfer")
public Result<String> transfer(@RequestBody TransferRequest request) {
    log.info("转账成功：{}", JSONUtil.toJsonStr(request));
    return ResultUtils.success("转账成功");
}
public class TransferRequest {
    //付款人账户id
    private String fromAccountId;
    //收款人账号id
    private String toAccountId;
    //转账金额
    private BigDecimal transferPrice;
}
```
比如张三给李四转账100元，请求如下
```http
POST http://localhost:8080/account/transfer
Content-Type: application/json
{
  "fromAccountId": "张三",
  "toAccountId": "李四",
  "transferPrice": 100
}
```
# 3、请求伪造
上面这个请求没有任何安全限制。
王五知道有这个接口，然后就可以通过这个接口偷偷给自己转账：比如下面这样，王五将张三的钱转到了自己的账户
```http
POST http://localhost:8080/account/transfer
Content-Type: application/json
{
  "fromAccountId": "张三",
  "toAccountId": "王五",
  "transferPrice": 100
}
```
这就是请求伪造，会导致严重的后果。
# 4、如何防止请求伪造呢？签名（sign）
需要引入签名，来看下如何实现。
## 双方引入秘钥（secretKey）
接口调用方和接口提供方，双方需要一个相同的秘钥（secretKey），这个秘钥不能让第三方知道。
秘钥就是一个普通的字符串，如下：
```java
secretKey = b0e8668b-bcf2-4d73-abd4-893bbc1c6079
```
## 接口调用方：利用秘钥对请求进行签名（sign）
可以通过一些算法对请求进行签名。
比如下面的算法，通过秘钥和请求体生成签名
```java
sign = md5(secretKey + http请求体)
```
**注意：**当secretKey或http请求体有任何变化的时候，sign都会发生改变，这点很关键
## 接口调用方：携带签名发送请求
```http
POST http://localhost:8080/account/transfer
Content-Type: application/json
X-Sign: 签名
{
  "fromAccountId": "张三",
  "toAccountId": "李四",
  "transferPrice": 100
}
```
## 服务端：校验签名
服务端接收到请求后，对签名进行校验，服务端知道秘钥，然后拿到请求体，计算出签名，和请求方传递的签名进行对比，若不一致，表示请求被篡改了，说明这个请求是被伪造的。
伪代码如下：
```java
//请求体字符串
String body = http请求体;
//签名
String sign = request.getHeader("X-Sign");
//计算签名
String expectSign = md5(秘钥 + body);
//校验签名
if(!expectSign.equals(sign)){
	//签名有误，非法请求
}
```
## 已杜绝请求伪造
由于请求伪造方是不知道秘钥的，当请求伪造方，将请求体改变了，那么签名校验是无法通过的，所以请求无法伪造。
# 5、新的问题：请求重放
目前请求伪造的问题已经解决了，但是又来了一个新的问题：请求重放。
下面给大家演示下请求重放。
## 步骤1：张三给李四转账100
```http
POST http://localhost:8080/account/transfer
Content-Type: application/json
X-Sign: 签名
{
  "fromAccountId": "张三",
  "toAccountId": "李四",
  "transferPrice": 100
}
```
## 步骤2：李四再次发起这个请求
李四将上面的请求拦截了，拿到了请求完整的数据，他便可以再次发送这个请求，会导致张三给李四转账多次。
# 6、如何防止请求重放呢？（随机字符串nonce+时间戳timestamp）
## 前端引入随机字符串(nonce)
可以在请求头中添加一个新的随机字符串（nonce），每次发送请求，nonce都是一个新的值。
```http
POST http://localhost:8080/account/transfer
Content-Type: application/json
X-Sign: 签名
X-Nonce: 随机字符串
{
  "fromAccountId": "张三",
  "toAccountId": "李四",
  "transferPrice": 100
}
```
签名的算法也需要改变，如下，将nonce也加入到签名的算法中，当参与计算的任何一个变量发生变化，则签名都会发生变化
```java
sign = md5(secretKey + nonce + http请求体)
```
## 后端确保同一个nonce只会被处理一次
请求过来后，先看一下redis中是否存在这个nonce，如果存在，则返回：nonce无效，否则，后端可以将nonce保存到redis中，有效期20分钟。
伪代码如下：
```java
@Autowired
private RedisTemplate<String, String> redisTemplate;
String nonceKey = "SignatureVerificationFilter:nonce:" + nonce;
if (!this.redisTemplate.opsForValue().setIfAbsent(nonceKey, "1", 20, TimeUnit.MINUTES)) {
    this.write(response, "nonce无效");
    return false;
}
```
## 新的问题：20分钟后，请求还是能够被重放
上面代码中，nonce被存储在redis中，有效期是20分钟，这样只能确保同一个请求在20分钟内无法重放
但是20钟后，redis中的数据已经过期了，同一个请求再次到达后端时，后端会认为这个nonce没有被使用过，会认为是新的请求，会导致请求再次被处理，这样就导致请求被重放了。
还是未解决请求重放的问题，这个时候我们需要引入一个时间戳了，向下看。
## 引入时间戳（timestamp）
前端发送请求是，将当前的时间戳(秒)，也加入到请求头中
```http
POST http://localhost:8080/account/transfer
Content-Type: application/json
X-Sign: 签名
X-Nonce: 随机字符串
X-Timestamp: 当前时间戳
{
  "fromAccountId": "张三",
  "toAccountId": "李四",
  "transferPrice": 100
}
```
签名的算法也需要改变
```java
sign = md5(secretKey + nonce + 当前时间戳 + http请求体)
```
## 后端对请求进行限制：请求10分钟内有效
将服务器当前时间和请求头中时间戳（timestamp）进行对比，绝对值在10分钟内，请求才算有效，否则，请求无效
```java
//timestamp 10分钟内有效
long timestamp = Long.parseLong(前端请求头中的时间戳);
long currentTimestamp = System.currentTimeMillis() / 1000;
if (Math.abs(currentTimestamp - timestamp) > 600) {
    //请求已过期
}
```
## 此时已杜绝请求重放
- 10分钟内请求被重放：由于nonce的有效期是20分钟，请求到达后端后，发现nonce已被使用，则请求无法重放
- 20分钟后请求被重放：由于时间戳timestamp的有效期是10分钟，请求到达后端后，发现timestamp已过期，则请求无法重放
# 7、使用场景
接口签名不是给前端用的，主要是作为后端接口安全验证的一种手段，比如后端和后端之间相互调用，或者为第三方提供一些安全接口等。
# 8、SpringBoot版本代码落地
## 创建SpringBoot项目
## 引入maven配置
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
<dependency>
    <groupId>cn.hutool</groupId>
    <artifactId>hutool-all</artifactId>
    <version>5.8.2</version>
</dependency>
<!-- Apache Lang3 -->
<dependency>
    <groupId>org.apache.commons</groupId>
    <artifactId>commons-lang3</artifactId>
</dependency>
<dependency>
    <groupId>commons-beanutils</groupId>
    <artifactId>commons-beanutils</artifactId>
    <version>1.9.3</version>
</dependency>
```
## application.yml 配置redis和签名的秘钥
```yaml
spring:
  redis:
    host: 192.168.216.128
secret-key: b0e8668b-bcf2-4d73-abd4-893bbc1c6079
```
## SignatureVerificationFilter：签名校验拦截器
```java
package com.itsoku.lesson067.sign;
import cn.hutool.crypto.digest.DigestUtil;
import cn.hutool.json.JSONUtil;
import com.itsoku.lesson067.common.ResultUtils;
import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.StreamUtils;
import org.springframework.web.filter.OncePerRequestFilter;
import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebFilter;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.TimeUnit;
/**
 * <b>description</b>实战
 * <b>time</b>：2024/7/26 20:17 <br>
 * <b>author</b>：gjy
 */
@Order(Ordered.HIGHEST_PRECEDENCE)
@WebFilter(urlPatterns = "/**", filterName = "SignatureVerificationFilter")
@Component
public class SignatureVerificationFilter extends OncePerRequestFilter {
    public static Logger logger = LoggerFactory.getLogger(SignatureVerificationFilter.class);
    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
        //对request进行包装，支持重复读取body
        ReusableBodyRequestWrapper requestWrapper = new ReusableBodyRequestWrapper(request);
        //校验签名
        if (this.verifySignature(requestWrapper, response)) {
            filterChain.doFilter(requestWrapper, response);
        }
    }
    @Autowired
    private RedisTemplate<String, String> redisTemplate;
    //签名秘钥
    @Value("${secretKey:b0e8668b-bcf2-4d73-abd4-893bbc1c6079}")
    private String secretKey;
    /**
     * 校验签名
     *
     * @param request
     * @param response
     * @return
     * @throws IOException
     */
    public boolean verifySignature(HttpServletRequest request, HttpServletResponse response) throws IOException {
        //签名
        String sign = request.getHeader("X-Sign");
        //随机数
        String nonce = request.getHeader("X-Nonce");
        //时间戳
        String timestampStr = request.getHeader("X-Timestamp");
        if (StringUtils.isBlank(sign) || StringUtils.isBlank(nonce) || StringUtils.isBlank(timestampStr)) {
            this.write(response, "参数错误");
            return false;
        }
        //timestamp 10分钟内有效
        long timestamp = Long.parseLong(timestampStr);
        long currentTimestamp = System.currentTimeMillis() / 1000;
        if (Math.abs(currentTimestamp - timestamp) > 600) {
            this.write(response, "请求已过期");
            return false;
        }
        //防止请求重放，nonce只能用一次，放在redis中，有效期 20分钟
        String nonceKey = "SignatureVerificationFilter:nonce:" + nonce;
        if (!this.redisTemplate.opsForValue().setIfAbsent(nonceKey, "1", 20, TimeUnit.MINUTES)) {
            this.write(response, "nonce无效");
            return false;
        }
        //请求体
        String body = StreamUtils.copyToString(request.getInputStream(), StandardCharsets.UTF_8);
        //需要签名的数据：secretKey+noce+timestampStr+body
        //校验签名
        String data = String.format("%s%s%s%s", this.secretKey, nonce, timestampStr, body);
        if (!DigestUtil.md5Hex(data).equals(sign)) {
            write(response, "签名有误");
            return false;
        }
        return true;
    }
    private void write(HttpServletResponse response, String msg) throws IOException {
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding(StandardCharsets.UTF_8.name());
        response.getWriter().write(JSONUtil.toJsonStr(ResultUtils.error(msg)));
    }
}
```
## 测试效果
1. 启动springboot应用
2. 运行测试用例：SignTest#transfer
