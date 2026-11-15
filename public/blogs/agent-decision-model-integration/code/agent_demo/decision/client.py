from __future__ import annotations

import asyncio
import math

import httpx

from .config import DecisionConfig
from .select import Candidate


class DecisionClient:
    def __init__(
        self,
        http: httpx.AsyncClient,
        config: DecisionConfig,
    ) -> None:
        self._http = http
        self._config = config

    async def score(
        self,
        state: str,
        candidates: list[Candidate],
    ) -> dict[str, float]:
        body = {
            "instruction": (
                "判断完成整个任务可能需要哪些工具，包括后续步骤依赖；只评分，不执行工具。"
            ),
            "state": state,
            "candidates": [{"id": item.id, "description": item.description} for item in candidates],
        }
        async with asyncio.timeout(self._config.timeout_s):
            response = await self._http.post(
                self._config.endpoint,
                json=body,
                timeout=self._config.timeout_s,
            )
            response.raise_for_status()
            payload = response.json()

        if not isinstance(payload, dict):
            raise ValueError("decision response must be an object")
        rows = payload.get("scores")
        if not isinstance(rows, dict):
            raise ValueError("decision response requires scores")

        asked = {item.id for item in candidates}
        scores: dict[str, float] = {}
        for name, value in rows.items():
            if name not in asked or isinstance(value, bool):
                continue
            if not isinstance(value, (int, float)):
                continue
            if math.isfinite(value) and 0 <= value <= 1:
                scores[name] = float(value)
        return scores
