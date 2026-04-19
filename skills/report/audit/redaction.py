"""Secret redaction — the ONLY path for config text into Finding.evidence.

`redact(text)` replaces known secret shapes with `[REDACTED:<kind>]`.
Idempotent: running it twice produces the same result as running it once.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class _Pattern:
    kind: str
    regex: re.Pattern[str]
    needs_entropy_check: bool = False


_PATTERNS: tuple[_Pattern, ...] = (
    _Pattern("anthropic_api_key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    _Pattern("openai_api_key", re.compile(r"sk-(?:proj-)?[A-Za-z0-9_\-]{20,}")),
    _Pattern("github_token", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    _Pattern("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    _Pattern("google_api_key", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    _Pattern("bearer_token", re.compile(r"[Bb]earer\s+[A-Za-z0-9_\-\.=]{16,}")),
    _Pattern("jwt", re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
    _Pattern("hex_token", re.compile(r"\b[a-f0-9]{40,}\b")),
    _Pattern("high_entropy_token", re.compile(r"\b[A-Za-z0-9+/=_\-]{32,}\b"), needs_entropy_check=True),
)

_ALREADY_REDACTED = re.compile(r"\[REDACTED:[a-z_]+\]")


def _looks_high_entropy(token: str) -> bool:
    has_upper = any(c.isupper() for c in token)
    has_lower = any(c.islower() for c in token)
    has_digit = any(c.isdigit() for c in token)
    return has_upper and has_lower and has_digit


def redact(text: str) -> str:
    """Replace secret-shaped substrings with [REDACTED:<kind>] markers.

    Patterns run in a deterministic order. An already-redacted marker is
    preserved verbatim so the function is idempotent.
    """
    if not text:
        return text

    result = text
    for pattern in _PATTERNS:
        if pattern.needs_entropy_check:
            def _replace(m: re.Match[str], kind: str = pattern.kind) -> str:
                token = m.group(0)
                if not _looks_high_entropy(token):
                    return token
                return f"[REDACTED:{kind}]"
            result = pattern.regex.sub(_replace, result)
        else:
            result = pattern.regex.sub(f"[REDACTED:{pattern.kind}]", result)
    return result


def was_redacted(original: str, redacted: str | None = None) -> bool:
    """True if running `redact(original)` would change the input."""
    if redacted is None:
        redacted = redact(original)
    return original != redacted
