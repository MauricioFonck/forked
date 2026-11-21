"""Read-side use cases: inspect one run, list runs."""

from dataclasses import dataclass

from forked.application.ports import EventLog, RunRepository
from forked.domain.runs.completeness import RunAssessment, assess
from forked.domain.runs.event import Event
from forked.domain.runs.run import RunSnapshot
from forked.domain.shared.identifiers import RunId


@dataclass(frozen=True, slots=True)
class RunReport:
    snapshot: RunSnapshot
    events: tuple[Event, ...]
    assessment: RunAssessment


class InspectRun:
    def __init__(self, events: EventLog, runs: RunRepository) -> None:
        self._events = events
        self._runs = runs

    def execute(self, run_id: RunId) -> RunReport:
        snapshot = self._runs.get(run_id)
        events = tuple(self._events.read(run_id))
        return RunReport(snapshot=snapshot, events=events, assessment=assess(snapshot, events))


class ListRuns:
    def __init__(self, runs: RunRepository) -> None:
        self._runs = runs

    def execute(self) -> list[RunSnapshot]:
        return [self._runs.get(run_id) for run_id in self._runs.list_ids()]
