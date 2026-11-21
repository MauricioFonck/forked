"""Use cases UC-02 (replay) and UC-03 (branch) over a recorded run.

Both start a **new** run whose ``run.started`` payload carries its lineage; the parent's
artifacts are only read, never written. Tools are never executed by a replay; a branch
executes only what the effect policy allows after its checkpoint.
"""

from forked.application.commands.record_run import RecordingService, RecordingSession
from forked.application.ports import EventLog, RunRepository
from forked.domain.branches.branch import BranchResolver, Intervention, log_digest
from forked.domain.effects.policy import DefaultDenyPolicy
from forked.domain.replay.cursor import ReplayCursor, ReplayDivergence
from forked.domain.runs.capabilities import AdapterCapabilities
from forked.domain.runs.event import Event
from forked.domain.shared.canonical import JsonValue
from forked.domain.shared.identifiers import RunId


class ReplayService:
    def __init__(self, recording: RecordingService, events: EventLog, runs: RunRepository) -> None:
        self._recording = recording
        self._events = events
        self._runs = runs

    def _load(self, source: RunId, capabilities: AdapterCapabilities) -> list[Event]:
        recorded = self._runs.get(source)
        if recorded.capabilities.name != capabilities.name:
            raise ReplayDivergence(
                f"{source} was recorded by adapter {recorded.capabilities.name!r}, "
                f"not {capabilities.name!r}"
            )
        return list(self._events.read(source))

    def start(
        self, source: RunId, capabilities: AdapterCapabilities
    ) -> tuple[RecordingSession, ReplayCursor]:
        cursor = ReplayCursor(source, self._load(source, capabilities))
        return self._recording.start(capabilities, lineage={"replay_of": source.value}), cursor

    def branch(
        self, parent: RunId, capabilities: AdapterCapabilities, intervention: Intervention
    ) -> tuple[RecordingSession, BranchResolver]:
        events = self._load(parent, capabilities)
        policy = DefaultDenyPolicy()
        resolver = BranchResolver(parent, events, intervention, policy)  # validates first
        lineage: dict[str, JsonValue] = {
            "branch_of": parent.value,
            "parent_log_digest": log_digest(events),
            "intervention": intervention.as_dict(),
            "effect_policy": policy.version,
        }
        return self._recording.start(capabilities, lineage=lineage), resolver
