"""AUD-06: flag partially-instrumented projects that lack recommended files.

Uninstrumented projects are reported via the top-level inventory summary,
not per-project here. This rule targets projects that HAVE some harness
config but are missing something useful on top of it.
"""
from __future__ import annotations

from collections.abc import Iterable

from harness.model import (
    CLAUDE_MD,
    HOOKS_FILE,
    Inventory,
    MCP_JSON,
    SETTINGS,
    SETTINGS_LOCAL,
)
from audit.model import Finding, MEDIUM


def evaluate(inventory: Inventory) -> Iterable[Finding]:
    # Global: no CLAUDE.md at ~/.claude/ is a real gap for a multi-project user.
    gh = inventory.global_harness
    if gh.exists:
        has_claude_md = any(a.kind == CLAUDE_MD for a in gh.artifacts)
        if not has_claude_md:
            yield Finding(
                id="AUD-06/missing-recommended",
                title="Global ~/.claude/CLAUDE.md is missing",
                severity=MEDIUM,
                scope=(gh.root,),
                evidence="No CLAUDE.md found at ~/.claude/",
                rationale=(
                    "A global CLAUDE.md lets you ship cross-project instructions "
                    "(coding style, who you are, preferred tools) once. Without "
                    "it, every project repeats the same preamble."
                ),
                suggested_fix=(
                    "Create ~/.claude/CLAUDE.md with your persistent preferences. "
                    "Keep it short — it's loaded into every session."
                ),
                dedup_key="AUD-06/missing-recommended|global-claude-md",
            )

    mcp_no_settings: list = []
    instrumented_no_claude_md: list = []
    for project in inventory.projects:
        if not project.is_instrumented:
            continue
        kinds = {a.kind for a in project.artifacts}
        if MCP_JSON in kinds and not (SETTINGS in kinds or SETTINGS_LOCAL in kinds):
            mcp_no_settings.append(project.root)
        if CLAUDE_MD not in kinds and (HOOKS_FILE in kinds or SETTINGS in kinds):
            instrumented_no_claude_md.append(project.root)

    if mcp_no_settings:
        yield Finding(
            id="AUD-06/missing-recommended",
            title="Project ships .mcp.json without a settings file",
            severity=MEDIUM,
            scope=tuple(mcp_no_settings),
            evidence=f"{len(mcp_no_settings)} project(s) have .mcp.json but no settings.json / settings.local.json",
            rationale=(
                "An .mcp.json declares servers but permissions/env/hooks belong "
                "in settings. Projects that ship MCP alone typically need at "
                "least a permissions allowlist so Claude auto-approves the tools."
            ),
            suggested_fix=(
                "Add .claude/settings.json (or settings.local.json) with a "
                "permissions.allow list for the MCP tools you actually use."
            ),
            dedup_key="AUD-06/missing-recommended|mcp-no-settings",
        )

    if instrumented_no_claude_md:
        yield Finding(
            id="AUD-06/missing-recommended",
            title="Instrumented project has no CLAUDE.md",
            severity=MEDIUM,
            scope=tuple(instrumented_no_claude_md),
            evidence=f"{len(instrumented_no_claude_md)} project(s) have settings/hooks but no CLAUDE.md",
            rationale=(
                "A project configured with hooks or settings but no CLAUDE.md "
                "leaves Claude without any project-specific guidance. "
                "The config runs; the context does not."
            ),
            suggested_fix=(
                "Add a short CLAUDE.md at the project root with: what the repo "
                "is, how to build / test, and non-obvious conventions."
            ),
            dedup_key="AUD-06/missing-recommended|instrumented-no-claude-md",
        )
