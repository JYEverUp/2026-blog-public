# MinIo课件

# 一、Minio介绍

MinIO是全球领先的对象存储先锋，目前在全世界有数百万的用户。

* **高性能** ，在标准硬件上，读/写速度上高达183GB/秒和171GB/秒，拥有更高的吞吐量和更低的延迟
* **可扩展性** ，为对象存储带来了简单的缩放模型，通过添加更多集群可以扩展空间
* **简单** ，极简主义是MinIO的指导性设计原则，即可在几分钟内安装和配置
* **与Amazon S3兼容** ，亚马逊云的 `S3 API`（接口协议）是在全球范围内达到共识的对象存储的协议，是全世界内大家都认可的标准
* **数据安全** ，使用纠删码来保护数据免受硬件故障和无声数据损坏

**纠删码**

**&emsp;&emsp;纠删码**是一种恢复丢失和损坏数据的数学算法， Minio默认采用 `Reed-Solomon code`将数据拆分成N/2个数据块和N/2个奇偶校验块。这就意味着如果是16块盘，一个对象会被分成8个数据块、8个奇偶校验块，你可以丢失任意8块盘（不管其是存放的数据块还是校验块），你仍可以从剩下的盘中的数据进行恢复。

http://docs.minio.org.cn/docs/master/java-client-quickstart-guide

**Minio和FastDFS的对比**

1. 安装难度
2. 文档
3. 性能
4. 容器化支持
5. SDK支持

# 二、Minio安装

&emsp;&emsp;为了快速搞定Minio的部署工作。我们通过Docker-Compose来一键快速部署操作

## 1.安装DockerCompose

&emsp;&emsp;安装DockerCompose的前提是先安装一个Docker环境，如果还没安装的参考波哥的博客地址：https://blog.csdn.net/qq_38526573/category_9619681.html

&emsp;&emsp;Compose 是用于定义和运行多容器 Docker 应用程序的工具。通过 Compose，您可以使用 YML 文件来配置应用程序需要的所有服务。然后，使用一个命令，就可以从 YML 文件配置中创建并启动所有服务。

> 一键启动所有的服务

DockerCompose的使用步骤

* 创建对应的DockerFile文件
* 创建yml文件，在yml文件中编排我们的服务
* 通过 `docker-compose up`命令 一键运行我们的容器

官网地址：https://docs.docker.com/compose

下载地址：

```shell
curl -L https://get.daocloud.io/docker/compose/releases/download/1.25.0/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose
```

修改文件夹权限

```shell
chmod +x /usr/local/bin/docker-compose
```

建立软连接

```shell
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
```

检查是否安装成功

```
docker-compose --version
```

## 2.安装Minio集群

官方推荐 `docker-compose.yaml`：

稍加修改，内容如下：

```yml
version: '3.7'

# 所有容器通用的设置和配置
x-minio-common: &minio-common
  image: minio/minio
  command: server --console-address ":9001" http://minio{1...4}/data
  expose:
    - "9000"
  # environment:
    # MINIO_ROOT_USER: minioadmin
    # MINIO_ROOT_PASSWORD: minioadmin
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
    interval: 30s
    timeout: 20s
    retries: 3

# 启动4个docker容器运行minio服务器实例
# 使用nginx反向代理9000端口，负载均衡, 你可以通过9001、9002、9003、9004端口访问它们的web console
services:
  minio1:
    <<: *minio-common
    hostname: minio1
    ports:
      - "9001:9001"
    volumes:
      - ./data/data1:/data

  minio2:
    <<: *minio-common
    hostname: minio2
    ports:
      - "9002:9001"
    volumes:
      - ./data/data2:/data

  minio3:
    <<: *minio-common
    hostname: minio3
    ports:
      - "9003:9001"
    volumes:
      - ./data/data3:/data

  minio4:
    <<: *minio-common
    hostname: minio4
    ports:
      - "9004:9001"
    volumes:
      - ./data/data4:/data

  nginx:
    image: nginx:1.19.2-alpine
    hostname: nginx
    volumes:
      - ./config/nginx.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "9000:9000"
    depends_on:
      - minio1
      - minio2
      - minio3
      - minio4
```

接着新建文件夹 `config`，新建配置 `nginx.conf`

```conf
user  nginx;
worker_processes  auto;

error_log  /var/log/nginx/error.log warn;
pid        /var/run/nginx.pid;

events {
    worker_connections  4096;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;
    sendfile        on;
    keepalive_timeout  65;

    # include /etc/nginx/conf.d/*.conf;

    upstream minio {
        server minio1:9000;
        server minio2:9000;
        server minio3:9000;
        server minio4:9000;
    }

    server {
        listen       9000;
        listen  [::]:9000;
        server_name  localhost;

        # To allow special characters in headers
        ignore_invalid_headers off;
        # Allow any size file to be uploaded.
        # Set to a value such as 1000m; to restrict file size to a specific value
        client_max_body_size 0;
        # To disable buffering
        proxy_buffering off;

        location / {
            proxy_set_header Host $http_host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            proxy_connect_timeout 300;
            # Default is HTTP/1, keepalive is only enabled in HTTP/1.1
            proxy_http_version 1.1;
            proxy_set_header Connection "";
            chunked_transfer_encoding off;

            proxy_pass http://minio;
        }
    }

}
```

然后执行对应的命令

```cmd
docker-compose up -d
```

![image.png](/blogs/_archive-2024-assets/6c68ecc475578c155e82.webp)

访问控制台：http://192.168.56.100:9000

![image.png](/blogs/_archive-2024-assets/162c21089c6f9cbe34e9.webp)

账号密码为：minioadmin

![image.png](/blogs/_archive-2024-assets/641590bdd9049b5335bb.webp)

# 三、Minio客户端

&emsp;&emsp;然后我们可以创建一个Java项目来操作文件上传下载操作。

## 1.Bucket

&emsp;&emsp;Bucket是桶的意思。我们创建一个Bucket

![image.png](/blogs/_archive-2024-assets/84d0b6b17ad6ad60de6d.webp)

![image.png](/blogs/_archive-2024-assets/c914c86be30389fe1140.webp)

我们还可以直接上传图片文件等

![image.png](/blogs/_archive-2024-assets/6310dca84f858c1781bc.webp)

![image.png](/blogs/_archive-2024-assets/e9535a42ee8ca046ea65.webp)

## 2.用户管理

&emsp;&emsp;针对客户端的操作，我们需要维护相关的账号来管理。

![image.png](/blogs/_archive-2024-assets/b5b1a8145d2bfe3c5850.webp)

直接点击创建相关的用户即可

![image.png](/blogs/_archive-2024-assets/c8d50e271c106edf6aa6.webp)

用户创建完成后我们就可以通过客户端工具来操作了。

## 3. Java项目

&emsp;&emsp;然后我们来看看如何在Java项目中来操作了。

首先添加必要的依赖

```xml
<dependency>
            <groupId>io.minio</groupId>
            <artifactId>minio</artifactId>
            <version>7.0.2</version>
        </dependency>
        <!-- https://mvnrepository.com/artifact/commons-io/commons-io -->
        <dependency>
            <groupId>commons-io</groupId>
            <artifactId>commons-io</artifactId>
            <version>2.8.0</version>
        </dependency>
```

然后通过相关的API操作即可

```java
    private String endpoint = "http://192.168.56.100:9000";
    private String accessKey = "dpb";
    private String secretKey = "12345678";

    @Test
    void contextLoads() throws Exception{
        // 1.使用MinIo服务的URL，端口 账号和密码 创建一个 MinIoClient对象
        MinioClient minioClient = new MinioClient(endpoint, accessKey, secretKey);
        boolean isExists = minioClient.bucketExists("test");
        if(isExists){
            System.out.println("已经存在了 test 这个 Bucket");
        }else{
            minioClient.makeBucket("test");
        }
        // 存储文件到 存储桶中
        minioClient.putObject("test","/group1/UserMapper.xml","d:/UserMapper.xml",null);
        System.out.println("文件上传成功...");
        // 下载文件
        InputStream in = minioClient.getObject("test", "/group1/UserMapper.xml");
        List<String> strings = IOUtils.readLines(in, "UTF-8");
        strings.stream().forEach(s -> System.out.println(s));
    }
```

执行后成功：

![image.png](/blogs/_archive-2024-assets/dd99331d2c708afa154e.webp)

![image.png](/blogs/_archive-2024-assets/d4a6cdfa3fba40db7468.webp)

搞定

## 4.获取图片地址

&emsp;&emsp;如果上传的是普通文件我们可以获取对应的字节流来操作，但是如果我们需要获取的是图片。只要访问就可以了，这时我们可以通过对应的API来获取图片的URL地址就可以了

![image.png](/blogs/_archive-2024-assets/c74d8ff544e9a7683b82.webp)

但是在访问的时候缺提示访问不了

![image.png](/blogs/_archive-2024-assets/166cf937eb5ad40d67aa.webp)

原因是我们需要设置下Bucket的策略

![image.png](/blogs/_archive-2024-assets/829ab4cb94a000b27119.webp)

![image.png](/blogs/_archive-2024-assets/e8e857612dad85bb72bf.webp)

访问就可以了

![image.png](/blogs/_archive-2024-assets/6422547b47d30a89485c.webp)

搞定~

# 四、Minio原理讲解

## 1.数据的存储结构

&emsp;&emsp;我们在Minio中存储一个比较大的文件。如下：

![image.png](/blogs/_archive-2024-assets/f22204fffe74576bdfa6.webp)

然后我们进入对应的磁盘目录中查看

![image.png](/blogs/_archive-2024-assets/d758d9b57d207d24e083.webp)

可以看到在4个磁盘目录中都有上传的文件。而且对应的目录下都有part.1和xl.meta数据

，前者是编码数据块及检验块，后者是元数据文件。

而且可以看看每个文件的大小都是57M【part.1】

```
ls -lh /mydata/minio/data/data4/test666/group1/nacos-server-2.1.0.zip/b7373349-f89c-4047-a460-ce6e28c6eb4a/part.1 
```

![image.png](/blogs/_archive-2024-assets/e7d9ef5b8718a43f0cab.webp)

## 2.纠删码

### 1.2 什么是EC纠删码

EC：纠删码-Erasure Code，是一种编码理论：

* EC是纠错码的一种，通过增加校验片，保证数据可靠性。
* 特性：将数据分成k个分片，生成m个校验片，假设n=k+m，在n个分片中任意选取k个分片，就可以将原始数据恢复回来。

EC不仅应用在存储领域，通信领域也是EC的主要应用场景。

### 1.3 EC(4+2)编解码简介

![image.png](/blogs/_archive-2024-assets/f973cdc551c92d6ba7f9.webp)

上图可以简单说明EC(4+2)的编码、解码以及故障恢复的主要流程，包括：

* chunk：将数据进行分片，如图分成4个片：d1、d2、d3、d4.
* encode：根据4个数据片，生成2个校验片（生成校验片的逻辑请看下一节），这样就形成4+2的EC数据片
* 故障：4+2的EC，允许这6个数据片任意损坏2个，假如损坏了d2和c1，如图
* decode：通过d1、d3、d4、c2，根据EC的计算，可以算出原始的数据块
* re-encode：将原始的数据块分成d1、d2、d3、d4，再次计算出c1、c2
* replace：将损坏的数据块d2、c1进行替换掉即可

可以发现EC的故障恢复比副本更复杂，副本直接再copy一份即可，但是EC比副本的优势是成本，相比于3副本，EC在保证同样可靠性的同时，并不需要保存3份数据。

### 1.4 EC存储的优缺点

**优势**

* 磁盘利用率高，存储成本低，通常是3副本存储的一半，甚至更低
* 和3副本相比，有较低的网络开销，尤其在write的时候表现明显

**劣势**

* 在编、解码过程中通常有较大的CPU占用和网络开销，主要体现在write和故障read、故障恢复的情况下
* EC必须满条带的读写，不足条带的情况下会有padding
* 和3副本相比，EC存储系统更复杂，集群稳定性挑战更大

EC编码的缺点，使得EC最开始并没有应用在线数据，一般都是应用在低频存储中，何为低频存储，就是访问频次较低数据的存储系统中，不过目前已经有的在线存储也开始使用EC编码了。


## 3. EC纠删码原理

![image.png](/blogs/_archive-2024-assets/e78277cb6394af0395a8.webp)


![image.png](/blogs/_archive-2024-assets/1f4dadb53c778d387acd.webp)

![image.png](/blogs/_archive-2024-assets/370a9f7314d822ba4a51.webp)

![image.png](/blogs/_archive-2024-assets/370a9f7314d822ba4a51.webp)
