"""AUD-04: detect secret-shaped tokens in config files."""
from __future__ import annotations

from collections.abc import Iterable

from harness.model import (
    Artifact,
    CLAUDE_MD,
    HOOKS_FILE,
    Inventory,
    INSTALLED_PLUGINS,
    KNOWN_MARKETPLACES,
    MCP_JSON,
    SETTINGS,
    SETTINGS_LOCAL,
)
from audit.io import read_text_safe
from audit.model import CRITICAL, Finding
from audit.redaction import redact, was_redacted


_SCANNABLE_KINDS = frozenset({
    SETTINGS, SETTINGS_LOCAL, MCP_JSON, HOOKS_FILE,
    INSTALLED_PLUGINS, KNOWN_MARKETPLACES, CLAUDE_MD,
})


def evaluate(inventory: Inventory) -> Iterable[Finding]:
    seen: list[tuple[str, tuple[str, ...]]] = []
    # scope collection per (dedup_key, redacted_sample)
    groups: dict[str, dict] = {}

    for artifact in _iter_all_artifacts(inventory):
        if artifact.kind not in _SCANNABLE_KINDS:
            continue
        text, err = read_text_safe(artifact.path)
        if err is not None or not text:
            continue
        redacted = redact(text)
        if not was_redacted(text, redacted):
            continue
        sample = _first_redacted_sample(redacted)
        key = f"AUD-04/secret-in-config|{sample}"
        bucket = groups.setdefault(key, {"scope": [], "sample": sample})
        if artifact.path not in bucket["scope"]:
            bucket["scope"].append(artifact.path)

    for key, bucket in groups.items():
        sample = bucket["sample"]
        yield Finding(
            id="AUD-04/secret-in-config",
            title="Secret-shaped token found in a Claude Code config file",
            severity=CRITICAL,
            scope=tuple(bucket["scope"]),
            evidence=f"Redacted sample: {sample}",
            rationale=(
                "A value matching a known secret shape (API key, bearer token, "
                "JWT, etc.) was detected on disk. Even read-only reports can "
                "leak if shared; the config itself is a liability."
            ),
            suggested_fix=(
                "Remove the secret from the config file and load it from an "
                "environment variable or a secret manager at runtime. Rotate "
                "the credential if it was committed to version control."
            ),
            dedup_key=key,
        )


def _iter_all_artifacts(inventory: Inventory) -> Iterable[Artifact]:
    yield from inventory.global_harness.artifacts
    for project in inventory.projects:
        yield from project.artifacts


def _first_redacted_sample(redacted_text: str) -> str:
    import re
    m = re.search(r"\[REDACTED:[a-z_]+\]", redacted_text)
    return m.group(0) if m else "[REDACTED:unknown]"
