"""HTML renderer — single self-contained file, inline CSS, no scripts.

Dark-mode report. Per-project drilldown uses <details> so no JS is needed.
"""
from __future__ import annotations

from html import escape

from render.view import FindingView, ProjectSummary, ReportData


_SEVERITY_LABELS = {
    "critical": "CRITICAL",
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "LOW",
}


_STYLE = """
:root {
  --bg: #0f1117;
  --surface: #1a1d27;
  --surface-hi: #242836;
  --border: #2e3345;
  --text: #e4e7ef;
  --text-dim: #8b90a0;
  --accent: #60a5fa;
  --accent-2: #a78bfa;
  --green: #34d399;
  --yellow: #fbbf24;
  --orange: #fb923c;
  --red: #f87171;
  --red-bg: rgba(248,113,113,0.12);
  --orange-bg: rgba(251,146,60,0.12);
  --yellow-bg: rgba(251,191,36,0.12);
  --green-bg: rgba(52,211,153,0.12);
  --blue-bg: rgba(96,165,250,0.12);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
html { color-scheme: dark; }
body {
  font-family: 'SF Mono', 'Cascadia Code', 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
  background: var(--bg);
  color: var(--text);
  padding: 2.5rem 1.5rem;
  line-height: 1.55;
  max-width: 1100px;
  margin: 0 auto;
}
header { text-align: center; margin-bottom: 2.5rem; padding-bottom: 1.5rem; border-bottom: 1px solid var(--border); }
header h1 {
  font-size: 1.7rem; font-weight: 700;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  -webkit-background-clip: text; background-clip: text; color: transparent;
  margin-bottom: 0.35rem;
}
header .meta { color: var(--text-dim); font-size: 0.82rem; }
header .roots { color: var(--text-dim); font-size: 0.75rem; margin-top: 0.4rem; }
header .roots code { background: var(--surface); padding: 0.1rem 0.4rem; border-radius: 4px; color: var(--text); }

.section-title {
  font-size: 1rem; font-weight: 600; margin: 2.2rem 0 1rem;
  padding-left: 0.6rem; border-left: 3px solid var(--accent);
  letter-spacing: 0.01em;
}
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.8rem;
  margin-bottom: 2rem;
}
.stat-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 1rem; text-align: center;
}
.stat-card .num { font-size: 1.8rem; font-weight: 700; line-height: 1.1; }
.stat-card .label { font-size: 0.7rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.35rem; }
.stat-card.critical .num { color: var(--red); }
.stat-card.high     .num { color: var(--orange); }
.stat-card.medium   .num { color: var(--yellow); }
.stat-card.low      .num { color: var(--accent); }
.stat-card.info     .num { color: var(--green); }

ol.top-reco { list-style: none; counter-reset: reco; padding-left: 0; }
ol.top-reco li {
  counter-increment: reco;
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 0.9rem 1.1rem 0.9rem 3rem; margin-bottom: 0.6rem; position: relative;
}
ol.top-reco li::before {
  content: counter(reco);
  position: absolute; left: 1rem; top: 50%; transform: translateY(-50%);
  width: 1.6rem; height: 1.6rem; border-radius: 50%;
  background: var(--accent-2); color: var(--bg);
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 0.8rem;
}
ol.top-reco .title { font-weight: 600; font-size: 0.88rem; }
ol.top-reco .fix { font-size: 0.78rem; color: var(--text-dim); margin-top: 0.25rem; }

.finding {
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 1rem 1.2rem; margin-bottom: 0.9rem;
  border-left: 3px solid var(--border);
}
.finding.critical { border-left-color: var(--red); }
.finding.high     { border-left-color: var(--orange); }
.finding.medium   { border-left-color: var(--yellow); }
.finding.low      { border-left-color: var(--accent); }

.finding .title-row { display: flex; gap: 0.6rem; align-items: center; flex-wrap: wrap; }
.finding .id { color: var(--text-dim); font-size: 0.72rem; }
.finding .title { font-weight: 600; font-size: 0.92rem; flex: 1; }
.badge {
  font-size: 0.62rem; padding: 0.18rem 0.55rem; border-radius: 4px;
  font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;
}
.badge.critical { background: var(--red-bg); color: var(--red); }
.badge.high     { background: var(--orange-bg); color: var(--orange); }
.badge.medium   { background: var(--yellow-bg); color: var(--yellow); }
.badge.low      { background: var(--blue-bg); color: var(--accent); }

.finding dl { margin-top: 0.7rem; display: grid; grid-template-columns: auto 1fr; gap: 0.25rem 0.9rem; font-size: 0.78rem; }
.finding dt { color: var(--text-dim); }
.finding dd code { background: var(--surface-hi); padding: 0.05rem 0.35rem; border-radius: 4px; font-size: 0.75rem; }
.finding .scope-list { display: flex; flex-wrap: wrap; gap: 0.35rem; }

details.project {
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  margin-bottom: 0.7rem; overflow: hidden;
}
details.project[open] { border-color: var(--accent); }
details.project.global { border-color: var(--accent-2); }
details.project summary {
  list-style: none;
  padding: 0.9rem 1.2rem;
  cursor: pointer; user-select: none;
  display: flex; justify-content: space-between; align-items: center; gap: 0.8rem;
}
details.project summary::-webkit-details-marker { display: none; }
details.project summary::before {
  content: "▸"; color: var(--text-dim); font-size: 0.75rem; transition: transform 0.2s;
}
details.project[open] summary::before { transform: rotate(90deg); }
.project-name { font-weight: 600; font-size: 0.92rem; }
.project-path { font-size: 0.72rem; color: var(--text-dim); margin-top: 0.2rem; }
.project-meta { font-size: 0.72rem; color: var(--text-dim); white-space: nowrap; }
.project-body { padding: 0 1.2rem 1.2rem; }
.project-body h4 { font-size: 0.78rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.05em; margin: 0.7rem 0 0.4rem; }
.project-body ul { list-style: none; padding-left: 0; font-size: 0.78rem; }
.project-body ul li { padding: 0.2rem 0; color: var(--text); }
.project-body ul li code { color: var(--text-dim); font-size: 0.72rem; }

footer { margin-top: 3rem; padding-top: 1.2rem; border-top: 1px solid var(--border); text-align: center; color: var(--text-dim); font-size: 0.72rem; }
footer code { background: var(--surface); padding: 0.1rem 0.35rem; border-radius: 4px; }

.empty { color: var(--text-dim); font-style: italic; }
"""


def render_html(data: ReportData) -> str:
    parts: list[str] = []
    parts.append("<!doctype html>")
    parts.append('<html lang="en">')
    parts.append("<head>")
    parts.append('<meta charset="utf-8">')
    parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    parts.append(f"<title>Claude Code Harness Audit — {escape(data.generated_at)}</title>")
    parts.append(f"<style>{_STYLE}</style>")
    parts.append("</head>")
    parts.append("<body>")
    parts.append(_render_header(data))
    parts.append(_render_stats(data))
    parts.append(_render_top_reco(data))
    parts.append(_render_all_findings(data))
    parts.append(_render_projects(data))
    parts.append(_render_footer())
    parts.append("</body></html>")
    return "\n".join(parts)


def _render_header(data: ReportData) -> str:
    t = data.totals
    roots_html = (
        " · ".join(f"<code>{escape(r)}</code>" for r in data.configured_roots)
        if data.configured_roots else "<span class='empty'>no roots configured</span>"
    )
    return (
        "<header>"
        "<h1>Claude Code Harness Audit</h1>"
        f"<div class='meta'>Generated {escape(data.generated_at)} · "
        f"{t['projects']} projects ({t['instrumented']} instrumented) · "
        f"{t['findings']} findings</div>"
        f"<div class='roots'>Project roots: {roots_html}</div>"
        "</header>"
    )


def _render_stats(data: ReportData) -> str:
    t = data.totals
    cards = [
        ("critical", "Critical", t["critical"]),
        ("high", "High", t["high"]),
        ("medium", "Medium", t["medium"]),
        ("low", "Low", t["low"]),
        ("info", "Instrumented", t["instrumented"]),
        ("info", "Uninstrumented", t["uninstrumented"]),
    ]
    html_parts = ['<section class="stats">']
    for cls, label, value in cards:
        html_parts.append(
            f'<div class="stat-card {cls}"><div class="num">{value}</div>'
            f'<div class="label">{escape(label)}</div></div>'
        )
    html_parts.append("</section>")
    return "".join(html_parts)


def _render_top_reco(data: ReportData) -> str:
    if not data.top_recommendations:
        return (
            '<div class="section-title">Top recommendations</div>'
            '<p class="empty">No findings — nothing to recommend.</p>'
        )
    out = ['<div class="section-title">Top recommendations</div>', '<ol class="top-reco">']
    for f in data.top_recommendations:
        out.append(
            f'<li><div class="title">{escape(f.title)}</div>'
            f'<div class="fix">{escape(f.suggested_fix)}</div></li>'
        )
    out.append("</ol>")
    return "".join(out)


def _render_all_findings(data: ReportData) -> str:
    out = ['<div class="section-title">All findings</div>']
    if not data.findings:
        out.append('<p class="empty">No findings.</p>')
        return "".join(out)
    for f in data.findings:
        out.append(_render_finding(f))
    return "".join(out)


def _render_finding(f: FindingView) -> str:
    sev = escape(f.severity)
    scope_html = " ".join(f"<code>{escape(p)}</code>" for p in f.scope_paths)
    return (
        f'<div class="finding {sev}">'
        f'<div class="title-row">'
        f'<span class="badge {sev}">{_SEVERITY_LABELS[f.severity]}</span>'
        f'<span class="title">{escape(f.title)}</span>'
        f'<span class="id">{escape(f.id)}</span>'
        f'</div>'
        f'<dl>'
        f'<dt>Scope ({len(f.scope_paths)})</dt><dd class="scope-list">{scope_html}</dd>'
        f'<dt>Evidence</dt><dd>{escape(f.evidence)}</dd>'
        f'<dt>Why it matters</dt><dd>{escape(f.rationale)}</dd>'
        f'<dt>Suggested fix</dt><dd>{escape(f.suggested_fix)}</dd>'
        f'</dl>'
        f'</div>'
    )


def _render_projects(data: ReportData) -> str:
    out = ['<div class="section-title">Per-project drilldown</div>']
    for p in data.projects:
        out.append(_render_project(p))
    return "".join(out)


def _render_project(p: ProjectSummary) -> str:
    cls = "project global" if p.is_global else "project"
    worst_badge = (
        f'<span class="badge {p.worst_severity}">{_SEVERITY_LABELS[p.worst_severity]}</span>'
        if p.worst_severity else ""
    )
    status = "instrumented" if p.is_instrumented else "uninstrumented"
    label = "Global" if p.is_global else escape(p.name)
    meta = (
        f"{len(p.artifacts)} artifacts · {len(p.findings)} findings · {status}"
    )
    body_parts: list[str] = ['<div class="project-body">']
    if p.artifacts:
        body_parts.append("<h4>Artifacts</h4><ul>")
        for kind, path in p.artifacts:
            body_parts.append(
                f"<li><strong>{escape(kind)}</strong> — <code>{escape(path)}</code></li>"
            )
        body_parts.append("</ul>")
    if p.findings:
        body_parts.append("<h4>Findings in scope</h4><ul>")
        for f in p.findings:
            body_parts.append(
                f"<li><span class='badge {escape(f.severity)}'>"
                f"{_SEVERITY_LABELS[f.severity]}</span> "
                f"<strong>{escape(f.id)}</strong> — {escape(f.title)}</li>"
            )
        body_parts.append("</ul>")
    if not p.artifacts and not p.findings:
        body_parts.append('<p class="empty">No harness artifacts, no findings.</p>')
    body_parts.append("</div>")

    return (
        f'<details class="{cls}">'
        f'<summary>'
        f'<div><div class="project-name">{label}</div>'
        f'<div class="project-path">{escape(p.display_path)}</div></div>'
        f'<div class="project-meta">{meta} {worst_badge}</div>'
        f'</summary>'
        f'{"".join(body_parts)}'
        f'</details>'
    )


def _render_footer() -> str:
    return (
        "<footer>"
        "Generated by <code>harness-audit</code> · single-file report · safe to share. "
        "Paths normalized to <code>~</code>; secrets redacted."
        "</footer>"
    )
