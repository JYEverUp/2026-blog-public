#  接口测试利器HTTP Client，不用Postman也可以
接口测试，用的比较多的可能是postman。
今天给大家推荐另一款接口测试工具，idea中自带的接口测试插件HTTP Client，非常好用，这样大家可以不用装postman，直接在idea一个工具中边开发边测试，非常方便。
## 1、安装插件HTTP Client
File->Settings->Plugins，搜索 HTTP Client
![image-20240606120459276](/blogs/_archive-2024-assets/892a06a15ea2e25a00a3.webp)
## 2、基本使用
### 接口代码
```java
com.itsoku.lesson045.IndexController
```
### HTTP Client接口测试文件
创建后缀为http的文件：IndexController.http，内容如下
```http
### get 请求
GET http://localhost:8080/get
### post 提交表单
POST http://localhost:8080/post
Content-Type: application/x-www-form-urlencoded
name=路人&age=30
### body 中传递json数据
POST http://localhost:8080/body
Content-Type: application/json
[3,10,40]
### put请求
PUT http://localhost:8080/put
### 多文件上传文件接口测试
POST http://localhost:8080/upload
Content-Type: multipart/form-data; boundary=WebAppBoundary
--WebAppBoundary
Content-Disposition: form-data; name="file1"; filename="1.png"
< D:\code\likun_557\luren\document\img\MQ常见使用场景.png
--WebAppBoundary--
Content-Disposition: form-data; name="file2"; filename="2.png"
< D:\code\likun_557\luren\document\img\幂等接口通用实现.png
--WebAppBoundary--
Content-Disposition: form-data;name=userName
tom
--WebAppBoundary--
Content-Disposition: form-data;name=age
23
```
## 3、不同环境的支持
环境变量文件
```json
{
  "dev": {
    "url": "http://localhost:8080"
  },
  "test": {
    "url": "http://localhost:8080"
  }
}
```
引用环境变量，可以通过{{变量名称}}，来引用环境的值
## 4、curl命令导入
 
