"""Shared view-model — the only thing renderers consume.

Built from Inventory + Finding[] via `build_report_data`. Both HTML and
Markdown renderers walk the same structure so feature parity is enforced
by construction.

Path normalization (SAFE-02) runs here, before any string reaches a
renderer.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from audit.model import Finding, SEVERITY_ORDER
from harness.model import GlobalHarness, Inventory, Project


TOP_RECOMMENDATIONS = 5


@dataclass(frozen=True)
class FindingView:
    id: str
    title: str
    severity: str
    scope_paths: tuple[str, ...]
    evidence: str
    rationale: str
    suggested_fix: str


@dataclass(frozen=True)
class ProjectSummary:
    name: str
    display_path: str
    is_global: bool
    is_instrumented: bool
    artifacts: tuple[tuple[str, str], ...]  # (kind, display_path)
    findings: tuple[FindingView, ...]
    worst_severity: str | None


@dataclass(frozen=True)
class ReportData:
    generated_at: str
    configured_roots: tuple[str, ...]
    totals: dict
    top_recommendations: tuple[FindingView, ...]
    findings: tuple[FindingView, ...]
    projects: tuple[ProjectSummary, ...]


def normalize_path(value: Path | str, home: Path) -> str:
    """Replace a $HOME prefix with `~` for shareability (SAFE-02)."""
    s = str(value)
    home_s = str(home)
    if s == home_s:
        return "~"
    if s.startswith(home_s + "/"):
        return "~" + s[len(home_s):]
    return s


def _normalize_text_paths(text: str, home: Path) -> str:
    """Replace any $HOME prefix inside an arbitrary string."""
    home_s = str(home)
    return text.replace(home_s, "~")


def build_report_data(
    inventory: Inventory,
    findings: list[Finding],
    *,
    home: Path | None = None,
) -> ReportData:
    home_path = home if home is not None else Path.home()

    finding_views = tuple(
        FindingView(
            id=f.id,
            title=f.title,
            severity=f.severity,
            scope_paths=tuple(normalize_path(p, home_path) for p in f.scope),
            evidence=_normalize_text_paths(f.evidence, home_path),
            rationale=f.rationale,
            suggested_fix=f.suggested_fix,
        )
        for f in findings
    )

    # Counts
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in finding_views:
        counts[f.severity] += 1

    totals = {
        "projects": len(inventory.projects),
        "instrumented": inventory.instrumented_count(),
        "uninstrumented": len(inventory.projects) - inventory.instrumented_count(),
        "findings": len(finding_views),
        **counts,
    }

    # Global pseudo-project first
    global_project = _build_global_summary(inventory.global_harness, finding_views, home_path)
    per_project = [
        _build_project_summary(p, finding_views, home_path) for p in inventory.projects
    ]
    projects = (global_project, *per_project) if global_project else tuple(per_project)

    top_reco = finding_views[:TOP_RECOMMENDATIONS]

    roots_display = tuple(normalize_path(r, home_path) for r in inventory.configured_roots)

    generated_at = (
        inventory.generated_at.isoformat(timespec="seconds")
        if isinstance(inventory.generated_at, datetime)
        else datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    )

    return ReportData(
        generated_at=generated_at,
        configured_roots=roots_display,
        totals=totals,
        top_recommendations=top_reco,
        findings=finding_views,
        projects=projects,
    )


def _build_global_summary(
    gh: GlobalHarness, findings: tuple[FindingView, ...], home: Path
) -> ProjectSummary | None:
    if not gh.exists:
        return None
    display_root = normalize_path(gh.root, home)
    artifacts = tuple(
        (a.kind, normalize_path(a.path, home)) for a in gh.artifacts
    )
    scoped = _findings_touching(findings, display_root)
    return ProjectSummary(
        name="Global",
        display_path=display_root,
        is_global=True,
        is_instrumented=True,
        artifacts=artifacts,
        findings=scoped,
        worst_severity=_worst_severity(scoped),
    )


def _build_project_summary(
    project: Project, findings: tuple[FindingView, ...], home: Path
) -> ProjectSummary:
    display_root = normalize_path(project.root, home)
    artifacts = tuple(
        (a.kind, normalize_path(a.path, home)) for a in project.artifacts
    )
    scoped = _findings_touching(findings, display_root)
    return ProjectSummary(
        name=project.name,
        display_path=display_root,
        is_global=False,
        is_instrumented=project.is_instrumented,
        artifacts=artifacts,
        findings=scoped,
        worst_severity=_worst_severity(scoped),
    )


def _findings_touching(findings: tuple[FindingView, ...], project_path: str) -> tuple[FindingView, ...]:
    out: list[FindingView] = []
    for f in findings:
        for sp in f.scope_paths:
            # Exact match or scope path is under project path (covers artifact-scoped findings).
            if sp == project_path or sp.startswith(project_path + "/"):
                out.append(f)
                break
    return tuple(out)


def _worst_severity(findings: tuple[FindingView, ...]) -> str | None:
    if not findings:
        return None
    return min(findings, key=lambda f: SEVERITY_ORDER[f.severity]).severity
