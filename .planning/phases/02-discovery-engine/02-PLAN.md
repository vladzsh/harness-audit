# Phase 2: Discovery Engine — Plan

**Created:** 2026-04-19
**Status:** Ready to execute
**Covers:** DISC-01, DISC-02, DISC-03, DISC-04, DISC-05, SAFE-03

## Goal

Walk the filesystem and produce a normalized in-memory `Inventory` of every Claude Code harness artifact — global config plus per-project config — without parsing semantics or making judgments. Read-only. Phase 3 turns this inventory into findings.

## Context from real survey (2026-04-19)

Inspected the user's actual harness to lock the shape of what we must detect:

**Global `~/.claude/` — collect:**
- `settings.json`, `settings.local.json`
- `CLAUDE.md`, `keybindings.json`
- `skills/<name>/` — each subdir is a user skill (SKILL.md inside)
- `commands/`, `agents/`, `hooks/` — if they exist at this level
- `plugins/installed_plugins.json`, `plugins/known_marketplaces.json`
- `plugins/marketplaces/<name>/` — each installed marketplace

**Global `~/.claude/` — IGNORE (runtime/cache/telemetry, not config):**
- `cache/`, `sessions/`, `projects/`, `todos/`, `tasks/`, `telemetry/`, `shell-snapshots/`
- `history.jsonl`, `stats-cache.json`, `session-env/`, `paste-cache/`, `file-history/`
- `backups/`, `chrome/`, `downloads/`, `debug/`, `ide/`, `memory/`, `channels/`
- `policy-limits.json`, `remote-settings.json`
- `harness-audit/` (our own output)
- `plugins/cache/`, `plugins/data/`, `plugins/install-counts-cache.json`, `plugins/blocklist.json`

**Per-project artifacts — collect:**
- `.claude/settings.json`, `.claude/settings.local.json`
- `.claude/commands/`, `.claude/skills/`, `.claude/agents/`, `.claude/hooks/`
- `CLAUDE.md`, `AGENTS.md` at project root
- `.mcp.json` at project root
- `.claude/agent-memory/` (observed in `~/rg/ksk-btz/.claude`)

**Observation on project roots:**
- User's real layout: `~/projects/` AND `~/rg/` both contain projects. Nested projects exist (`~/rg/ksk-btz/ksk-bz/`). Some "roots" have their own `.claude/` (e.g. `~/rg/.claude`, `~/projects/.claude`) that applies to all sub-projects.
- Default project roots list: `["~/projects"]` per roadmap. Configurable via `--roots` flag.
- Walk depth: treat each immediate subdirectory of a root as a project candidate; additionally scan one more level deep for nested layouts (e.g. `rg/ksk-btz/ksk-bz`). Skip hidden dirs except `.claude`.

## Implementation decisions

### D-05: Data model as dataclasses

`Inventory` is a single dataclass holding `GlobalHarness` + `list[Project]`. Each artifact (file/dir) is represented by a small `Artifact` dataclass with: `kind` (enum-lite string), `path` (Path), `exists` (bool), `size_bytes` (int | None), `error` (str | None). Content not read in Phase 2 — Phase 3 reads selectively.

Rationale: dataclasses + stdlib `json` for Phase 3 serialization, no schema library needed. `kind` is an enum-lite string for easy JSON round-trip.

### D-06: No content reads in Phase 2 (except to enumerate children)

Phase 2 answers *what exists*, not *what's inside*. Exceptions:
- Directory listings (required to enumerate `skills/`, `commands/`, `agents/`, `plugins/marketplaces/`).
- Stat calls for size (cheap, useful for the report).

Rationale: separates discovery from parsing. Phase 3 can read any file it wants via the Artifact's `path`, but Phase 2 stays small and fast. Also simplifies SAFE-03 reasoning: read-only means only `os.stat` + `os.listdir` in Phase 2.

### D-07: Uninstrumented projects are first-class

A project with no `.claude/`, no `CLAUDE.md`, no `AGENTS.md`, no `.mcp.json` is still listed in the inventory with `is_instrumented=False`. Empty artifact lists, no errors. This satisfies DISC-05 and lets Phase 3 emit an "uninstrumented project" recommendation.

### D-08: Project root discovery — shallow walk with nesting

Given a configured root (e.g. `~/projects`):
1. List immediate subdirectories (skip hidden, skip symlinks that escape root).
2. For each subdir: it's a `Project`. If it has no harness files AND it contains further subdirectories that each look like projects (has `.git/` or any harness file), recurse one level deeper and treat those as sibling projects too.
3. Max depth: 2 levels below root. Deeper is out of scope for v1.

Rationale: matches observed layouts (`~/rg/ksk-btz/ksk-bz` nested) without turning into a full filesystem walker.

### D-09: Symlinks — resolve but don't follow out-of-tree

`Path.is_symlink()` is checked; symlinks pointing outside the configured roots are recorded with `kind=symlink_out_of_tree` and not followed. Prevents the walker from wandering into unexpected places.

### D-10: Absolute paths preserved internally, normalized at render time

Inventory stores absolute `Path` objects (internal data). SAFE-02 (`$HOME` normalization in output) is a Phase 4 renderer concern, not a discovery concern. Keeping raw paths internally makes it easier for Phase 3 rules to inspect them.

### D-11: Error handling — record, don't raise

Any `OSError` (permission denied, broken symlink, missing file after listing) is recorded on the relevant `Artifact` as `error=str(exc)` and skipped. The walker never crashes on the user's real filesystem.

## Files to create / modify

| Path | Purpose |
|------|---------|
| `skills/report/harness/__init__.py` | Package marker (empty) |
| `skills/report/harness/model.py` | `Inventory`, `GlobalHarness`, `Project`, `Artifact` dataclasses + `ArtifactKind` constants |
| `skills/report/harness/discovery.py` | `discover(roots: list[Path]) -> Inventory` — the walker |
| `skills/report/cli.py` | Wire discovery into the CLI; emit inventory summary in the placeholder report |

## Detailed design

### `harness/model.py`

```python
# Enum-lite kinds — strings for easy JSON round-trip
SETTINGS = "settings"
SETTINGS_LOCAL = "settings_local"
CLAUDE_MD = "claude_md"
AGENTS_MD = "agents_md"
KEYBINDINGS = "keybindings"
MCP_JSON = "mcp_json"
SKILL_DIR = "skill_dir"       # a skills/<name>/ directory
COMMAND_FILE = "command_file" # a commands/<name>.md file
AGENT_FILE = "agent_file"     # an agents/<name>.md file
HOOKS_FILE = "hooks_file"     # hooks/hooks.json
INSTALLED_PLUGINS = "installed_plugins"
MARKETPLACES = "marketplaces"
MARKETPLACE_DIR = "marketplace_dir"
AGENT_MEMORY = "agent_memory"
SYMLINK_OUT = "symlink_out_of_tree"

@dataclass(frozen=True)
class Artifact:
    kind: str
    path: Path
    size_bytes: int | None = None
    error: str | None = None

@dataclass(frozen=True)
class GlobalHarness:
    root: Path                # ~/.claude
    exists: bool
    artifacts: tuple[Artifact, ...]

@dataclass(frozen=True)
class Project:
    root: Path
    name: str                 # last path component
    is_instrumented: bool     # has any harness artifact
    artifacts: tuple[Artifact, ...]

@dataclass(frozen=True)
class Inventory:
    generated_at: datetime
    configured_roots: tuple[Path, ...]
    global_harness: GlobalHarness
    projects: tuple[Project, ...]
```

### `harness/discovery.py`

Public API:

```python
def discover(
    project_roots: Iterable[Path] | None = None,
    *,
    home: Path | None = None,
) -> Inventory
```

Defaults:
- `project_roots`: `[Path.home() / "projects"]` if None.
- `home`: `Path.home()` — injectable for tests.

Internal:

```python
_GLOBAL_IGNORE_DIRS = frozenset({
    "cache", "sessions", "projects", "todos", "tasks", "telemetry",
    "shell-snapshots", "session-env", "paste-cache", "file-history",
    "backups", "chrome", "downloads", "debug", "ide", "memory",
    "channels", "harness-audit",
})
_GLOBAL_IGNORE_FILES = frozenset({
    "history.jsonl", "stats-cache.json",
    "policy-limits.json", "remote-settings.json",
})

def _discover_global(home: Path) -> GlobalHarness: ...
def _discover_project(project_root: Path) -> Project: ...
def _walk_project_roots(roots: Iterable[Path]) -> list[Path]: ...
```

`_walk_project_roots` implements D-08: list immediate subdirs, recurse one level if the subdir contains further project-shaped children. Dedupe paths.

### `cli.py` integration

Phase 1 placeholder stays responsible for writing the final output file, but now we invoke `discover()` first and embed inventory summary counts into the placeholder. This proves end-to-end: discovery works, its output reaches the renderer path.

Minimal summary in the placeholder report:
- Number of global artifacts found
- Number of projects scanned, and how many are instrumented
- Configured project roots

Phase 4 replaces this with real rendering; Phase 2 just demonstrates the wiring.

## Build sequence

1. `harness/__init__.py` (empty).
2. `harness/model.py` — dataclasses + kind constants.
3. `harness/discovery.py` — walker; start with global, then projects.
4. Integrate into `cli.py` — import `discover`, call it, embed summary.
5. Run `cli.py` and inspect the generated report — confirm counts match manual `find` survey.
6. Read-only verification: instrument the walker with a `tracemalloc`-style hook? Simpler: review the code to confirm no `open(..., 'w')`, no `.write_text`, no `mkdir` outside the output dir (already in `cli.py`). SAFE-03 passes by construction, not by runtime check.

## Success criteria validation

| SC | Verification |
|----|--------------|
| SC-1 — all real artifacts found | Run `cli.py` against user's real filesystem. Compare the reported count/paths against `find ~/projects ~/rg -maxdepth 3 \( -name ".claude" -type d -o -name "CLAUDE.md" ... \)`. Zero misses for known artifact kinds. |
| SC-2 — uninstrumented projects listed, not errored | Ensure at least one project (e.g. `~/projects/sebih` or a fresh fixture) has no config, confirm it appears in inventory with `is_instrumented=False`. |
| SC-3 — no writes outside output dir | Code review: `discovery.py` contains zero write operations. Walker uses only `Path.iterdir`, `Path.stat`, `Path.is_*`. CLI writes only under `~/.claude/harness-audit/`. |

## Out of scope for Phase 2

- Parsing settings.json content, MCP server definitions, skill frontmatter — Phase 3.
- Any rule evaluation or severity assignment — Phase 3.
- Redaction — Phase 3.
- Multi-user / team-shared config — out of v1 (single developer).
- Windows paths — v1 targets macOS + Linux per PROJECT.md.

## Risks

- **False positives in project root walker**: a directory under `~/projects` that isn't a project (e.g. `sebih` is a prototype). Mitigation: everything immediately under a configured root is a project candidate; uninstrumented flag is honest, not an error.
- **Very large `~/.claude/skills/` trees**: stat-only walk keeps this cheap.
- **Permission errors on nested dirs under external company repos**: D-11 handles by recording on Artifact.

---
*Plan locked: 2026-04-19*
