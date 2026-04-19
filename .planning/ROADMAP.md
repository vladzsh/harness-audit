# Roadmap: harness-audit

**Created:** 2026-04-19
**Granularity:** Coarse (5 phases)
**Total v1 requirements:** 29

## Overview

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | Skill Scaffold | Establish a valid, installable Claude Code plugin skeleton that invokes and says hello | DIST-03, DIST-05 | 3 |
| 2 | Discovery Engine | Walk the filesystem and collect every harness artifact (global + per-project) into a normalized inventory | DISC-01..05, SAFE-03 | 3 |
| 3 | Audit Rules + Findings Model | Turn inventory into structured findings using deterministic rules; enforce de-dup and redaction | AUD-01..08, AGG-01, SAFE-01 | 4 |
| 4 | Dual-Format Report Renderer | Render the common findings model into both a beautiful HTML page and a functional Markdown file | OUT-01..05, AGG-02..03, SAFE-02 | 4 |
| 5 | GitHub Release + README | Package, document, and publish so a stranger can discover, install, and run in one minute | DIST-01, DIST-02, DIST-04 | 3 |

**UI hint:** yes (Phase 4 renders HTML — visual design matters)

---

## Phase 1: Skill Scaffold

**Goal:** A minimal `harness-audit` Claude Code plugin that installs cleanly, surfaces the `report` skill to Claude Code, and produces a trivial "hello" output when invoked — proving end-to-end plumbing before we touch audit logic.

**Requirements:**
- DIST-03 — packaged as Claude Code plugin with `report` skill conforming to spec
- DIST-05 — skill is invocable after install and self-describes via standard metadata

**Success Criteria:**
1. Running the documented install command on a fresh machine registers `harness-audit:report` as a visible skill in Claude Code within one session
2. Invoking `/harness-audit:report` (or natural-language trigger) runs the skill and writes a placeholder output file without errors
3. Repository structure matches Claude Code plugin spec (`.claude-plugin/plugin.json`, `skills/report/SKILL.md`) and passes any available plugin validator

---

## Phase 2: Discovery Engine

**Goal:** Given a user's filesystem, produce a normalized in-memory inventory of every Claude Code harness artifact — global, per-project, MCP configs, instruction files — without parsing or judging content. Read-only and safe.

**Requirements:**
- DISC-01 — global `~/.claude/` config read
- DISC-02 — project roots walked (default `~/projects/`, configurable)
- DISC-03 — all `CLAUDE.md` / `AGENTS.md` files collected
- DISC-04 — MCP server configurations enumerated (global + project)
- DISC-05 — uninstrumented projects handled gracefully
- SAFE-03 — read-only guarantee (no writes outside skill's own output directory)

**Success Criteria:**
1. On a real filesystem with at least 5 projects, the inventory lists every `.claude/` directory, settings.json, hooks, MCP config, `CLAUDE.md`, and `AGENTS.md` that exists — zero known-artifact misses
2. Projects with no harness config appear in the inventory tagged as "uninstrumented" rather than raising errors
3. Discovery writes nothing outside the skill's own output directory (verified by read-only filesystem or audit log)

---

## Phase 3: Audit Rules + Findings Model

**Goal:** Turn the raw inventory into a structured `Finding[]` stream via deterministic rules covering configuration correctness, security red flags, hygiene, and best-practice gaps. De-duplicate across projects. Redact any detected secrets before they leave this phase.

**Requirements:**
- AUD-01..08 — rules for settings.json schema, permissions, suspicious hooks, secrets, CLAUDE.md hygiene, missing recommended config, best-practice gaps, finding shape
- AGG-01 — cross-project de-duplication
- SAFE-01 — secret redaction mandatory at this layer

**Success Criteria:**
1. Fixture inventories (constructed to trigger each AUD rule) produce the expected findings with correct severity and scope — deterministic, snapshot-testable
2. A fixture containing a known-shape secret (e.g., a fake `sk-...` token) results in a finding where the raw secret is absent from the emitted data — only a redacted marker appears
3. Two projects with identical misconfig yield one de-duplicated finding whose `scope` lists both projects, not two separate findings
4. Every finding carries: id, title, severity, scope (project list), evidence snippet, rationale, suggested fix — schema-validated

---

## Phase 4: Dual-Format Report Renderer

**Goal:** Consume the `Finding[]` stream and produce two all-in-one artifacts — a beautiful self-contained HTML page (matching the `harness-audit.html` reference) and a functional Markdown file — with identical content coverage. Include cross-project summary and per-project drill-down in both.

**Requirements:**
- OUT-01 — format flag (`html` default, `markdown` opt-in)
- OUT-02 — HTML is single self-contained file with inline CSS and no external assets
- OUT-03 — Markdown is single functional `.md` file
- OUT-04 — common data model renders to both; feature parity enforced
- OUT-05 — output written to predictable location, path echoed to user
- AGG-02 — top-level summary (counts, severity breakdown, top-N recommendations)
- AGG-03 — per-project drill-down section
- SAFE-02 — absolute paths normalized for shareability

**Success Criteria:**
1. Given the same findings fixture, HTML and Markdown outputs each include every finding exactly once, plus summary and per-project sections
2. The generated HTML opens standalone in a browser with no network requests (verified: file:// URL, no external fetches in dev tools)
3. The Markdown renders correctly in a terminal pager and in a standard IDE preview without broken syntax
4. No absolute `$HOME` path appears verbatim in either output — all user-identifying paths normalized

---

## Phase 5: GitHub Release + README

**Goal:** Make the skill discoverable and installable from GitHub. The first paragraph of the README has to sell it; the install command has to work on the first try; the LICENSE has to be there.

**Requirements:**
- DIST-01 — public GitHub repo with LICENSE and README at root
- DIST-02 — README opening paragraph self-contained and convincing
- DIST-04 — single-path install with no compile step

**Success Criteria:**
1. A developer who has never seen the project lands on the GitHub page, reads only the first paragraph, and can state: what it does, why they might want it, how to install — verifiable via a quick peer test
2. The documented install command runs end-to-end on a fresh Claude Code setup (no prior state) and leaves `harness-audit:report` invocable
3. Repo has LICENSE, README, and a tagged release; repo is linked from at least the project's own documentation and is ready to be submitted to awesome-claude-skills lists

---

## Coverage Check

- Total v1 requirements: 29
- Mapped: 29
- Unmapped: 0 ✓

## Dependencies

- Phase 2 depends on Phase 1 (needs the plugin shell to run discovery)
- Phase 3 depends on Phase 2 (needs inventory to run rules)
- Phase 4 depends on Phase 3 (needs findings to render)
- Phase 5 can start in parallel with Phase 1 for the repo skeleton but completes after Phase 4 so the README can demo real output

---
*Roadmap created: 2026-04-19*
