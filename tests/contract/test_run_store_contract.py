"""Contract every ``EventLog`` + ``RunRepository`` implementation must pass.

Runs against the real filesystem adapter AND the in-memory test double, so the double
can never be looser than production.
"""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Protocol

import pytest

from forked.adapters.outbound.persistence.filesystem.store import FileSystemRunStore
from forked.application.errors import RunNotFound
from forked.domain.effects.effect_class import EffectClass
from forked.domain.runs.event import CaptureStatus, Event, EventDraft, EventType
from forked.domain.runs.run import PreparedPayload, Run, RunSnapshot
from forked.domain.shared.identifiers import EventId, RunId
from tests.conftest import CAPS
from tests.fakes import T0, InMemoryRunStore, StaticProbe


class Store(Protocol):
    def append(self, event: Event) -> None: ...
    def read(self, run_id: RunId) -> "object": ...
    def save(self, snapshot: RunSnapshot) -> None: ...
    def get(self, run_id: RunId) -> RunSnapshot: ...
    def list_ids(self) -> list[RunId]: ...


def _fs(tmp_path: Path) -> FileSystemRunStore:
    return FileSystemRunStore(tmp_path / "store")


def _mem(_: Path) -> InMemoryRunStore:
    return InMemoryRunStore()


@pytest.fixture(params=[_fs, _mem], ids=["filesystem", "in-memory"])
def store(request: pytest.FixtureRequest, tmp_path: Path) -> Store:
    factory: Callable[[Path], Store] = request.param
    return factory(tmp_path)


def make_run(index: int = 1) -> tuple[Run, list[Event]]:
    run = Run.start(RunId(f"run_{index:08d}"), CAPS, StaticProbe().fingerprint(CAPS), T0)
    drafts = [
        EventDraft(EventType.RUN_STARTED, "t", {"a": 1}),
        EventDraft(
            EventType.TOOL_CALL,
            "t",
            {"inputs": {"text": "héllo ✓"}},
            tool_name="echo",
            effect_class=EffectClass.PURE_LOCAL,
            trace_id="0af7651916cd43dd8448eb211c80319c",
            span_id="b7ad6b7169203331",
        ),
    ]
    events = [
        run.append(
            d,
            PreparedPayload(payload=d.payload, capture_status=CaptureStatus.CAPTURED),
            EventId(f"evt_{index:04d}{i:04d}"),
            T0,
        )
        for i, d in enumerate(drafts)
    ]
    return run, events


def test_events_round_trip_in_order(store: Store) -> None:
    run, events = make_run()
    for event in events:
        store.append(event)
    assert list(store.read(run.run_id)) == events  # type: ignore[call-overload]


def test_snapshot_round_trips_and_save_replaces(store: Store) -> None:
    run, _ = make_run()
    store.save(run.snapshot())
    assert store.get(run.run_id) == run.snapshot()
    run.complete(T0)
    store.save(run.snapshot())
    assert store.get(run.run_id) == run.snapshot()


def test_unknown_run_raises_run_not_found(store: Store) -> None:
    with pytest.raises(RunNotFound):
        store.get(RunId("run_00000404"))
    with pytest.raises(RunNotFound):
        list(store.read(RunId("run_00000404")))  # type: ignore[call-overload]


def test_runs_are_isolated_and_listed_sorted(store: Store) -> None:
    run_b, events_b = make_run(2)
    run_a, events_a = make_run(1)
    for run, events in ((run_b, events_b), (run_a, events_a)):
        store.save(run.snapshot())
        for event in events:
            store.append(event)
    assert store.list_ids() == [run_a.run_id, run_b.run_id]
    assert list(store.read(run_a.run_id)) == events_a  # type: ignore[call-overload]


def test_stored_snapshot_is_not_aliased(store: Store) -> None:
    run, _ = make_run()
    snapshot = run.snapshot()
    store.save(snapshot)
    store.save(replace(snapshot, next_sequence=9))
    assert store.get(run.run_id).next_sequence == 9
    assert snapshot.next_sequence == 2  # the original value object is untouched
