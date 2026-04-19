# Phase 1: Skill Scaffold - Context

**Gathered:** 2026-04-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Ship a minimal `harness-audit` Claude Code plugin that installs cleanly, registers `harness-audit:report` as a discoverable skill, and writes a placeholder output file when invoked — proving end-to-end plumbing. No audit logic, no filesystem walk, no findings model. Just plumbing.

Fixed from ROADMAP.md:
- Repo layout: `.claude-plugin/plugin.json` + `skills/report/SKILL.md`
- Skill identifier: `harness-audit:report`
- Requirements covered: DIST-03, DIST-05
- Success criteria: (1) install registers skill, (2) invocation writes placeholder output without errors, (3) structure passes any available plugin validator.

</domain>

<decisions>
## Implementation Decisions

### Skill runtime model
- **D-01:** Bundled **Python** script as the skill's workhorse. SKILL.md is the thin entry contract (progressive disclosure <5k tokens) that instructs Claude to invoke `python3 skills/report/cli.py [--format html|markdown]`. All audit logic (filesystem walk, rules, redaction, renderers) lives in Python, not in SKILL.md prose.
  - Rationale: AUD-08 requires schema-validated findings, Phase 3 SC-1 requires deterministic snapshot-testable output, OUT-04 requires feature parity between HTML and MD via a shared data model. These are code concerns, not prompt concerns. Rejecting pure-SKILL.md (non-deterministic, token-heavy on 20+ projects, can't enforce SAFE-01 redaction programmatically), rejecting Node (macOS doesn't ship it by default, npm install conflicts with DIST-04 "no compilation step"), rejecting hybrid (blurs schema validation boundary).
- **D-02:** **stdlib-only**. No `requirements.txt`, no pip install, no external packages. Target Python 3.11+ (macOS ships 3.12+; Linux distros broadly ship 3.11+).
  - Implementations: HTML rendering via f-strings + `string.Template`; secret detection via `re`; filesystem walk via `pathlib`; finding schema via `dataclasses` with manual validation; JSON via `json`.
  - Rationale: DIST-04 demands single-path install with no compile step. Every added dependency is an install-time failure mode. stdlib eliminates pip entirely.
- **D-03:** Entry point lives at `skills/report/cli.py`. SKILL.md references it via a relative path inside the skill directory. Not a Python package (no `__main__.py`/`__init__.py` machinery), not a top-level `bin/` script. Plugin convention: the skill's code lives under `skills/{name}/`.
- **D-04:** Phase 1 placeholder writes **both** stub HTML and stub Markdown to the final location: `~/.claude/harness-audit/report-YYYYMMDD-HHMMSS.{html,md}`. Content is minimal — title, ISO timestamp, `harness-audit scaffold OK` line — but it exercises the real output path, write-permission handling, and the `--format` flag surface from day one.
  - Rationale: SC-2 explicitly requires "writes a placeholder output file"; writing to the real location (OUT-05) means Phase 4 replaces content, not plumbing.

### Claude's Discretion
- Exact placeholder content (wording, HTML skeleton markup, MD heading structure) — as long as it's deterministic and references OUT-05 path conventions.
- `--format` flag surface: default value handling (must be `html` per OUT-01), short vs long flag, help text.
- Local install/dev loop for testing SC-1 (symlink under `~/.claude/plugins/`, `/plugin install` from git URL, or both documented) — researcher should verify against current Claude Code plugin spec before planner locks this.
- Whether Phase 1 emits a stub LICENSE and placeholder README at repo root, or fully defers both to Phase 5 (ROADMAP maps these to Phase 5, but a no-op LICENSE file is trivially cheap here).
- Error handling and exit code semantics for the scaffold (Phase 1 can't fail — output directory auto-creation, permission error messaging).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project-internal
- `.planning/PROJECT.md` — core value, non-negotiables (read-only, secrets redaction, single-file outputs), competitor wedge, distribution model
- `.planning/REQUIREMENTS.md` §Distribution (DIST-03, DIST-05), §Output Formats (OUT-05 for placeholder location), §Safety (SAFE-03 read-only guarantee applies even to scaffold)
- `.planning/ROADMAP.md` §Phase 1 — goal, mapped requirements, success criteria
- `CLAUDE.md` — repo-level non-negotiables, especially "Skill audits the harness, not the user's code" and "Single-file outputs"

### External (researcher must fetch via Context7 / docs)
- **Claude Code plugin spec** — exact schema for `.claude-plugin/plugin.json`, required fields, versioning convention, skill discovery rules. Check current documentation; spec evolves. Use `mcp__plugin_context7_context7__*` with library id for Claude Code, or `WebFetch` against the official plugin docs.
- **Claude Code skill spec** — `skills/<name>/SKILL.md` frontmatter requirements (name, description, allowed tools), progressive disclosure size budget (<5k tokens on activation), natural-language trigger mechanics. Same fetch path as plugin spec.
- **Plugin validator (if any exists)** — SC-3 references "any available plugin validator". Researcher must determine whether one ships with Claude Code today or whether this success criterion becomes best-effort.

No project-internal ADRs or feature docs exist yet — this is Phase 1 of a greenfield repo.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None. Greenfield repo: `.git/`, `.planning/`, `CLAUDE.md` only. No prior scaffolding, no patterns to reuse.

### Established Patterns
- **Documentation discipline:** CLAUDE.md is terse and orientation-focused; it should stay that way. SKILL.md must follow the same spirit — progressive disclosure, point-at rather than embed.
- **Planning system:** `.planning/` directory structure per GSD conventions (phases/, config.json, STATE.md).

### Integration Points
- **Claude Code plugin runtime** — the only integration. Plugin is loaded from user's `~/.claude/plugins/` (or via `/plugin install`), metadata surfaces the skill to Claude, Claude's Bash tool invokes `python3 skills/report/cli.py`.
- **User filesystem** — Phase 1 touches only the output path (`~/.claude/harness-audit/`) for the placeholder write. Everything else is read-only (SAFE-03), but Phase 1 has nothing to read yet.

</code_context>

<specifics>
## Specific Ideas

- Python stdlib-only as a deliberate design constraint, not a temporary shortcut — downstream phases must not introduce dependencies to solve a problem that stdlib can solve cleanly.
- Placeholder should use the real output path and the real filename pattern from OUT-05, so Phase 4's renderer literally replaces content, not plumbing.
- Single `cli.py` entry point keeps the skill discoverable and the SKILL.md reference trivial; no Python package machinery until a real reason appears.

</specifics>

<deferred>
## Deferred Ideas

- **LICENSE + README polish** — ROADMAP maps to Phase 5. A bare `LICENSE` file at Phase 1 might be worth it cheaply, but content-free per intent; full DIST-01/02 work stays in Phase 5.
- **Plugin install documentation** — install instructions are a Phase 5 README concern. Phase 1 only needs a path that works for the developer testing SC-1.
- **Filesystem walker, discovery, inventory** — Phase 2.
- **Audit rules, findings model, redaction logic** — Phase 3.
- **HTML/Markdown renderers with real content and parity enforcement** — Phase 4.
- **Plugin validator CI workflow** — not required by v1 requirements; revisit if/when Anthropic ships a validator or the community converges on one.
- **uv / PEP 723 runner** — considered but rejected (D-02) to avoid adding a runner dependency. Revisit if stdlib HTML rendering becomes painful in Phase 4.

</deferred>

---

*Phase: 01-skill-scaffold*
*Context gathered: 2026-04-19*
