"""Outbound ports: the capabilities use cases need from the outside world.

Each port is a small ``Protocol``. An implementation (and every test double) must pass
the contract suite in ``tests/contract``.
"""

from collections.abc import Iterator
from datetime import datetime
from typing import Protocol

from forked.domain.runs.capabilities import AdapterCapabilities
from forked.domain.runs.environment import EnvironmentFingerprint
from forked.domain.runs.event import Event
from forked.domain.runs.run import RunSnapshot
from forked.domain.shared.identifiers import EventId, RunId


class EventLog(Protocol):
    """Append-only, ordered event storage for one run at a time."""

    def append(self, event: Event) -> None:
        """Persist ``event`` after every previously appended event of its run."""
        ...

    def read(self, run_id: RunId) -> Iterator[Event]:
        """Yield events in persisted order.

        Raises ``RunNotFound`` if the run has no log and ``CorruptRecording`` on a
        malformed or unsupported record.
        """
        ...


class RunRepository(Protocol):
    """Run metadata storage. ``save`` replaces the previous snapshot atomically."""

    def save(self, snapshot: RunSnapshot) -> None: ...

    def get(self, run_id: RunId) -> RunSnapshot:
        """Raises ``RunNotFound`` or ``CorruptRecording``."""
        ...

    def list_ids(self) -> list[RunId]:
        """All known run ids, sorted."""
        ...


class Clock(Protocol):
    def now(self) -> datetime:
        """Current time, timezone-aware."""
        ...


class IdGenerator(Protocol):
    def new_run_id(self) -> RunId: ...

    def new_event_id(self) -> EventId: ...


class EnvironmentProbe(Protocol):
    def fingerprint(self, capabilities: AdapterCapabilities) -> EnvironmentFingerprint: ...


class ArtifactReader(Protocol):
    """Raw bytes of a run's stored artifacts, keyed by file name (for evidence export)."""

    def raw_files(self, run_id: RunId) -> dict[str, bytes]: ...
