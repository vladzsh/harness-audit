# harness-audit — project guide

A Claude Code skill (`harness-audit:report`) that scans a developer's Claude Code harness across all projects and produces a single report — beautiful HTML or functional Markdown.

## Orientation

- **What this is:** see `.planning/PROJECT.md`
- **Scope boundaries:** see `.planning/REQUIREMENTS.md` (v1 / v2 / out of scope)
- **Phase plan:** see `.planning/ROADMAP.md`
- **Current state:** see `.planning/STATE.md`
- **Sample output target:** `harness-audit.html` (visual bar for HTML renderer)

## Workflow

This project uses GSD (`.planning/` directory). Key commands:

- `/gsd-progress` — where are we, what's next
- `/gsd-discuss-phase N` — gather context before planning a phase
- `/gsd-plan-phase N` — create PLAN.md for a phase
- `/gsd-execute-phase N` — execute the plan
- `/gsd-verify-work` — validate phase outcomes

Config defaults: coarse granularity, YOLO mode, balanced models, plan-check + verifier on.

## Non-negotiables

- **Skill audits the harness, not the user's code.** Never mix these scopes.
- **Read-only by default.** The skill writes only to its own output directory. No user-code edits.
- **Secrets redaction before render.** Any detected token/key is redacted in the `Finding` pipeline, before it can reach HTML or Markdown.
- **Single-file outputs.** HTML has inline CSS and no external assets. Markdown is one file. Both share the same finding model.
- **README first paragraph is the pitch.** Treat it as product copy, not documentation.

## Competitor landscape (2026-04)

- `sam-illingworth/audit-setup` — single-MD command, 5 categories, no HTML, per-instance
- `tdccccc/claude-security-audit` — Python scanner, severity-tiered, security-only
- `affaan-m/everything-claude-code` (AgentShield) — big toolkit, `npx ecc-agentshield`, 102 rules

Our wedge: **cross-project aggregation + dual HTML/Markdown output + prescriptive recommendations**.
