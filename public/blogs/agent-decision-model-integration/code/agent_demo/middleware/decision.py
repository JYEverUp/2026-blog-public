from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import cast

import httpx
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.tools import BaseTool

from ..decision.client import DecisionClient
from ..decision.config import DecisionConfig
from ..decision.select import Candidate, select_tool_names

logger = logging.getLogger(__name__)


def build_state(request: ModelRequest) -> str:
    lines: list[str] = []
    for message in request.messages[-8:]:
        content = message.content
        if isinstance(content, str):
            text = content
        else:
            text = "\n".join(
                str(block.get("text", ""))
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            )
        lines.append(f"{message.type}: {text}")
    return "\n".join(lines)[-2400:]


class DecisionMiddleware(AgentMiddleware):
    def __init__(
        self,
        config: DecisionConfig,
        client: DecisionClient,
    ) -> None:
        super().__init__()
        self._config = config
        self._client = client

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        config = self._config
        if not config.enabled:
            return await handler(request)

        # 本示例仅注册 BaseTool；服务商原生工具字典需另行适配。
        tools = cast(list[BaseTool], request.tools)
        candidates = [
            Candidate(tool.name, tool.description)
            for tool in tools
            if tool.name not in config.always_keep
        ]
        if len(candidates) < config.tool_min_count:
            return await handler(request)

        try:
            scores = await self._client.score(build_state(request), candidates)
        except (httpx.HTTPError, TimeoutError, ValueError) as exc:
            logger.warning(
                "decision unavailable; keeping current catalog (%s)",
                type(exc).__name__,
            )
            return await handler(request)

        kept = select_tool_names(
            candidate_ids=[tool.name for tool in tools],
            asked_ids={item.id for item in candidates},
            scores=scores,
            config=config,
        )
        narrowed = request.override(
            tools=[tool for tool in tools if tool.name in kept],
        )
        return await handler(narrowed)
