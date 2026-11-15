from __future__ import annotations

import asyncio
import logging
import os

import httpx
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from .decision.client import DecisionClient
from .decision.config import DecisionConfig
from .middleware.decision import DecisionMiddleware
from .tools import TOOLS


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    config = DecisionConfig(
        enabled=os.getenv("DECISION_ENABLED", "1") == "1",
        endpoint=os.getenv("DECISION_ENDPOINT", ""),
    )
    key = os.getenv("DECISION_API_KEY", "")
    headers = {"Authorization": f"Bearer {key}"} if key else {}

    async with httpx.AsyncClient(headers=headers) as http:
        client = DecisionClient(http, config)
        middleware = [DecisionMiddleware(config, client)] if config.enabled else []
        model = ChatOpenAI(
            model=os.environ["CHAT_MODEL"],
            base_url=os.environ["CHAT_BASE_URL"],
            api_key=os.environ["CHAT_API_KEY"],
            temperature=0,
        )
        agent = create_agent(
            model=model,
            tools=TOOLS,
            middleware=middleware,
            system_prompt=(
                "你是业务助手。相对日期先通过工具确认具体日期。"
                "发电量必须来自查询工具，导出时使用实际查询结果。"
                "工具数据若标记 demo，回答中必须说明是演示数据。"
            ),
        )
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "查询昨天的发电量，并导出报表"}]}
        )
        print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
