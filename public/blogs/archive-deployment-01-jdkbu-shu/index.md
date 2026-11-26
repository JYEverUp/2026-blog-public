## JDK环境

用yum命令安装，这种办法简单粗暴，就像盖伦丢技能一样。废话不多说，直接开始操作。

1.首先执行以下命令查看可安装的jdk版本：

```bash
yum -y list java*
```

执行成功后可看到如下界面：

![image-20240924174837500](/blogs/_archive-2024-assets/a94530e9e3a95f2a5971.webp)

选择你要的版本

```bash
yum install -y java-1.8.0-openjdk-devel.x86_64
```

安装完成之后，查看安装的jdk版本，输入以下指令:

```bash
java -version
```

![img](/blogs/_archive-2024-assets/9f5f2b07be799764a9b2.webp)

就安装成功了，环境变量都不用配置。
