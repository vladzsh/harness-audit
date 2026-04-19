"""AUD-07: best-practice gaps — intentionally small, opinionated seed."""
from __future__ import annotations

from collections.abc import Iterable

from harness.model import Inventory, INSTALLED_PLUGINS
from audit.io import read_json_safe
from audit.model import Finding, LOW


_RECOMMENDED_PLUGINS = ("superpowers", "claude-md-management")


def evaluate(inventory: Inventory) -> Iterable[Finding]:
    plugin_artifact = None
    for artifact in inventory.global_harness.artifacts:
        if artifact.kind == INSTALLED_PLUGINS:
            plugin_artifact = artifact
            break
    if plugin_artifact is None:
        return

    data, err = read_json_safe(plugin_artifact.path)
    if err is not None or not isinstance(data, dict):
        return
    installed_names = _collect_installed_names(data)

    missing = [name for name in _RECOMMENDED_PLUGINS if not _is_installed(name, installed_names)]
    if not missing:
        return

    yield Finding(
        id="AUD-07/best-practice-gap",
        title="Recommended plugins are not installed",
        severity=LOW,
        scope=(inventory.global_harness.root,),
        evidence=f"Missing: {', '.join(missing)}",
        rationale=(
            "A small curated set of plugins covers common gaps "
            "(workflow scaffolding, CLAUDE.md maintenance). Skipping them is "
            "fine if you don't need them — flagged here only so you know they exist."
        ),
        suggested_fix=(
            "Install via /plugin install. These are opt-in recommendations, "
            "not required: " + ", ".join(missing)
        ),
        dedup_key="AUD-07/best-practice-gap|recommended-plugins",
    )


def _collect_installed_names(data: dict) -> set[str]:
    out: set[str] = set()
    for key in ("installed", "plugins", "enabledPlugins"):
        val = data.get(key)
        if isinstance(val, dict):
            out.update(val.keys())
        elif isinstance(val, list):
            for entry in val:
                if isinstance(entry, dict):
                    name = entry.get("name")
                    if isinstance(name, str):
                        out.add(name)
                elif isinstance(entry, str):
                    out.add(entry)
    return out


def _is_installed(short_name: str, installed: set[str]) -> bool:
    for full in installed:
        # Match on the part before @marketplace suffix, if any.
        head = full.split("@", 1)[0]
        if head == short_name:
            return True
    return False
