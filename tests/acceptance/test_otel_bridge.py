"""OpenTelemetry bridge acceptance: export tool spans, import a trace as an `unknown`-effect run."""

import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from forked.adapters.inbound.cli.app import app as cli
from forked.bootstrap.container import Application
from forked.demo.toy_agent import DEMO_API_KEY, run_toy_agent
from forked.domain.branches.branch import Intervention
from forked.domain.effects.effect_class import EffectClass
from forked.domain.effects.policy import EffectDenied
from forked.domain.runs.event import EventType
from forked.domain.runs.run import RunStatus
from forked.domain.shared.identifiers import RunId
from forked.domain.telemetry.otlp import InvalidTrace, parse_tool_spans

runner = CliRunner()


def _spans(document: dict[str, Any]) -> list[dict[str, Any]]:
    return document["resourceSpans"][0]["scopeSpans"][0]["spans"]  # type: ignore[no-any-return]


def _attrs(span: dict[str, Any]) -> dict[str, Any]:
    return {a["key"]: next(iter(a["value"].values())) for a in span["attributes"]}


@pytest.fixture
def run_id(app: Application, tmp_path: Path) -> RunId:
    return run_toy_agent(app.recorder, tmp_path / "outbox")


def test_export_maps_tool_calls_to_genai_spans(app: Application, run_id: RunId) -> None:
    spans = _spans(app.export_trace.execute(run_id))

    root, *tools = spans
    assert root["name"].startswith("forked.run ")
    assert [s["name"] for s in tools] == [
        "execute_tool search_policy",
        "execute_tool get_exchange_rate",
        "execute_tool send_email",
    ]
    assert {s["parentSpanId"] for s in tools} == {root["spanId"]}
    assert len({s["traceId"] for s in spans}) == 1
    assert all(len(s["traceId"]) == 32 and len(s["spanId"]) == 16 for s in spans)
    write = _attrs(tools[2])
    assert write["gen_ai.operation.name"] == "execute_tool"
    assert write["forked.effect_class"] == "external_write"
    assert tools[2]["status"] == {"code": 1}


def test_payloads_and_secrets_stay_out_unless_requested(app: Application, run_id: RunId) -> None:
    quiet = json.dumps(app.export_trace.execute(run_id))
    assert "gen_ai.tool.call.arguments" not in quiet
    assert DEMO_API_KEY not in quiet

    loud = json.dumps(app.export_trace.execute(run_id, include_payloads=True))
    assert "gen_ai.tool.call.arguments" in loud
    assert "[REDACTED]" in loud  # already redacted at capture
    assert DEMO_API_KEY not in loud


def test_export_is_deterministic(app: Application, run_id: RunId) -> None:
    assert app.export_trace.execute(run_id) == app.export_trace.execute(run_id)


def test_denied_call_exports_as_error_span_with_decision(app: Application, run_id: RunId) -> None:
    from forked.demo.toy_agent import CAPABILITIES

    branch = run_toy_agent(
        app.recorder,
        app.store_root / "outbox",
        session=app.recorder.branch(run_id, CAPABILITIES, Intervention(3, 0.5)),
    )
    send = _spans(app.export_trace.execute(branch))[-1]
    assert send["status"]["code"] == 2
    assert _attrs(send)["forked.decision"] == "deny"
    assert _attrs(send)["error.type"] == "EffectDenied"


def test_round_trip_import_marks_every_effect_unknown(app: Application, run_id: RunId) -> None:
    document = app.export_trace.execute(run_id, include_payloads=True)

    imported = app.import_trace.execute(parse_tool_spans(document))

    report = app.inspect_run.execute(imported)
    assert report.snapshot.status is RunStatus.COMPLETED
    calls = [e for e in report.events if e.event_type is EventType.TOOL_CALL]
    assert [c.tool_name for c in calls] == ["search_policy", "get_exchange_rate", "send_email"]
    assert {c.effect_class for c in calls} == {EffectClass.UNKNOWN}
    assert calls[0].trace_id == _spans(document)[1]["traceId"]
    assert report.assessment.completeness.ratio is None  # nothing declared: unknown, not 100%
    assert any("completeness is unknown" in m for m in report.assessment.missing_evidence)
    assert any("effect classes are unknown" in x for x in report.snapshot.capabilities.limitations)


def test_imported_run_can_be_branched_and_denies_unknown_effects(
    app: Application, run_id: RunId
) -> None:
    imported = app.import_trace.execute(
        parse_tool_spans(app.export_trace.execute(run_id, include_payloads=True))
    )
    report = app.inspect_run.execute(imported)
    first = next(e for e in report.events if e.event_type is EventType.TOOL_CALL)
    assert isinstance(first.payload, dict)
    original = next(
        e for e in app.inspect_run.execute(run_id).events if e.event_type is EventType.TOOL_CALL
    )
    assert first.payload == original.payload  # round trip keeps the SDK payload shape
    inputs = first.payload["inputs"]
    assert isinstance(inputs, dict)

    with app.recorder.branch(
        imported, report.snapshot.capabilities, Intervention(first.sequence, "replaced")
    ) as run:
        assert run.call_tool("search_policy", EffectClass.UNKNOWN, _never, **inputs) == "replaced"
        with pytest.raises(EffectDenied):
            run.call_tool("something_new", EffectClass.UNKNOWN, _never, x=1)


def _never(**_: object) -> Any:
    raise AssertionError("executed")


def test_error_span_imports_as_tool_error(app: Application) -> None:
    document = {
        "resourceSpans": [
            {
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "traceId": "a" * 32,
                                "spanId": "b" * 16,
                                "name": "execute_tool lookup",
                                "startTimeUnixNano": "5",
                                "attributes": [
                                    {"key": "error.type", "value": {"stringValue": "Timeout"}}
                                ],
                                "status": {"code": 2, "message": "took too long"},
                            }
                        ]
                    }
                ]
            }
        ]
    }
    run_id = app.import_trace.execute(parse_tool_spans(document))
    events = app.inspect_run.execute(run_id).events
    error = next(e for e in events if e.event_type is EventType.TOOL_ERROR)
    assert isinstance(error.payload, dict)
    assert (error.payload["error_type"], error.payload["message"]) == ("Timeout", "took too long")
    provenance = error.payload["otel"]
    assert isinstance(provenance, dict)
    assert provenance["start_unix_nano"] == "5"
    assert error.span_id == "b" * 16


def test_secret_in_imported_arguments_is_redacted(app: Application) -> None:
    secret = "sk-live-abcdefghijklmnopqrstuvwxyz0123"  # noqa: S105 - fake credential shape
    span = {
        "name": "execute_tool call_api",
        "attributes": [
            {
                "key": "gen_ai.tool.call.arguments",
                "value": {"stringValue": json.dumps({"x": secret})},
            }
        ],
    }
    app.import_trace.execute(
        parse_tool_spans({"resourceSpans": [{"scopeSpans": [{"spans": [span]}]}]})
    )
    for path in (app.store_root / "runs").rglob("*"):
        if path.is_file():
            assert secret.encode() not in path.read_bytes()


@pytest.mark.parametrize(
    "document",
    [
        [],
        {"resourceSpans": "nope"},
        {"resourceSpans": []},  # no tool spans
        {"resourceSpans": [{"scopeSpans": [{"spans": ["not-an-object"]}]}]},
        {"resourceSpans": [{"scopeSpans": [{"spans": [{"name": "execute_tool "}]}]}]},
    ],
)
def test_malformed_traces_are_rejected(document: object) -> None:
    with pytest.raises(InvalidTrace):
        parse_tool_spans(document)


def test_too_many_spans_are_refused() -> None:
    span = {"name": "execute_tool t"}
    document = {"resourceSpans": [{"scopeSpans": [{"spans": [span] * 10_001}]}]}
    with pytest.raises(InvalidTrace, match="more than"):
        parse_tool_spans(document)


def test_cli_export_then_import(tmp_path: Path) -> None:
    store = tmp_path / "store"
    recorded = runner.invoke(cli, ["record", "toy-agent", "--store", str(store)])
    run = recorded.output.split()[1]
    out = tmp_path / "trace.json"

    exported = runner.invoke(
        cli, ["otel-export", run, "--include-payloads", "--out", str(out), "--store", str(store)]
    )
    assert exported.exit_code == 0, exported.output
    imported = runner.invoke(cli, ["otel-import", str(out), "--store", str(store)])
    assert imported.exit_code == 0, imported.output
    assert "forked-otel-import" in imported.output

    out.write_text("{broken", encoding="utf-8")
    bad = runner.invoke(cli, ["otel-import", str(out), "--store", str(store)])
    assert bad.exit_code == 2
    assert "error[invalid_trace]" in bad.output
    missing = runner.invoke(
        cli, ["otel-import", str(tmp_path / "nope.json"), "--store", str(store)]
    )
    assert missing.exit_code == 2
    assert "error[storage_failure]" in missing.output
