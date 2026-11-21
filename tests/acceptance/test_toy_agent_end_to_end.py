"""UC-01 acceptance: record the toy agent and inspect it, fully offline."""

import json
import socket
from pathlib import Path

import pytest

from forked.bootstrap.container import Application
from forked.demo.toy_agent import run_toy_agent
from forked.domain.effects.effect_class import EffectClass
from forked.domain.runs.event import CaptureStatus, EventType
from forked.domain.runs.run import RunStatus


@pytest.fixture
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def guard(*_: object, **__: object) -> None:
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket.socket, "connect", guard)
    monkeypatch.setattr(socket, "create_connection", guard)


@pytest.mark.usefixtures("no_network")
def test_record_and_inspect_toy_agent(app: Application, tmp_path: Path) -> None:
    outbox = tmp_path / "outbox"
    run_id = run_toy_agent(app.recorder, outbox)
    report = app.inspect_run.execute(run_id)

    assert report.snapshot.status is RunStatus.COMPLETED
    assert report.assessment.effective_status is RunStatus.COMPLETED
    assert report.assessment.sequence.is_valid
    assert report.assessment.completeness.ratio == 1.0
    assert report.assessment.missing_evidence == ()
    assert report.assessment.redacted_events == 1

    kinds = [(e.event_type, e.tool_name, e.effect_class) for e in report.events]
    assert kinds == [
        (EventType.RUN_STARTED, None, None),
        (EventType.TOOL_CALL, "search_policy", EffectClass.PURE_LOCAL),
        (EventType.TOOL_RESULT, "search_policy", EffectClass.PURE_LOCAL),
        (EventType.TOOL_CALL, "get_exchange_rate", EffectClass.EXTERNAL_READ),
        (EventType.TOOL_RESULT, "get_exchange_rate", EffectClass.EXTERNAL_READ),
        (EventType.TOOL_CALL, "send_email", EffectClass.EXTERNAL_WRITE),
        (EventType.TOOL_RESULT, "send_email", EffectClass.EXTERNAL_WRITE),
        (EventType.RUN_COMPLETED, None, None),
    ]
    assert report.events[3].capture_status is CaptureStatus.REDACTED
    assert report.events[-1].payload == {
        "converted": 92.0,
        "rate": 0.92,
        "policy_hits": 1,
        "email": {"accepted": True, "message_file": "message-0001.json"},
    }
    # the external write happened exactly once, during recording
    assert len(list(outbox.glob("message-*.json"))) == 1
    limitations = report.snapshot.capabilities.limitations
    assert any("no network call" in item for item in limitations)


def test_interrupted_run_is_reported_incomplete(app: Application, tmp_path: Path) -> None:
    run_id = run_toy_agent(app.recorder, tmp_path / "outbox")
    run_dir = app.store_root / "runs" / run_id.value
    # simulate a crash: metadata still says "recording" and the tail of the log is lost
    meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    meta.update(status="recording", finished_at=None)
    (run_dir / "run.json").write_text(json.dumps(meta), encoding="utf-8")
    lines = (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines(keepends=True)
    (run_dir / "events.jsonl").write_text("".join(lines[:5]), encoding="utf-8")

    report = app.inspect_run.execute(run_id)
    assert report.assessment.effective_status is RunStatus.INCOMPLETE
    missing = " | ".join(report.assessment.missing_evidence)
    assert "never finalized" in missing
    assert "declared capture point never observed: tool:send_email" in missing
    assert "metadata expects 8 events but log has 5" in missing
