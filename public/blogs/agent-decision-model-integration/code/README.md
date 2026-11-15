# 决策模型接入示例

来自博客文章《给公司的 Agent 加一层决策模型：为什么需要，代码怎么接》。

Python 3.12；只运行离线测试：

```bash
python -m pip install httpx pytest pytest-asyncio
python -m pytest tests/test_decision.py -q
```

在线 Agent 另需安装文章指定版本的 LangChain 和模型集成，并配置真实主模型与决策端点。
业务查询返回演示数据；导出工具会在当前目录创建 reports/，同一天的文件会覆盖。
