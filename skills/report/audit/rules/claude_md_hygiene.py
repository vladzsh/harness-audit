"""AUD-05: CLAUDE.md / AGENTS.md hygiene checks."""
from __future__ import annotations

import re
from collections.abc import Iterable

from harness.model import AGENTS_MD, CLAUDE_MD, Inventory
from audit.io import read_text_safe
from audit.model import Finding, LOW


_SIZE_MAX = 12 * 1024
_SIZE_MIN = 80
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", re.MULTILINE)


def evaluate(inventory: Inventory) -> Iterable[Finding]:
    for owner_root, path in _iter_md_sources(inventory):
        text, err = read_text_safe(path)
        if err is not None or text is None:
            continue
        size = len(text.encode("utf-8"))

        if size > _SIZE_MAX:
            yield Finding(
                id="AUD-05/claude-md-hygiene",
                title="Instructions file exceeds recommended size",
                severity=LOW,
                scope=(path,),
                evidence=f"{path.name} is {size} bytes (>{_SIZE_MAX})",
                rationale=(
                    "Every CLAUDE.md / AGENTS.md is loaded into context on "
                    "session start. Oversized files waste tokens and dilute "
                    "the high-signal content with noise."
                ),
                suggested_fix=(
                    "Split the file: keep the orientation terse, move deep "
                    "docs to referenced sub-files. Aim under 8 KB."
                ),
                dedup_key=f"AUD-05/claude-md-hygiene|oversize|{path}",
            )
        elif size < _SIZE_MIN:
            yield Finding(
                id="AUD-05/claude-md-hygiene",
                title="Instructions file is effectively empty",
                severity=LOW,
                scope=(path,),
                evidence=f"{path.name} is {size} bytes",
                rationale=(
                    "A near-empty instructions file signals abandoned scaffolding "
                    "and pushes no useful context into the session."
                ),
                suggested_fix=(
                    "Either delete the file or fill it with the project's "
                    "one-paragraph orientation + build/test commands."
                ),
                dedup_key=f"AUD-05/claude-md-hygiene|empty|{path}",
            )

        headings = _HEADING_RE.findall(text)
        if size > _SIZE_MIN and not headings:
            yield Finding(
                id="AUD-05/claude-md-hygiene",
                title="Instructions file has no headings",
                severity=LOW,
                scope=(path,),
                evidence=f"{path.name} contains no Markdown headings",
                rationale=(
                    "Headings let both the reader and the model navigate the "
                    "file. A single wall of text is hard to scan."
                ),
                suggested_fix=(
                    "Add top-level section headings (## Goal, ## Commands, "
                    "## Conventions) to structure the content."
                ),
                dedup_key=f"AUD-05/claude-md-hygiene|no-headings|{path}",
            )

        duplicated = _duplicate_headings(headings)
        if duplicated:
            yield Finding(
                id="AUD-05/claude-md-hygiene",
                title="Instructions file has duplicate headings",
                severity=LOW,
                scope=(path,),
                evidence=f"Duplicate heading(s): {', '.join(sorted(duplicated))}",
                rationale=(
                    "Duplicate headings usually indicate copy-paste or an "
                    "unintentional section merge that makes the structure "
                    "ambiguous to readers."
                ),
                suggested_fix=(
                    "Rename duplicated headings or merge their sections."
                ),
                dedup_key=f"AUD-05/claude-md-hygiene|dup-headings|{path}",
            )


def _iter_md_sources(inventory: Inventory) -> Iterable[tuple["Path", "Path"]]:  # type: ignore[name-defined]
    for artifact in inventory.global_harness.artifacts:
        if artifact.kind in {CLAUDE_MD, AGENTS_MD}:
            yield inventory.global_harness.root, artifact.path
    for project in inventory.projects:
        for artifact in project.artifacts:
            if artifact.kind in {CLAUDE_MD, AGENTS_MD}:
                yield project.root, artifact.path


def _duplicate_headings(headings: list[str]) -> set[str]:
    seen: dict[str, int] = {}
    for h in headings:
        key = h.strip().lower()
        seen[key] = seen.get(key, 0) + 1
    return {h for h, count in seen.items() if count > 1}
