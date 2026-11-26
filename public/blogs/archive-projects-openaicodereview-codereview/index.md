# 动态代码评审

## 项目背景：
《OpenAI 代码⾃动评审组件》结合 GitHub Actions、Git/Github、OpenAI、微信公众号，多⽅⾯技术完成代码评审和⾃动推送通知。

## 项目价值：
AI代码⾃动评审组件显著提升软件开发效率与质量，通过智能分析代码⻛格、潜在缺陷及性能瓶颈，减少⼈⼯复审负担，加速产品迭代周期，确保代码合规性与稳定性，是现代软件开发流程中不可或缺的智能化⼯具。

## 业务介绍、设计思考、功能演示

### 功能框架：

![image-20241004235426098](/blogs/_archive-2024-assets/9a1848db30173dd82d53.webp)

### 功能演示：
1. 创建⼀个github项⽬，⽤于存储openai-code-review-sdk功能开发代码，触发github action时，通过cicd部署并调⽤该sdk的⽅法。
2. github上编写 github action 执⾏脚本
3. 开发openai-code-review组件代码，提交到步骤1的github仓库中。

4. 提交代码到openai-code-review仓库，触发github action，从⽽调⽤sdk⽅法
5. 执⾏sdk⽅法，通过git diff命令将本次提交的代码内容获取到，输⼊给chatglm, 获取评审结果
6. 评审结果获取后，⽣成对应的⽂件，存储到另⼀个公开的github ⽇志仓库，获取访问链接
7. 调⽤微信公众号测试接⼝，将评审结果⽇志链接、评审项⽬信息通过公众号信息发送给关注的⽤户。

![image-20241004235453577](/blogs/_archive-2024-assets/43b64e6f88f07d4ce2d5.webp)

### 开源项目
[源码地址](https://github.com/18194085604/openai-code-review)
