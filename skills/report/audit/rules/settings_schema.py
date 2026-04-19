"""AUD-01: flag malformed or unknown-shape settings.json files."""
from __future__ import annotations

from collections.abc import Iterable

from harness.model import Artifact, Inventory, SETTINGS, SETTINGS_LOCAL
from audit.io import read_json_safe, read_text_safe
from audit.model import Finding, MEDIUM
from audit.redaction import redact


_KNOWN_TOP_LEVEL_KEYS = frozenset({
    "permissions", "hooks", "env", "enabledPlugins", "extraKnownMarketplaces",
    "enableAllProjectMcpServers", "enabledMcpjsonServers", "disabledMcpjsonServers",
    "language", "effortLevel", "voice", "skipAutoPermissionPrompt",
    "voiceEnabled", "model", "theme", "apiKeyHelper",
    "includeCoAuthoredBy", "statusLine", "agent", "subagentStatusLine",
    "autoUpdater", "telemetry", "forceLoginMethod", "cleanupPeriodDays",
    "agents",
})


def evaluate(inventory: Inventory) -> Iterable[Finding]:
    parse_errors: dict[str, dict] = {}
    unknown_keys: dict[str, dict] = {}

    for owner_root, artifact in _iter_settings_sources(inventory):
        data, err = read_json_safe(artifact.path)
        if err is not None:
            key = "AUD-01/settings-schema|parse-error"
            # Evidence stripped of secrets even though it's an error message.
            snippet = redact(err)
            bucket = parse_errors.setdefault(key, {"scope": [], "snippet": snippet})
            if artifact.path not in bucket["scope"]:
                bucket["scope"].append(artifact.path)
            continue
        if not isinstance(data, dict):
            continue
        for top_key in data.keys():
            if top_key not in _KNOWN_TOP_LEVEL_KEYS:
                gkey = f"AUD-01/settings-schema|unknown-key|{top_key}"
                bucket = unknown_keys.setdefault(gkey, {"scope": [], "top_key": top_key})
                if owner_root not in bucket["scope"]:
                    bucket["scope"].append(owner_root)

    for key, bucket in parse_errors.items():
        yield Finding(
            id="AUD-01/settings-schema",
            title="settings.json fails to parse",
            severity=MEDIUM,
            scope=tuple(bucket["scope"]),
            evidence=f"Parse error: {bucket['snippet']}",
            rationale=(
                "Claude Code will silently ignore a malformed settings file. "
                "Any permissions, hooks, or model preferences declared there "
                "are effectively absent until the JSON is valid again."
            ),
            suggested_fix=(
                "Open the file and fix the JSON syntax. Validators: "
                "`python3 -m json.tool < settings.json` or an editor's JSON lint."
            ),
            dedup_key=key,
        )

    for key, bucket in unknown_keys.items():
        yield Finding(
            id="AUD-01/settings-schema",
            title=f"Unknown top-level key in settings: {bucket['top_key']}",
            severity=MEDIUM,
            scope=tuple(bucket["scope"]),
            evidence=f"Unrecognized key: {bucket['top_key']}",
            rationale=(
                "Keys outside the documented Claude Code settings schema are "
                "ignored. Either it's a typo that silently disables a real "
                "setting, or a deprecated name from an older version."
            ),
            suggested_fix=(
                "Check https://code.claude.com/docs/en/settings for the current "
                "schema. Remove the key or correct it to match a supported name."
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
