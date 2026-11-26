学习参考文档https://java.isture.com/arch/minio/minio-concept.html

比较完整https://blog.csdn.net/weixin_39060009/article/details/115520696

创建挂载目录

```bash
#创建挂载目录
mkdir -p /data/minio
```

创建yml文件

```bash
vim /data/minio/docker-compose.yml
```

填入配置

```bash
version: '3'
services:
  minio:
    image: "quay.io/minio/minio:RELEASE.2022-08-02T23-59-16Z"
    container_name: minio
    ports:
      - "9000:9000" # api 端口
      - "9001:9001" # 控制台端口
    environment:
      TZ: Asia/Shanghai # 时区上海
      MINIO_ROOT_USER: admin # 管理后台用户名
      MINIO_ROOT_PASSWORD: 12345678 # 管理后台密码，最小8个字符
      MINIO_SERVER_URL: "https://minio.mallchat.cn" # 指定分享的域名
      MINIO_COMPRESS: "off" # 开启压缩 on 开启 off 关闭
      MINIO_COMPRESS_EXTENSIONS: "" # 扩展名 .pdf,.doc 为空 所有类型均压缩
      MINIO_COMPRESS_MIME_TYPES: "" # mime 类型 application/pdf 为空 所有类型均压缩
    volumes:
      - /data/minio/data:/data/ # 映射当前目录下的data目录至容器内/data目录      
      - /data/minio/config:/root/.minio/ # 映射配置目录
    command: server --address ':9000' --console-address ':9001' /data  # 指定容器中的目录 /data
    privileged: true
```

有些非大陆服务器,，会出现登录不上，密码不对`invalid Login`的错误提示，改用下面的配置重新构建

```
docker-compose up --force-recreate -d
version: '3'
services:
  minio:
    image: "quay.io/minio/minio:RELEASE.2022-08-02T23-59-16Z"
    container_name: minio
    ports:
      - "9000:9000" # api 端口
      - "9001:9001" # 控制台端口
    environment:
      MINIO_ROOT_USER: admin # 管理后台用户名
      MINIO_ROOT_PASSWORD: 12345678 # 管理后台密码，最小8个字符
      MINIO_COMPRESS: "off" # 开启压缩 on 开启 off 关闭
      MINIO_COMPRESS_EXTENSIONS: "" # 扩展名 .pdf,.doc 为空 所有类型均压缩
      MINIO_COMPRESS_MIME_TYPES: "" # mime 类型 application/pdf 为空 所有类型均压缩
    volumes:
      - /data/minio/data:/data/ # 映射当前目录下的data目录至容器内/data目录      
      - /data/minio/config:/root/.minio/ # 映射配置目录
    command: server --address ':9000' --console-address ':9001' /data  # 指定容器中的目录 /data
    privileged: true
```

有些非大陆服务器,，会出现登录不上，密码不对`invalid Login`的错误提示，改用下面的配置重新构建

```
docker-compose up --force-recreate -d
version: '3'
services:
  minio:
    image: "quay.io/minio/minio:RELEASE.2022-08-02T23-59-16Z"
    container_name: minio
    ports:
      - "9000:9000" # api 端口
      - "9001:9001" # 控制台端口
    environment:
      MINIO_ROOT_USER: admin # 管理后台用户名
      MINIO_ROOT_PASSWORD: 12345678 # 管理后台密码，最小8个字符
      MINIO_COMPRESS: "off" # 开启压缩 on 开启 off 关闭
      MINIO_COMPRESS_EXTENSIONS: "" # 扩展名 .pdf,.doc 为空 所有类型均压缩
      MINIO_COMPRESS_MIME_TYPES: "" # mime 类型 application/pdf 为空 所有类型均压缩
    volumes:
      - /data/minio/data:/data/ # 映射当前目录下的data目录至容器内/data目录      
      - /data/minio/config:/root/.minio/ # 映射配置目录
    command: server --address ':9000' --console-address ':9001' /data  # 指定容器中的目录 /data
    privileged: true
```

到对应目录下启动容器

```bash
cd /data/minio
docker-compose up -d
#如果需要强制重新构建
docker-compose up --force-recreate -d
```

打开对应的控制台

[http://ip:9001/](http://101.33.251.36:9001/)

**记得防火墙开端口号 9000,9001  !!!**，输入帐号密码admin，12345678

![img](/blogs/_archive-2024-assets/791ad772571259b5f79f.webp)

创建一个测试捅，尝试上传一张图片。

![img](/blogs/_archive-2024-assets/cf21856612dae64b0098.webp)

设置桶为公开桶

![image-20240924190744319](/blogs/_archive-2024-assets/5a09cf6fdc310ed24d64.webp)

![image-20240924190736898](/blogs/_archive-2024-assets/553d53c07a1d51b7f0cc.webp)

![image-20240924190728843](/blogs/_archive-2024-assets/f4ddef775be9d0ddb2fd.webp)

点击分享

![image-20240924190720460](/blogs/_archive-2024-assets/8927de5006327791658f.webp)

url替换成自己的服务器ip，删除后面的权限信息。尝试访问（不成功也没关系）

创建一个权限用户，获取密钥

![image-20240924190704984](/blogs/_archive-2024-assets/c7e15a04a9af8ce4fd90.webp)

![image-20240924190656149](/blogs/_archive-2024-assets/3f1ce46a3473c658754f.webp)

会随机生成accessKey secretKey，点击create按钮后.
会将这两个key进行展示，此时可以复制粘贴到一个文本文件上，后续使用代码上传文件时需要用到这两个key

在配置文件中配置如下信息

![image-20240924190647949](/blogs/_archive-2024-assets/4c832771d3bf4657d061.webp)

endpoint就是你的minio部署的ip地址。

配置nginx的转发，一次性配置规范点，为对象存储搞个二级域名和https。

端口重定向增加minio.mallchat.cn

```plain
server {
    listen       80;
    server_name  api.mallchat.cn minio.mallchat.cn;
    #将请求转成https
    rewrite ^(.*)$ https://$host$1 permanent;
}
```

增加一个二级域名的监听

```bash
server {
    listen       443 ssl;
    server_name  minio.mallchat.cn;
    #频率控制
    limit_req zone=one burst=10 nodelay;

    ssl_certificate      ../cert/minio.mallchat.cn.pem;
    ssl_certificate_key  ../cert/minio.mallchat.cn.key;

    ssl_session_cache    shared:SSL:1m;
    ssl_session_timeout  5m;
    location / {
        client_body_buffer_size 10M;
        client_max_body_size 10G;
        proxy_buffers 1024 4k;
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

证书放在指定位置，你懂的。

![img](/blogs/_archive-2024-assets/87e2a95cb3b5b731fe45.png)
