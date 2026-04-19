"""Small, safe file readers used by rules.

Rules MUST NOT call `open()` directly — go through these helpers so errors
and size limits are enforced uniformly.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MAX_READ_BYTES = 512 * 1024


def read_text_safe(path: Path) -> tuple[str | None, str | None]:
    """Return (text, error). Caps reads at MAX_READ_BYTES."""
    try:
        size = path.stat().st_size
        if size > MAX_READ_BYTES:
            return None, f"file exceeds {MAX_READ_BYTES} bytes ({size})"
        return path.read_text(encoding="utf-8", errors="replace"), None
    except OSError as exc:
        return None, str(exc)


def read_json_safe(path: Path) -> tuple[Any, str | None]:
    """Return (parsed, error). Parses JSON after read_text_safe."""
    text, err = read_text_safe(path)
    if err is not None:
        return None, err
    try:
        return json.loads(text or ""), None
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc.msg} at line {exc.lineno}"
