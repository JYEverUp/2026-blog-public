# 动态线程池组件

# 项目介绍

## 简介

本项目是采用分布式架构的动态线程池组件，通过SpringBoot Starter的形式引入业务项目，自带web页面，可监控系统的线程池运行状态，动态修改线程池参数，解决并发业务中实际环境复杂，线程池参数不易设置恰当，而重新设置参数却需要重启系统的弊端。

## 技术选型

- Umi
- React
- Ant Design
- SpringBoot
- Redis
- Micrometer
- Prometheus
- Grafana

## 预览

[![image-20240827115452285](/blogs/_archive-2024-assets/54560215ddd3e889e29e.webp)](/blogs/_archive-2024-assets/54560215ddd3e889e29e.webp)

[![image-20240827115504869](/blogs/_archive-2024-assets/873f483553355363796c.webp)](/blogs/_archive-2024-assets/873f483553355363796c.webp)

[![image-20240827115515976](/blogs/_archive-2024-assets/5cd9cfb4646070948c34.webp)](/blogs/_archive-2024-assets/5cd9cfb4646070948c34.webp)

[![image-20240827115538458](/blogs/_archive-2024-assets/7f62b4dcc520ae8b25fc.webp)](/blogs/_archive-2024-assets/7f62b4dcc520ae8b25fc.webp)

[![image-20240827123325986](/blogs/_archive-2024-assets/ed679eeb6b963599228e.webp)](/blogs/_archive-2024-assets/ed679eeb6b963599228e.webp)

## Web管理界面

所有引入 starter 的项目中，有一个节点是 master, 只有master 会注入 web管理端的 bean (当时感觉这样比较方便，做到后面感觉不如单独抽出一个管理系统的项目来)

指定 master 的方式: 配置 `dynamic-thread-pool.web.enabled = true`

## 配置文件详解

```
dynamic-thread-pool:
  # 注册中心配置
  registry:
    redis:
      host: 192.168.67.129
      port: 16379
      # 在 docs/dev-ops/redis/redis.conf 中可以配置
      password: bancheng666..
    # 上报线程池列表的定时任务cron
    report-cron: "0/10 * * * * ?"
  
  # web管理页面配置
  web:
    # 权限管理
    auth:
      # 是否开启权限管理
      enable: true
      # 用户名
      username: dtp
      # 密码
      password: dtp
    # 全局请求路径前缀
    context-path: /dtp
    # 是否开启web管理页面(开启的节点作为master)
    enabled: true
    # grafana dashboard 的url
    grafana-dashboard-url: http://192.168.67.129:3000/d/cdvvy9felux34e/e58aa8-e68081-e7babf-e7a88b-e6b1a0-e79b91-e68ea7?orgId=2&refresh=5s&theme=light

  
  # 告警推送配置
  alarm:
    # 是否开启
    enabled: true
    # 钉钉webhook机器人access-token
    access-token:
      ding-ding: xxxxx
    # 使用哪些平台进行告警推送 (目前只实现了钉钉)
    use-platform:
      - "DingDing"
```

# 部署

## 1. 依赖组件部署 Redis Prometheus Grafana

1. Redis 配置 `docs/dev-ops/redis/redis.conf`

2. Prometheus 配置 `docs/dev-ops/prometheus/prometheus.yml`

   ```
       static_configs:
       # 业务项目的公网地址 (引入动态线程池组件starter的项目)
       # 不要写localhost/127.0.0.1, 写局域网ip/host, 因为prometheus是
       # 在容器内的, localhost访问的是容器本身的端口, 但目的是访问宿主机
         - targets: ['192.168.67.1:8091', '192.168.67.1:8092']
   ```

3. Grafana 配置 `docs/dev-ops/grafana/grafana.ini`

   ```
   [auth.anonymous]
   ; 开启匿名登录
   enabled=true
   ; 匿名登录的组织名
   org_name=Dynamic-thread-pool-guest
   ; 匿名登录的组织权限
   org_role=Viewer
   ; 是否隐藏版本号
   hide_version=true
   [security]
   ; 允许被 iframe/embed/object 等标签嵌入
   allow_embedding = true
   ```

4. 部署 `docs/dev-ops/docker-compose.yml`

## 2. Grafana 配置 Dashboard

1. 访问 Grafana 管理页面  http://host:3000

2. 默认账号密码 admin/admin

3. 首次登录需要修改密码

4. 创建组织，组织名为 `docs/dev-ops/grafana/grafana.ini` 中的 `org_name`

   [![image-20240827112413363](/blogs/_archive-2024-assets/6e89babec71069ea4896.webp)](/blogs/_archive-2024-assets/6e89babec71069ea4896.webp)

   [![image-20240827112432470](/blogs/_archive-2024-assets/9ddf41497bd4bd224688.webp)](/blogs/_archive-2024-assets/9ddf41497bd4bd224688.webp)

5. 切换组织到新创建的组织，如何切换的时候出现一直自动重定向到 localhost, 把url里的org参数删除然后重新访问 http://host:3000 即可，或者修改 grafana 的配置文件 (自查)

   [![image-20240827112632390](/blogs/_archive-2024-assets/70cb49224b53d14e68d2.webp)](/blogs/_archive-2024-assets/70cb49224b53d14e68d2.webp)

6. 创建datasource (prometheus)

   [![image-20240827112756189](/blogs/_archive-2024-assets/483c7285a7c8aa01caef.webp)](/blogs/_archive-2024-assets/483c7285a7c8aa01caef.webp)

   [![image-20240827112807222](/blogs/_archive-2024-assets/e22c955507adf3bbc835.webp)](/blogs/_archive-2024-assets/e22c955507adf3bbc835.webp)

   [![image-20240827112852251](/blogs/_archive-2024-assets/b365057d553e8eef2383.webp)](/blogs/_archive-2024-assets/b365057d553e8eef2383.webp)

   [![image-20240827112932519](/blogs/_archive-2024-assets/c81b50b6f6f59b19fdbf.webp)](/blogs/_archive-2024-assets/c81b50b6f6f59b19fdbf.webp)

   [![image-20240827113012125](/blogs/_archive-2024-assets/76b30c424c576d04889c.webp)](/blogs/_archive-2024-assets/76b30c424c576d04889c.webp)

7. 创建 dashboard

   [![image-20240827113317054](/blogs/_archive-2024-assets/faac935003abd5c99879.webp)](/blogs/_archive-2024-assets/faac935003abd5c99879.webp)

   [![image-20240827113334430](/blogs/_archive-2024-assets/24d6c4f4a9dfc71dd053.webp)](/blogs/_archive-2024-assets/24d6c4f4a9dfc71dd053.webp)

   [![image-20240827113609897](/blogs/_archive-2024-assets/e38a8ba78bcba0b1ad88.webp)](/blogs/_archive-2024-assets/e38a8ba78bcba0b1ad88.webp)

   [![image-20240827113525322](/blogs/_archive-2024-assets/df32ce49bd403839ac6f.webp)](/blogs/_archive-2024-assets/df32ce49bd403839ac6f.webp)

   [![image-20240827113703821](/blogs/_archive-2024-assets/20bbdb3615e7a0042278.webp)](/blogs/_archive-2024-assets/20bbdb3615e7a0042278.webp)

   [![image-20240827114120358](/blogs/_archive-2024-assets/c4c7c56427ec4d9eb7d8.webp)](/blogs/_archive-2024-assets/c4c7c56427ec4d9eb7d8.webp)

   删除掉from参数和to参数，每次就会自动选择 last 6 hours, 而不是固定区间，体验会好一些

   [![image-20240827114451399](/blogs/_archive-2024-assets/3c2486c7155f25cfcc05.webp)](/blogs/_archive-2024-assets/3c2486c7155f25cfcc05.webp)

## 3. 钉钉配置

1. 创建一个群组，设置 => 机器人 => 添加机器人 => 自定义

   [![image-20240827114913775](/blogs/_archive-2024-assets/91df09f4a78efb1be0aa.webp)](/blogs/_archive-2024-assets/91df09f4a78efb1be0aa.webp)

2. 复制机器人url，有个access_token 参数，把它写到 application 配置文件里  | 可以配置关键词，配置之后，推送的消息中必须包含所配置的关键词，否则不予推送

   [![image-20240827115050494](/blogs/_archive-2024-assets/839beaadb85cb9f03313.webp)](/blogs/_archive-2024-assets/839beaadb85cb9f03313.webp)

## 开源项目
[源码地址](https://github.com/18194085604/dynamic-thread-pool)
