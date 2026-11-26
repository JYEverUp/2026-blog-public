## 一、网络请求

目前可以发送网络请求的方式：

1. xhr（基于XMLHttpRequest） 存在的问题：配置调用混乱；编码方式复杂；实际开发中经常被JQuery-Ajax代替
2. JQuery-Ajax 存在的问题：Vue开发中不需要调用jQuery这个重量级框架（1w＋行）
3. vue-resource（vue1.x推出） vue2.0之后不在更新和维护，作者推荐了axios
4. fetch 基于promis 但兼容性差

### 1. axios发送网络请求

axios特点

- 在浏览器中发送 XMLHttpRquest 请求
- 在 node.js 中发送http请求
- 支持 Promise API
- 拦截（转换）请求和响应
- 转换请求和响应

axios基本使用:

1. 安装：npm install axios --save
2. 引入：import axios from "axios"
3. 使用（默认使用get请求）：

```js
// 请求方法 1
axios ({
  url: 'http://127.0.0.1:3001/data',
  // params 可选 针对get请求的参数拼接 如：127.0.0.1:3000/data?type=pop
  params: {
    type: "pop",
    page: 1
  }
}).then(res => {
  console.log(res);
})

// 简化方法
axios.get('url').then(
  // 成功的回调
  response => {
    console.log(response.data);
  }
  // 失败的回调
  error => {
    console.log(error.message);
  }
)
```


### 2. 跨域问题

报错，违反了同源策略（协议、域名和端口相同，可访问资源）

``` 
Access to XMLHttpRequest at 'https://www.runoob.com/try/ajax/json_demo.json' from origin 'http://localhost:8080' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

解决跨域问题

1. cros （后端使用）
2. jsonp (面试题，但实际应用少)
3. 代理服务器 
   服务器之间使用http协议传输数据，不受同源策略限制，前端正向代理后端反向代理
   缺点：会导致请求和服务器都不知道来自哪里

方式1:借助vue cli开启单个代理服务器,在vue.config.js中添加如下配置：
[官方配置参考文档](https://cli.vuejs.org/zh/config/#devserver-proxy)：
说明：
优点：配置简单，请求资源时直接发给 8080 端口即可。
缺点：不能配置多个代理，不能灵活的控制请求是否走代理。
工作方式：若按照上述配置代理，当请求了前端 (public) 不存在的资源时，那么该请求会转发给服务器 （优先匹配前端资源）

```js
// 配置代理服务器
const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  lintOnSave:false ,//关闭 es lite 语法检查
  devServer: { //开启代理服务器(转发端口) ---> 跨域问题
    proxy: 'https://www.runoob.com:443'
  }
})

// 请求资源
axios.get('http://localhost:8080/try/ajax/json_demo.json').then(
  response => {
    console.log('成功',response.data);
  },
  error => {
    console.log('失败',error);
  }
)
```

方式2:
可以配置多个代理,且可以灵活控制是否请求代理;缺点 配置较为繁琐,请求资源必须加前缀

```js
// 配置代理服务器
const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
      proxy: {
      '/api1': {// 匹配以 '/api1'开头的请求路径
        target: 'http://localhost:5000',// 代理目标服务器协议+主机名
        pathRewrite: {'^/api1': ''},// 控制实际请求地址会将 /api1 匹配前缀删除
        ws: true,// 默认true ,用于支持 websocket
        changeOrigin: true,//默认true,用于控制请求头中的 host 值
      },
      '/api2': {
        target: 'http://localhost:5001',
        pathRewrite: {'^/api2': ''}
      }
    }
  }
})

// 请求资源
axios.get('http://localhost:8080/api1'+'/')
axios.get('http://localhost:8080/api2'+'/')
```


## 
