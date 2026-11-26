# 使用hutool生成&解析二维码，特好用

# 1、前言
二维码，在日常开发中用的挺多的，最常见的2个功能：生成二维码、解析二维码
hutool工具中已经包含了二维码的各种工具类，非常好用。
本文将给大家演示，springboot中，如何使用hutool中的工具类实现这2个功能。
# 2、生成二维码
![image-20240719122027028](/blogs/_archive-2024-assets/984e3c0f2508d1f655f2.webp)
## 1）引入二维码相关maven工具包
```xml
<dependency>
    <groupId>cn.hutool</groupId>
    <artifactId>hutool-all</artifactId>
    <version>5.8.2</version>
</dependency>
<dependency>
    <groupId>com.google.zxing</groupId>
    <artifactId>javase</artifactId>
    <version>3.5.3</version>
</dependency>
```
## 2）生成二维码的接口
com.itsoku.lesson064.QRCodeController#generateQrCode
```java
/**
 * 生成二维码
 *
 * @param content 二维码内容
 * @param width 二维码宽度
 * @param height 二维码高度
 * @return
 */
@GetMapping("/generateQrCode")
@ResponseBody
public ResponseEntity<byte[]> generateQrCode(@RequestParam("content") String content, @RequestParam("width") int width, @RequestParam("height") int height) {
    //生成二维码（hutool工具类QrCodeUtil）
    byte[] bytes = QrCodeUtil.generatePng(content, width, height);
    //返回二维码图片（png格式）
    return ResponseEntity.ok().header(HttpHeaders.CONTENT_TYPE, MediaType.IMAGE_PNG_VALUE).body(bytes);
}
```
## 3）查看效果
浏览器中访问：http://localhost:8080/generateQrCode?width=300&height=300&content=http://www.itsoku.com
## 4）小结
QrCodeUtil 工具类，默认生成白底黑色的二维码，也可以自定义二维码的样式，比如：设置背景色、前景色、设置边距以及在二维码中心显示自定义的 logo 等等
如下图，generate相关的方法有很多，都是用于生成二维码的，大家可以去体验下
![image-20240718122450839](/blogs/_archive-2024-assets/7c60f5d86e5a2e3d9ab4.webp)
# 3、二维码解析
二维码解析也比较简单，用的也是 hutool 中的 QrCodeUtil工具类，此类中有多个decode方法，如下图，都是用于解析二维码的。
![image-20240718122112832](/blogs/_archive-2024-assets/7e107b581f509971bef4.webp)
## 案例代码
```java
import cn.hutool.extra.qrcode.QrCodeUtil;
import org.junit.jupiter.api.Test;
import java.io.File;
public class QRCodeTest {
    @Test
    public void qrCodeDecode() {
        //二维码文件
        File qrCodeFile = new File("D:\\code\\likun_557\\luren\\lesson064\\src\\test\\resources\\二维码.png");
        //使用hutool中的工具类解析二维码，得到二维码中的内容
        String content = QrCodeUtil.decode(qrCodeFile);
        System.out.println(content);
    }
}
```
