from __future__ import annotations

from dataclasses import dataclass

from .config import DecisionConfig


@dataclass(frozen=True)
class Candidate:
    id: str
    description: str


def select_tool_names(
    candidate_ids: list[str],
    asked_ids: set[str],
    scores: dict[str, float],
    config: DecisionConfig,
) -> set[str]:
    """Keep high scores, unknowns, and configured core tools."""
    available = set(candidate_ids)
    asked = asked_ids & available
    ranked = sorted(
        (name for name in asked if name in scores),
        key=lambda name: (-scores[name], name),
    )
    above_threshold = [name for name in ranked if scores[name] >= config.threshold]
    selected = set(above_threshold[: config.max_selected])
    unasked = available - asked
    missing = asked - scores.keys()
    core = config.always_keep & available
    return selected | unasked | missing | core
