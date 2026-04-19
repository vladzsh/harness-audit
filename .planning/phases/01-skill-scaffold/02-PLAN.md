# Phase 1: Skill Scaffold — Plan

**Created:** 2026-04-19
**Status:** Ready to execute
**Covers:** DIST-03, DIST-05

## Goal

Minimal installable `harness-audit` Claude Code plugin that registers `harness-audit:report` and writes a placeholder output file when invoked. No audit logic.

## Spec lock-in (from docs)

Verified against https://code.claude.com/docs/en/plugins (fetched 2026-04-19):

- Plugin manifest: `.claude-plugin/plugin.json` — required fields: `name`, `description`, `version`; optional `author`, `homepage`, `repository`, `license`.
- Skill layout: `skills/<name>/SKILL.md` — folder name becomes the skill name. Plugin-namespaced as `/<plugin-name>:<skill-name>` → `/harness-audit:report`.
- SKILL.md frontmatter: `description` (required). No explicit `name` field — folder name wins. `disable-model-invocation: true` suppresses automatic invocation (we want manual/explicit invocation in Phase 1).
- Body of SKILL.md is the instruction to Claude when the skill is invoked. It can instruct Claude to run a bundled script via Bash.
- Local testing loop: `claude --plugin-dir ./harness-audit` + `/reload-plugins` to pick up changes.

## Files to create

| Path | Purpose |
|------|---------|
| `.claude-plugin/plugin.json` | Plugin manifest (name, description, version, author) |
| `skills/report/SKILL.md` | Entry contract — instructs Claude to invoke `cli.py` |
| `skills/report/cli.py` | Python stdlib-only CLI; writes placeholder HTML + MD |

Deferred to Phase 5 (per context D-04 + ROADMAP): LICENSE, README. No top-level files added in Phase 1.

## Detailed file specs

### `.claude-plugin/plugin.json`

```json
{
  "name": "harness-audit",
  "description": "Audit your Claude Code harness across all projects — one HTML or Markdown report.",
  "version": "0.1.0",
  "author": { "name": "Vladyslav Zhuravel" }
}
```

### `skills/report/SKILL.md`

Frontmatter:
- `description`: instructs Claude when to use the skill (explicit user request).
- `disable-model-invocation: true` — user-triggered only for Phase 1; we don't want Claude to auto-run an audit from ambient context.

Body (terse, progressive disclosure):
- One short paragraph framing what the skill does.
- Bash invocation: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/report/cli.py" --format "$FORMAT"` where `$FORMAT` defaults to `html`, accepts `markdown`.
- Argument parsing note: `$ARGUMENTS` may contain `html`, `markdown`, or be empty; Claude extracts the format and passes it.
- On completion: show the output path echoed by the script.

`${CLAUDE_PLUGIN_ROOT}` is the documented env var for the plugin's install directory (per Claude Code plugin runtime). If unavailable in this Claude Code version, fall back to a relative path resolved from SKILL.md's directory.

### `skills/report/cli.py`

Python 3.11+ stdlib-only. Shape:

```
argparse → --format {html, markdown}, default "html"
output_dir = Path.home() / ".claude" / "harness-audit"
output_dir.mkdir(parents=True, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
# Phase 1 writes BOTH formats regardless of --format, so the scaffold proves
# the real output path for both renderers from day one (per D-04).
# --format still affects which path is echoed to the user as "the report".
html_path = output_dir / f"report-{timestamp}.html"
md_path   = output_dir / f"report-{timestamp}.md"
write placeholder HTML (title, timestamp, "harness-audit scaffold OK")
write placeholder Markdown (same content)
print(primary_path)   # the --format one
```

Placeholder content requirements:
- Deterministic (no randomness, no non-ISO timestamps in the body beyond the one we chose)
- HTML: `<!doctype html>`, `<title>`, inline `<style>`, single `<main>` with title + timestamp + "harness-audit scaffold OK" line. No external assets (OUT-02 forward-compatibility).
- Markdown: `# harness-audit — scaffold`, an ISO timestamp line, `harness-audit scaffold OK`. One file, no frontmatter.

Exit code: 0 on success; nonzero on permission error with a clear stderr message.

## Build sequence

1. Create `.claude-plugin/plugin.json`.
2. Create `skills/report/SKILL.md`.
3. Create `skills/report/cli.py`.
4. Execute `python3 skills/report/cli.py` locally and `python3 skills/report/cli.py --format markdown`; confirm both write the expected files and print the primary path.
5. Inspect one HTML and one MD output to verify they're syntactically valid placeholders.
6. Optional local install test: `claude --plugin-dir ./` — deferred to the user since it's interactive; we validate structure via the script run instead.

## Success criteria validation

| SC | How we verify in Phase 1 |
|----|--------------------------|
| SC-1 — install registers skill | Structural: matches exact plugin-spec layout (`.claude-plugin/plugin.json` + `skills/report/SKILL.md`). User can confirm by running `claude --plugin-dir ./` separately. |
| SC-2 — invocation writes placeholder | Direct: run `cli.py` and confirm files land at `~/.claude/harness-audit/report-TIMESTAMP.{html,md}`. |
| SC-3 — passes plugin validator | No official validator exists today (per research); structural conformance to docs is our proxy. Best-effort per context. |

## Out of scope for Phase 1

- LICENSE, README (Phase 5)
- Any real discovery, audit, or rendering logic (Phases 2–4)
- CI workflow (not in v1 scope)
- Multi-project walker (Phase 2)

## Risks

- **`${CLAUDE_PLUGIN_ROOT}` env var availability**: if not defined in current Claude Code runtime, fallback path inside SKILL.md must still resolve. Mitigation: use a Bash one-liner that resolves via `python3 -c` if needed, or document a hard-coded skill path; verify during SC-1 smoke test.
- **Placeholder file collision**: timestamp precision is seconds. Two invocations in the same second overwrite. Acceptable for Phase 1; revisit in Phase 4 if it matters.

---
*Plan locked: 2026-04-19*
