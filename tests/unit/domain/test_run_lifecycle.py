import pytest

from forked.domain.runs.event import CaptureStatus, EventDraft, EventType
from forked.domain.runs.run import PreparedPayload, Run, RunStatus
from forked.domain.shared.errors import IllegalTransition, InvalidEvent
from forked.domain.shared.identifiers import EventId, RunId
from tests.conftest import CAPS
from tests.fakes import T0, StaticProbe

CAPTURED = PreparedPayload(payload=None, capture_status=CaptureStatus.CAPTURED)


def new_run() -> Run:
    return Run.start(RunId("run_00000001"), CAPS, StaticProbe().fingerprint(CAPS), T0)


def started() -> EventDraft:
    return EventDraft(EventType.RUN_STARTED, "test")


def test_append_assigns_contiguous_sequences() -> None:
    run = new_run()
    events = [run.append(started(), CAPTURED, EventId(f"evt_{i:08d}"), T0) for i in range(3)]
    assert [e.sequence for e in events] == [0, 1, 2]
    assert run.snapshot().next_sequence == 3


def test_invalid_draft_does_not_consume_a_sequence_number() -> None:
    run = new_run()
    bad = EventDraft(EventType.TOOL_CALL, "test")  # tool event without tool name
    with pytest.raises(InvalidEvent):
        run.append(bad, CAPTURED, EventId("evt_00000001"), T0)
    assert run.snapshot().next_sequence == 0


@pytest.mark.parametrize("finish", ["complete", "fail", "mark_incomplete"])
def test_terminal_states_reject_further_events_and_transitions(finish: str) -> None:
    run = new_run()
    if finish == "complete":
        run.complete(T0)
    elif finish == "fail":
        run.fail(T0, "boom")
    else:
        run.mark_incomplete(T0, "crash")
    with pytest.raises(IllegalTransition):
        run.append(started(), CAPTURED, EventId("evt_00000001"), T0)
    with pytest.raises(IllegalTransition):
        run.complete(T0)
    with pytest.raises(IllegalTransition):
        run.fail(T0, "again")


def test_failed_run_keeps_reason_and_finish_time() -> None:
    run = new_run()
    run.fail(T0, "tool exploded")
    snap = run.snapshot()
    assert snap.status is RunStatus.FAILED
    assert snap.reason == "tool exploded"
    assert snap.finished_at == T0
