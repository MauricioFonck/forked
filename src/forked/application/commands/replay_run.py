"""Use case UC-02: replay a recorded run from its observations.

A replay is itself a new recorded run (``run.started`` carries ``replay_of``), so it can
be inspected like any other. Tools are never executed: every call resolves through a
``ReplayCursor`` over the source run, and anything unresolvable fails closed.
"""

from forked.application.commands.record_run import RecordingService, RecordingSession
from forked.application.ports import EventLog, RunRepository
from forked.domain.replay.cursor import ReplayCursor, ReplayDivergence
from forked.domain.runs.capabilities import AdapterCapabilities
from forked.domain.shared.identifiers import RunId


class ReplayService:
    def __init__(self, recording: RecordingService, events: EventLog, runs: RunRepository) -> None:
        self._recording = recording
        self._events = events
        self._runs = runs

    def start(
        self, source: RunId, capabilities: AdapterCapabilities
    ) -> tuple[RecordingSession, ReplayCursor]:
        recorded = self._runs.get(source)
        if recorded.capabilities.name != capabilities.name:
            raise ReplayDivergence(
                f"{source} was recorded by adapter {recorded.capabilities.name!r}, "
                f"not {capabilities.name!r}"
            )
        cursor = ReplayCursor(source, list(self._events.read(source)))
        return self._recording.start(capabilities, replay_of=source), cursor
