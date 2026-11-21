"""Test doubles for the outbound ports.

``InMemoryRunStore`` must honor the same contract as the real adapter: it runs the very
same suite in ``tests/contract``. A double that is looser than the adapter hides bugs.
"""

import copy
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

from forked.application.errors import RunNotFound, StorageFailure
from forked.domain.runs.capabilities import AdapterCapabilities
from forked.domain.runs.environment import EnvironmentFingerprint
from forked.domain.runs.event import Event
from forked.domain.runs.run import RunSnapshot
from forked.domain.shared.identifiers import EventId, RunId

T0 = datetime(2026, 11, 21, 12, 0, 0, tzinfo=UTC)


class InMemoryRunStore:
    def __init__(self) -> None:
        self._events: dict[RunId, list[Event]] = {}
        self._runs: dict[RunId, RunSnapshot] = {}

    def append(self, event: Event) -> None:
        self._events.setdefault(event.run_id, []).append(event)

    def read(self, run_id: RunId) -> Iterator[Event]:
        if run_id not in self._events:
            raise RunNotFound(f"no event log for run {run_id}")
        yield from list(self._events[run_id])

    def save(self, snapshot: RunSnapshot) -> None:
        self._runs[snapshot.run_id] = copy.copy(snapshot)

    def get(self, run_id: RunId) -> RunSnapshot:
        if run_id not in self._runs:
            raise RunNotFound(f"run {run_id} not found")
        return self._runs[run_id]

    def list_ids(self) -> list[RunId]:
        return sorted(self._runs, key=lambda run_id: run_id.value)


class FailingEventLog(InMemoryRunStore):
    """Fails on the n-th append (0-based) to simulate a full disk."""

    def __init__(self, fail_at: int) -> None:
        super().__init__()
        self._fail_at = fail_at
        self._count = 0

    def append(self, event: Event) -> None:
        if self._count == self._fail_at:
            self._count += 1
            raise StorageFailure("disk full (simulated)")
        self._count += 1
        super().append(event)


class SteppingClock:
    """Deterministic clock: each call advances one millisecond."""

    def __init__(self, start: datetime = T0) -> None:
        self._now = start

    def now(self) -> datetime:
        current = self._now
        self._now += timedelta(milliseconds=1)
        return current


class SequentialIds:
    def __init__(self) -> None:
        self._runs = 0
        self._events = 0

    def new_run_id(self) -> RunId:
        self._runs += 1
        return RunId(f"run_{self._runs:032x}")

    def new_event_id(self) -> EventId:
        self._events += 1
        return EventId(f"evt_{self._events:032x}")


class StaticProbe:
    def __init__(self, missing: tuple[str, ...] = ()) -> None:
        self._missing = missing

    def fingerprint(self, capabilities: AdapterCapabilities) -> EnvironmentFingerprint:
        facts: dict[str, str | None] = {
            "python_version": "3.11.0",
            "platform": "test-os",
            "forked_version": "0.0.0-test",
            "adapter": capabilities.name,
            "adapter_version": capabilities.version,
        }
        for name in self._missing:
            facts[name] = None
        return EnvironmentFingerprint.of(facts)
