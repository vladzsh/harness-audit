"""Rule registry. Order here is the stable rule evaluation order."""
from __future__ import annotations

from collections.abc import Callable, Iterable

from audit.model import Finding
from harness.model import Inventory

from . import (
    best_practice_gap,
    broad_permissions,
    claude_md_hygiene,
    missing_recommended,
    secret_in_config,
    settings_schema,
    suspicious_hooks,
)


RuleFn = Callable[[Inventory], Iterable[Finding]]


REGISTRY: tuple[RuleFn, ...] = (
    secret_in_config.evaluate,
    suspicious_hooks.evaluate,
    broad_permissions.evaluate,
    settings_schema.evaluate,
    missing_recommended.evaluate,
    claude_md_hygiene.evaluate,
    best_practice_gap.evaluate,
)
