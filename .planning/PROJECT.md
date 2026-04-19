# harness-audit

## What This Is

A Claude Code skill (`harness-audit:report`) distributed via GitHub that scans a developer's entire Claude Code harness — the global `~/.claude/` config plus every project's `.claude/` and `CLAUDE.md` — and produces a single structured report (either a beautiful self-contained HTML page or a functional Markdown file) showing what's configured, what's misaligned with current best practices, and what to fix first. Built for developers who juggle many projects and need one view across all of them.

## Core Value

**Run one command, get one report — either a beautiful HTML page or a functional Markdown file — that makes the state of your Claude Code harness across all projects obvious and actionable.**

Everything else (cross-project aggregation, security checks, best-practice diff) serves that single outcome. If the generated report is not immediately useful when opened, the skill has failed.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] GitHub README first paragraph sells the skill in <5 seconds (what it is, why you need it, how to install)
- [ ] Single-command install (`/plugin install` or documented clone) completes in one step
- [ ] Skill discovers all Claude Code harness surfaces: `~/.claude/` (global), every `.claude/` under configured project roots, every `CLAUDE.md`/`AGENTS.md` encountered
- [ ] Skill aggregates findings across N projects into a single cross-project view (not per-project reports)
- [ ] Output format is selectable: **HTML** (beautiful, self-contained, opens in browser — matches provided `harness-audit.html` example) or **Markdown** (functional, pipeable, readable in terminal/IDE) — same findings, different presentation
- [ ] Both formats share a common finding data model so the two renderers stay in sync (no HTML-only or MD-only content)
- [ ] Report has a structured top-level summary: counts, severity breakdown, top recommendations — visible in both formats
- [ ] Each finding includes: what was detected, which project(s) it affects, why it matters, concrete suggested fix
- [ ] Findings cover: settings.json sanity, hooks, permissions, MCP servers, skills/plugins, CLAUDE.md hygiene, missing-recommended-config gaps
- [ ] Findings cover: deprecated/outdated patterns vs current Claude Code docs
- [ ] Findings cover: security red flags (exfiltration-shaped hooks, suspicious commands, secrets in configs)
- [ ] Recommendations are prioritized (critical → nice-to-have) and de-duplicated across projects
- [ ] No secrets, tokens, or sensitive paths are embedded in either report format
- [ ] Project hosted on GitHub with clear LICENSE, README, and install instructions

### Out of Scope

- Auto-applying fixes — report is read-only; user applies changes themselves — trust & reversibility concerns dominate v1
- Team dashboards / multi-user reports — single-developer use case first
- Web-hosted service / SaaS — static local HTML only, no network dependency for viewing the report
- Non-Claude-Code harnesses (Codex, Gemini, OpenCode) — out of v1 scope; may revisit after validation
- Code-quality audit of user's own code — this audits the harness, not the codebase
- Real-time monitoring / CI gating — one-shot audit only for v1

## Context

- **Ecosystem state (2026-04):** Claude Code skills market is dense. Direct adjacencies:
  - `sam-illingworth/audit-setup` — single-MD command, 5 categories (Adopt/Improve/Remove/Security/Parked), no HTML, per-instance only
  - `tdccccc/claude-security-audit` — Python scanner, severity-tiered findings, security-only
  - `affaan-m/everything-claude-code` / AgentShield — big toolkit with `/harness-audit`, 102 rules, CI-friendly, bundled inside a larger product
- **Gap we fill:** none of the above produce a cross-project aggregated HTML report aimed at a developer with many projects on disk. Our wedge = HTML output + cross-project aggregation + opinionated prescriptive suggestions.
- **Reference artifact:** `harness-audit.html` sample provided as the visual target for the generated report.
- **Target user:** Developers running Claude Code across many repos (the user himself fits — see `~/CLAUDE.md` map of `~/projects/`, `~/rg/`). First paragraph of README must hook this audience in seconds.
- **Distribution model:** public GitHub repository, installable as a Claude Code plugin (`harness-audit` plugin with a `report` skill). Users land on GitHub → read first paragraph → install → run → open HTML.

## Constraints

- **Platform:** Claude Code skill/plugin format — must conform to current Claude Code plugin spec (`.claude-plugin/plugin.json`, `skills/<name>/SKILL.md`, progressive disclosure <5k tokens on activation)
- **Distribution:** GitHub-hosted, public. Installation cannot require compilation or package-manager choices the user doesn't already have (zero-install beyond Claude Code itself is ideal)
- **Privacy:** Report must be safe to share with teammates — no secrets, no absolute paths tied to the user, no tokens
- **Output:** Two mutually exclusive all-in-one formats — (a) self-contained HTML (single file, no external assets), (b) single Markdown file. User picks per-invocation; both must render the full finding set, no feature gating by format.
- **Scope hygiene:** v1 audits Claude Code only — explicitly excludes other harnesses to keep surface area small

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Dual output format: beautiful HTML OR functional Markdown | User reference `harness-audit.html` sets the HTML visual bar; Markdown preserves pipeability/IDE-native reading. Both share one finding model so coverage parity is enforced | — Pending |
| Cross-project aggregation as differentiator | All three known competitors audit a single instance; developers with many repos have no good option today | — Pending |
| GitHub distribution, skill-first (not MCP / not SaaS) | Matches Claude Code ecosystem convention; lowest install friction; README is the landing page | — Pending |
| Scope limited to Claude Code harness (not Codex/Gemini) for v1 | Keeps v1 shippable; validation comes from one audience before expanding | — Pending |
| Read-only report — no auto-fix in v1 | Reversibility/trust concerns dominate; pairing Claude Code suggestions with user review is safer | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-19 after initialization*
