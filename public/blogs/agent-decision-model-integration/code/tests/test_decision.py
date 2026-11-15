from __future__ import annotations

import json

import httpx
import pytest

from agent_demo.decision.client import DecisionClient
from agent_demo.decision.config import DecisionConfig
from agent_demo.decision.select import Candidate, select_tool_names


def make_config() -> DecisionConfig:
    return DecisionConfig(endpoint="https://decision.example.com/score")


def test_high_scores_and_core_are_kept() -> None:
    kept = select_tool_names(
        ["current_time", "query_generation", "query_profit", "export_report"],
        {"query_generation", "query_profit", "export_report"},
        {"query_generation": 0.98, "query_profit": 0.06, "export_report": 0.93},
        make_config(),
    )
    assert kept == {"current_time", "query_generation", "export_report"}


def test_missing_and_unasked_tools_are_kept() -> None:
    kept = select_tool_names(
        ["current_time", "query_generation", "query_profit", "export_report"],
        {"query_generation", "query_profit"},
        {"query_generation": 0.1},
        make_config(),
    )
    assert kept == {"current_time", "query_profit", "export_report"}


def test_fully_scored_low_scores_leave_only_core() -> None:
    kept = select_tool_names(
        ["current_time", "query_generation", "query_profit"],
        {"query_generation", "query_profit"},
        {"query_generation": 0.1, "query_profit": 0.2},
        make_config(),
    )
    assert kept == {"current_time"}


@pytest.mark.asyncio
async def test_client_filters_invalid_and_unknown_scores() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["state"] == "查询发电量"
        assert [item["id"] for item in body["candidates"]] == ["a", "b", "c"]
        return httpx.Response(
            200,
            json={"scores": {"a": 0.98, "b": True, "c": 1.2, "unknown": 0.99}},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as http:
        scores = await DecisionClient(http, make_config()).score(
            "查询发电量",
            [Candidate("a", "查询"), Candidate("b", "利润"), Candidate("c", "天气")],
        )
    assert scores == {"a": 0.98}
