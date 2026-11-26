### 下载docker

根据提示输入`y`。

```bash
#yum install docker（这个下载的是老版本，不要用视频的这个，用下面的）
# 1.阿里云镜像资源（先执行这个下载加速）
yum-config-manager --add-rep https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
#2.安装docker
yum install -y docker-ce
```

![image-20240924191013134](/blogs/_archive-2024-assets/bc7e1bbcb280930be010.webp)

### **启动Docker服务**

安装完成后，使用下面的命令来启动 docker 服务，并将其设置为开机启动：

```bash
service docker start
chkconfig docker on
```

![image-20240924191005820](/blogs/_archive-2024-assets/7706df2bddd7571807e7.webp)

测试Docker是否安装成功

```bash
docker version
```

![img](/blogs/_archive-2024-assets/7586fc6dda8acc4a1821.webp)

输入上述命令，返回docker的版本相关信息，证明docker安装成功。

### 设置国内镜像

```bash
vi  /etc/docker/daemon.json

#添加后
{
    "registry-mirrors": ["https://mirror.ccs.tencentyun.com"],
    "live-restore": true
}
```

•依次执行以下命令，重新启动 Docker 服务。

```bash
systemctl daemon-reload
service docker restart
```

• 检查是否生效

```bash
docker info
```

查看是否有如下信息

```bash
Registry Mirrors:
    https://mirror.ccs.tencentyun.com/
```

![image-20240924190955180](/blogs/_archive-2024-assets/2b33c2e33db3862e9528.webp)

### Docker Compose的安装

我们一般都是通过docker compose来安装中间件，所以这个必不可少。会比较慢，可手动下载

```bash
curl -L https://github.com/docker/compose/releases/download/1.28.6/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
```

![img](/blogs/_archive-2024-assets/b515321534bb120cc7a4.webp)

[下载地址](https://github.com/docker/compose/releases/download/1.28.6/docker-compose-Linux-x86_64)，下载后执行命令 

[百度云下载地址](https://pan.baidu.com/s/1xbK9p9Gz_2qVNgZhU2HseA?pwd=8888) 

```bash
cd /usr/local/bin
rz #直接通过rz导入文件
```

将可执行权限应用于二进制文件：

```bash
sudo chmod +x /usr/local/bin/docker-compose
```

测试是否安装成功：

```bash
docker-compose --version
```

![img](/blogs/_archive-2024-assets/1518433a21974caf450b.webp)

### **常用命令**

除过以上我们使用的Docker命令外，Docker还有一些其它常用的命令

拉取docker镜像

```
docker pull image_name
```

查看宿主机上的镜像，Docker镜像保存在/var/lib/docker目录下:

```
docker images
```

删除镜像

```
docker rmi docker.io/tomcat:7.0.77-jre7 或者 docker rmi b39c68b7af30
```

查看当前有哪些容器正在运行

```
docker ps
```

查看所有容器

```
docker ps -a
```

启动、停止、重启容器命令：

```
docker start container_name/container_id docker stop container_name/container_id docker restart container_name/container_id
```

后台启动一个容器后，如果想进入到这个容器，可以使用attach命令：

```
docker attach container_name/container_id
```

删除容器的命令：

```
docker rm container_name/container_id
```

删除所有停止的容器：

```
docker rm $(docker ps -a -q)
```

查看当前系统Docker信息

```
docker info
```

从Docker hub上下载某个镜像:

```
docker pull centos:latest docker pull centos:latest
```

查找Docker Hub上的nginx镜像

```
docker search nginx
```

执行docker pull centos会将Centos这个仓库下面的所有镜像下载到本地repository。

1、查看某个容器的使用状态

2、限制内存使用

![img](/blogs/_archive-2024-assets/bac64246feb1a1e7315a.webp)
