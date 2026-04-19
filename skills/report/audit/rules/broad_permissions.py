"""AUD-02: flag over-broad or missing-deny permissions."""
from __future__ import annotations

from collections.abc import Iterable

from harness.model import Artifact, Inventory, SETTINGS, SETTINGS_LOCAL
from audit.io import read_json_safe
from audit.model import Finding, HIGH
from audit.redaction import redact


_BROAD_MARKERS = ("*", "**", "Bash(**)", "Bash(*)")


def evaluate(inventory: Inventory) -> Iterable[Finding]:
    groups: dict[str, dict] = {}

    for owner_root, artifact in _iter_settings_sources(inventory):
        data, err = read_json_safe(artifact.path)
        if err is not None or not isinstance(data, dict):
            continue
        perms = data.get("permissions")
        if not isinstance(perms, dict):
            continue
        allow = perms.get("allow") or []
        deny = perms.get("deny") or []
        if not isinstance(allow, list):
            continue

        for entry in allow:
            if not isinstance(entry, str):
                continue
            if _is_broad(entry):
                key = f"AUD-02/broad-permissions|{entry}"
                bucket = groups.setdefault(key, {"scope": [], "entry": entry})
                if owner_root not in bucket["scope"]:
                    bucket["scope"].append(owner_root)

        if allow and not deny:
            key = "AUD-02/broad-permissions|no-deny"
            bucket = groups.setdefault(key, {"scope": [], "entry": "(no deny list)"})
            if owner_root not in bucket["scope"]:
                bucket["scope"].append(owner_root)

    for key, bucket in groups.items():
        entry = bucket["entry"]
        yield Finding(
            id="AUD-02/broad-permissions",
            title=(
                "Blanket permission grant in settings"
                if entry != "(no deny list)"
                else "Permissions define allow but no deny list"
            ),
            severity=HIGH,
            scope=tuple(bucket["scope"]),
            evidence=f"permissions.allow entry: {redact(str(entry))}",
            rationale=(
                "Broad allowlists (or an allow list without a companion deny "
                "list) mean Claude Code will auto-approve tool calls that you "
                "may not intend to permit. Prefer explicit per-command scopes."
            ),
            suggested_fix=(
                "Replace the broad entry with specific patterns (e.g. "
                "`Bash(git status:*)`). Add a deny list for destructive commands "
                "(rm -rf, git push --force, etc.)."
            ),
            dedup_key=key,
        )


def _iter_settings_sources(inventory: Inventory) -> Iterable[tuple["Path", Artifact]]:  # type: ignore[name-defined]
    for artifact in inventory.global_harness.artifacts:
        if artifact.kind in {SETTINGS, SETTINGS_LOCAL}:
            yield inventory.global_harness.root, artifact
    for project in inventory.projects:
        for artifact in project.artifacts:
            if artifact.kind in {SETTINGS, SETTINGS_LOCAL}:
                yield project.root, artifact


def _is_broad(entry: str) -> bool:
    stripped = entry.strip()
    return stripped in _BROAD_MARKERS or stripped.endswith("(*)") or stripped.endswith("(**)")
