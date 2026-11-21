"""The ``Run`` aggregate: one recorded execution and its lifecycle.

State machine::

    RECORDING ──complete()──▶ COMPLETED
        │ ├────fail()──────▶ FAILED
        │ └─mark_incomplete()▶ INCOMPLETE
        (terminal states accept no transition)

``COMPLETED`` means the workflow finished and the recorder finalized the run. It does
**not** mean the capture was complete: completeness is reported separately against the
adapter's declared capture points.
"""

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from forked.domain.runs.capabilities import AdapterCapabilities
from forked.domain.runs.environment import EnvironmentFingerprint
from forked.domain.runs.event import CaptureStatus, Event, EventDraft
from forked.domain.shared.canonical import JsonValue
from forked.domain.shared.errors import IllegalTransition
from forked.domain.shared.identifiers import EventId, RunId
from forked.domain.shared.schema import EVENT_SCHEMA_VERSION


class RunStatus(StrEnum):
    RECORDING = "recording"
    COMPLETED = "completed"
    FAILED = "failed"
    INCOMPLETE = "incomplete"


_TRANSITIONS: dict[RunStatus, frozenset[RunStatus]] = {
    RunStatus.RECORDING: frozenset({RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.INCOMPLETE}),
    RunStatus.COMPLETED: frozenset(),
    RunStatus.FAILED: frozenset(),
    RunStatus.INCOMPLETE: frozenset(),
}


@dataclass(frozen=True, slots=True)
class PreparedPayload:
    """A payload after the capture pipeline (redaction / omission) ran."""

    payload: JsonValue
    capture_status: CaptureStatus
    redacted_paths: tuple[str, ...] = ()
    payload_digest: str | None = None


@dataclass(frozen=True, slots=True)
class RunSnapshot:
    """Persistable state of a run. Restoring it yields an equivalent aggregate."""

    run_id: RunId
    capabilities: AdapterCapabilities
    environment: EnvironmentFingerprint
    status: RunStatus
    started_at: datetime
    next_sequence: int
    finished_at: datetime | None = None
    reason: str | None = None


class Run:
    """Aggregate root. Only its methods change run state."""

    def __init__(self, snapshot: RunSnapshot) -> None:
        self._state = snapshot

    @classmethod
    def start(
        cls,
        run_id: RunId,
        capabilities: AdapterCapabilities,
        environment: EnvironmentFingerprint,
        started_at: datetime,
    ) -> "Run":
        return cls(
            RunSnapshot(
                run_id=run_id,
                capabilities=capabilities,
                environment=environment,
                status=RunStatus.RECORDING,
                started_at=started_at,
                next_sequence=0,
            )
        )

    @property
    def run_id(self) -> RunId:
        return self._state.run_id

    @property
    def status(self) -> RunStatus:
        return self._state.status

    def snapshot(self) -> RunSnapshot:
        return self._state

    def append(
        self, draft: EventDraft, prepared: PreparedPayload, event_id: EventId, at: datetime
    ) -> Event:
        """Create the next event in order. Only allowed while recording."""
        self._require(RunStatus.RECORDING, "append an event")
        event = Event(
            schema_version=EVENT_SCHEMA_VERSION,
            event_id=event_id,
            run_id=self._state.run_id,
            sequence=self._state.next_sequence,
            event_type=draft.event_type,
            timestamp=at,
            source=draft.source,
            capture_status=prepared.capture_status,
            payload=prepared.payload,
            payload_digest=prepared.payload_digest,
            redacted_paths=prepared.redacted_paths,
            tool_name=draft.tool_name,
            effect_class=draft.effect_class,
            parent_event_id=draft.parent_event_id,
            trace_id=draft.trace_id,
            span_id=draft.span_id,
        )
        self._state = replace(self._state, next_sequence=self._state.next_sequence + 1)
        return event

    def complete(self, at: datetime) -> None:
        self._transition(RunStatus.COMPLETED, at, None)

    def fail(self, at: datetime, reason: str) -> None:
        self._transition(RunStatus.FAILED, at, reason)

    def mark_incomplete(self, at: datetime, reason: str) -> None:
        self._transition(RunStatus.INCOMPLETE, at, reason)

    def _require(self, status: RunStatus, action: str) -> None:
        if self._state.status is not status:
            raise IllegalTransition(
                f"cannot {action}: run {self._state.run_id} is {self._state.status}"
            )

    def _transition(self, target: RunStatus, at: datetime, reason: str | None) -> None:
        if target not in _TRANSITIONS[self._state.status]:
            raise IllegalTransition(
                f"run {self._state.run_id} cannot go from {self._state.status} to {target}"
            )
        self._state = replace(self._state, status=target, finished_at=at, reason=reason)
