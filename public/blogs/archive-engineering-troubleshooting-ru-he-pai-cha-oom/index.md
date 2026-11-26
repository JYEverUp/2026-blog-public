# 如何排查OOM

## 1、排查oom:2个步骤

1.导出内存快照
2.使用Eclipse MAT工具分析内存快照，定位问题代码

## 2、步骤1:导出堆内存快照文件

有2种方案

### 方式1:jmap命令导出文件

```
jmap -dump:format=b,file=E:/dump/dump.hprof pid
```

* 方式1适合程序没有没有退出的情况，若程序退出了，需采用方式2

### 方式2:系统oom时自动生成堆内存快照

在java-jar 后面添加2个启动参数

* -XX:+HeapDumpOnOutOfMemoryError: 开启内存溢出时自动生成内存快照
* -XX:HeapDumpPath=/xxx/dump.hprof: 指定dump文件的位置和文件名称

```
java -jar -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=E:/dump/heap-dump.hprof -Xmx1000m lesson055-0.0.1-SNAPSHOT.jar
```
