# Phase 5: GitHub Release + README — Plan

**Created:** 2026-04-19
**Status:** Ready to execute
**Covers:** DIST-01, DIST-02, DIST-04; finalizes DIST-05

## Goal

Make the skill discoverable and installable from GitHub:
- Repo has LICENSE + README at root.
- README opening paragraph sells the tool in <60 words.
- Install is a single documented path with no compile step.

Push to remote and tag a release are user-gated — the plan prepares everything; the user runs the push.

## Decisions

### D-17: LICENSE — MIT

- Simplest permissive license, matches the ecosystem default for Claude Code plugins (per competitor survey: `sam-illingworth/audit-setup`, `affaan-m/everything-claude-code`, etc. all use permissive licenses).
- Copyright holder: Vladyslav Zhuravel, 2026.

### D-18: Install path — `claude plugin install`

Per `https://code.claude.com/docs/en/plugins`, plugins are installed from a marketplace or directly via git URL. The simplest path once the repo is on GitHub:

```
/plugin install harness-audit@https://github.com/<user>/harness-audit
```

We document both this and the `--plugin-dir` local-development path. No compilation or pip install anywhere — stdlib-only Python already guarantees DIST-04.

### D-19: README sections (short)

Opening paragraph (the pitch): **what / who / how**, in ~55 words, no marketing fluff. Follow with:
- One screenshot reference (`.planning/assets/screenshot.png` — defer actual image to a follow-up, but reference path so the HTML report can be captured later).
- `## Install` — two paths: plugin install (recommended) and local dev (`claude --plugin-dir`).
- `## Usage` — invocation + output location + format flag.
- `## What it audits` — bullet list of the 7 rule kinds, one line each.
- `## Safety` — read-only, redaction, path normalization, single-file output.
- `## Requirements` — Python 3.11+, that's it.
- `## License` — MIT.

Keep it under ~1500 words. CLAUDE.md mandates "README first paragraph is the pitch."

### D-20: No screenshot file in Phase 5

A real screenshot needs a browser capture of the HTML report. That's a manual step. Plan references the path but leaves the asset creation to the user post-merge. README gracefully handles a missing image (the reference line degrades to a missing-image icon in GitHub's render, not a build failure).

Actually: drop the screenshot from the README for v1 to avoid a broken-image hole. README relies on prose + a small output sample.

## Files to create

| Path | Purpose |
|------|---------|
| `LICENSE` | MIT, 2026, Vladyslav Zhuravel |
| `README.md` | Pitch + install + usage + safety + license |

## Build sequence

1. `LICENSE` — standard MIT text.
2. `README.md`:
   - Draft opening paragraph (hard limit: 60 words, single paragraph).
   - Fill out install + usage + audit-coverage sections.
   - Keep total length tight.
3. Verify with a fresh-pair-of-eyes re-read: after reading only the first paragraph, a stranger can state (a) what it does, (b) why they'd want it, (c) how to install.
4. User-gated: push to `github.com-personal:vladzsh/harness-audit.git` + create tag `v0.1.0`. Do not run until the user approves.

## DIST-05 final check

After install, `/harness-audit:report` must be invocable. Already structurally validated in Phase 1 (`.claude-plugin/plugin.json` + `skills/report/SKILL.md` conform to current spec). Release pipeline does not add new ways this can break. DIST-05 stays green.

## Out of scope

- Marketplace submission — v2.
- Screenshots — post-release manual task.
- CI workflow — not required for v1.
- awesome-claude-skills submission — V2-COM-01.

---
*Plan locked: 2026-04-19*
