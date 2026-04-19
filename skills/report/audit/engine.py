"""Rule orchestration + cross-project de-duplication (AGG-01)."""
from __future__ import annotations

from harness.model import Inventory
from audit.model import Finding, SEVERITY_ORDER
from .rules import REGISTRY


def audit(inventory: Inventory) -> list[Finding]:
    raw: list[Finding] = []
    for rule in REGISTRY:
        raw.extend(rule(inventory))
    merged = _merge_by_dedup_key(raw)
    merged.sort(key=lambda f: (SEVERITY_ORDER[f.severity], f.id, f.dedup_key))
    return merged


def _merge_by_dedup_key(findings: list[Finding]) -> list[Finding]:
    """Findings with the same dedup_key collapse; their scopes are unioned.

    Non-scope fields come from the first finding in each group (rules must
    keep them stable per dedup_key — that is the contract of the key).
    """
    groups: dict[str, Finding] = {}
    ordered_keys: list[str] = []
    for finding in findings:
        existing = groups.get(finding.dedup_key)
        if existing is None:
            groups[finding.dedup_key] = finding
            ordered_keys.append(finding.dedup_key)
            continue
        # Union scope, preserve order of first appearance.
        seen = set(existing.scope)
        extra = tuple(p for p in finding.scope if p not in seen)
        if not extra:
            continue
        merged_scope = existing.scope + extra
        groups[finding.dedup_key] = Finding(
            id=existing.id,
            title=existing.title,
            severity=existing.severity,
            scope=merged_scope,
            evidence=existing.evidence,
            rationale=existing.rationale,
            suggested_fix=existing.suggested_fix,
            dedup_key=existing.dedup_key,
        )
    return [groups[key] for key in ordered_keys]
