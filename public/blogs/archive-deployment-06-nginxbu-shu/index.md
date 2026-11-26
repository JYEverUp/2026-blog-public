## nginx部署

去官网也下个[windows版本](https://nginx.org/en/download.html)的，本地调试成功，再放到服务器去执行，容易排查错误。

**用docker的坑太多了，nginx决定用原生的o(╥﹏╥)o。**

1、安装nginx前首先安装四个依赖包 --以下命令一键安装四个依赖

`yum -y install gcc zlib zlib-devel pcre-devel openssl openssl-devel`
2、在你的linux服务器上创建目录：install

```
cd /root`
`mkdir install
```

make报错可看，[参考](https://blog.csdn.net/qq_45697992/article/details/120028370)
3、进入刚刚创建的目录：

`cd install`
4、下载并解压安装包

`wget http://nginx.org/download/nginx-1.13.7.tar.gz`
`tar -zxvf nginx-1.13.7.tar.gz`     ---解压nginx安装包
5、进入刚刚解压好的目录：

```
cd nginx-1.13.7
```

5.1、增加https模块，后期就不麻烦

```bash
./configure --prefix=/usr/local/nginx --conf-path=/usr/local/nginx/conf/nginx.conf --pid-path=/usr/local/nginx/conf/nginx.pid --lock-path=/usr/local/nginx/lock/nginx.lock --with-http_ssl_module
```


6、分别执行下面命令
`make`          --- 用来编译( 从Makefile中读取指令，然后编译)
`make install`     --- 用来安装( 从Makefile中读取指令，安装到指定的位置)
7、编辑启动端口(图片的端口是经过修改的，默认是80端口)

```
cd /usr/local/nginx/conf
vim nginx.conf
```

编辑好之后，按esc退出编辑模式，然后  :wq 进行保存退出
8、启动nginx

```
/usr/local/nginx/sbin/nginx
```

访问服务器ip测试

![image-20240924190501434](/blogs/_archive-2024-assets/3c987fbc533e60f40ac8.webp)

**windows本地调试nginx注意，不要重复启动。同时运行多个nginx，导致配置一直不生效，坑死了！！！**

**常用命令**

nginx -s stop

nginx -s reload

## nginx配置

我项目的nginx配置如下，可直接复制使用.下面一个个介绍里面的用途

```bash
#user  nobody;
worker_processes  1;

#error_log  logs/error.log;
#error_log  logs/error.log  notice;
#error_log  logs/error.log  info;

#pid        logs/nginx.pid;


events {
    worker_connections  25000;
}

http {
    include       mime.types;
    include       ip.black;
    default_type  application/octet-stream;
    ###############频率控制#######################
    geo $limit {
        default 1;
        127.0.0.1 0;     # 本机地址
    }

    map $limit $limit_key {
        0 "";
        1 $binary_remote_addr;
    }

    limit_req_zone $limit_key zone=one:2m rate=10r/s;
    ###############频率控制#######################
    #log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
    #                  '$status $body_bytes_sent "$http_referer" '
    #                  '"$http_user_agent" "$http_x_forwarded_for"';

    #access_log  logs/access.log  main;

    sendfile        on;
    #tcp_nopush     on;

    #keepalive_timeout  0;
    keepalive_timeout  65;

    #gzip  on;

    server {
        listen       80;
        server_name  api.mallchat.cn minio.mallchat.cn;
		#将请求转成https
		rewrite ^(.*)$ https://$host$1 permanent;
    }
    #对象存储专用
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
            proxy_pass http://127.0.0.1:9000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            client_body_buffer_size 10M;
            client_max_body_size 10G;
            proxy_buffers 1024 4k;
        }
    }
    server {
            listen       443 ssl;
            server_name  api.mallchat.cn;
            #频率控制
            limit_req zone=one burst=10 nodelay;

            ssl_certificate      ../cert/api.mallchat.cn.pem;
            ssl_certificate_key  ../cert/api.mallchat.cn.key;

            ssl_session_cache    shared:SSL:1m;
            ssl_session_timeout  5m;

    		location = /websocket {
                proxy_pass http://127.0.0.1:8090/;
    			proxy_http_version 1.1;
    			proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "upgrade";
    			proxy_read_timeout 600s;
            }
            location / {
                proxy_pass http://127.0.0.1:8080;
    			proxy_set_header Host $host;
    			proxy_set_header X-Real-IP $remote_addr;
                add_header 'Access-Control-Allow-Origin' '*';
                add_header 'Access-Control-Allow-Headers' '*';
                add_header 'Access-Control-Allow-Methods' '*';
                # OPTIONS 直接返回204
                if ($request_method = 'OPTIONS') {
                     return 204;
                 }
                            }
                location = /MP_verify_GTPosqCvKIDnld6z.txt {
                                alias /usr/local/nginx/html/MP_verify_GTPosqCvKIDnld6z.txt;
                            }



            #error_page  404              /404.html;

            # redirect server error pages to the static page /50x.html
            #
            error_page   500 502 503 504  /50x.html;
            location = /50x.html {
                root   html;
            }

            # proxy the PHP scripts to Apache listening on 127.0.0.1:80
            #
            #location ~ \.php$ {
            #    proxy_pass   http://127.0.0.1;
            #}

            # pass the PHP scripts to FastCGI server listening on 127.0.0.1:9000
            #
            #location ~ \.php$ {
            #    root           html;
            #    fastcgi_pass   127.0.0.1:9000;
            #    fastcgi_index  index.php;
            #    fastcgi_param  SCRIPT_FILENAME  /scripts$fastcgi_script_name;
            #    include        fastcgi_params;
            #}

            # deny access to .htaccess files, if Apache's document root
            # concurs with nginx's one
            #
            #location ~ /\.ht {
            #    deny  all;
            #}
        }


    # another virtual host using mix of IP-, name-, and port-based configuration
    #
    #server {
    #    listen       8000;
    #    listen       somename:8080;
    #    server_name  somename  alias  another.alias;

    #    location / {
    #        root   html;
    #        index  index.html index.htm;
    #    }
    #}


    # HTTPS server
    #
    #server {
    #    listen       443 ssl;
    #    server_name  localhost;

    #    ssl_certificate      cert.pem;
    #    ssl_certificate_key  cert.key;

    #    ssl_session_cache    shared:SSL:1m;
    #    ssl_session_timeout  5m;

    #    ssl_ciphers  HIGH:!aNULL:!MD5;
    #    ssl_prefer_server_ciphers  on;

    #    location / {
    #        root   html;
    #        index  index.html index.htm;
    #    }
    #}

}
#user  nobody;
worker_processes  1;

#error_log  logs/error.log;
#error_log  logs/error.log  notice;
#error_log  logs/error.log  info;

#pid        logs/nginx.pid;


events {
    worker_connections  1024;
}


http {
    include       mime.types;
    include ip.black;
    default_type  application/octet-stream;

    #log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
    #                  '$status $body_bytes_sent "$http_referer" '
    #                  '"$http_user_agent" "$http_x_forwarded_for"';

    #access_log  logs/access.log  main;

    sendfile        on;
    #tcp_nopush     on;

    #keepalive_timeout  0;
    keepalive_timeout  65;

    #gzip  on;
    #不限制的ip
    geo $limit {
        default 1;
        127.0.0.1 0;     # 本机地址
    }

    map $limit $limit_key {
        0 "";
        1 $binary_remote_addr;
    }
    #频控全局配置
    limit_req_zone $limit_key zone=one:2m rate=10r/s;
    server {
        listen       80;
        server_name  testapi.mallchat.cn;
        #频控生效位置
        limit_req zone=one burst=10 nodelay;
        #charset koi8-r;

        #access_log  logs/host.access.log  main;

        location / {
                proxy_pass http://127.0.0.1:8080;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                add_header 'Access-Control-Allow-Origin' '*';
                add_header 'Access-Control-Allow-Headers' '*';
                add_header 'Access-Control-Allow-Methods' '*';
                # OPTIONS 直接返回204
                if ($request_method = 'OPTIONS') {
                     return 204;
                 }
        }
        location = /websocket {
                proxy_pass http://127.0.0.1:8090/;
                proxy_http_version 1.1;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "upgrade";
                proxy_read_timeout 600s;
            }

        #error_page  404              /404.html;

        # redirect server error pages to the static page /50x.html
        #
        error_page   500 502 503 504  /50x.html;
        location = /50x.html {
            root   html;
        }

        # proxy the PHP scripts to Apache listening on 127.0.0.1:80
        #
        #location ~ \.php$ {
        #    proxy_pass   http://127.0.0.1;
        #}

        # pass the PHP scripts to FastCGI server listening on 127.0.0.1:9000
        #
        #location ~ \.php$ {
        #    root           html;
        #    fastcgi_pass   127.0.0.1:9000;
        #    fastcgi_index  index.php;
        #    fastcgi_param  SCRIPT_FILENAME  /scripts$fastcgi_script_name;
        #    include        fastcgi_params;
        #}

        # deny access to .htaccess files, if Apache's document root
        # concurs with nginx's one
        #
        #location ~ /\.ht {
        #    deny  all;
        #}
    }
    server {
        listen       80;
        server_name  testweb.mallchat.cn;
        location / {
            root   html;
            index  index.html index.htm;
        }
    }

    # another virtual host using mix of IP-, name-, and port-based configuration
    #
    #server {
    #    listen       8000;
    #    listen       somename:8080;
    #    server_name  somename  alias  another.alias;

    #    location / {
    #        root   html;
    #        index  index.html index.htm;
    #    }
    #}


    # HTTPS server
    #
    #server {
    #    listen       443 ssl;
    #    server_name  localhost;

    #    ssl_certificate      cert.pem;
    #    ssl_certificate_key  cert.key;

    #    ssl_session_cache    shared:SSL:1m;
    #    ssl_session_timeout  5m;

    #    ssl_ciphers  HIGH:!aNULL:!MD5;
    #    ssl_prefer_server_ciphers  on;

    #    location / {
    #        root   html;
    #        index  index.html index.htm;
    #    }
    #}

}
```

### 请求转发

针对所有请求，https协议默认访问的是443端口。我们可以配置对应的请求域名和端口，做相关的转发。转发的时候被nginx代理了一层，ip会丢失，需要记录真实ip在请求头`X-Real-IP`。

```bash
server {
    listen       443 ssl;
    server_name  api.mallchat.cn;
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        # OPTIONS 直接返回204
        if ($request_method = 'OPTIONS') {
             return 204;
         }
    }
}
```

### 跨域配置

```bash
add_header 'Access-Control-Allow-Origin' '*';
add_header 'Access-Control-Allow-Headers' '*';
add_header 'Access-Control-Allow-Methods' '*';
```

### websocket配置

websocket的请求是ws或者wss协议，但是一开始都是http请求，我们需要将它升级为websocket协议。可以这样配置

```bash
#websocket
location = /websocket {
        proxy_pass http://127.0.0.1:8090/;
        proxy_http_version 1.1;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 600s;
    }
```

针对于websocket路径的请求，我们标识他为websocket协议转发给后端对应的websocket监听端口。用户请求`ws://api.mallchat.cn/websocket`会被我们转为`127.0.0.1:8090`给websocket服务。

### 静态文件配置

微信公众号的用户授权需要我们将一个文件放在项目路径下标识身份。为了让文件被访问到，需要配置静态文件路由。对应的vue项目也可以通过这样的配置被访问到

```bash
location = /MP_verify_GTPosqCvKIDnld6z.txt {
      alias /usr/local/nginx/html/MP_verify_GTPosqCvKIDnld6z.txt;
}
```

location命中后

如果是root，会把请求url的 ip/域名+port替换为root指定的目录，访问资源

如果是alias，会把请求url的ip/域名+port+匹配到的路径替换为alias指定的目录，访问资源

### 频率控制

为了防止项目被别有用心的人攻击，毕竟单击一个jmeter就可以打爆我的服务是吧。ddos那种我们虽然防不住，但是这个还是能拦一下，提高他们的攻击门槛的。

限制原理并不难，可一句话概括为：“根据客户端特征，限制其访问频率”，客户端特征主要指IP、UserAgent等。使用IP比UserAgent更可靠，因为IP无法造假，UserAgent可随意伪造。

有两个关键参数

**limit_req_zone**

- key，表示作为限制的请求特征，可以包含文本与变量，IP场景使用$binary_remote_addr
- name，zone的名称，limit_req会用到
- size，zone的大小，1M大小在64位系统可存储8000个state(ip、count...)，每次添加新state时，可能删除至多两个前60秒未使用的state，若添加新state时zone大小不够，则删除较旧的state，释放空间后依旧不够返回503
- rate，访问速率，支持秒或者分钟为单位，但nginx内部使用毫秒追踪请求数，如果限制是10r/1s，实际上是1r/100ms

**limit_req**

- name，limit_req_zone中配置的名称
- burst，可理解为缓冲卡槽，如果设置则所有请求都经由缓冲卡槽转发给upstream，通常可并发接收的请求数为number + 1，但当number为0时会拒绝所有请求
- nodelay，缓冲卡槽中请求转发给upstream的时机，不设置时，会按照zone的速率逐个转发，当设置为nodelay时，请求到达缓冲卡槽后会立即转发给upstream，但卡槽中的占位依旧按照频率释放

了解配置方式后开始实际操作，在Nginx配置中的http内添加：

```plain
limit_req_zone $binary_remote_addr zone=one:2m rate=10r/s;
```

在需要限制的server内添加：

```plain
limit_req zone=one burst=10 nodelay;
```

按照官方文档，2M大小在64位系统中大约可存储16000个状态数据，针对自己的个人网站足够，10r/s即1r/100ms，配合burst=10应该也OK，重启Nginx，然后使用压测工具检验一下。

但是很多时候我们自己需要压测，每次去改配置也不方便，可以加上**白名单**。

修改配置文件中http的内容：

```plain
geo $limit {
    default 1;
    127.0.0.1 0;     # 本机地址
    172.31.0.0/16 0; # 内网地址
}
 
map $limit $limit_key {
    0 "";
    1 $binary_remote_addr;
}

limit_req_zone $limit_key zone=one:2m rate=10r/s;
```

这主要借助Nginx中的geo与map功能，通过geo将IP映射成值，然后再通过map将值映射成变量或常量，恰好`limit_req_zone`中如果key为''表示不对其进行频率限制，所以只需要将白名单用户的key设置为''。

用户进入被频控限制后，会在nginx的error日志中打印记录。

下面是坏蛋借助我们的网站漏洞进行攻击，被拦截的例子。

![image-20240924190520213](/blogs/_archive-2024-assets/69a46ca7a552d7cc2579.webp)

### 黑名单

尽管你配置了频率控制，但是nginx只能做到严格按照频率来执行。比如我们设置10/s次，那用户一直用每秒10次 的并发来请求，我们也很难受啊。我们想做的是超过限制直接给他加进黑名单。

黑名单的配置其实很简单，在conf目录下创建黑名单文件ip.black

```bash
deny 127.0.0.1;
deny 127.0.0.2;
```

然后在配置文件http模块下引入

```plain
http {
  include ip.black;
}
```

生效效果，会有`forbidden`

![image-20240924190531914](/blogs/_archive-2024-assets/35a51369b4c5ae02b7ce.webp)

上面是静态黑名单配置。当然我们也可以动态的去加黑名单。比如发现被频率限制很多次的ip给它扔进黑名单。

原理是写个脚本任务，定时拉取请求日志，超过一定次数的请求，就加进黑名单。参考https://blog.csdn.net/u012965203/article/details/108983589

（我们项目暂时不配置）

### https配置

https对应的证书可以免费向阿里云申请，具体步骤参考：https://blog.csdn.net/torrytang/article/details/127530734

首先我们需要确认nginx有https模块。

===============有https模块跳过==================

执行命令./nginx -V,看看是否有htps模块

![image-20240924190540214](/blogs/_archive-2024-assets/fde16ef4823c30e4d973.webp)

没有的话可以选择重新安装的时候在configure的时候设置，也可以不需要卸载增加。

我的nginx的

安装目录是 **/usr/local/nginx**，

源码解压目录是 **/root/install/****nginx-1.13.7**

1.先把nginx停止运行

```plain
/usr/local/nginx/sbin/nginx -s stop
```

2.进入源码目录，准备配置configure参数

```plain
cd /root/install/nginx-1.13.7
```

3.先看看原来的配置

```plain
/usr/local/nginx/sbin/nginx -V
```

4.我们要在原来的配置基础上去追加配置**--with-http_ssl_module**。追加在最后（如果原有没配置，那就直接追加https模块就好）

```plain
./configure --prefix=/usr/local/nginx --conf-path=/usr/local/nginx/conf/nginx.conf --pid-path=/usr/local/nginx/conf/nginx.pid --lock-path=/usr/local/nginx/lock/nginx.lock --with-http_ssl_module
```

5.配置完成后运行`make`命令，别运行成make install，否则变成覆盖安装了

6.把编译好的文件覆盖掉原来的nginx

```plain
cp ./objs/nginx /usr/local/nginx/sbin/
```

7.查看是否配置成功

```plain
/usr/local/nginx/sbin/nginx -V
```

能看到这样，就成功了

![image-20240924190550365](/blogs/_archive-2024-assets/12991ad2ea8e72a6830b.webp)

然后我们可以开始配置https了。

===============有https模块跳过==================

1.下载申请好的 ssl 证书文件压缩包到本地并解压（这里是用的 pem 与 key 文件，文件名可以更改）。
在 nginx 目录新建 cert 文件夹存放证书文件。

```plain
cd /usr/local/nginx
 mkdir cert
```

2.将原有的配置改成443端口，并且新增证书的配置

```plain
server {
        listen       443 ssl;
        server_name  api.mallchat.cn;

        ssl_certificate      ../cert/api.mallchat.cn.pem;
        ssl_certificate_key  ../cert/api.mallchat.cn.key;

        ssl_session_cache    shared:SSL:1m;
        ssl_session_timeout  5m;
```

3.将http都重定向到https

```plain
server {
    listen 80;
    server_name somnus.test.com;
    #将请求转成https
    rewrite ^(.*)$ https://$host$1 permanent;
}
```

4.重启nginx

```plain
./nginx -s reload
```

在浏览器访问网址，就会发现被重定向到https了。

一开始可以在自己的本地先配置成功再去服务器上配置，如果访问的是本地不是对应的域名，会有不安全提示，不用理就好啦。

![image-20240924190600544](/blogs/_archive-2024-assets/976ce835987c07c548f6.webp)

## 参考

频率控制：https://amsimple.com/blog/article/47.html

黑名单配置：https://jiaokangyang.com/692.html

动态黑名单：https://blog.csdn.net/u012965203/article/details/108983589
