---
description: Scan the user's Claude Code harness across all projects and produce a single HTML or Markdown report. Use when the user asks to audit, review, or inspect their Claude Code setup, settings, hooks, MCP servers, or CLAUDE.md files across projects.
disable-model-invocation: true
---

# harness-audit:report

Audits the user's Claude Code harness — global `~/.claude/` config plus per-project `.claude/` and `CLAUDE.md` files — and writes one self-contained report to `~/.claude/harness-audit/report-<timestamp>.{html,md}`.

## How to run

The skill delegates to a bundled Python script. Invoke it with the Bash tool:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/report/cli.py" --format "$FORMAT"
```

Where `$FORMAT` is `html` (default) or `markdown`.

## Arguments

`$ARGUMENTS` may contain one of: `html`, `markdown`, or be empty.

- Empty or `html` → pass `--format html`
- `markdown` or `md` → pass `--format markdown`
- Anything else → default to `html`

## After running

The script prints the absolute path of the generated report on stdout. Relay that path to the user so they can open it.

## Current status

This is the Phase 1 scaffold. It writes a placeholder report to prove end-to-end plumbing. Real discovery, audit, and rendering arrive in later phases.
