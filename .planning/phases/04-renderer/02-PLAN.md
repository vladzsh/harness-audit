# Phase 4: Dual-Format Report Renderer — Plan

**Created:** 2026-04-19
**Status:** Ready to execute
**Covers:** OUT-01, OUT-02, OUT-03, OUT-04, OUT-05, AGG-02, AGG-03, SAFE-02

## Goal

Consume `Inventory` + `list[Finding]`, produce two single-file artifacts with identical content coverage:
- **HTML**: self-contained, inline CSS, no JS, no external assets — visual quality bar per `harness-audit.html` reference.
- **Markdown**: single `.md` file, readable in terminal/IDE, same findings + summary + per-project drilldown.

Absolute `$HOME` paths are normalized to `~` across both outputs (SAFE-02).

## Design decisions

### D-11: Shared view-model (`ReportData`)

A single dataclass `ReportData` is the only thing renderers consume. It's built by one function `build_report_data(inventory, findings)` that does all the shaping work — severity counts, top-N recommendations, per-project groupings, path normalization.

Both renderers receive identical data and walk it the same way. Feature parity is enforced by construction: adding a field without updating both renderers is a visible diff; neither renderer queries `inventory` or `findings` directly.

### D-12: SAFE-02 — path normalization in the view-model

`normalize_path(p: Path, home: Path) -> str` replaces a `$HOME` prefix with `~`. Runs inside `build_report_data()` before any string reaches a renderer. Applied to:
- `Inventory.configured_roots`
- `Project.root`
- `GlobalHarness.root`
- `Finding.scope` entries

Evidence strings already passed through `redact()` in Phase 3 — no second pass needed, and `redact()` won't touch `/Users/maclad/...` paths anyway. But any *path-like substrings inside evidence* are also run through `normalize_path`-aware substitution, so if a rule embedded a full path in evidence, it gets normalized too.

Renderers never see raw `/Users/<name>/...` segments for the invoking user.

### D-13: Self-contained HTML — no JS, no external fetches

- All CSS inline in `<style>`.
- No `<script>`.
- Per-project drilldown uses native `<details><summary>` — collapses without JS.
- No `<link>` to fonts or CDNs.
- Dark theme via CSS variables (close to reference `harness-audit.html`).

Verifying "no external fetches" is trivial: grep the output for `http://`, `https://`, `//cdn`, `src=`, `<link` — only allowed: `<link>` with nothing, or none at all. We'll assert none.

### D-14: AGG-02 — top-level summary

Summary block includes:
- Counts: projects scanned, instrumented, uninstrumented; findings total.
- Severity breakdown: critical / high / medium / low counts.
- Top-N recommendations: the top 5 findings sorted by severity (already sorted by engine), displayed as a prioritized action list.

### D-15: AGG-03 — per-project drilldown

Each project (including the global pseudo-project `~/.claude/`) gets a collapsible section:
- Summary line: normalized path + artifact count + finding count + worst severity.
- Artifacts list (kinds present).
- Findings that apply to that project, with full evidence / rationale / fix.

A finding whose scope covers N projects appears in each of them — the top-level findings section has the de-duplicated version, but per-project drilldown makes every scope occurrence visible where it matters. Both renderers follow this pattern so parity holds.

### D-16: Markdown = functional, not fancy

- GitHub-flavored Markdown: `#` headings, `-` bullets, fenced code blocks, simple tables for the summary.
- `<details>` works in GitHub / many viewers — use it there too for parity with HTML, but falls back gracefully to a plain heading otherwise.

## Files to create / modify

| Path | Purpose |
|------|---------|
| `skills/report/render/__init__.py` | Package marker |
| `skills/report/render/view.py` | `ReportData` dataclass + `build_report_data()` + path normalization |
| `skills/report/render/html.py` | `render_html(data: ReportData) -> str` |
| `skills/report/render/markdown.py` | `render_markdown(data: ReportData) -> str` |
| `skills/report/cli.py` | Replace placeholder `build_html` / `build_markdown` with the new renderers |

## Detailed structure

### `render/view.py`

```python
@dataclass(frozen=True)
class ProjectSummary:
    name: str
    display_path: str         # home-normalized
    artifacts: tuple[tuple[str, str], ...]  # (kind, display_path) per artifact
    is_global: bool
    is_instrumented: bool
    findings: tuple[FindingView, ...]     # findings touching this project
    worst_severity: str | None

@dataclass(frozen=True)
class FindingView:
    id: str
    title: str
    severity: str
    scope_paths: tuple[str, ...]   # normalized
    evidence: str                  # already redacted + path-normalized
    rationale: str
    suggested_fix: str

@dataclass(frozen=True)
class ReportData:
    generated_at: str                # ISO string
    configured_roots: tuple[str, ...]
    totals: dict                     # {projects, instrumented, findings, critical, high, medium, low}
    top_recommendations: tuple[FindingView, ...]   # top 5
    findings: tuple[FindingView, ...]               # all, engine-sorted
    projects: tuple[ProjectSummary, ...]            # including global pseudo-project first
```

`build_report_data(inventory, findings, home=None) -> ReportData`

### `render/html.py`

Skeleton:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Claude Code Harness Audit — {generated_at}</title>
  <style>/* inline — CSS variables, dark theme, responsive */</style>
</head>
<body>
  <header>
    <h1>Claude Code Harness Audit</h1>
    <p class="muted">Generated {generated_at} · {N} projects · {M} findings</p>
  </header>

  <section class="stats">
    <!-- stat cards for critical/high/medium/low counts -->
  </section>

  <section class="top-reco">
    <h2>Top recommendations</h2>
    <ol>…</ol>
  </section>

  <section class="all-findings">
    <h2>All findings</h2>
    <!-- grouped by severity with severity badge colors -->
  </section>

  <section class="projects">
    <h2>Per-project drilldown</h2>
    <!-- <details> per project -->
  </section>

  <footer>Generated by harness-audit · single-file report · safe to share</footer>
</body>
</html>
```

Strings are HTML-escaped via `html.escape()` before insertion. Evidence snippets rendered inside `<code>` so JSON/shell fragments read naturally.

### `render/markdown.py`

```
# Claude Code Harness Audit

_Generated: {timestamp} · {N} projects · {M} findings_

## Summary

| Severity | Count |
|----------|-------|
| Critical | … |
| High     | … |
| Medium   | … |
| Low      | … |

## Top recommendations

1. **[CRITICAL] Title** — fix summary.
2. …

## All findings

### [CRITICAL] AUD-04/secret-in-config — Secret-shaped token found…

- **Scope (2):** `~/.claude/plugins/installed_plugins.json`, `~/CLAUDE.md`
- **Evidence:** Redacted sample: [REDACTED:hex_token]
- **Why it matters:** …
- **Fix:** …

## Per-project drilldown

### Global (~/.claude/)
<details><summary>13 artifacts · 2 findings</summary>
- settings_local: `~/.claude/settings.local.json`
- ...
Findings:
- [HIGH] …
</details>
```

## Build sequence

1. `render/view.py` — `ReportData` + builder + normalization. Unit-test the normalization (fixture with a few paths).
2. `render/markdown.py` — simplest renderer first, easier to read while iterating.
3. `render/html.py` — HTML with CSS. Check in a browser.
4. Wire both into `cli.py`; remove inline placeholder generators.
5. Run end-to-end; open HTML; verify parity by diffing a structural summary (same finding ids appear in both).

## Verification checklist

| SC | Check |
|----|-------|
| SC-1 — each finding once + summary + per-project | Count findings in output via grep; compare to `len(findings)`; confirm per-project sections present. |
| SC-2 — HTML opens with no network calls | `grep -E 'https?://\|<script\|<link' output.html` → must be empty (ignore CSS variable values). |
| SC-3 — MD renders cleanly | Inspect in terminal + VSCode preview. |
| SC-4 — no raw `$HOME` paths | `grep '/Users/' output.{html,md}` → must be empty. |

## Out of scope for Phase 4

- Interactive filtering / search (v2 — OUT-05 alt).
- Diff-mode / time-series reports (v2).
- README / install docs (Phase 5).
- Copy-to-clipboard fix snippets (v2).

## Risks

- **HTML escaping gaps**: evidence strings may contain `<`, `&` — must be escaped. Use `html.escape()`; treat this as a non-negotiable rule.
- **Path normalization regex collisions**: if user's home contains special characters, `str.replace` beats regex — use exact prefix match on `str(path).startswith(str(home))`.
- **Empty inventory / zero findings**: renderer must produce a valid "no findings" report, not crash. Explicit branches in both renderers.

---
*Plan locked: 2026-04-19*
