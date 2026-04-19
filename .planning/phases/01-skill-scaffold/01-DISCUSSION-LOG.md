# Phase 1: Skill Scaffold - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-19
**Phase:** 01-skill-scaffold
**Areas discussed:** Skill runtime model

---

## Gray-area selection

User was offered four candidate gray areas and selected **one**:

| Gray Area | Selected |
|-----------|----------|
| Skill runtime model | ✓ |
| Placeholder output contract | |
| Local dev/install loop | |
| Phase 1 doc minimum (LICENSE/README stub) | |

Unselected areas deferred to Claude's discretion in CONTEXT.md.

---

## Skill runtime model

### Q1 — Architecture for harness-audit skill

| Option | Description | Selected |
|--------|-------------|----------|
| Bundled Python script (Recommended) | SKILL.md → `python3 skills/report/cli.py`. Deterministic, schema-validated, stdlib-only fits DIST-04 / AUD-08 / Phase 3 SC-1 / OUT-04. | ✓ |
| Pure SKILL.md instructions | Zero-install, Claude drives everything via Glob/Read/Grep. Non-deterministic, token-heavy, hard to snapshot-test, SAFE-01 redaction not programmatic. | |
| Bundled Node/TS script | Nice HTML+JSON ergonomics, but macOS doesn't ship Node and npm install conflicts with DIST-04. | |
| Hybrid (Bash walker + Claude judgement) | Flexible for best-practice diff, but blurs schema validation and makes output non-deterministic. | |

**User's choice:** Bundled Python script
**Notes:** Recommended option taken. Aligns with the user's Python/Django background and existing macOS/Arch toolchain.

---

### Q2 — Python dependencies

| Option | Description | Selected |
|--------|-------------|----------|
| stdlib-only (Recommended) | Python 3.11+ stdlib only. f-strings + `string.Template`, `re`, `pathlib`, `dataclasses`, `json`. No pip. | ✓ |
| Minimal deps + lockfile | Allow 1–2 packages (jinja2, pydantic) documented in install flow. Cleaner code, more install steps. | |
| uv + pyproject.toml (PEP 723 inline deps) | Deterministic runner, but adds uv as a hard dep — not ubiquitous yet. | |

**User's choice:** stdlib-only
**Notes:** Locks downstream phases: Phase 4 HTML rendering cannot reach for jinja2. If stdlib rendering becomes painful in Phase 4, the decision is revisited, not silently eroded.

---

### Q3 — Phase 1 placeholder content

| Option | Description | Selected |
|--------|-------------|----------|
| Stub HTML + MD at final location (Recommended) | Write both `~/.claude/harness-audit/report-YYYYMMDD-HHMMSS.{html,md}` with title + timestamp + "harness-audit scaffold OK". Exercises OUT-05 path and `--format` flag from day one. | ✓ |
| stdout 'hello' + path only | Prints a string, writes no file. Fails SC-2 ("writes a placeholder output file"). | |
| HTML only (default format) | Writes only `.html` since OUT-01 default is html; defers MD renderer to Phase 4. Breaks parity test earlier than needed. | |

**User's choice:** Stub HTML + MD at final location
**Notes:** Both formats ship empty-but-valid from Phase 1 so Phase 4 replaces content only, not plumbing.

---

### Q4 — Entry point location

| Option | Description | Selected |
|--------|-------------|----------|
| `skills/report/cli.py` (Recommended) | Script lives beside SKILL.md inside the skill directory. Plain `python3` invocation, no packaging machinery. | ✓ |
| `skills/report/` as a Python package | `__init__.py` + `__main__.py`, invoke via `python3 -m report`. Clean imports but needs PYTHONPATH wiring in SKILL.md. | |
| `bin/harness-audit` at plugin root | Shebang executable outside `skills/`. CLI-like but violates plugin convention that skill code lives under `skills/{name}/`. | |

**User's choice:** `skills/report/cli.py`
**Notes:** Simplest resolvable path from a SKILL.md that Claude Code loads.

---

## Claude's Discretion

Areas the workflow explicitly left to Claude (planner + executor):
- Exact placeholder HTML/MD skeleton markup and wording
- `--format` flag details (default handling, help text)
- Local install/dev loop for testing SC-1 (symlink vs `/plugin install` vs git clone)
- Whether Phase 1 also emits a stub LICENSE and placeholder README, or defers both to Phase 5
- Error handling and exit-code semantics for the scaffold
- Output-directory auto-creation behaviour

## Deferred Ideas

- LICENSE + README polish → Phase 5
- Filesystem walk → Phase 2
- Audit rules, findings model, redaction → Phase 3
- HTML/MD renderers with real content → Phase 4
- Plugin validator CI workflow → not in v1 requirements
- uv / PEP 723 runner → reconsider only if Phase 4 stdlib rendering becomes painful
