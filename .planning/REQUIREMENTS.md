# Requirements: harness-audit

**Defined:** 2026-04-19
**Core Value:** Run one command, get one report — HTML or Markdown — that makes the state of your Claude Code harness across all projects obvious and actionable.

## v1 Requirements

### Distribution

- [ ] **DIST-01**: Project hosted as a public GitHub repository with LICENSE and README at root
- [ ] **DIST-02**: README opening paragraph (first ~60 words) explains what the skill is, who needs it, and how to install — stands alone without scrolling
- [ ] **DIST-03**: Skill is packaged as a Claude Code plugin with a `report` skill (`harness-audit:report`) conforming to current plugin/skill spec
- [ ] **DIST-04**: Installation works via a single documented path (plugin install or one-line clone into `~/.claude/`) with no compilation step
- [ ] **DIST-05**: After install, the skill is invocable in Claude Code (e.g., `/harness-audit:report` or natural language) and discovers itself via standard skill metadata

### Discovery

- [ ] **DISC-01**: Skill reads global harness config from `~/.claude/` (settings.json, skills/, plugins/, hooks, commands, agents)
- [ ] **DISC-02**: Skill discovers project-level harness artifacts under user-configured project roots (default: `~/projects/`, configurable list)
- [ ] **DISC-03**: Skill parses `CLAUDE.md` and `AGENTS.md` at every level encountered (global + per-project)
- [ ] **DISC-04**: Skill enumerates MCP server configurations (global and per-project)
- [ ] **DISC-05**: Skill handles projects with no Claude Code config gracefully (reports them as "uninstrumented" without crashing)

### Auditing

- [ ] **AUD-01**: Skill flags settings.json entries that are deprecated, misspelled, or don't match current Claude Code schema
- [ ] **AUD-02**: Skill flags overly broad permissions (e.g., blanket allow) and missing recommended defaults
- [ ] **AUD-03**: Skill flags hooks with security-suspicious shapes: commands sending data to remote hosts, eval-style patterns, obfuscated args
- [ ] **AUD-04**: Skill flags potential secrets in config files (tokens, keys, bearer strings) and redacts them from the report
- [ ] **AUD-05**: Skill flags CLAUDE.md hygiene issues: stale instructions, duplicated sections, conflicting rules across files
- [ ] **AUD-06**: Skill flags missing recommended configuration (e.g., no hooks, no CLAUDE.md, no permissions allowlist)
- [ ] **AUD-07**: Skill compares installed skills/plugins against a curated best-practice list and suggests high-value additions
- [ ] **AUD-08**: Each finding has: id, title, severity (critical/high/medium/low), scope (which projects), evidence snippet, rationale, suggested fix

### Aggregation

- [ ] **AGG-01**: Findings that appear across multiple projects are de-duplicated and listed once with a project-count
- [ ] **AGG-02**: Report shows a top-level summary: total projects scanned, total findings, severity breakdown, top-N recommendations
- [ ] **AGG-03**: Report provides per-project drill-down so user can see what's specific to each repo

### Output Formats

- [ ] **OUT-01**: User can select output format per invocation: `html` (default) or `markdown` — both are "all-in-one" single files
- [ ] **OUT-02**: HTML output is a single self-contained file (inline CSS, no external assets, no JS dependencies that require a server) — matches the `harness-audit.html` visual bar
- [ ] **OUT-03**: Markdown output is a single functional `.md` file, human-readable in terminal/IDE, with the same findings and summary as HTML
- [ ] **OUT-04**: Both formats render from a common intermediate finding data structure — feature parity is enforced
- [ ] **OUT-05**: Report file is written to a predictable location (e.g., `~/.claude/harness-audit/report-YYYYMMDD-HHMMSS.{html,md}`) and the path is shown to the user on completion

### Safety & Privacy

- [ ] **SAFE-01**: Report never contains raw detected secrets — redaction is mandatory before render
- [ ] **SAFE-02**: Absolute paths are normalized (e.g., `$HOME` substitution) so reports are safe to share with teammates
- [ ] **SAFE-03**: Skill performs only read operations on user files — no writes outside its own output directory

## v2 Requirements

### Additional Harnesses

- **V2-HARN-01**: Audit OpenAI Codex harness (`~/.codex/`)
- **V2-HARN-02**: Audit Gemini CLI harness (`~/.gemini/`)
- **V2-HARN-03**: Audit OpenCode harness
- **V2-HARN-04**: Unified cross-harness report for developers using multiple CLIs

### Advanced

- **V2-ADV-01**: Interactive HTML report (collapsible sections, filter by severity/project, search) — JS-light
- **V2-ADV-02**: Suggested-fix copy-to-clipboard snippets
- **V2-ADV-03**: Diff-mode: compare current audit against a previous one to show drift
- **V2-ADV-04**: CI mode: exit-code contract for pipelines
- **V2-ADV-05**: Auto-apply selected fixes with per-item confirmation

### Community

- **V2-COM-01**: Submit to awesome-claude-skills / awesome-claude-plugins directories
- **V2-COM-02**: Listing in Anthropic official plugin directory
- **V2-COM-03**: Contribution guide for users to propose new audit rules

## Out of Scope

| Feature | Reason |
|---------|--------|
| Auto-applying fixes in v1 | Trust/reversibility concerns; user should review before changing configs. Deferred to v2. |
| Team/org dashboard | Single-developer focus keeps v1 shippable. |
| Hosted SaaS / web UI | Static local file keeps privacy story simple and distribution friction near-zero. |
| Auditing user's application code | This skill audits the Claude Code harness, not the codebase itself. |
| Real-time monitoring | One-shot audit only; long-running daemons are out of scope. |
| Non-Claude-Code harnesses in v1 | Scope hygiene — ship one audience first, validate, expand in v2. |
| LLM-as-judge / model-based rules | Deterministic rules only for v1 — fast, explainable, reviewable. |

## Traceability

(Populated during roadmap creation.)

| Requirement | Phase | Status |
|-------------|-------|--------|
| DIST-01 | Phase 5 | Pending |
| DIST-02 | Phase 5 | Pending |
| DIST-03 | Phase 1 | Pending |
| DIST-04 | Phase 5 | Pending |
| DIST-05 | Phase 1 | Pending |
| DISC-01 | Phase 2 | Pending |
| DISC-02 | Phase 2 | Pending |
| DISC-03 | Phase 2 | Pending |
| DISC-04 | Phase 2 | Pending |
| DISC-05 | Phase 2 | Pending |
| AUD-01 | Phase 3 | Pending |
| AUD-02 | Phase 3 | Pending |
| AUD-03 | Phase 3 | Pending |
| AUD-04 | Phase 3 | Pending |
| AUD-05 | Phase 3 | Pending |
| AUD-06 | Phase 3 | Pending |
| AUD-07 | Phase 3 | Pending |
| AUD-08 | Phase 3 | Pending |
| AGG-01 | Phase 3 | Pending |
| AGG-02 | Phase 4 | Pending |
| AGG-03 | Phase 4 | Pending |
| OUT-01 | Phase 4 | Pending |
| OUT-02 | Phase 4 | Pending |
| OUT-03 | Phase 4 | Pending |
| OUT-04 | Phase 4 | Pending |
| OUT-05 | Phase 4 | Pending |
| SAFE-01 | Phase 3 | Pending |
| SAFE-02 | Phase 4 | Pending |
| SAFE-03 | Phase 2 | Pending |

**Coverage:**
- v1 requirements: 29 total
- Mapped to phases: 29
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-19*
*Last updated: 2026-04-19 after initial definition*
