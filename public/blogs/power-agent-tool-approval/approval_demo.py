"""电力 Agent 工具审核的离线示例：工具均为模拟函数，不执行 Shell 或业务写入。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class Action(TypedDict):
    name: str
    args: dict[str, Any]


class State(TypedDict):
    action: Action
    result: str
    executed: list[str]
    warnings: list[str]


@dataclass(frozen=True)
class ApprovalPolicy:
    enabled: bool = False
    tools: frozenset[str] = frozenset({"publish_report", "submit_maintenance_ticket"})

    def to_interrupt_on(self) -> dict[str, Any]:
        if not self.enabled:
            return {}
        return {name: {"allowed_decisions": ["approve", "reject"]} for name in sorted(self.tools)}


GuardMode = Literal["warn", "block", "require_approval"]


@dataclass(frozen=True)
class Rule:
    id: str
    severity: Literal["MEDIUM", "HIGH", "CRITICAL"]
    pattern: str
    description: str


RULES = (
    Rule("remove_files", "HIGH", r"\b(rm|del|Remove-Item)\b", "命令包含文件删除操作"),
    Rule("move_files", "MEDIUM", r"\bmv\b", "命令可能移动或覆盖报表"),
)

THRESHOLDS = {
    "warn": frozenset(),
    "block": frozenset({"HIGH", "CRITICAL"}),
    "require_approval": frozenset({"MEDIUM", "HIGH", "CRITICAL"}),
}


def scan_command(action: Action) -> list[Rule]:
    if action["name"] not in {"bash", "execute"}:
        return []
    command = str(action["args"].get("command", ""))
    return [rule for rule in RULES if re.search(rule.pattern, command, re.IGNORECASE)]


def make_review(action: Action, description: str) -> dict[str, Any]:
    return {
        "action_requests": [{**action, "description": description}],
        "review_configs": [{"action_name": action["name"], "allowed_decisions": ["approve", "reject"]}],
    }


def ask_approval(action: Action, description: str) -> bool:
    response = interrupt(make_review(action, description))
    decision = response["decisions"][0]
    if decision["type"] not in {"approve", "reject"}:
        raise ValueError("此示例仅接受 approve 或 reject")
    return decision["type"] == "approve"


def execute_mock(action: Action) -> str:
    """只返回演示数据，不执行真实命令、不访问电厂系统。"""
    name = action["name"]
    if name == "query_generation":
        return "演示发电量：12800.5 MWh"
    if name == "publish_report":
        return "模拟：日报发布完成"
    if name == "submit_maintenance_ticket":
        return "模拟：检修工单提交完成"
    if name in {"bash", "execute"}:
        return "模拟 Shell 调用，未启动进程"
    raise ValueError(f"未注册的演示工具：{name}")


def build_graph(policy: ApprovalPolicy, mode: GuardMode):
    """两个审核节点与一个模拟执行节点；权限及业务鉴权由宿主另行实现。"""
    interrupt_on = policy.to_interrupt_on()

    def name_review(state: State) -> Command:
        action = state["action"]
        if action["name"] in interrupt_on:
            if not ask_approval(action, "该业务工具的每次调用都需要确认"):
                return Command(update={"result": "用户拒绝工具调用"}, goto=END)
        return Command(goto="command_review")

    def command_review(state: State) -> Command:
        action = state["action"]
        findings = scan_command(action)
        risky = [rule for rule in findings if rule.severity in THRESHOLDS[mode]]
        if mode == "block" and risky:
            return Command(update={"result": "风险规则直接阻止"}, goto=END)
        if mode == "require_approval" and risky:
            description = "；".join(f"[{rule.severity}] {rule.description}" for rule in risky)
            if not ask_approval(action, description):
                return Command(update={"result": "用户拒绝风险命令"}, goto=END)
        warnings = [rule.description for rule in findings] if mode == "warn" else []
        return Command(update={"warnings": warnings}, goto="execute")

    def execute(state: State) -> dict[str, Any]:
        action = state["action"]
        return {
            "result": execute_mock(action),
            "executed": [*state["executed"], action["name"]],
        }

    builder = StateGraph(State)
    builder.add_node("name_review", name_review)
    builder.add_node("command_review", command_review)
    builder.add_node("execute", execute)
    builder.add_edge(START, "name_review")
    builder.add_edge("execute", END)
    return builder.compile(checkpointer=InMemorySaver())


def start(graph: Any, action: Action, thread_id: str) -> dict[str, Any]:
    return graph.invoke(
        {"action": action, "result": "", "executed": [], "warnings": []},
        config={"configurable": {"thread_id": thread_id}},
    )


def resume(graph: Any, thread_id: str, decision: Literal["approve", "reject"]) -> dict[str, Any]:
    return graph.invoke(
        Command(resume={"decisions": [{"type": decision}]}),
        config={"configurable": {"thread_id": thread_id}},
    )


def verify() -> None:
    """离线验证九个有可观察结果的审核场景。"""
    query: Action = {"name": "query_generation", "args": {"date": "2026-11-14"}}
    publish: Action = {"name": "publish_report", "args": {"report_id": "daily-demo"}}
    remove: Action = {"name": "execute", "args": {"command": "rm reports/old.csv"}}
    named = ApprovalPolicy(enabled=True)

    graph = build_graph(named, "require_approval")
    result = start(graph, query, "query")
    assert not result.get("__interrupt__") and result["executed"] == ["query_generation"]

    graph = build_graph(named, "warn")
    result = start(graph, publish, "publish")
    assert result["__interrupt__"] and result["executed"] == []
    result = resume(graph, "publish", "approve")
    assert result["executed"] == ["publish_report"]

    graph = build_graph(named, "warn")
    start(graph, publish, "reject")
    result = resume(graph, "reject", "reject")
    assert result["executed"] == [] and "拒绝" in result["result"]

    graph = build_graph(ApprovalPolicy(), "require_approval")
    result = start(graph, remove, "risk")
    assert result["__interrupt__"] and result["executed"] == []
    result = resume(graph, "risk", "approve")
    assert result["executed"] == ["execute"]

    graph = build_graph(ApprovalPolicy(), "warn")
    result = start(graph, remove, "warn")
    assert result["executed"] == ["execute"] and result["warnings"]

    graph = build_graph(ApprovalPolicy(), "block")
    result = start(graph, remove, "block")
    assert not result.get("__interrupt__") and result["executed"] == []

    graph = build_graph(ApprovalPolicy(), "require_approval")
    start(graph, remove, "risk-reject")
    result = resume(graph, "risk-reject", "reject")
    assert result["executed"] == []

    graph = build_graph(ApprovalPolicy(enabled=True, tools=frozenset({"execute"})), "require_approval")
    result = start(graph, remove, "double")
    assert result["__interrupt__"] and result["executed"] == []
    result = resume(graph, "double", "approve")
    assert result["__interrupt__"] and result["executed"] == []
    result = resume(graph, "double", "approve")
    assert not result.get("__interrupt__") and result["executed"] == ["execute"]

    graph = build_graph(named, "warn")
    start(graph, publish, "thread-a")
    start(graph, publish, "thread-b")
    result = resume(graph, "thread-a", "approve")
    assert result["executed"] == ["publish_report"]
    state_b = graph.get_state({"configurable": {"thread_id": "thread-b"}})
    assert state_b.next and state_b.values["executed"] == []
    result = resume(graph, "thread-b", "reject")
    assert result["executed"] == []

    print("9 个离线审核场景通过；未执行 Shell、模型请求或真实业务写入。")


if __name__ == "__main__":
    verify()
