"""Capture completeness and missing-evidence assessment of a recorded run.

This module turns a run snapshot plus its events into an honest statement of what is
known and what is not. It never upgrades uncertainty into a claim.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from forked.domain.runs.event import CaptureStatus, Event, EventType
from forked.domain.runs.run import RunSnapshot, RunStatus
from forked.domain.runs.sequence import SequenceReport, check_sequence

_TERMINAL_EVENTS = {
    RunStatus.COMPLETED: EventType.RUN_COMPLETED,
    RunStatus.FAILED: EventType.RUN_FAILED,
}


@dataclass(frozen=True, slots=True)
class CaptureCompleteness:
    declared: frozenset[str]
    observed: frozenset[str]

    @property
    def missing(self) -> frozenset[str]:
        """Declared capture points with no event."""
        return self.declared - self.observed

    @property
    def undeclared(self) -> frozenset[str]:
        """Observed capture points the adapter never declared."""
        return self.observed - self.declared

    @property
    def ratio(self) -> float | None:
        """Observed/declared, or ``None`` when nothing was declared (unknown, not 100%)."""
        if not self.declared:
            return None
        return len(self.declared & self.observed) / len(self.declared)


@dataclass(frozen=True, slots=True)
class RunAssessment:
    effective_status: RunStatus
    sequence: SequenceReport
    completeness: CaptureCompleteness
    redacted_events: int
    omitted_events: int
    missing_evidence: tuple[str, ...]


def assess(snapshot: RunSnapshot, events: Sequence[Event]) -> RunAssessment:
    """Assess a run. A run left in ``RECORDING`` is reported as ``INCOMPLETE``."""
    sequence = check_sequence(events, snapshot.run_id)
    observed = frozenset(p for p in (e.capture_point for e in events) if p is not None)
    completeness = CaptureCompleteness(snapshot.capabilities.capture_points, observed)
    missing: list[str] = []

    effective = snapshot.status
    if effective is RunStatus.RECORDING:
        effective = RunStatus.INCOMPLETE
        missing.append("run was never finalized (recording interrupted or still running)")
    elif effective is RunStatus.INCOMPLETE and snapshot.reason:
        missing.append(f"run marked incomplete: {snapshot.reason}")

    if not events or events[0].event_type is not EventType.RUN_STARTED:
        missing.append("first event is not run.started")
    terminal = _TERMINAL_EVENTS.get(snapshot.status)
    if terminal is not None and (not events or events[-1].event_type is not terminal):
        missing.append(f"last event is not {terminal} although run is {snapshot.status}")
    if len(events) != snapshot.next_sequence:
        missing.append(
            f"metadata expects {snapshot.next_sequence} events but log has {len(events)}"
        )
    if sequence.gaps:
        missing.append(f"sequence gaps: {list(sequence.gaps)}")
    if sequence.duplicates:
        missing.append(f"duplicate sequence numbers: {list(sequence.duplicates)}")
    if sequence.out_of_order:
        missing.append(f"out-of-order sequence numbers: {list(sequence.out_of_order)}")
    if sequence.foreign_events:
        missing.append(f"events from another run: {list(sequence.foreign_events)}")
    for point in sorted(completeness.missing):
        missing.append(f"declared capture point never observed: {point}")
    for point in sorted(completeness.undeclared):
        missing.append(f"observed capture point was not declared: {point}")
    if not snapshot.capabilities.capture_points:
        missing.append("adapter declared no capture points; completeness is unknown")
    for fact in snapshot.environment.missing():
        missing.append(f"environment fact not captured: {fact}")

    omitted = sum(1 for e in events if e.capture_status is CaptureStatus.OMITTED)
    if omitted:
        missing.append(f"{omitted} event payload(s) omitted; only digests were kept")

    return RunAssessment(
        effective_status=effective,
        sequence=sequence,
        completeness=completeness,
        redacted_events=sum(1 for e in events if e.capture_status is CaptureStatus.REDACTED),
        omitted_events=omitted,
        missing_evidence=tuple(missing),
    )
