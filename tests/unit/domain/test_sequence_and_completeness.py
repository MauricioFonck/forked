from dataclasses import replace

from hypothesis import given
from hypothesis import strategies as st

from forked.domain.effects.effect_class import EffectClass
from forked.domain.runs.capabilities import AdapterCapabilities
from forked.domain.runs.completeness import assess
from forked.domain.runs.event import CaptureStatus, EventDraft, EventType
from forked.domain.runs.run import PreparedPayload, Run, RunStatus
from forked.domain.runs.sequence import check_sequence
from forked.domain.shared.identifiers import EventId, RunId
from tests.conftest import CAPS
from tests.fakes import T0, StaticProbe

RUN = RunId("run_00000001")
CAPTURED = PreparedPayload(payload=None, capture_status=CaptureStatus.CAPTURED)


def record(
    drafts: list[EventDraft], *, finish: str | None = "complete", caps: AdapterCapabilities = CAPS
) -> Run:
    run = Run.start(RUN, caps, StaticProbe().fingerprint(caps), T0)
    for index, draft in enumerate(drafts):
        run.append(draft, CAPTURED, EventId(f"evt_{index:08d}"), T0)
    if finish == "complete":
        run.complete(T0)
    return run


def happy_drafts() -> list[EventDraft]:
    return [
        EventDraft(EventType.RUN_STARTED, "t"),
        EventDraft(EventType.TOOL_CALL, "t", tool_name="echo", effect_class=EffectClass.PURE_LOCAL),
        EventDraft(
            EventType.TOOL_RESULT, "t", tool_name="echo", effect_class=EffectClass.PURE_LOCAL
        ),
        EventDraft(EventType.RUN_COMPLETED, "t"),
    ]


def events_of(drafts: list[EventDraft]) -> list:  # type: ignore[type-arg]
    run = Run.start(RUN, CAPS, StaticProbe().fingerprint(CAPS), T0)
    return [run.append(d, CAPTURED, EventId(f"evt_{i:08d}"), T0) for i, d in enumerate(drafts)]


def test_happy_run_has_no_missing_evidence() -> None:
    drafts = happy_drafts()
    run = record(drafts)
    result = assess(run.snapshot(), events_of(drafts))
    assert result.effective_status is RunStatus.COMPLETED
    assert result.sequence.is_valid
    assert result.completeness.ratio == 1.0
    assert result.missing_evidence == ()


def test_unfinished_run_is_reported_incomplete() -> None:
    drafts = happy_drafts()[:2]
    run = record(drafts, finish=None)
    result = assess(run.snapshot(), events_of(drafts))
    assert result.effective_status is RunStatus.INCOMPLETE
    assert any("never finalized" in m for m in result.missing_evidence)


def test_missing_capture_point_and_lost_events_are_reported() -> None:
    drafts = [happy_drafts()[0], happy_drafts()[3]]
    run = record(drafts)
    events = events_of(drafts)[:1]  # log lost the terminal event
    result = assess(run.snapshot(), events)
    joined = " | ".join(result.missing_evidence)
    assert "declared capture point never observed: tool:echo" in joined
    assert "last event is not run.completed" in joined
    assert "metadata expects 2 events but log has 1" in joined
    assert result.completeness.ratio == 0.0


def test_no_declared_points_means_unknown_not_complete() -> None:
    caps = AdapterCapabilities(name="bare", version="1")
    drafts = [happy_drafts()[0], happy_drafts()[3]]
    run = record(drafts, caps=caps)
    result = assess(run.snapshot(), events_of(drafts))
    assert result.completeness.ratio is None
    assert any("completeness is unknown" in m for m in result.missing_evidence)


def test_missing_environment_fact_is_reported() -> None:
    drafts = happy_drafts()
    run = Run.start(RUN, CAPS, StaticProbe(missing=("platform",)).fingerprint(CAPS), T0)
    for index, draft in enumerate(drafts):
        run.append(draft, CAPTURED, EventId(f"evt_{index:08d}"), T0)
    run.complete(T0)
    result = assess(run.snapshot(), events_of(drafts))
    assert "environment fact not captured: platform" in result.missing_evidence


def test_sequence_detects_gaps_duplicates_disorder_and_foreign_runs() -> None:
    events = events_of(happy_drafts())
    shuffled = [events[0], events[2], events[1], events[1], events[3]]
    foreign = replace(events[3], run_id=RunId("run_99999999"), sequence=5)
    report = check_sequence([*shuffled, foreign], RUN)
    assert report.out_of_order == (1,)
    assert report.duplicates == (1,)
    assert report.gaps == (4,)
    assert report.foreign_events == (foreign.event_id.value,)
    assert not report.is_valid


@given(st.integers(min_value=0, max_value=50))
def test_any_contiguous_stream_is_valid(n: int) -> None:
    drafts = [EventDraft(EventType.RUN_STARTED, "t")] * n
    assert check_sequence(events_of(drafts), RUN).is_valid


@given(st.lists(st.integers(min_value=0, max_value=30), min_size=1, max_size=30))
def test_any_non_identity_permutation_is_invalid(order: list[int]) -> None:
    base = events_of([EventDraft(EventType.RUN_STARTED, "t")] * 31)
    picked = [base[i] for i in order]
    is_identity = order == list(range(len(order)))
    assert check_sequence(picked, RUN).is_valid is is_identity
