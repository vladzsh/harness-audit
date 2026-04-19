#!/usr/bin/env python3
"""harness-audit report CLI.

Discover → audit → render. Produces a single self-contained HTML report
(default) plus a functional Markdown file, both derived from the same
view-model.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from audit.engine import audit
from harness.discovery import discover
from render.html import render_html
from render.markdown import render_markdown
from render.view import build_report_data


OUTPUT_DIRNAME = ".claude/harness-audit"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="harness-audit",
        description="Audit your Claude Code harness across all projects.",
    )
    parser.add_argument(
        "--format",
        choices=("html", "markdown"),
        default="html",
        help="Primary output format (default: html). Both files are always written; "
             "this flag only decides which path is echoed as the report to open.",
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
    findings = audit(inventory)
    data = build_report_data(inventory, findings)

    now = datetime.now(timezone.utc).astimezone()
    timestamp_file = now.strftime("%Y%m%d-%H%M%S")

    output_dir = Path.home() / OUTPUT_DIRNAME
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"harness-audit: cannot create {output_dir}: {exc}", file=sys.stderr)
        return 2

    html_path = output_dir / f"report-{timestamp_file}.html"
    md_path = output_dir / f"report-{timestamp_file}.md"

    try:
        html_path.write_text(render_html(data), encoding="utf-8")
        md_path.write_text(render_markdown(data), encoding="utf-8")
    except OSError as exc:
        print(f"harness-audit: cannot write report: {exc}", file=sys.stderr)
        return 2

    primary = html_path if args.format == "html" else md_path
    print(primary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
