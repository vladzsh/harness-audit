"""AUD-03: flag hook commands with exfiltration-shaped or eval-style patterns."""
from __future__ import annotations

import re
from collections.abc import Iterable

from harness.model import Artifact, HOOKS_FILE, Inventory, SETTINGS, SETTINGS_LOCAL
from audit.io import read_json_safe
from audit.model import CRITICAL, Finding
from audit.redaction import redact


_SUSPICIOUS_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("remote-curl",   re.compile(r"\bcurl\b(?![^|]*localhost)(?![^|]*127\.0\.0\.1)")),
    ("remote-wget",   re.compile(r"\bwget\b")),
    ("netcat",        re.compile(r"\bnc\b\s+[A-Za-z0-9.\-]+\s+\d+")),
    ("eval-style",    re.compile(r"\beval\b")),
    ("base64-pipe",   re.compile(r"base64\s+(?:-d|--decode)\s*\|")),
    ("bash-c-from-net", re.compile(r"(?:curl|wget)\b[^|]*\|\s*(?:bash|sh)\b")),
)


def evaluate(inventory: Inventory) -> Iterable[Finding]:
    groups: dict[str, dict] = {}

    for owner_root, artifact in _iter_hook_sources(inventory):
        data, err = read_json_safe(artifact.path)
        if err is not None or not isinstance(data, dict):
            continue
        hooks_blob = data.get("hooks") if artifact.kind != HOOKS_FILE else data.get("hooks", data)
        for command in _iter_hook_commands(hooks_blob):
            for kind, rx in _SUSPICIOUS_PATTERNS:
                if rx.search(command):
                    key = f"AUD-03/suspicious-hooks|{kind}"
                    snippet = redact(command if len(command) <= 120 else command[:120] + "…")
                    bucket = groups.setdefault(key, {"scope": [], "snippet": snippet, "kind": kind})
                    if owner_root not in bucket["scope"]:
                        bucket["scope"].append(owner_root)
                    break

    for key, bucket in groups.items():
        yield Finding(
            id="AUD-03/suspicious-hooks",
            title=f"Hook command uses a suspicious pattern ({bucket['kind']})",
            severity=CRITICAL,
            scope=tuple(bucket["scope"]),
            evidence=f"Example command: {bucket['snippet']}",
            rationale=(
                "Hooks run with your shell's privileges. Remote downloads, "
                "pipes into bash, eval, or netcat in a hook are vectors for "
                "credential theft or persistent compromise if a config file "
                "is ever tampered with."
            ),
            suggested_fix=(
                "Replace the hook with a local script committed to the repo, "
                "or remove the hook entirely. If a network call is truly "
                "required, hard-code a trusted host and check HTTPS + hash."
            ),
            dedup_key=key,
        )


def _iter_hook_sources(inventory: Inventory) -> Iterable[tuple["Path", Artifact]]:  # type: ignore[name-defined]
    from pathlib import Path
    for artifact in inventory.global_harness.artifacts:
        if _is_hook_source(artifact):
            yield inventory.global_harness.root, artifact
    for project in inventory.projects:
        for artifact in project.artifacts:
            if _is_hook_source(artifact):
                yield project.root, artifact


def _is_hook_source(artifact: Artifact) -> bool:
    return artifact.kind in {HOOKS_FILE, SETTINGS, SETTINGS_LOCAL}


def _iter_hook_commands(blob) -> Iterable[str]:
    if not isinstance(blob, dict):
        return
    for event, groups in blob.items():
        if not isinstance(groups, list):
            continue
        for group in groups:
            if not isinstance(group, dict):
                continue
            hooks = group.get("hooks")
            if not isinstance(hooks, list):
                continue
            for hook in hooks:
                if isinstance(hook, dict) and isinstance(hook.get("command"), str):
                    yield hook["command"]
