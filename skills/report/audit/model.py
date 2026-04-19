"""Finding data model — the contract rules produce and the renderer consumes."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


CRITICAL = "critical"
HIGH = "high"
MEDIUM = "medium"
LOW = "low"

SEVERITY_ORDER = {CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3}


@dataclass(frozen=True)
class Finding:
    id: str
    title: str
    severity: str
    scope: tuple[Path, ...]
    evidence: str
    rationale: str
    suggested_fix: str
    dedup_key: str

    def __post_init__(self) -> None:
        assert self.severity in SEVERITY_ORDER, f"bad severity: {self.severity}"
        for field_name in ("id", "title", "evidence", "rationale", "suggested_fix", "dedup_key"):
            if not getattr(self, field_name):
                raise ValueError(f"Finding.{field_name} is empty")
        if not self.scope:
            raise ValueError("Finding.scope is empty")
