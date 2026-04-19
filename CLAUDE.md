# harness-audit — project guide

A Claude Code skill (`harness-audit:report`) that scans a developer's Claude Code harness across all projects and produces a single report — beautiful HTML or functional Markdown.

## Orientation

- **What this is:** see `.planning/PROJECT.md`
- **Scope boundaries:** see `.planning/REQUIREMENTS.md` (v1 / v2 / out of scope)
- **Phase plan:** see `.planning/ROADMAP.md`
- **Current state:** see `.planning/STATE.md`
- **Sample output target:** `harness-audit.html` (visual bar for HTML renderer)

## Workflow

This project uses GSD (`.planning/` directory). The flow is conceptual — Claude performs each step manually by reading `.planning/STATE.md` and the relevant phase folder. Key steps:

- **Progress** — read `.planning/STATE.md` to see current phase and next action
- **Discuss phase N** — gather context into `.planning/phases/0N-<name>/01-CONTEXT.md`
- **Plan phase N** — write `.planning/phases/0N-<name>/02-PLAN.md` with decisions + file list
- **Execute phase N** — implement the plan, verify on real fs + fixtures
- **Verify work** — cross-check success criteria before marking phase complete

Config defaults: coarse granularity, YOLO mode, balanced models, plan-check + verifier on.

## Non-negotiables

- **Skill audits the harness, not the user's code.** Never mix these scopes.
- **Read-only by default.** The skill writes only to its own output directory. No user-code edits.
- **Secrets redaction before render.** Any detected token/key is redacted in the `Finding` pipeline, before it can reach HTML or Markdown.
- **Single-file outputs.** HTML has inline CSS and no external assets. Markdown is one file. Both share the same finding model.
- **README first paragraph is the pitch.** Treat it as product copy, not documentation.
- **`.claude-plugin/marketplace.json` is load-bearing.** Users install via `/plugin marketplace add <repo>` + `/plugin install <plugin>@<marketplace>`; without this file the repo is not installable. Validate with `claude plugin validate .` after any edit.

## Code constraints

- **Python 3.11+, stdlib-only.** No `requirements.txt`, no pip deps — `DIST-04` forbids a compile step. Solve it with stdlib or rethink.
- **Absolute imports only** (e.g. `from harness.model import X`, not `from ..harness.model`). `cli.py` loads `harness/` and `audit/` as top-level packages; relative imports raise `ImportError: attempted relative import beyond top-level package`.

## Competitor landscape (2026-04)

- `sam-illingworth/audit-setup` — single-MD command, 5 categories, no HTML, per-instance
- `tdccccc/claude-security-audit` — Python scanner, severity-tiered, security-only
- `affaan-m/everything-claude-code` (AgentShield) — big toolkit, `npx ecc-agentshield`, 102 rules

Our wedge: **cross-project aggregation + dual HTML/Markdown output + prescriptive recommendations**.
