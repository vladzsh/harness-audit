#!/usr/bin/env python3
"""harness-audit report CLI.

Phase 2: invokes the read-only discovery walker and embeds an inventory
summary into the placeholder report. Real rendering arrives in Phase 4.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from harness.discovery import discover
from harness.model import Inventory

OUTPUT_DIRNAME = ".claude/harness-audit"
SCAFFOLD_MARKER = "harness-audit scaffold OK"


def _summary_lines(inv: Inventory) -> list[str]:
    gh = inv.global_harness
    gh_status = "present" if gh.exists else "missing"
    instrumented = inv.instrumented_count()
    total = len(inv.projects)
    roots = ", ".join(str(r) for r in inv.configured_roots) or "(none)"
    return [
        f"Global harness at {gh.root}: {gh_status} ({len(gh.artifacts)} artifacts)",
        f"Project roots scanned: {roots}",
        f"Projects found: {total} ({instrumented} instrumented, {total - instrumented} uninstrumented)",
    ]


def build_html(timestamp_iso: str, summary: list[str]) -> str:
    items = "\n".join(f"    <li>{line}</li>" for line in summary)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>harness-audit report</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         max-width: 720px; margin: 3rem auto; padding: 0 1.5rem; color: #222; }}
  h1 {{ font-size: 1.6rem; margin-bottom: 0.25rem; }}
  .timestamp {{ color: #666; font-size: 0.9rem; }}
  .marker {{ margin-top: 2rem; padding: 1rem 1.25rem;
             background: #f4f4f5; border-left: 3px solid #0ea5e9; }}
  ul.summary {{ margin-top: 1.5rem; padding-left: 1.25rem; line-height: 1.55; }}
</style>
</head>
<body>
<main>
  <h1>harness-audit — report</h1>
  <div class="timestamp">Generated: {timestamp_iso}</div>
  <ul class="summary">
{items}
  </ul>
  <div class="marker">{SCAFFOLD_MARKER}</div>
</main>
</body>
</html>
"""


def build_markdown(timestamp_iso: str, summary: list[str]) -> str:
    lines = "\n".join(f"- {line}" for line in summary)
    return f"""# harness-audit — report

Generated: {timestamp_iso}

## Summary

{lines}

{SCAFFOLD_MARKER}
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="harness-audit",
        description="Audit your Claude Code harness and write a single report.",
    )
    parser.add_argument(
        "--format",
        choices=("html", "markdown"),
        default="html",
        help="Output format (default: html). Both formats are always written; "
             "this flag selects which path is echoed as the primary report.",
    )
    parser.add_argument(
        "--roots",
        action="append",
        default=None,
        metavar="PATH",
        help="Project root to scan (repeatable). Default: ~/projects",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    roots = [Path(r).expanduser() for r in args.roots] if args.roots else None
    inventory = discover(project_roots=roots)
    summary = _summary_lines(inventory)

    now = datetime.now(timezone.utc).astimezone()
    timestamp_file = now.strftime("%Y%m%d-%H%M%S")
    timestamp_iso = now.isoformat(timespec="seconds")

    output_dir = Path.home() / OUTPUT_DIRNAME
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"harness-audit: cannot create {output_dir}: {exc}", file=sys.stderr)
        return 2

    html_path = output_dir / f"report-{timestamp_file}.html"
    md_path = output_dir / f"report-{timestamp_file}.md"

    try:
        html_path.write_text(build_html(timestamp_iso, summary), encoding="utf-8")
        md_path.write_text(build_markdown(timestamp_iso, summary), encoding="utf-8")
    except OSError as exc:
        print(f"harness-audit: cannot write report: {exc}", file=sys.stderr)
        return 2

    primary = html_path if args.format == "html" else md_path
    print(primary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
