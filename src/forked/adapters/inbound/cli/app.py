"""``forked`` command-line interface (Phase 1: record, inspect, runs).

Exit codes: 0 ok · 1 ``--strict`` found missing evidence · 2 a FORKED error occurred.
"""

import dataclasses
import json
from pathlib import Path
from typing import Annotated, Any

import typer

from forked import __version__
from forked.application.queries.inspect_run import RunReport
from forked.bootstrap.container import Application, build_application
from forked.demo.toy_agent import CAPABILITIES, run_toy_agent
from forked.domain.branches.branch import Intervention
from forked.domain.comparison.compare import Comparison
from forked.domain.shared.errors import ForkedError
from forked.domain.shared.identifiers import RunId
from forked.domain.shared.schema import EVENT_SCHEMA_VERSION

app = typer.Typer(
    help="FORKED — record, inspect and (soon) branch instrumented executions. Local-first.",
    no_args_is_help=True,
    add_completion=False,
)

StoreOption = Annotated[
    Path,
    typer.Option(
        "--store",
        envvar="FORKED_STORE",
        help="Directory where runs are stored.",
        file_okay=False,
    ),
]
DEFAULT_STORE = Path(".forked")
WORKFLOWS = ("toy-agent",)


def _fail(exc: ForkedError) -> typer.Exit:
    typer.echo(f"error[{exc.code}]: {exc}", err=True)
    return typer.Exit(code=2)


def _app(store: Path) -> Application:
    return build_application(store)


def report_to_dict(report: RunReport) -> dict[str, Any]:
    snap = report.snapshot
    assessment = report.assessment
    ratio = assessment.completeness.ratio
    return {
        "run_id": snap.run_id.value,
        "recorded_status": snap.status.value,
        "effective_status": assessment.effective_status.value,
        "reason": snap.reason,
        "started_at": snap.started_at.isoformat(),
        "finished_at": snap.finished_at.isoformat() if snap.finished_at else None,
        "adapter": {
            "name": snap.capabilities.name,
            "version": snap.capabilities.version,
            "limitations": list(snap.capabilities.limitations),
        },
        "environment": snap.environment.as_dict(),
        "events": assessment.sequence.count,
        "sequence_valid": assessment.sequence.is_valid,
        "capture_completeness": {
            "declared": sorted(assessment.completeness.declared),
            "observed": sorted(assessment.completeness.observed),
            "ratio": ratio,
        },
        "redacted_events": assessment.redacted_events,
        "omitted_events": assessment.omitted_events,
        "missing_evidence": list(assessment.missing_evidence),
    }


def _print_report(report: RunReport, show_events: bool) -> None:
    data = report_to_dict(report)
    ratio = data["capture_completeness"]["ratio"]
    typer.echo(f"run        {data['run_id']}")
    typer.echo(f"status     {data['effective_status']} (recorded: {data['recorded_status']})")
    if data["reason"]:
        typer.echo(f"reason     {data['reason']}")
    typer.echo(f"adapter    {data['adapter']['name']} {data['adapter']['version']}")
    typer.echo(f"events     {data['events']} (sequence valid: {data['sequence_valid']})")
    typer.echo(
        "capture    "
        + ("unknown (nothing declared)" if ratio is None else f"{ratio:.0%} of declared points")
    )
    typer.echo(f"redacted   {data['redacted_events']} event(s)")
    typer.echo(f"omitted    {data['omitted_events']} event(s)")
    for limitation in data["adapter"]["limitations"]:
        typer.echo(f"limitation {limitation}")
    if data["missing_evidence"]:
        typer.echo("missing evidence:")
        for item in data["missing_evidence"]:
            typer.echo(f"  - {item}")
    else:
        typer.echo("missing evidence: none detected")
    if show_events:
        typer.echo("events:")
        for event in report.events:
            tool = f" {event.tool_name}" if event.tool_name else ""
            effect = f" [{event.effect_class}]" if event.effect_class else ""
            typer.echo(
                f"  {event.sequence:>4} {event.event_type}{tool}{effect} ({event.capture_status})"
            )


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"forked {__version__}")
        raise typer.Exit


@app.callback()
def main_callback(
    version: Annotated[
        bool,
        typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version."),
    ] = False,
) -> None:
    """FORKED command-line interface."""


@app.command()
def record(
    workflow: Annotated[str, typer.Argument(help=f"Workflow to record: {', '.join(WORKFLOWS)}.")],
    store: StoreOption = DEFAULT_STORE,
) -> None:
    """Execute a supported demo workflow and record it locally."""
    if workflow not in WORKFLOWS:
        typer.echo(f"error[unknown_workflow]: supported: {', '.join(WORKFLOWS)}", err=True)
        raise typer.Exit(code=2)
    application = _app(store)
    try:
        run_id = run_toy_agent(application.recorder, store / "toy-outbox")
        report = application.inspect_run.execute(run_id)
    except ForkedError as exc:
        raise _fail(exc) from exc
    typer.echo(f"recorded {run_id}")
    _print_report(report, show_events=False)


@app.command()
def replay(
    run_id: Annotated[str, typer.Argument(help="Recorded run to replay.")],
    store: StoreOption = DEFAULT_STORE,
) -> None:
    """Re-run the toy-agent workflow from RUN_ID's recorded observations.

    No tool executes: every result comes from the recording, so the outbox is never
    written. A call the recording cannot answer fails the replay (exit 2).
    """
    application = _app(store)
    try:
        new_id = run_toy_agent(
            application.recorder,
            store / "toy-outbox",
            session=application.recorder.replay(RunId(run_id), CAPABILITIES),
        )
        report = application.inspect_run.execute(new_id)
    except ForkedError as exc:
        raise _fail(exc) from exc
    typer.echo(f"replayed {run_id} as {new_id} (0 tools executed)")
    _print_report(report, show_events=False)


def comparison_to_dict(c: Comparison) -> dict[str, Any]:
    return {
        "cip_version": EVENT_SCHEMA_VERSION,
        "baseline": c.baseline_id,
        "branch": c.branch_id,
        "branch_status": c.branch_status.value,
        "intervention": c.intervention,
        "steps": [dataclasses.asdict(s) for s in c.steps],
        "outcome_changes": [
            {"field": k, "baseline": a, "branch": b} for k, a, b in c.outcome_changes
        ],
        "invariants": [{**dataclasses.asdict(i), "status": i.status.value} for i in c.invariants],
        "claim_level": c.claim_level.value,
        "statement": c.statement,
        "missing_evidence": list(c.missing_evidence),
    }


@app.command()
def branch(
    run_id: Annotated[str, typer.Argument(help="Parent run to fork.")],
    at: Annotated[
        int, typer.Option("--at", help="Sequence of a tool.call event (see inspect --events).")
    ],
    value: Annotated[
        str, typer.Option("--value", help="JSON value that replaces that call's result.")
    ],
    store: StoreOption = DEFAULT_STORE,
) -> None:
    """Fork RUN_ID at a tool call, replace its result, and re-run the toy-agent workflow.

    Calls before the checkpoint replay; later calls replay if unchanged, otherwise only
    pure_local tools execute and everything else is denied (nothing is sent).
    """
    try:
        replacement = json.loads(value)
    except json.JSONDecodeError as exc:
        typer.echo(f"error[invalid_value]: --value is not JSON: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    application = _app(store)
    parent = RunId(run_id)
    try:
        new_id = run_toy_agent(
            application.recorder,
            store / "toy-outbox",
            session=application.recorder.branch(
                parent, CAPABILITIES, Intervention(checkpoint=at, value=replacement)
            ),
        )
        comparison = application.compare_runs.execute(parent, new_id)
    except ForkedError as exc:
        raise _fail(exc) from exc
    typer.echo(f"branched {run_id} at sequence {at} as {new_id}")
    _print_comparison(comparison)


@app.command()
def compare(
    baseline: Annotated[str, typer.Argument(help="Baseline (parent) run.")],
    branch_id: Annotated[str, typer.Argument(metavar="BRANCH", help="Branch of the baseline.")],
    store: StoreOption = DEFAULT_STORE,
    as_json: Annotated[bool, typer.Option("--json", help="Machine-readable output.")] = False,
) -> None:
    """Compare a baseline with its branch: steps, outcome, invariants, claim level."""
    try:
        comparison = _app(store).compare_runs.execute(RunId(baseline), RunId(branch_id))
    except ForkedError as exc:
        raise _fail(exc) from exc
    if as_json:
        typer.echo(json.dumps(comparison_to_dict(comparison), indent=2))
    else:
        _print_comparison(comparison)


def _print_comparison(c: Comparison) -> None:
    typer.echo(f"baseline   {c.baseline_id}")
    typer.echo(f"branch     {c.branch_id} ({c.branch_status})")
    typer.echo("steps:")
    for s in c.steps:
        typer.echo(f"  #{s.index} {s.tool}: {s.status} [{s.decision}]")
    typer.echo("outcome changes:")
    for field, before, after in c.outcome_changes:
        typer.echo(f"  {field}: {json.dumps(before)} -> {json.dumps(after)}")
    typer.echo("invariants:")
    for inv in c.invariants:
        typer.echo(f"  {inv.status:<8} {inv.id}  ({inv.evidence})")
    typer.echo(f"claim      {c.claim_level}")
    typer.echo(f"statement  {c.statement}")
    for item in c.missing_evidence:
        typer.echo(f"missing    {item}")


@app.command()
def inspect(
    run_id: Annotated[str, typer.Argument(help="Run id, e.g. run_0a1b2c3d...")],
    store: StoreOption = DEFAULT_STORE,
    as_json: Annotated[bool, typer.Option("--json", help="Machine-readable output.")] = False,
    events: Annotated[bool, typer.Option("--events", help="List every event.")] = False,
    strict: Annotated[
        bool, typer.Option("--strict", help="Exit 1 if any evidence is missing.")
    ] = False,
) -> None:
    """Report status, ordering, capture completeness and missing evidence of a run."""
    try:
        report = _app(store).inspect_run.execute(RunId(run_id))
    except ForkedError as exc:
        raise _fail(exc) from exc
    if as_json:
        typer.echo(json.dumps(report_to_dict(report), indent=2))
    else:
        _print_report(report, show_events=events)
    if strict and report.assessment.missing_evidence:
        raise typer.Exit(code=1)


@app.command()
def runs(store: StoreOption = DEFAULT_STORE) -> None:
    """List recorded runs."""
    try:
        snapshots = _app(store).list_runs.execute()
    except ForkedError as exc:
        raise _fail(exc) from exc
    if not snapshots:
        typer.echo(f"no runs in {store}")
        return
    for snap in snapshots:
        typer.echo(
            f"{snap.run_id}  {snap.status:<10}  {snap.capabilities.name}  "
            f"{snap.started_at.isoformat()}"
        )


def main() -> None:
    app()
