#  SpringBoot中数据脱敏优雅设计与实现
## 本文内容
本文主要介绍 SpringBoot 中数据脱敏优雅的设计与实现，坚持看完，相信你会有所收获。
## 先带大家看下效果
接口代码
```java
@RestController
public class TestController {
    @GetMapping("/getUser")
    public Result<User> getUser() {
        User user = new User();
        user.setId("001");
        user.setName("路人");
        user.setPhone("18612345678");
        user.setEmail("likun_557@163.com");
        user.setIdCard("420123432112121332");
        user.setPassword("123456");
        user.setAddress("上海市闵行区漕河泾开发区");
        user.setBankCard("6226090211114567");
        return ResultUtils.success(user);
    }
}
```
访问接口输出如下，敏感信息自动按照某种格式脱敏了。
```json
{
  "success": true,
  "data": {
    "id": "001",
    "name": "路*",
    "phone": "186****5678",
    "email": "l********@163.com",
    "idCard": "4***************32",
    "password": "******",
    "address": "上海市闵********",
    "bankCard": "6226 **** **** 4567"
  },
  "msg": null,
  "code": null
}
```
## 如何实现？
Controler方法的返回值，会被SpringBoot统一处理，其内部会使用jackson将对象序列化为json字符，然后由SpringBoot输出到客户端。
所以，我们只需在jackson序列化这一步，将需要脱敏的数据统一处理就可以了。
我们可以自定义一个脱敏的注解，注解中指定脱敏的策略，这个策略其实就是一个字符串替换的函数，可以将这个注解标注在需要脱敏的字段上面。
然后自定义一个脱敏的jackson序列化器，这个序列化器会对标注了脱敏注解的字段进行处理，会将注解上的脱敏策略取出来，使用脱敏策略对原字符串进行替换，然后输出替换后的字符串。
## 源码
### 脱敏注解
> 如下，需要添加
>
> @JacksonAnnotationsInside
> @JsonSerialize(using = DesensitizationJsonSerializable.class)
```java
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
@JacksonAnnotationsInside
@JsonSerialize(using = DesensitizationJsonSerializable.class)
public @interface Desensitization {
    /**
     * 脱敏策略
     *
     * @return
     */
    DesensitizationStrategy value();
}
```
### 脱敏策略
> 如下，脱敏策略就是一个字符串替换函数，参数就是原本的字符串，返回值是脱敏后的字符串。
>
> 下面默认定义了 7 种，这里脱敏方法，使用到了hutool中自带的工具，这个工具内部已经提供了场景的一些数据脱敏的函数。
>
> 如果感觉不够用，也可以自己拓展。
```java
public enum DesensitizationStrategy {
    // 手机号脱敏策略，保留前三位和后四位
    PHONE(s -> DesensitizedUtil.desensitized(s, DesensitizedUtil.DesensitizedType.MOBILE_PHONE)),
    // 邮箱脱敏策略，保留邮箱用户名第一个字符和@符号前后部分
    EMAIL(s -> DesensitizedUtil.desensitized(s, DesensitizedUtil.DesensitizedType.EMAIL)),
    // 身份证号脱敏策略，保留前四位和后四位
    ID_CARD(s -> DesensitizedUtil.desensitized(s, DesensitizedUtil.DesensitizedType.ID_CARD)),
    // 地址脱敏策略，保留省市信息，其余部分脱敏为**
    ADDRESS(s -> DesensitizedUtil.desensitized(s, DesensitizedUtil.DesensitizedType.ADDRESS)),
    // 银行卡号脱敏策略，保留前四位和后三位
    BANK_CARD(s -> DesensitizedUtil.desensitized(s, DesensitizedUtil.DesensitizedType.BANK_CARD)),
    // 姓名脱敏策略，保留姓氏第一个字符，其余部分脱敏为**
    NAME(s -> DesensitizedUtil.desensitized(s, DesensitizedUtil.DesensitizedType.CHINESE_NAME)),
    // 密码脱敏策略，统一显示为******
    PASSWORD(s -> "******");
    private final Function<String, String> desensitization;
    DesensitizationStrategy(Function<String, String> desensitization) {
        this.desensitization = desensitization;
    }
    public Function<String, String> getDesensitization() {
        return desensitization;
    }
}
```
### jackson脱敏序列化器
```java
public class DesensitizationJsonSerializable extends JsonSerializer<String> implements ContextualSerializer {
    //脱敏策略
    private DesensitizationStrategy desensitizationStrategy;
    @Override
    public void serialize(String s, JsonGenerator gen, SerializerProvider serializers) throws IOException {
        // 使用脱敏策略将字符串处理后序列化到json中
        gen.writeString(desensitizationStrategy.getDesensitization().apply(s));
    }
    @Override
    public JsonSerializer<?> createContextual(SerializerProvider prov, BeanProperty property) throws JsonMappingException {
        // 获取属性上的 Desensitization 注解
        Desensitization annotation = property.getAnnotation(Desensitization.class);
        // 注解不为空 && 属性类型必须是字符串类型
        if (Objects.nonNull(annotation) && Objects.equals(String.class, property.getType().getRawClass())) {
            //设置脱敏策略
            this.desensitizationStrategy = annotation.value();
            return this;
        }
        // 返回默认的序列化器
        return prov.findValueSerializer(property.getType(), property);
    }
}
```
### 使用
```java
public class User {
    // id
    private String id;
    // 姓名
    @Desensitization(DesensitizationStrategy.NAME)
    private String name;
    // 手机号
    @Desensitization(DesensitizationStrategy.PHONE)
    private String phone;
    // 邮箱
    @Desensitization(DesensitizationStrategy.EMAIL)
    private String email;
    // 银行卡
    @Desensitization(DesensitizationStrategy.ID_CARD)
    private String idCard;
    // 密码
    @Desensitization(DesensitizationStrategy.PASSWORD)
    private String password;
    // 地址
    @Desensitization(DesensitizationStrategy.ADDRESS)
    private String address;
    @Desensitization(DesensitizationStrategy.BANK_CARD)
    private String backCard;
	//getter setter方法省略...
}
```
