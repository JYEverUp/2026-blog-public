## **一、本章诉求**

完成一下应用服务的镜像打包和部署操作。因为这个时候代码的开发量还不多，也不需要在部署的时候考虑如：MySQL、Redis 以及各个配置文件的操作。但又可以支撑我们验证服务。所以先来完成下这块的内容。

## **二、流程设计**

整个流程为；在工程中添加 Dockerfile 配置文件，对工程进行镜像打包。并把工程推送到本地和远程 Docker 仓库进行部署验证。 ![img](/blogs/_archive-2024-assets/8a6422d8f4c2e1a0935d.webp)

本地的 Docker 直接在 IDEA 配置即可启动，远程的服务仓库一种是配置开启2375端口，另外一种把镜像文件推送到 [**https://hub.docker.com**](https://hub.docker.com/) 再通过拉取的方式使用。

## **三、方案实现**

### **1. 镜像配置**

首先需要在 chatgpt-api 工程中添加 Dockerfile 文件，这样才能去操作镜像文件的打包处理。这个过程一共有3个文件；Dockerfile、[build.sh](http://build.sh/)、[start.sh](http://start.sh/)![img](/blogs/_archive-2024-assets/3bfbf309513d3fab06af.webp)

1. 文件：https://gitcode.net/KnowledgePlanet/chatgpt/chatgpt-api/-/tree/230504-xfg-docker - 3个文件可以直接从仓库的源码中获取。

### **2. 镜像打包**

![img](/blogs/_archive-2024-assets/7190a201a71665f56fdd.webp)

1. 操作前，本地机器要先开启 Docker 服务。☞ [**https://t.zsxq.com/0dgNDOINd**](https://t.zsxq.com/0dgNDOINd)
2. 通过 IDEA 右侧的 Maven 中 install 进行进行打包。每次修改代码后，记得打包。如果本机配置较低，最好执行一次clean，否则文件可能没法拿到更多的服务器资源进行主动刷新。机器配置差，代码霸哥多
3. install 构建完成后，执行 [build.sh](http://build.sh/) 这个时候会把镜像打包到 Docker 容器。
4. 启动服务，你可以通过命令或者直接点击绿色箭头运行，这样就可以把服务部署到Docker容器了。

### **3. 推送镜像**

这里我们先不用着急启动服务，小傅哥先教大家，怎么把文件推送到 Docker 的仓库。

#### **3.1 创建仓库**

![img](/blogs/_archive-2024-assets/3a0ef711517752b7c83a.webp)

1. 首先，你需要在 [**https://hub.docker.com/repository/create**](https://hub.docker.com/repository/create) 创建一个仓库。仓库中的名字也是你配置到 [build.sh](http://build.sh/) 中脚本的名字 docker build -f ./Dockerfile -t fuzhengwei/chatgpt-api . 千万一致，否则是不能使用的。

#### **3.2 Push 镜像**

![img](/blogs/_archive-2024-assets/521ee42abcce31cc33a8.webp)

1. 之后，你就可以打开 Docker 找到 Images 你的镜像。如果较多，你可以搜索哈。
2. 通过 Push to Hub 把你的镜像推送到仓库中。现在你可以像使用其他任何一个镜像一样，使用你的镜像文件了。

![img](/blogs/_archive-2024-assets/dfe971fee7924f3097ae.webp)

### **4. 使用镜像**

在一个任意已经安装了 Docker 发服务器上，执行此段脚本，即可运行服务。



![img](/blogs/_archive-2024-assets/9df235f665124fb000ac.webp)

docker run -p 8080:8080 \

--name chatgpt-api \

-d fuzhengwei/chatgpt-api

1. 如果是本地 Docker 部署，就不需要执行步骤3推送镜像到仓库中了。

## **四、IDEA 配置 Docker**

### **1. 本地配置**  

![img](/blogs/_archive-2024-assets/677d7efc29255bb5e326.webp)

![img](/blogs/_archive-2024-assets/84ffa0deb7381a6c7cc6.webp)

![img](/blogs/_archive-2024-assets/7de1b12a1cc47496e1ca.webp)

```plain
# 基础镜像
FROM openjdk:8-jre-slim

# 作者
MAINTAINER xiaofuge

# 配置
ENV PARAMS=""

# 时区
ENV TZ=PRC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 添加应用
ADD target/chatgpt-chat-app.jar /chatgpt-chat-app.jar

ENTRYPOINT ["sh","-c","java -jar $JAVA_OPTS /chatgpt-chat-app.jar $PARAMS"]
```

在 IDEA 中是可以直接配置Docker 的，这样你可以通过这一个配置后的操作界面管理 Docker 容器。比如，你可以发布镜像、删除镜像、部署服务。也可以看到服务的启动日志。**注意**：本地连接的速度没问题，但如果是远程连接会有一些卡顿。

1. 在 IntelliJ IDEA【Ultimate版】界面👇🏻下面有一个 Services 服务，可以打开配置 Docker 连接。
2. 配置后，你就可以点击绿色箭头，或者双击 Docker 打开服务了。

![img](/blogs/_archive-2024-assets/0c961b867dcb6d5a0fce.webp)

### **2. 远程配置**  

为了可以让本地连接到远程的 Dcoker 容器，那么需要修改 docker.service 开启 2375 端口，并且云服务器也需要开启这个端口。注意：用完关闭！！！

![img](/blogs/_archive-2024-assets/e068af39f9d51fcaee5a.webp)

操作步骤；

#### **2.1 查看 docker.service**

```
cat /usr/lib/systemd/system/docker.service
```

#### **2.2 修改 docker.service**

```
vim /usr/lib/systemd/system/docker.service

ExecStart=/usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock 修改为 ExecStart=/usr/bin/dockerd -H tcp://0.0.0.0:2375 -H fd:// --containerd=/run/containerd/containerd.sock
```

#### **2.3 重启服务**

systemctl daemon-reload && systemctl restart docker

#### **2.4 查看监听端口和进程**

```
ps -ef | grep docker

ss -ntl | grep 2375

[root@chatgpt-guide ~]# ps -ef | grep docker

root 130911001:33 ? 00:00:00 /usr/bin/dockerd -H tcp://0.0.0.0:2375 -H fd:// --containerd=/run/containerd/containerd.sock

root 1321813091001:33 ? 00:00:00 /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 9000 -container-ip 172.17.0.2 -container-port 9000

root 1322213091001:33 ? 00:00:00 /usr/bin/docker-proxy -proto tcp -host-ip :: -host-port 9000 -container-ip 172.17.0.2 -container-port 9000

root 1323413091001:33 ? 00:00:00 /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 443 -container-ip 172.17.0.3 -container-port 443

root 1323813091001:33 ? 00:00:00 /usr/bin/docker-proxy -proto tcp -host-ip :: -host-port 443 -container-ip 172.17.0.3 -container-port 443

root 1327613091001:33 ? 00:00:00 /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 80 -container-ip 172.17.0.3 -container-port 80

root 1328513091001:33 ? 00:00:00 /usr/bin/docker-proxy -proto tcp -host-ip :: -host-port 80 -container-ip 172.17.0.3 -container-port 80

root 1341612656001:34 pts/100:00:00 grep --color=auto docker

[root@chatgpt-guide ~]# ss -ntl | grep 2375

LISTEN 0128 [::]:2375 [::]:*

[root@chatgpt-guide ~]#
```



### **2.5 配置 IDEA Docker 链接**  

![img](/blogs/_archive-2024-assets/35c89c8ae3be9563946f.webp)

1. 配置的时候把地址粘贴进去就可以了；tcp://180.76.171.***:2375 - 把IP地址换你的。【2375 云服务器体验完，记得关闭端口，避免被当矿机】
2. 虽然能配置使用，但速度较差。尤其把打包的镜像文件推送到服务器的时候，速度更差一些。不如使用推送镜像到 [**https://hub.docker.com/**](https://hub.docker.com/) 再使用。

## **五、测试验证**

```
@Test

public void test_chatGPT()throws IOException {

CloseableHttpClienthttpClient= HttpClientBuilder.create().build();

// 用获取的 token 替换，默认有效期60分钟。地址非长期有效，只做学习验证。

HttpPostpost=newHttpPost("https://api.xfg.im/b8b6/v1/completions?token=eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ4ZmciLCJleHAiOjE2O");

 post.addHeader("Content-Type", "application/json");

 post.addHeader("Authorization", "Bearer sk-替换为你的 Api Keys");

// text-davinci-003 可以更新最新 chatgpt-sdk-java 测试 master 分支的 BusyTest 里面的代码

StringparamJson="{\"model\": \"text-davinci-003\", \"prompt\": \"帮我写一个java冒泡排序\", \"temperature\": 0, \"max_tokens\": 1024}";

StringEntitystringEntity=newStringEntity(paramJson, ContentType.create("text/json", "UTF-8"));

 post.setEntity(stringEntity);

 System.out.println("请求入参：" + paramJson);

CloseableHttpResponseresponse= httpClient.execute(post);

if (response.getStatusLine().getStatusCode() == HttpStatus.SC_OK) {

Stringres= EntityUtils.toString(response.getEntity());

// api.xfg.im:443 requested authentication 表示 token 错误或者过期。

 System.out.println("测试结果：" + res);

 } else {

 System.out.println(response.getStatusLine().getStatusCode());

 }

}
```

**操作步骤**：

1. 获取 token：http://api.xfg.im:8080/authorize?username=xfg&password=123 - 这个是测试的地址，已经不在需要了。如果你自己按照课程学习部署了一个，可以访问自己的地址获取 token。另外还可以阅读链接评论置顶第一条获取key https://t.zsxq.com/163o5FKvc 也能完成本节测试。
2. Bearer sk-替换为你的 Api Keys，需要你有一个 API Key。因为ChatGPT比较难申请Key，建议按照课程说明中，对接ChatGLM。https://t.zsxq.com/133o5FKvc 如果你非得要 ChatGPT Key 也可以联系小傅哥获取。

**测试结果**：

```
{

 "id": "chatcmpl-8hwa1EXAUokxyJ92EVjIhcPrxfRAr",

 "object": "chat.completion",

 "created": 1705483977,

 "model": "gpt-3.5-turbo-1106",

 "choices": [

 {

 "index": 0,

 "message": {

 "role": "assistant",

 "content": "```java\npublic class BubbleSort {\n\n public static void main(String[] args) {\n int[] arr = {5, 2, 9, 1, 6, 4, 3, 7, 8};\n bubbleSort(arr);\n for (int num : arr) {\n System.out.print(num + \" \");\n }\n }\n\n public static void bubbleSort(int[] arr) {\n int n = arr.length;\n for (int i = 0; i < n - 1; i++) {\n for (int j = 0; j < n - i - 1; j++) {\n if (arr[j] > arr[j + 1]) {\n int temp = arr[j];\n arr[j] = arr[j + 1];\n arr[j + 1] = temp;\n }\n }\n }\n }\n}\n```"

 },

 "logprobs": null,

 "finish_reason": "stop"

 }

 ],

 "usage": {

 "prompt_tokens": 15,

 "completion_tokens": 186,

 "total_tokens": 201

 },

 "system_fingerprint": "fp_fe56e538d5"

}
```

1. 从测试结果可以看到，我们已经可以通过 Token 授权的方式控制访问 OpenAI 了。
