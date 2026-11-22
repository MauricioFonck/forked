"""A self-contained HTML report of a run, or of a baseline and its branch (ADR-017).

One file you can open in a browser: no server, no network, **no JavaScript, no external
resource**. Everything recorded is untrusted data (tool names, arguments, results and error
messages come from the workflow), so:

* every dynamic string goes through :func:`e` (HTML-escaped, quotes included);
* a ``Content-Security-Policy`` meta tag forbids scripts, frames, images and connections
  altogether, so even a future escaping bug could not run code or phone home;
* the output is deterministic (no timestamps, no randomness): the same runs give the same bytes.

It only *presents* what the application layer already computed; it decides nothing.
"""

import html
import json
from collections.abc import Sequence
from importlib.resources import files

from forked import __version__
from forked.application.commands.evidence import VerificationReport
from forked.application.queries.inspect_run import RunReport
from forked.domain.comparison.compare import Comparison, Step
from forked.domain.runs.event import Event, EventType
from forked.domain.shared.canonical import JsonValue

MAX_PAYLOAD_CHARS = 4000
CSP = "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"

CSS = (
    files("forked.adapters.inbound.cli").joinpath("report.css").read_text(encoding="utf-8").strip()
)


def e(value: object) -> str:
    """Escape any dynamic value for HTML text and attribute contexts."""
    return html.escape(str(value), quote=True)


def _json(value: JsonValue) -> str:
    text = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True)
    if len(text) > MAX_PAYLOAD_CHARS:
        return text[:MAX_PAYLOAD_CHARS] + "\n... (truncated here; the full data is in the run file)"
    return text


def _badge(text: object, css: str) -> str:
    return f'<span class="badge {e(css)}">{e(text)}</span>'


def _chip(text: object, css: str) -> str:
    return f'<span class="chip {e(css)}">{e(text)}</span>'


def _decision(payload: JsonValue) -> str | None:
    tag = payload.get("forked") if isinstance(payload, dict) else None
    decision = tag.get("decision") if isinstance(tag, dict) else None
    return decision if isinstance(decision, str) else None


# -- one run ------------------------------------------------------------------------------


def _summary(report: RunReport, title: str) -> str:
    a, s = report.assessment, report.snapshot
    ratio = a.completeness.ratio
    percent = (
        "unknown (nothing declared)"
        if ratio is None
        else f"{round(ratio * 100)}% of declared points"
    )
    bar = (
        ""
        if ratio is None
        else f'<span class="bar"><i style="width:{round(ratio * 100)}%"></i></span> '
    )
    missing = (
        '<p class="ok">missing evidence: none detected</p>'
        if not a.missing_evidence
        else "<p><strong>missing evidence</strong></p><ul>"
        + "".join(f"<li>{e(m)}</li>" for m in a.missing_evidence)
        + "</ul>"
    )
    limits = "".join(f"<li>{e(x)}</li>" for x in s.capabilities.limitations)
    recorded_as = (
        ""
        if str(s.status) == str(a.effective_status)
        else f'<span class="muted">recorded as</span> {_chip(s.status, f"st-{s.status}")}'
    )
    return f"""
<div class="card">
<h3>{e(title)} <span class="mono">{e(s.run_id)}</span></h3>
<p>{_badge(a.effective_status, f"st-{a.effective_status}")}
 {recorded_as}
 &nbsp; adapter <strong>{e(s.capabilities.name)} {e(s.capabilities.version)}</strong>
 &nbsp; {len(report.events)} events &nbsp; sequence valid: <strong>{e(a.sequence.is_valid)}</strong></p>
<p>capture {bar}{e(percent)} &nbsp; redacted {e(a.redacted_events)} &nbsp; omitted {e(a.omitted_events)}</p>
{missing}
<details open><summary>adapter limitations (declared)</summary><ul>{limits}</ul></details>
</div>"""


def _timeline(events: Sequence[Event]) -> str:
    rows = []
    for ev in events:
        parts = [
            f'<span class="seq mono">{ev.sequence}</span>',
            f"<strong>{e(ev.event_type)}</strong>",
        ]
        if ev.tool_name:
            parts.append(f'<span class="mono">{e(ev.tool_name)}</span>')
        if ev.effect_class:
            parts.append(_badge(ev.effect_class, f"fx-{ev.effect_class}"))
        parts.append(_chip(ev.capture_status, f"st-{ev.capture_status}"))
        decision = _decision(ev.payload)
        if decision:
            parts.append(_chip(decision, f"dec-{decision}"))
        if ev.event_type is EventType.TOOL_ERROR:
            parts.append(_chip("error", "st-failed"))
        shown: JsonValue = (
            ev.payload if ev.payload is not None else {"payload_digest": ev.payload_digest}
        )
        parts.append(f"<details><summary>payload</summary><pre>{e(_json(shown))}</pre></details>")
        rows.append("<li>" + " ".join(parts) + "</li>")
    return '<ol class="ev">' + "".join(rows) + "</ol>"


# -- baseline vs branch -------------------------------------------------------------------

_NODE_W = 130


def _label(text: str) -> str:
    return e(text if len(text) <= 18 else text[:17] + "...")


def _flow_svg(steps: Sequence[Step]) -> str:
    n = max(len(steps), 1)
    width = 120 + n * _NODE_W
    summary = "; ".join(f"step {s.index} {s.tool}: {s.decision}" for s in steps)
    out = [
        f'<svg role="img" viewBox="0 0 {width} 230" aria-label="{e("Baseline and branch: " + summary)}">',
        '<text class="lbl" x="8" y="64">baseline</text><text class="lbl" x="8" y="164">branch</text>',
    ]
    if steps:
        x0, x1 = 110, 110 + (n - 1) * _NODE_W
        out.append(f'<line class="rail" x1="{x0}" y1="60" x2="{x1}" y2="60"/>')
        out.append(f'<line class="rail" x1="{x0}" y1="160" x2="{x1}" y2="160"/>')
    for i, step in enumerate(steps):
        x = 110 + i * _NODE_W
        decision = (
            step.decision if step.decision in {"replay", "intervene", "deny", "allow"} else "none"
        )
        title = e(f"step {step.index}: {step.tool} ({step.status}, {step.decision})")
        out.append(f'<line class="conn dec-{decision}" x1="{x}" y1="78" x2="{x}" y2="142"/>')
        out.append(
            f'<g class="dec-recorded"><title>{title}</title><circle cx="{x}" cy="60" r="16"/></g>'
        )
        out.append(
            f'<g class="dec-{decision}"><title>{title}</title><circle cx="{x}" cy="160" r="16"/></g>'
        )
        out.append(f'<text x="{x + 10}" y="114" class="lbl">{step.index}</text>')
        out.append(f'<text x="{x}" y="204" text-anchor="middle">{_label(step.tool or "-")}</text>')
        out.append(
            f'<text x="{x}" y="220" text-anchor="middle" class="lbl">{e(step.decision)}</text>'
        )
    out.append("</svg>")
    return "".join(out)


def _comparison(c: Comparison) -> str:
    inter = c.intervention if isinstance(c.intervention, dict) else {}
    steps = "".join(
        f'<tr><td>{s.index}</td><td class="mono">{e(s.tool)}</td><td>{_chip(s.status, "st-" + s.status if s.status == "same" else "st-redacted")}</td>'
        f"<td>{_chip(s.decision, 'dec-' + (s.decision if s.decision in {'replay', 'intervene', 'deny', 'allow'} else 'none'))}</td>"
        f"<td><pre>{e(_json(s.baseline))}</pre></td><td><pre>{e(_json(s.branch))}</pre></td></tr>"
        for s in c.steps
    )
    changes = (
        "".join(
            f'<tr><td class="mono">{e(k)}</td><td><pre>{e(_json(a))}</pre></td><td><pre>{e(_json(b))}</pre></td></tr>'
            for k, a, b in c.outcome_changes
        )
        or '<tr><td colspan="3" class="muted">no outcome field changed</td></tr>'
    )
    invariants = "".join(
        f'<tr><td>{_badge(i.status, f"st-{i.status}")}</td><td class="mono">{e(i.id)}</td>'
        f'<td>{e(i.description)}<br><span class="muted mono">{e(i.evidence)}</span></td></tr>'
        for i in c.invariants
    )
    missing = "".join(f"<li>{e(m)}</li>" for m in c.missing_evidence)
    return f"""
<h2>Baseline vs branch</h2>
<div class="card">
<p><strong>Intervention</strong> {e(inter.get("operation", "?"))} at sequence
<span class="mono">{e(inter.get("checkpoint", "?"))}</span> with value
<span class="mono">{e(json.dumps(inter.get("value"), sort_keys=True))}</span></p>
<p class="legend muted">branch decision per step:
{_chip("replay", "dec-replay")} answered from the recording ·
{_chip("intervene", "dec-intervene")} replaced by the intervention ·
{_chip("deny", "dec-deny")} not executed (policy) ·
{_chip("allow", "dec-allow")} ran live (pure_local only)</p>
{_flow_svg(c.steps)}
</div>
<h3>Steps</h3>
<table><tr><th>#</th><th>tool</th><th>vs baseline</th><th>branch decision</th><th>baseline result</th><th>branch result</th></tr>{steps}</table>
<h3>Outcome changes</h3>
<table><tr><th>field</th><th>baseline</th><th>branch</th></tr>{changes}</table>
<h2>Invariants and claim</h2>
<table><tr><th>status</th><th>invariant</th><th>what was checked</th></tr>{invariants}</table>
<div class="card">
<p class="big">claim level {_badge(c.claim_level, "st-verified" if c.claim_level == "controlled_comparison" else "st-redacted")}</p>
<p>{e(c.statement)}</p>
<p class="muted">One recorded run pair. This is never a causal estimate and carries no confidence score.</p>
{"<p><strong>missing evidence</strong></p><ul>" + missing + "</ul>" if missing else ""}
</div>"""


def _evidence(v: VerificationReport) -> str:
    i, val = v.integrity, v.validity
    findings = "".join(
        f"<li>{e(kind)}: {e(item)}</li>"
        for kind, items in (
            ("changed", i.changed),
            ("missing", i.missing),
            ("unexpected", i.unexpected),
            ("problem", i.problems),
        )
        for item in items
    )
    problems = "".join(f"<li>{e(p)}</li>" for p in val.problems)
    validity = (
        _badge("not evaluated", "st-unknown")
        if not val.evaluated
        else _badge(
            val.claim_level or "unsupported", "st-verified" if not val.problems else "st-violated"
        )
    )
    return f"""
<h2>Evidence package (exported and verified offline now)</h2>
<div class="card">
<p>integrity {_badge("ok" if i.ok else "FAILED", "st-verified" if i.ok else "st-violated")}
 &nbsp; validity {validity} &nbsp; overall {_badge("ok" if v.ok else "FAILED", "st-verified" if v.ok else "st-violated")}</p>
<p class="mono muted">package_digest {e(i.package_digest)}</p>
{"<ul>" + findings + "</ul>" if findings else ""}{"<ul>" + problems + "</ul>" if problems else ""}
<p class="muted">{e(val.note)}</p>
</div>"""


def render_html(
    run: RunReport,
    branch: RunReport | None = None,
    comparison: Comparison | None = None,
    verification: VerificationReport | None = None,
) -> str:
    title = "FORKED report: baseline and branch" if branch else "FORKED report: run"
    body = [f"<h1>{e(title)}</h1>", _summary(run, "baseline" if branch else "run")]
    if branch is not None:
        body.append(_summary(branch, "branch"))
    if comparison is not None:
        body.append(_comparison(comparison))
    if verification is not None:
        body.append(_evidence(verification))
    legend = " ".join(
        _badge(fx, f"fx-{fx}")
        for fx in (
            "pure_local",
            "recorded_read",
            "external_read",
            "external_write",
            "local_write",
            "unknown",
        )
    )
    body.append(
        f'<h2>Timeline: {"baseline" if branch else "run"}</h2><p class="legend">effect classes: {legend}</p>'
    )
    body.append(_timeline(run.events))
    if branch is not None:
        body.append("<h2>Timeline: branch</h2>" + _timeline(branch.events))
    body.append(
        f'<p class="muted">Generated locally by FORKED {e(__version__)}. This file has no scripts and loads '
        "nothing from the network.</p>"
    )
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        f'<meta http-equiv="Content-Security-Policy" content="{e(CSP)}">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{e(title)}</title><style>{CSS}</style></head><body><main>"
        + "\n".join(body)
        + "</main></body></html>\n"
    )
