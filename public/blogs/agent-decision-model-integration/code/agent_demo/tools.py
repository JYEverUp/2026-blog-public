from __future__ import annotations

import csv
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from langchain_core.tools import tool


@tool
def current_time() -> str:
    """查询北京时间，用于确定今天、昨天等相对日期。"""
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


@tool
def query_generation(day: str) -> dict[str, str | float]:
    """查询指定日期的发电量。day 格式为 YYYY-MM-DD，返回单位为 MWh。"""
    normalized = date.fromisoformat(day).isoformat()
    return {"day": normalized, "generation_mwh": 1250.0, "source": "demo"}


@tool
def query_profit(day: str) -> dict[str, str | float]:
    """查询指定日期的利润。day 格式为 YYYY-MM-DD，返回单位为元。"""
    normalized = date.fromisoformat(day).isoformat()
    return {"day": normalized, "profit_yuan": 80000.0, "source": "demo"}


@tool
def query_weather(day: str) -> dict[str, str]:
    """查询指定日期的天气。day 格式为 YYYY-MM-DD。"""
    normalized = date.fromisoformat(day).isoformat()
    return {"day": normalized, "weather": "晴", "source": "demo"}


@tool
def export_report(day: str, generation_mwh: float) -> str:
    """将查询到的日期和发电量导出为本地 CSV；返回文件绝对路径。"""
    normalized = date.fromisoformat(day).isoformat()
    folder = Path("reports")
    folder.mkdir(exist_ok=True)
    path = folder / f"generation-{normalized}.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["day", "generation_mwh"])
        writer.writerow([normalized, generation_mwh])
    return str(path.resolve())


TOOLS = [current_time, query_generation, query_profit, query_weather, export_report]
