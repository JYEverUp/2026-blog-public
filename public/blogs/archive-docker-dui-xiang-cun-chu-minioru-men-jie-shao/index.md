## [常见的对象存储方式对比](https://note.moguit.cn/#/./Docker/对象存储MinIO入门简介/README?id=常见的对象存储方式对比)

- 直接将图片保存到服务的硬盘
  - 优点：开发便捷，成本低
  - 缺点：扩容困难
- 使用分布式文件系统进行存储
  - 优点：容易实现扩容
  - 缺点：开发复杂度稍大（尤其是开发复杂的功能）
- 使用nfs做存储
  - 优点：开发较为便捷
  - 缺点：需要有一定的运维知识进行部署和维护
- 使用第三方的存储服务
  - 优点：开发简单，拥有强大功能，免维护
  - 缺点：付费

## [为何不采取FastDFs进行文件存储](https://note.moguit.cn/#/./Docker/对象存储MinIO入门简介/README?id=为何不采取fastdfs进行文件存储)

我们前面使用分布式文件系统FastDFS简直不要太爽，但是有几个问题不知道大家发现没有

- 第一个就是FastDFS没有一个完善的官方文档，各种第三方文档满天飞。
- 第二个就是创建容器比较麻烦，要创建存储服务与跟踪服务.
- 第三个就是安全性问题

## [对象存储MinIO](https://note.moguit.cn/#/./Docker/对象存储MinIO入门简介/README?id=对象存储minio)

MinIO是世界上最快的对象存储服务器，在标准硬件上，读写速度分贝为183GB/s 和 171GB/s，对象存储可以作为主要存储层，用于Spark，Presto，TensorFlow，H20.ai 以及替代产品等各种工作负载用于Hadoop HDFS

MinIO是一种高性能的分布式对象存储系统，它是软件定义的，可在行业标准硬件上运行，并且在Apache 2.0许可下，百分百开放源代码。

文档地址：https://docs.min.io/cn/

## [下载](https://note.moguit.cn/#/./Docker/对象存储MinIO入门简介/README?id=下载)

我们使用的是Docker的方式安装MinIO，首先拉取对应的镜像

```bash
docker pull minio/minioCopy to clipboardErrorCopied
```

然后我们需要创建两个目录，用于保存我们的文件和配置

```bash
mkdir -p /home/minio/data
mkdir -p /home/minio/configCopy to clipboardErrorCopied
```

## [启动容器](https://note.moguit.cn/#/./Docker/对象存储MinIO入门简介/README?id=启动容器)

然后我们启动我们的容器，后面有个目录，就是我们需要挂载的硬盘目录

```bash
docker run -p 9000:9000 --name minio \
-e "MINIO_ACCESS_KEY=mogu2018" \
--privileged=true \
-e "MINIO_SECRET_KEY=mogu2018" \
-v /home/minio/data:/data \
-v /home/minio/config:/root/.minio \
minio/minio server /dataCopy to clipboardErrorCopied
```

上面的配置中，包含两个重要的信息【以后登录时会用到，可以修改成自己的】

- MINIO_ACCESS_KEY：公钥
- MINIO_SECRET_KEY：密钥

运行成功后，我们就能看到我们下面的提示信息

![image-20201015150408263](/blogs/_archive-2024-assets/76bc07007e34063785a8.webp)

如果需要后台运行，使用这条语句

```bash
docker run --privileged -d -it -p 9000:9000 --name minio \
-e "MINIO_ACCESS_KEY=mogu2018" \
--privileged=true \
-e "MINIO_SECRET_KEY=mogu2018" \
-v /home/minio/data:/data \
-v /home/minio/config:/root/.minio \
minio/minio server /dataCopy to clipboardErrorCopied
```

## [访问](https://note.moguit.cn/#/./Docker/对象存储MinIO入门简介/README?id=访问)

我们只需要访问上面提到的ip地址，就能够进入到我们的页面了【部署云服务器，需要自行开启安全组！】

```bash
http://192.168.1.101:9000Copy to clipboardErrorCopied
```

![image-20201015150747476](/blogs/_archive-2024-assets/52ed0edc9e5a46018a56.webp)

会有一个不错的登录页面，我们输入刚刚配置的账号和密码 mogu2018 mogu2018 即可进入

![image-20201015150824563](/blogs/_archive-2024-assets/059c315bd1006210591d.webp)

## [创建bucket](https://note.moguit.cn/#/./Docker/对象存储MinIO入门简介/README?id=创建bucket)

我们首先需要创建一个桶，可以当成是一个目录，点击我们的右下角 加号 按钮，选择 create bucket进行创建

我们创建一个叫 mogublog 的桶，创建完成后，在侧边栏就能够看到我们刚刚创建的了

![image-20201015151202753](/blogs/_archive-2024-assets/4d13ba3688421c3bcb92.webp)

## [上传文件](https://note.moguit.cn/#/./Docker/对象存储MinIO入门简介/README?id=上传文件)

然后我们选中我们的桶，在点击加号，选择 upload file进行文件上传

![image-20201015151340507](/blogs/_archive-2024-assets/e17b73cea04a9ddd70e1.webp)

上传成功后，即可看到我们刚刚上传的文件列表了~

## [SpringBoot整合MinIO](https://note.moguit.cn/#/./Docker/对象存储MinIO入门简介/README?id=springboot整合minio)

参考文档：Java Client API文档

### [修改权限](https://note.moguit.cn/#/./Docker/对象存储MinIO入门简介/README?id=修改权限)

如果要使用SDK，比如Java客户端来操作我们的minio的话，那么我们还需要修改一下我们的bucket权限

![image-20201015151639447](/blogs/_archive-2024-assets/1290ed8cfb0a1499ddd9.webp)

首先点击我们的mogublog的右边区域，点击Edit policy，然后添加我们的权限为 可读可写，保存即可

### [添加依赖](https://note.moguit.cn/#/./Docker/对象存储MinIO入门简介/README?id=添加依赖)

```xml
<dependency>
    <groupId>io.minio</groupId>
    <artifactId>minio</artifactId>
    <version>7.0.2</version>
</dependency>Copy to clipboardErrorCopied
```

### [添加application.yml](https://note.moguit.cn/#/./Docker/对象存储MinIO入门简介/README?id=添加applicationyml)

```yml
server:
  port: 9001
spring:
  application:
    name: minio-application
  main:
    allow-bean-definition-overriding: true

minio:
  endpoint: http://192.168.1.101:9000
  accessKey: mogu2018
  secretKey: mogu2018
  bucketImageName: mogublogCopy to clipboardErrorCopied
```

### [添加配置文件](https://note.moguit.cn/#/./Docker/对象存储MinIO入门简介/README?id=添加配置文件)

然后我们需要编写配置文件，用于初始化配置 MinioClient装载到spring容器中

```bash
@Configuration
public class MinIoConfig {
    @Value("${minio.endpoint}")
    private String endpoint;

    @Value("${minio.accessKey}")
    private String accessKey;

    @Value("${minio.secretKey}")
    private String secretKey;

    @Bean
    public MinioClient minioClient() throws Exception{
        // 使用MinIO服务的URL，端口，Access key和Secret key创建一个MinioClient对象
        MinioClient minioClient = new MinioClient(endpoint, accessKey, secretKey);
        return minioClient;
    }
}Copy to clipboardErrorCopied
```

### [编写Controller](https://note.moguit.cn/#/./Docker/对象存储MinIO入门简介/README?id=编写controller)

然后在写一个前端控制器

```java
@RestController
public class MinIoController {

    @Autowired
    MinioClient minioClient;

    @PostMapping("/upload")
    public String upload(@RequestParam("data") MultipartFile data) throws Exception{
        String fileName = data.getOriginalFilename();
        InputStream inputStram = data.getInputStream();
        minioClient.putObject(
                PutObjectArgs.builder().bucket("mogublog").object(fileName).stream(
                        inputStram, data.getSize(), -1)
                        .contentType(data.getContentType())
                        .build());
        return "上传成功";
    }

    @PostMapping("/download")
    public String download(@RequestParam("fileName")String fileName) throws Exception{
        String url = minioClient.presignedGetObject("mogublog", fileName, 60*60*24*7);
        return url;
    }
}Copy to clipboardErrorCopied
```

### [测试图片上传](https://note.moguit.cn/#/./Docker/对象存储MinIO入门简介/README?id=测试图片上传)

下面我们就需要进行测试了，我们运行我们的项目，然后使用postman进行上传测试

首先我们在postman中添加我们的上传接口，然后在修改请求头中添加Content-Type

```bash
Content-Type  multipart/form-dataCopy to clipboardErrorCopied
```

![image-20201018222200593](/blogs/_archive-2024-assets/39e5ffe24f64c51cc1f9.webp)

然后在选择我们的图片上传

![image-20201018222251132](/blogs/_archive-2024-assets/b04aa9c4e8cae9fdf7ee.webp)

最后在刷新MinIO，就能够看到我们刚刚上传的文件了

![img](/blogs/_archive-2024-assets/ff9d41261369ff285365.webp)

我们可以通过下面的地址直接访问我们的图片

```bash
http://192.168.1.101:9000/mogublog/1578926382309.jpgCopy to clipboardErrorCopied
```

## [蘑菇博客配置Minio](https://note.moguit.cn/#/./Docker/对象存储MinIO入门简介/README?id=蘑菇博客配置minio)

蘑菇博客已经集成了Minio对象存储服务，我们只需要在系统配置，找到我们的Minio对象存储

例如：我在上面已经部署了 [http://101.132.122.175:8080](http://101.132.122.175:8080/) 的Minio服务【按照你部署的ip和端口填写】

![image-20201024085505782](/blogs/_archive-2024-assets/93df2fd8b76366b304cc.webp)

这里有5个内容需要我们填写的

- Minio访问域名：文件上传到Minio对象存储服务器后，通过哪个域名或者ip进行访问
- Minio连接地址：Minio的访问地址，也就是上面提到的EndPoint
- Minio公钥：创建Minio容器时的公钥
- Minio私钥：创建Minio容器时的私钥
- Minio上传空间：创建Minio时的bucket

配置完成后，我们就需要访问我们的Minio服务，然后创建对应的 Minio上传空间【Bucket】，访问Minio地址

```bash
http://101.132.122.175:8080Copy to clipboardErrorCopied
```

输入账号和密码，然后选择 Create Bucket

![image-20201024090123987](/blogs/_archive-2024-assets/5db75afb980f7a5ec166.webp)

还需要修改一下我们的bucket权限，允许读写权限

![image-20201015151639447](/blogs/_archive-2024-assets/1290ed8cfb0a1499ddd9.webp)

最后在回到我们的系统配置，开启Minio上传功能，同时在开启Minio的图片显示

![image-20201024090404973](/blogs/_archive-2024-assets/47be1fd45c5da4811705.webp)

我们可以上传图片进行测试，打开博客管理，添加博客后进行图片上传测试

![image-20201024090500799](/blogs/_archive-2024-assets/59bc4d84c10ff4163186.webp)

通过上图发现，能够成功的访问到我们的图片了~，我们再到 minio后台管理查看

![image-20201024090556372](/blogs/_archive-2024-assets/f62250ab93d21f45c158.webp)

也能够看到我们刚刚上传的文件了~

![image-20201024090606824](/blogs/_archive-2024-assets/d8c5fe1dbacfbba76b23.webp)
