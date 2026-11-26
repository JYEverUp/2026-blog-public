##  一、对接微信支付

- 蓝兔支付官网API接口分析，包括；扫码支付、H5支付、公众号支付、小程序支付、订单退款、查询订单、支付通知等功能。
- 通过 okhttp3、retrofit2 框架，对接官网 http api 接口。框架的能力可以让支付对接更加标准、清晰，易扩展。
- 不同的支付方式会有自己的签名字段，所以通过聚合支付对象，提供签名处理。
- 每个支付方式提供独立的接口实现，保证单一职责，不同的支付就是每一个单独的策略实现。
- 提供工厂服务，封装支付 API 服务的创建，统一管理。
- 通过 SpringBoot 工程，配置支付 sdk 对接使用。
- 使用 natapp 内网穿透工具，验证支付回调。

## 二、项目介绍

### 1. sdk工程

![img](/blogs/_archive-2024-assets/e49f0d4e01eee5e333ca.webp)

### 2. sdk使用

![img](/blogs/_archive-2024-assets/c66fd8f1520afc44e313.webp)

### 3. 交易订单

![img](/blogs/_archive-2024-assets/8726560f2090da47769c.webp)

## 三、源码
[源码地址](https://github.com/18194085604/ltzf-wx-pay.git)
