from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionConfig:
    enabled: bool = True
    endpoint: str = ""
    threshold: float = 0.6
    max_selected: int = 3
    tool_min_count: int = 4
    timeout_s: float = 3.0
    always_keep: frozenset[str] = frozenset({"current_time"})

    def __post_init__(self) -> None:
        if not 0 < self.threshold < 1:
            raise ValueError("threshold must be between 0 and 1")
        if min(self.max_selected, self.tool_min_count) < 1:
            raise ValueError("tool counts must be positive")
        if self.timeout_s <= 0:
            raise ValueError("timeout_s must be positive")
        if self.enabled and not self.endpoint:
            raise ValueError("enabled decision requires an endpoint")
