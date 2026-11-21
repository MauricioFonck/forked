"""Composition root: the only place that picks concrete adapters.

Everything else receives its collaborators through constructors.
"""

from dataclasses import dataclass
from pathlib import Path

from forked.adapters.inbound.sdk.recorder import Recorder
from forked.adapters.outbound.persistence.filesystem.store import FileSystemRunStore
from forked.adapters.outbound.system.runtime import PlatformProbe, RandomIdGenerator, SystemClock
from forked.application.capture import CaptureLimits, CapturePipeline
from forked.application.commands.record_run import RecordingDependencies, RecordingService
from forked.application.commands.replay_run import ReplayService
from forked.application.ports import Clock, IdGenerator
from forked.application.queries.inspect_run import InspectRun, ListRuns
from forked.domain.runs.redaction import RedactionPolicy


@dataclass(frozen=True, slots=True)
class Application:
    store_root: Path
    recorder: Recorder
    inspect_run: InspectRun
    list_runs: ListRuns


def build_application(
    store_root: Path,
    *,
    clock: Clock | None = None,
    ids: IdGenerator | None = None,
    redaction: RedactionPolicy | None = None,
    limits: CaptureLimits | None = None,
) -> Application:
    store = FileSystemRunStore(store_root)
    effective_limits = limits or CaptureLimits()
    deps = RecordingDependencies(
        events=store,
        runs=store,
        clock=clock or SystemClock(),
        ids=ids or RandomIdGenerator(),
        probe=PlatformProbe(),
        pipeline=CapturePipeline(redaction or RedactionPolicy(), effective_limits),
        limits=effective_limits,
    )
    recording = RecordingService(deps)
    return Application(
        store_root=store_root,
        recorder=Recorder(recording, ReplayService(recording, store, store)),
        inspect_run=InspectRun(store, store),
        list_runs=ListRuns(store),
    )
