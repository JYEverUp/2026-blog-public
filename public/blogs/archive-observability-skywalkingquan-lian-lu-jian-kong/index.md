## 一、章节目的

![img](/blogs/_archive-2024-assets/d86981c474174633aa01.webp)

本章节通过 Docker 方式部署一套 skywalking 非入侵的全链路监控系统，并在对应的测试工程中通过 skywalking-agent 字节码增强组件，采集系统运行时的各项信息到 skywalking-ui 监控平台观察数据。

- **源码**：https://github.com/18194085604/skywalking.git

## 二、基本环境

- Docker version 1.13.1
- Docker compose - 用于在云服务器环境中执行的 docker-compose 文件
- Portainer Docker 容器管理面板

## 三、监控配置

skywalking 的安装，需要 elasticsearch - 存放数据、skywalking-oap 接收数据、skywalking-ui 界面展示。以及还需要一个 skywalking-agent 用于配置到应用程序中，采集监控数据。注意这些内容在官网中，都已提供，地址：[https://skywalking.apache.org/downloads/(opens new window)](https://skywalking.apache.org/downloads/)

这里提供了Docker的自动部署以及下载好了 skywalking-agent 所以你就不需要一个个去下载安装了。接下来会分别介绍在`本地环境`和`云服务器`两套环境安装，这样可以更加方便小伙伴做测试验证。

在进行下面的步骤前，请先下载 skywalking 监控工程；https://github.com/18194085604/skywalking.git

![img](/blogs/_archive-2024-assets/652c06d2b07dadedb8f7.webp)

### 1. 本地环境

**脚本**：`/road-map/skywalking/docs/dev-ops/skywalking` - 你可以打开工程找到这个位置，查看最新脚本。

```java
version: '3.8'
services:
  elasticsearch:
    image: elasticsearch:7.16.2
    container_name: elasticsearch
    ports:
      - "9200:9200"
    healthcheck:
      test: [ "CMD-SHELL", "curl --silent --fail localhost:9200/_cluster/health || exit 1" ]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    environment:
      - discovery.type=single-node
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - ./data/es_data:/usr/share/elasticsearch/data

  oap:
    image: apache/skywalking-oap-server:8.9.0
    container_name: oap
    depends_on:
      elasticsearch:
        condition: service_healthy
    links:
      - elasticsearch
    ports:
      - "11800:11800"
      - "12800:12800"
    healthcheck:
      test: [ "CMD-SHELL", "/skywalking/bin/swctl ch" ]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    environment:
      SW_STORAGE: elasticsearch
      SW_STORAGE_ES_CLUSTER_NODES: elasticsearch:9200
      SW_HEALTH_CHECKER: default
      SW_TELEMETRY: prometheus
      JAVA_OPTS: "-Xms1024m -Xmx1024m"

  skywalking-ui:
    image: apache/skywalking-ui:8.9.0
    container_name: skywalking-ui
    depends_on:
      oap:
        condition: service_healthy
    links:
      - oap
    ports:
      - "9090:8080"
    environment:
      SW_OAP_ADDRESS: http://oap:12800
 
  
```

![img](/blogs/_archive-2024-assets/587bfb8fe63951a8c196.webp)

- 在 Docker 安装并正确✅启动后，你就可以点击这个按钮了。它会帮你自动运行安装出整套的 skywalking 监控系统。非常方便。
- 如果你点击红圈下面的单个按钮，那么代表的是只安装当前一个应用。
- 你可以通过命令执行 `skywalking-docker-compose.yml` 的安装：`/usr/local/bin/docker-compose -f /docs/dev-ops/skywalking/skywalking-docker-compose.yml up -d` - 在云服务器端也是使用这个命令安装。

访问验证：[http://localhost:9090/ (opens new window)](http://localhost:9090/)- 我设置的端口是9090，如果你是其他的则需要修改。

### 2. 云服务器

- 准备一台2核4G的云服务器，整个服务启动后会占用2-3G左右
- 下载 ssh 工具，用于连接云服务。
- docker-compose 安装

#### 2.1 文件上传

通过 ssh 的 sftp 工具，把 skywalking/docs 全部上传到云服务器。

![img](/blogs/_archive-2024-assets/e316af1e9ed16b99b44f.webp)

#### 2.2 执行脚本

![img](/blogs/_archive-2024-assets/c541d26786ac3e0e7519.webp)

```shell
[root@dev-ops ~]# cd /docs/
[root@dev-ops docs]# ls
dev-ops  skywalking-agent  sql
[root@dev-ops docs]# cd dev-ops/
[root@dev-ops dev-ops]# ls
environment  skywalking
[root@dev-ops dev-ops]# cd skywalking/
[root@dev-ops skywalking]# ls
skywalking-docker-compose.yml
[root@dev-ops skywalking]# /usr/local/bin/docker-compose -f /docs/dev-ops/skywalking/skywalking-docker-compose.yml up -d
[+] Building 0.0s (0/0)                                                                          
[+] Running 3/3
 ✔ Container elasticsearch  Healthy                                                         0.5s 
 ✔ Container oap            Healthy                                                         1.0s 
 ✔ Container skywalking-ui  Running                                                         0.0s
 
    
```

安装完成记得开放端口；

- 9090 端口；skywalking-ui 界面端口
- 11800 端口；监控数据上报端口

安装完成后就可以访问监控界面了；[http://180.76.138.**:9090/ (opens new window)](http://180.76.0.138:9090**/)- 替换为你的IP地址

## 四、数据上报

监控数据的上报使用的是 Javaagent 技术，在程序加载时候通过字节码增强技术，在需要监控的位置自动加上额外的监控代码，来采集系统的运行数据。所以我们这里可以把 Javaagent 配置到程序启动上，也可以配置到 Docker 镜像打包上。

### 1. 程序启动 - 加入探针

配置到 IDEA 程序启动中，VM Options 参数：`-javaagent:/Users/fuzhengwei/1024/KnowledgePlanet/road-map/skywalking/docs/skywalking-agent/skywalking-agent.jar -Dskywalking.agent.service_name=skywalking-app-dev -Dskywalking.collector.backend_service=127.0.0.1:11800`

![img](/blogs/_archive-2024-assets/720d9ed8d1a9ecd16620.webp)

- 注意修改；`地址`、`应用名`、`IP`【如果是云服务，就配置云服务的IP地址】

### 2. 镜像打包 - 加入探针

当程序需要运行在云服务的 Docker 容器了，就不能这样配置了，需要把配置打包到镜像里，更加方便执行。

```java
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
ADD /target/skywalking-app.jar /skywalking-app.jar
## 在镜像运行为容器后执行的命令
ENTRYPOINT ["java", "-Xmx512m", "-javaagent:/docs/skywalking-agent/skywalking-agent.jar", "-Dskywalking.agent.service_name=skywalking-app", "-Dskywalking.collector.backend_service=180.76.138.41:11800", "-jar", "/skywalking-app.jar"]
 
```

- 注意；`/docs/skywalking-agent/skywalking-agent.jar` 这个是通过 SFTP 工具上传到云服务器端的。但不在 Docker 容器里，等部署程序的时候还需要做一次文件映射。

## 五、启动服务

如果你希望在把应用程序部署到云服务端，一种是通过 IDEA 连接 Docker 服务，另外一种是把应用程序的镜像发布到Docker Hub。这里我们通过 IDEA 连接 Docker 服务。

**脚本**：`skywalking/src/bin/main/start.sh`

```java
CONTAINER_NAME=skywalking-app
IMAGE_NAME=fuzhengwei/skywalking-app:1.0
PORT=9091

echo "容器部署开始 ${CONTAINER_NAME}"

# 停止容器
docker stop ${CONTAINER_NAME}

# 删除容器
docker rm ${CONTAINER_NAME}

# 启动容器 skywalking-agent 下载：https://archive.apache.org/dist/skywalking/java-agent/8.9.0/apache-skywalking-java-agent-8.9.0.tgz
docker run --name ${CONTAINER_NAME} \
-p ${PORT}:${PORT} \
-v /docs/skywalking-agent/:/docs/skywalking-agent/ \
-d ${IMAGE_NAME}

#docker run --name skywalking-app \
#-p 9091:9091 \
#-v /docs/skywalking-agent/:/docs/skywalking-agent/ \
#-d fuzhengwei/skywalking-app:1.2

echo "容器部署成功 ${CONTAINER_NAME}"

docker logs -f ${CONTAINER_NAME}
 

    
```

- 你可以在云服务执行 start.sh 脚本，或者直接复制 docker run 命令，去执行启动。
- 注意；`-v /docs/skywalking-agent/:/docs/skywalking-agent/ \` 是你的映射地址，只有这样才能拿到 skywalking-agent
- 另外记得按照 MySQL【environment-docker-compose.yml】 到云服务以及执行 road-map.sql 文件。
