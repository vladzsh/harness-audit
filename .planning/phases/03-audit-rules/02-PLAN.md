# Phase 3: Audit Rules + Findings Model — Plan

**Created:** 2026-04-19
**Status:** Ready to execute
**Covers:** AUD-01..08, AGG-01, SAFE-01

## Goal

Convert an `Inventory` into a deterministic `list[Finding]`:
- Every finding has a canonical shape (AUD-08).
- Secrets detected in configs are redacted *before* any finding is emitted (SAFE-01).
- Findings that are truly the same issue across projects collapse to one with an aggregated scope (AGG-01).

Phase 4 renders this list; Phase 3 never renders.

## Finding data model

```python
@dataclass(frozen=True)
class Finding:
    id: str                  # e.g. "AUD-04/secret-in-settings"
    title: str
    severity: str            # critical | high | medium | low
    scope: tuple[Path, ...]  # which projects / globals it applies to
    evidence: str            # redacted snippet, already safe to display
    rationale: str           # why it matters
    suggested_fix: str       # concrete action
    dedup_key: str           # stable fingerprint for AGG-01 merging
```

Severity levels are a four-step scale. Rules map to one deterministically.

## Secret redaction (SAFE-01)

Central `redact(text: str) -> str` lives in `audit/redaction.py`. Runs on every raw string before it enters a Finding's `evidence`. Patterns (ordered — longest/most-specific first):

| Kind | Pattern |
|------|---------|
| Anthropic API key | `sk-ant-[A-Za-z0-9_\-]{20,}` |
| Generic `sk-` token | `sk-[A-Za-z0-9_\-]{16,}` |
| Bearer token in string | `Bearer\s+[A-Za-z0-9_\-\.=]{16,}` |
| AWS access key id | `AKIA[0-9A-Z]{16}` |
| Google API key | `AIza[0-9A-Za-z\-_]{35}` |
| GitHub token | `gh[pousr]_[A-Za-z0-9]{36}` |
| JWT-shaped | `eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}` |
| Long hex token (≥40) | `\b[a-f0-9]{40,}\b` |
| Long base64-ish token (≥32 mixed-case+digits, with at least one upper, one lower, one digit) | `\b[A-Za-z0-9+/=_\-]{32,}\b` (with entropy-ish filter — require ≥1 upper, ≥1 lower, ≥1 digit) |

All matches replaced with `[REDACTED:<kind>]`. The redactor is idempotent. It's the **only** path for raw config strings into findings. Rules never return raw secret material — they always call `redact()` on evidence snippets before constructing `Finding`.

Test: a fixture with a literal `"anthropic_api_key": "sk-ant-abcd...1234567890123456789012"` yields a finding whose `evidence` contains `[REDACTED:anthropic_api_key]` and no substring of the original key.

## Rule catalog

Rule modules live under `skills/report/audit/rules/`. One file per rule; each exports `RULE: Rule` and `evaluate(ctx) -> Iterable[RawFinding]`. A central registry in `audit/rules/__init__.py` lists them in stable order.

| Req | Rule id | Module | Severity | What it flags |
|-----|---------|--------|----------|---------------|
| AUD-01 | `AUD-01/settings-schema` | `settings_schema.py` | medium | Settings JSON parse errors; unknown top-level keys outside a known-valid set; deprecated key shapes |
| AUD-02 | `AUD-02/broad-permissions` | `broad_permissions.py` | high | Permissions allow that contains blanket `"Bash(**)"`, `"*"`, no `deny` alongside broad allow, or empty permissions when hooks present |
| AUD-03 | `AUD-03/suspicious-hooks` | `suspicious_hooks.py` | critical | Hook commands with `curl`/`wget` to non-localhost, `nc` to remote, `eval`, base64-decoded pipes, unquoted env exfiltration |
| AUD-04 | `AUD-04/secret-in-config` | `secret_in_config.py` | critical | Any config file where `redact()` would have changed content (indicates secret material present on disk) |
| AUD-05 | `AUD-05/claude-md-hygiene` | `claude_md_hygiene.py` | low | CLAUDE.md over 12 KB or under 80 bytes; heading duplication within one file; zero headings; only boilerplate |
| AUD-06 | `AUD-06/missing-recommended` | `missing_recommended.py` | medium | Instrumented project without CLAUDE.md; project with `.mcp.json` but no `settings*.json`; global with no CLAUDE.md |
| AUD-07 | `AUD-07/best-practice-gap` | `best_practice_gap.py` | low | Global lacks a curated set of recommended skills/plugins (v1 seed list short and opinionated — see below) |
| AUD-08 | enforced by Finding dataclass | — | — | Schema guarantee: every Finding carries id/title/severity/scope/evidence/rationale/suggested_fix/dedup_key |

**AUD-07 seed list (v1):** two plugins and one hook pattern that materially help most Claude Code users. Keep tiny — it's a demo rule, not a plugin directory.

Seed:
- Recommend at least one of: `superpowers`, `claude-md-management` plugins enabled.
- Recommend a `SessionStart` hook for session state hygiene (if many projects use hooks but global does not).

Intentionally conservative — we don't want the report to nag about a dozen plugins. Better to leave this sparse and let Phase 4 / v2 expand via config.

## Orchestration layer

`audit/engine.py`:

```python
def audit(inventory: Inventory) -> list[Finding]:
    raw = []
    for rule in REGISTRY:
        raw.extend(rule.evaluate(inventory))
    deduped = _dedup(raw)
    return sorted(deduped, key=lambda f: (SEVERITY_ORDER[f.severity], f.id))
```

`_dedup(raw)`:
- Group by `dedup_key`.
- For each group, merge `scope` (preserving order of first appearance, de-duplicating paths).
- Pick the first finding's fields for everything else (they're identical by contract — `dedup_key` must capture all varying fields).

Rules choose `dedup_key` to scope merging correctly. Examples:
- `AUD-04/secret-in-config` dedup by `rule_id + kind_of_secret` — if 3 projects leak `sk-ant-*`, merge.
- `AUD-02/broad-permissions` dedup by `rule_id + exact-broad-pattern` — if 5 projects allow `Bash(**)`, merge.
- `AUD-05/claude-md-hygiene` per-file — `rule_id + file_path`, never merges across projects (intentional).

Rules that must NOT merge (e.g. AUD-05 per-file) use the full path in the key so groups collapse to one entry each.

## File reads in Phase 3

Up to Phase 3 we've only stat'd files. Now rules need *content*:
- `settings.json` / `settings.local.json` — parsed as JSON (`json.loads`), wrapped in try/except. On parse error → AUD-01 finding, no further rules for that file.
- `hooks/hooks.json` — JSON, same handling.
- `.mcp.json` — JSON.
- `CLAUDE.md`, `AGENTS.md` — read as text, only size and heading structure inspected.

All reads go through a tiny helper `audit/io.py::read_text_safe(path)` that:
- Caps reads at 512 KB (anything bigger is a finding on its own).
- Returns `(text, error)`; rules skip on error.

## Files to create / modify

| Path | Purpose |
|------|---------|
| `skills/report/audit/__init__.py` | Package marker |
| `skills/report/audit/model.py` | `Finding` dataclass + severity constants |
| `skills/report/audit/redaction.py` | `redact()` + patterns |
| `skills/report/audit/io.py` | `read_text_safe`, `read_json_safe` |
| `skills/report/audit/rules/__init__.py` | Registry list + `Rule` protocol |
| `skills/report/audit/rules/settings_schema.py` | AUD-01 |
| `skills/report/audit/rules/broad_permissions.py` | AUD-02 |
| `skills/report/audit/rules/suspicious_hooks.py` | AUD-03 |
| `skills/report/audit/rules/secret_in_config.py` | AUD-04 |
| `skills/report/audit/rules/claude_md_hygiene.py` | AUD-05 |
| `skills/report/audit/rules/missing_recommended.py` | AUD-06 |
| `skills/report/audit/rules/best_practice_gap.py` | AUD-07 |
| `skills/report/audit/engine.py` | `audit(inventory) -> list[Finding]` + dedup |
| `skills/report/cli.py` | Invoke `audit()` after `discover()`, embed counts in placeholder |

## Build sequence

1. `audit/model.py`, `audit/redaction.py`, `audit/io.py` — foundation layer. Redaction first so rules can depend on it.
2. `audit/rules/__init__.py` — empty registry stub.
3. Implement rules one-by-one, adding each to the registry: AUD-04 first (because it validates redaction), then AUD-01, 02, 03, 05, 06, 07.
4. `audit/engine.py` — orchestrate + dedup.
5. Wire into `cli.py`: after discovery, call `audit()`, add summary counts (total findings, severity breakdown) to the placeholder report.
6. Verify:
   - Redaction: write a fixture file under a temp project with a fake `sk-ant-*` token, run audit, assert `redact()` was applied.
   - Dedup: synthesize two projects with the same broad permission shape, assert merged scope.
   - Real filesystem: run against user's real harness, sanity-check findings counts and titles.

## Success criteria validation

| SC | Verification |
|----|--------------|
| SC-1 — rules produce expected findings | Fixture per rule (constructed input → expected finding id/severity). Run via `python3 -m skills.report.audit.engine` or inline assertions. |
| SC-2 — secret redaction | Fixture containing `sk-ant-xxx...`; confirm raw token absent from any `Finding.evidence`. |
| SC-3 — dedup aggregates scope | Two fixture projects, same rule trigger; assert single finding with both paths in scope. |
| SC-4 — finding shape | Dataclass enforces schema at construction. A static check in engine asserts all fields are non-empty before returning. |

## Out of scope for Phase 3

- Rendering anything — Phase 4.
- Path normalization (`$HOME` → `~`) — Phase 4 (SAFE-02).
- Best-practice rule becoming a real plugin recommender with a big curated list — v2.

## Risks

- **Over-eager secret regex**: the long-base64 pattern can false-positive on minified JS blobs or hashes. Mitigation: entropy filter requires mixed case + digits; still, rules that emit evidence always run `redact()` — a false positive here just redacts a harmless string, never leaks.
- **JSON parse errors cascading**: a malformed settings.json should only produce AUD-01, not propagate failures into other rules. Rules check `error is not None` on their inputs and skip cleanly.
- **Noise on uninstrumented projects**: AUD-06 must NOT fire for every project without `.claude/` — scope it to projects that are partially instrumented (have some files but are missing the recommended one). Uninstrumented projects are reported differently via the inventory summary, not as a per-project finding.

---
*Plan locked: 2026-04-19*
