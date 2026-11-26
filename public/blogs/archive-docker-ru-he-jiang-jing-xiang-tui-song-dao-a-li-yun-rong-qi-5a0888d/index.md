## [前言](https://note.moguit.cn/#/./Docker/如何将镜像推送到阿里云容器镜像服务/README?id=前言)

原来我都是将镜像推送到Dockerhub中的，因为Dockerhub是国外的软件，所以经常会各种超时的问题，这阵子研究了一下阿里云容器镜像服务，发现可以把一些常用的镜像推送到自己的容器镜像仓库里，然后就可以快速的进行拉取了~，所以我也打算将蘑菇博客的镜像也推送到阿里云，提高后面镜像拉取的速度。

## [阿里云容器镜像服务](https://note.moguit.cn/#/./Docker/如何将镜像推送到阿里云容器镜像服务/README?id=阿里云容器镜像服务)

首先我们需要开通 [阿里云容器镜像服务](https://cr.console.aliyun.com/cn-qingdao/instances/repositories) ，然后创建命名空间

![image-20201130101950767](/blogs/_archive-2024-assets/060e7eac2e3cfca0133b.webp)

这里我已经创建了一个 `mogublog`，创建完成后，我们需要到访问凭证设置我们的密码，然后复制 登录脚本

![image-20201130102300039](/blogs/_archive-2024-assets/6a0f93b4595b540a9a55.webp)

然后在我们的服务器登录docker进行测试

```bash
# 登录阿里云容器镜像服务
docker login --username=moxi****@163.com registry.cn-shenzhen.aliyuncs.comCopy to clipboardErrorCopied
```

登录成功

![image-20201130102403332](/blogs/_archive-2024-assets/608176159d9cd6d40b11.webp)

## [提交镜像](https://note.moguit.cn/#/./Docker/如何将镜像推送到阿里云容器镜像服务/README?id=提交镜像)

登录后，首先可以查看目前已经存在的镜像有哪些

![image-20201130103411570](/blogs/_archive-2024-assets/ade6e757ed956e8504f2.webp)

我们就可以开始给镜像打tag了 【针对已经制作好的镜像打TAG】

```bash
# 格式
docker tag [ImageId] registry.cn-shenzhen.aliyuncs.com/mogublog/mogu_admin:[镜像版本号]
# 样例代码【如下】
docker tag 5f96da15eb94  registry.cn-shenzhen.aliyuncs.com/mogublog/mogu_blog_nacos:latestCopy to clipboardErrorCopied
```

如果你的镜像没有制作好，可以先制作镜像

```bash
# 查看容器ID
docker ps -a
# 提交镜像
docker commit -m "制作镜像" 容器ID registry.cn-shenzhen.aliyuncs.com/mogublog/mogu_blog_nacos:latestCopy to clipboardErrorCopied
```

打完tag后，我们就能够看到我们的镜像的tag了

```bash
docker images;Copy to clipboardErrorCopied
```

![image-20201130103608482](/blogs/_archive-2024-assets/b14aaae59dd980618ba9.webp)

下面我们就可以提交到我们的阿里云仓库

```bash
docker push registry.cn-shenzhen.aliyuncs.com/mogublog/mogu_blog_nacos:latestCopy to clipboardErrorCopied
```

![image-20201130104229395](/blogs/_archive-2024-assets/06eff6ec21d48dbe28df.webp)

推送完成后，我们到阿里云容器服务仓库，即可看到我们刚刚提交的了
