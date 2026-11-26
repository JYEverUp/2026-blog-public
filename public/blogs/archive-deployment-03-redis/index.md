创建挂载目录

```bash
#创建挂载目录
mkdir -p /data/redis
```

创建yml文件

```bash
vim /data/redis/docker-compose.yml
```

填入配置

```bash
version: '3'
services:
  redis:
    image: redis:6.2.6
    container_name: redis
    restart: always
    ports:
      - 6379:6379
    volumes:
      - /data/redis/redis.conf:/etc/redis/redis.conf
      - /data/redis/data:/data
      - /data/redis/logs:/logs
    command: ["redis-server","/etc/redis/redis.conf"]
```

创建挂载的配置文件

```
vim /data/redis/redis.conf
protected-mode no
port 6379
timeout 0
#rdb配置
save 900 1
save 300 10
save 60 10000
rdbcompression yes
dbfilename dump.rdb
dir /data
appendonly yes
appendfsync everysec
#设置你的redis密码
requirepass 123456
```

`protected-mode no`不加，服务连不上redis的，大坑！！！

到对应目录下启动容器

```bash
cd /data/redis
docker-compose up -d
#如果需要强制重新构建
docker-compose up --force-recreate -d
```

**记得防火墙开端口号 6379  !!!**

用another测试连接
