from typing import Any

import pytest

from forked.adapters.inbound.sdk.recorder import Recorder
from forked.application.capture import CaptureLimits, CapturePipeline
from forked.application.commands.record_run import RecordingService
from forked.application.errors import CaptureFailed, RunNotFound
from forked.application.queries.inspect_run import InspectRun, ListRuns
from forked.domain.effects.effect_class import EffectClass
from forked.domain.runs.event import CaptureStatus, EventDraft, EventType
from forked.domain.runs.redaction import REDACTED, RedactionPolicy
from forked.domain.runs.run import RunStatus
from forked.domain.shared.errors import IllegalTransition, InvalidEvent
from forked.domain.shared.identifiers import RunId
from tests.conftest import CAPS, make_deps
from tests.fakes import FailingEventLog, InMemoryRunStore


def echo(text: str) -> str:
    return text


def not_json() -> Any:
    return object()


def test_recording_produces_ordered_typed_events(
    service: RecordingService, store: InMemoryRunStore
) -> None:
    with Recorder(service).record(CAPS) as run:
        assert run.call_tool("echo", EffectClass.PURE_LOCAL, echo, text="hi") == "hi"
        run.set_outcome({"ok": True})
    events = list(store.read(run.run_id))
    assert [e.event_type for e in events] == [
        EventType.RUN_STARTED,
        EventType.TOOL_CALL,
        EventType.TOOL_RESULT,
        EventType.RUN_COMPLETED,
    ]
    assert [e.sequence for e in events] == [0, 1, 2, 3]
    assert events[2].parent_event_id == events[1].event_id
    assert events[3].payload == {"ok": True}
    assert store.get(run.run_id).status is RunStatus.COMPLETED


def test_tool_exception_is_recorded_and_run_fails(
    service: RecordingService, store: InMemoryRunStore
) -> None:
    def boom() -> str:
        raise RuntimeError("tool exploded")

    recorder = Recorder(service)
    with pytest.raises(RuntimeError, match="tool exploded"), recorder.record(CAPS) as run:
        run.call_tool("echo", EffectClass.PURE_LOCAL, boom)
    events = list(store.read(run.run_id))
    assert events[2].event_type is EventType.TOOL_ERROR
    assert events[2].payload == {"error_type": "RuntimeError", "message": "tool exploded"}
    assert events[-1].event_type is EventType.RUN_FAILED
    snap = store.get(run.run_id)
    assert snap.status is RunStatus.FAILED
    assert snap.reason == "RuntimeError: tool exploded"


def test_secret_in_failure_reason_is_redacted_everywhere(
    service: RecordingService, store: InMemoryRunStore
) -> None:
    secret = "sk-live-abcdefghijklmnopqrstuv"  # noqa: S105 - fake value under test
    with pytest.raises(ValueError, match="sk-live"), Recorder(service).record(CAPS) as run:
        raise ValueError(f"bad key {secret}")
    snap = store.get(run.run_id)
    assert secret not in (snap.reason or "")
    assert snap.reason == REDACTED
    assert all(secret not in str(e.payload) for e in store.read(run.run_id))


def test_redaction_happens_before_persistence(
    service: RecordingService, store: InMemoryRunStore
) -> None:
    with Recorder(service).record(CAPS) as run:
        run.call_tool("echo", EffectClass.PURE_LOCAL, lambda api_key: "ok", api_key="s3cr3t")
    call = list(store.read(run.run_id))[1]
    assert call.capture_status is CaptureStatus.REDACTED
    assert call.payload == {"inputs": {"api_key": REDACTED}}
    assert call.redacted_paths == ("$.inputs.api_key",)


def test_oversized_payload_is_omitted_with_digest_not_truncated(store: InMemoryRunStore) -> None:
    service = RecordingService(make_deps(store, limits=CaptureLimits(max_payload_bytes=64)))
    with Recorder(service).record(CAPS) as run:
        run.call_tool("echo", EffectClass.PURE_LOCAL, echo, text="x" * 500)
    result = list(store.read(run.run_id))[2]
    assert result.capture_status is CaptureStatus.OMITTED
    assert result.payload is None
    assert result.payload_digest is not None
    assert result.payload_digest.startswith("sha256:")


def test_non_json_tool_output_fails_the_run_visibly(
    service: RecordingService, store: InMemoryRunStore
) -> None:
    with pytest.raises(InvalidEvent), Recorder(service).record(CAPS) as run:
        run.call_tool("echo", EffectClass.PURE_LOCAL, not_json)
    assert store.get(run.run_id).status is RunStatus.FAILED


def test_storage_failure_marks_run_incomplete_and_raises(store: InMemoryRunStore) -> None:
    failing = FailingEventLog(fail_at=1)
    deps = make_deps(failing)
    session = RecordingService(deps).start(CAPS)
    with pytest.raises(CaptureFailed, match="disk full"):
        session.capture(
            EventDraft(
                EventType.TOOL_CALL, "t", tool_name="echo", effect_class=EffectClass.PURE_LOCAL
            )
        )
    snap = failing.get(session.run_id)
    assert snap.status is RunStatus.INCOMPLETE
    assert snap.reason is not None
    assert "could not be persisted" in snap.reason
    report = InspectRun(failing, failing).execute(session.run_id)
    assert any(
        "metadata expects 2 events but log has 1" in item
        for item in report.assessment.missing_evidence
    )


def test_event_limit_fails_closed(store: InMemoryRunStore) -> None:
    service = RecordingService(make_deps(store, limits=CaptureLimits(max_events_per_run=3)))

    def five_calls() -> RunId:
        with Recorder(service).record(CAPS) as run:
            for _ in range(5):
                run.call_tool("echo", EffectClass.PURE_LOCAL, echo, text="a")
        raise AssertionError("unreachable")

    with pytest.raises(CaptureFailed):
        five_calls()
    (run_id,) = store.list_ids()
    assert store.get(run_id).status is RunStatus.INCOMPLETE


def test_finished_session_rejects_capture(service: RecordingService) -> None:
    session = service.start(CAPS)
    session.complete()
    with pytest.raises(IllegalTransition):
        session.complete()


def test_inspect_unknown_run_fails_clearly(store: InMemoryRunStore) -> None:
    with pytest.raises(RunNotFound):
        InspectRun(store, store).execute(RunId("run_00000099"))


def test_list_runs(service: RecordingService, store: InMemoryRunStore) -> None:
    first = service.start(CAPS)
    first.complete()
    second = service.start(CAPS)
    ids = [s.run_id for s in ListRuns(store).execute()]
    assert ids == sorted([first.run_id, second.run_id], key=lambda r: r.value)


def test_pipeline_rejects_non_json_payload() -> None:
    pipeline = CapturePipeline(RedactionPolicy(), CaptureLimits())
    with pytest.raises(InvalidEvent):
        pipeline.prepare({"x": float("inf")})
