"""Read-only walker that produces an Inventory from a real filesystem.

No content is read beyond directory listings and stat calls. No writes.
Errors (permission, broken symlinks) are recorded on the Artifact, never raised.
"""
from __future__ import annotations

from collections.abc import Iterable, Iterator
from datetime import datetime, timezone
from pathlib import Path

from .model import (
    AGENT_FILE,
    AGENT_MEMORY,
    AGENTS_MD,
    Artifact,
    CLAUDE_MD,
    COMMAND_FILE,
    GlobalHarness,
    HOOKS_FILE,
    INSTALLED_PLUGINS,
    Inventory,
    KEYBINDINGS,
    KNOWN_MARKETPLACES,
    MARKETPLACE_DIR,
    MCP_JSON,
    Project,
    SETTINGS,
    SETTINGS_LOCAL,
    SKILL_DIR,
    SYMLINK_OUT,
)


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
_PLUGIN_IGNORE = frozenset({
    "cache", "data", "install-counts-cache.json", "blocklist.json",
})
_PROJECT_MAX_DEPTH = 2


def discover(
    project_roots: Iterable[Path] | None = None,
    *,
    home: Path | None = None,
) -> Inventory:
    home_path = home if home is not None else Path.home()
    roots = tuple(
        Path(r).expanduser().resolve()
        for r in (project_roots if project_roots is not None else [home_path / "projects"])
    )

    global_harness = _discover_global(home_path / ".claude")

    seen: set[Path] = set()
    projects: list[Project] = []
    for root in roots:
        # A configured root can itself be harness-instrumented (e.g. ~/projects
        # with a shared ~/projects/.claude/ dir). Capture it as a project so
        # its config doesn't silently drop from the audit.
        if _is_project_shaped(root) and root not in seen:
            seen.add(root)
            projects.append(_discover_project(root))
        for project_root in _iter_project_roots(root):
            if project_root in seen:
                continue
            seen.add(project_root)
            projects.append(_discover_project(project_root))

    return Inventory(
        generated_at=datetime.now(timezone.utc).astimezone(),
        configured_roots=roots,
        global_harness=global_harness,
        projects=tuple(projects),
    )


def _safe_stat_size(path: Path) -> tuple[int | None, str | None]:
    try:
        return path.stat().st_size, None
    except OSError as exc:
        return None, str(exc)


def _artifact(kind: str, path: Path) -> Artifact:
    size, error = _safe_stat_size(path)
    return Artifact(kind=kind, path=path, size_bytes=size, error=error)


def _safe_iterdir(path: Path) -> list[Path]:
    try:
        return sorted(path.iterdir())
    except OSError:
        return []


def _discover_global(claude_root: Path) -> GlobalHarness:
    if not claude_root.exists():
        return GlobalHarness(root=claude_root, exists=False, artifacts=())

    artifacts: list[Artifact] = []

    for entry in _safe_iterdir(claude_root):
        name = entry.name
        if entry.is_file():
            if name in _GLOBAL_IGNORE_FILES:
                continue
            if name == "settings.json":
                artifacts.append(_artifact(SETTINGS, entry))
            elif name == "settings.local.json":
                artifacts.append(_artifact(SETTINGS_LOCAL, entry))
            elif name == "CLAUDE.md":
                artifacts.append(_artifact(CLAUDE_MD, entry))
            elif name == "keybindings.json":
                artifacts.append(_artifact(KEYBINDINGS, entry))
            elif name == "AGENTS.md":
                artifacts.append(_artifact(AGENTS_MD, entry))
        elif entry.is_dir():
            if name in _GLOBAL_IGNORE_DIRS:
                continue
            if name == "skills":
                artifacts.extend(_collect_named_dir_children(entry, SKILL_DIR))
            elif name == "commands":
                artifacts.extend(_collect_named_file_children(entry, COMMAND_FILE, ".md"))
            elif name == "agents":
                artifacts.extend(_collect_named_file_children(entry, AGENT_FILE, ".md"))
            elif name == "hooks":
                hooks_json = entry / "hooks.json"
                if hooks_json.exists():
                    artifacts.append(_artifact(HOOKS_FILE, hooks_json))
            elif name == "plugins":
                artifacts.extend(_collect_plugins_dir(entry))

    return GlobalHarness(root=claude_root, exists=True, artifacts=tuple(artifacts))


def _collect_named_dir_children(parent: Path, kind: str) -> list[Artifact]:
    out: list[Artifact] = []
    for entry in _safe_iterdir(parent):
        if entry.is_dir() and not entry.name.startswith("."):
            out.append(_artifact(kind, entry))
    return out


def _collect_named_file_children(parent: Path, kind: str, suffix: str) -> list[Artifact]:
    out: list[Artifact] = []
    for entry in _safe_iterdir(parent):
        if entry.is_file() and entry.suffix == suffix and not entry.name.startswith("."):
            out.append(_artifact(kind, entry))
    return out


def _collect_plugins_dir(plugins_root: Path) -> list[Artifact]:
    out: list[Artifact] = []
    for entry in _safe_iterdir(plugins_root):
        name = entry.name
        if name in _PLUGIN_IGNORE:
            continue
        if entry.is_file():
            if name == "installed_plugins.json":
                out.append(_artifact(INSTALLED_PLUGINS, entry))
            elif name == "known_marketplaces.json":
                out.append(_artifact(KNOWN_MARKETPLACES, entry))
        elif entry.is_dir() and name == "marketplaces":
            for mp in _safe_iterdir(entry):
                if mp.is_dir() and not mp.name.startswith("."):
                    out.append(_artifact(MARKETPLACE_DIR, mp))
    return out


def _iter_project_roots(root: Path) -> Iterator[Path]:
    if not root.exists() or not root.is_dir():
        return
    yield from _iter_project_roots_depth(root, current_depth=0, base=root)


def _iter_project_roots_depth(dir_path: Path, current_depth: int, base: Path) -> Iterator[Path]:
    if current_depth >= _PROJECT_MAX_DEPTH:
        return
    for entry in _safe_iterdir(dir_path):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        if entry.is_symlink():
            try:
                target = entry.resolve()
            except OSError:
                continue
            try:
                target.relative_to(base)
            except ValueError:
                # Symlink escapes the configured root — skip.
                continue
        # At depth 0, every subdirectory of a configured root is a project
        # candidate. At depth > 0, only yield subdirs that are themselves
        # project-shaped — prevents monorepo internals (deployment/, tz/, etc.)
        # from polluting the inventory as "uninstrumented projects".
        if current_depth == 0 or _is_project_shaped(entry):
            yield entry
        if _looks_like_project_container(entry):
            yield from _iter_project_roots_depth(entry, current_depth + 1, base)


def _is_project_shaped(candidate: Path) -> bool:
    if (candidate / ".git").exists():
        return True
    if (candidate / "CLAUDE.md").exists() or (candidate / "AGENTS.md").exists():
        return True
    if (candidate / ".claude").is_dir():
        return True
    if (candidate / ".mcp.json").exists():
        return True
    return False


def _looks_like_project_container(candidate: Path) -> bool:
    """True if `candidate` holds at least one project-shaped subdirectory.

    Matches umbrella layouts like ~/rg/ksk-btz/ksk-bz/ even when the parent
    is itself instrumented — the user can legitimately have an umbrella repo
    with a nested working project under it.
    """
    for child in _safe_iterdir(candidate):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if (child / ".git").exists():
            return True
        if (child / "CLAUDE.md").exists() or (child / "AGENTS.md").exists():
            return True
        if (child / ".claude").is_dir():
            return True
    return False


def _discover_project(project_root: Path) -> Project:
    artifacts: list[Artifact] = []

    for fname, kind in (
        ("CLAUDE.md", CLAUDE_MD),
        ("AGENTS.md", AGENTS_MD),
        (".mcp.json", MCP_JSON),
    ):
        p = project_root / fname
        if p.exists():
            artifacts.append(_artifact(kind, p))

    claude_dir = project_root / ".claude"
    if claude_dir.is_dir():
        for entry in _safe_iterdir(claude_dir):
            name = entry.name
            if entry.is_file():
                if name == "settings.json":
                    artifacts.append(_artifact(SETTINGS, entry))
                elif name == "settings.local.json":
                    artifacts.append(_artifact(SETTINGS_LOCAL, entry))
                elif name == "CLAUDE.md":
                    artifacts.append(_artifact(CLAUDE_MD, entry))
            elif entry.is_dir():
                if name == "skills":
                    artifacts.extend(_collect_named_dir_children(entry, SKILL_DIR))
                elif name == "commands":
                    artifacts.extend(_collect_named_file_children(entry, COMMAND_FILE, ".md"))
                elif name == "agents":
                    artifacts.extend(_collect_named_file_children(entry, AGENT_FILE, ".md"))
                elif name == "hooks":
                    hooks_json = entry / "hooks.json"
                    if hooks_json.exists():
                        artifacts.append(_artifact(HOOKS_FILE, hooks_json))
                elif name == "agent-memory":
                    artifacts.append(_artifact(AGENT_MEMORY, entry))

    return Project(
        root=project_root,
        name=project_root.name,
        is_instrumented=bool(artifacts),
        artifacts=tuple(artifacts),
    )
