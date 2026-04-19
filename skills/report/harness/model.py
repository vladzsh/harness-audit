"""Inventory data model — what the discovery walker produces."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


SETTINGS = "settings"
SETTINGS_LOCAL = "settings_local"
CLAUDE_MD = "claude_md"
AGENTS_MD = "agents_md"
KEYBINDINGS = "keybindings"
MCP_JSON = "mcp_json"
SKILL_DIR = "skill_dir"
COMMAND_FILE = "command_file"
AGENT_FILE = "agent_file"
HOOKS_FILE = "hooks_file"
INSTALLED_PLUGINS = "installed_plugins"
KNOWN_MARKETPLACES = "known_marketplaces"
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
    root: Path
    exists: bool
    artifacts: tuple[Artifact, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Project:
    root: Path
    name: str
    is_instrumented: bool
    artifacts: tuple[Artifact, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Inventory:
    generated_at: datetime
    configured_roots: tuple[Path, ...]
    global_harness: GlobalHarness
    projects: tuple[Project, ...]

    def instrumented_count(self) -> int:
        return sum(1 for p in self.projects if p.is_instrumented)
