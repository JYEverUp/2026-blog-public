# SpringBoot中，接口加解密，通用方案实战

# 1、背景
有些接口中，数据敏感度高，为了防止数据在传输过程中被窃取，我们可以采用密文传输，这样数据传输过程中，被别人窃取后，拿到的也是密文，他不知道如何解密，没有任何意义。
调用方发送请求前，先对明文加密，然后发送密文，被调用方收到数据后，先进行解密，然后再进行处理。
返回的结果同样也可以加密，被调用方将需要返回的数据进行加密，然后将密文返回给调用方，调用方收到后，再进行解密便得到明文。
# 2、案例1：接口入参自动解密
com.itsoku.lesson068.controller.TestController#decryptTest
# 3、案例2：接口返回值自动加密
com.itsoku.lesson068.controller.TestController#encryptTest
# 4、案例3：请求和返回值同时加密
com.itsoku.lesson068.controller.TestController#secureTest
# 5、原理
## 统一加解密
加密和解密对接口来说，属于通用功能，这些功能可以从业务代码中剥离出来，进行统一处理
- 请求解密：可以通过拦截器，拦截所有需要解密的请求，将密文解密为明文，然后再由接口去处理
- 返回值加密：可以通过拦截器，拦截所有所有需要加密的返回值，将明文加密为密文，然后返回给客户端
## 请求自动解密：@Decrypt + DecryptRequestBodyAdvice
- 若请求是密文，则需要在接口的方法上加上 @Decrypt 注解
  ```java
  @Decrypt
  @PostMapping("/decryptTest")
  public List<String> decryptTest(@RequestBody List<String> body) {
      log.info("参数加密测试，请求参数：{}", body);
      return body;
  }
  ```
- 请求到达controller中的方法之前，会拦截标注有 @Decrypt 注解的方法，负责将原始请求中的密文转换为明文
  ```java
  源码：com.itsoku.lesson068.secure.DecryptRequestBodyAdvice
  ```
## 返回值自动加密：@Encrypt + EncryptResponseBodyAdvice
- 若返回值需要加密，则需要在方法上添加 @Encrypt  注解
  ```java
  @Encrypt
  @GetMapping("/encryptTest")
  public String encryptTest() {
      return "高并发 & 微服务 & 性能调优实战案例 100 讲";
  }
  ```
- 在结果返回给调用者之前，会拦截标注有@Encrypt 注解的方法，对接口的返回值进行处理，将其转换为密文
  ```java
  源码：com.itsoku.lesson068.secure.EncryptResponseBodyAdvice
  ```
