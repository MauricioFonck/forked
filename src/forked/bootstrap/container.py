"""Composition root: the only place that picks concrete adapters.

Everything else receives its collaborators through constructors.
"""

from dataclasses import dataclass
from pathlib import Path

from forked.adapters.inbound.sdk.recorder import Recorder
from forked.adapters.outbound.evidence.directory import read_package, write_package
from forked.adapters.outbound.persistence.filesystem.store import FileSystemRunStore
from forked.adapters.outbound.system.runtime import PlatformProbe, RandomIdGenerator, SystemClock
from forked.application.capture import CaptureLimits, CapturePipeline
from forked.application.commands.evidence import (
    ExportEvidence,
    VerificationReport,
    verify_evidence,
)
from forked.application.commands.record_run import RecordingDependencies, RecordingService
from forked.application.commands.replay_run import ReplayService
from forked.application.ports import Clock, IdGenerator
from forked.application.queries.inspect_run import CompareRuns, InspectRun, ListRuns
from forked.domain.runs.redaction import RedactionPolicy
from forked.domain.shared.identifiers import RunId


@dataclass(frozen=True, slots=True)
class Application:
    store_root: Path
    recorder: Recorder
    inspect_run: InspectRun
    list_runs: ListRuns
    compare_runs: CompareRuns
    export: ExportEvidence

    def export_evidence(self, baseline: RunId, branch: RunId, out: Path) -> dict[str, bytes]:
        files = self.export.execute(baseline, branch)
        write_package(out, files)
        return files


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
    inspect = InspectRun(store, store)
    compare = CompareRuns(store, store)
    return Application(
        store_root=store_root,
        recorder=Recorder(recording, ReplayService(recording, store, store)),
        inspect_run=inspect,
        list_runs=ListRuns(store),
        compare_runs=compare,
        export=ExportEvidence(inspect, compare, store, redaction or RedactionPolicy()),
    )


def verify_package(package: Path) -> VerificationReport:
    """Verify an evidence package offline. Needs nothing but the package directory."""
    files = read_package(package)
    view = FileSystemRunStore(package)  # the package's runs/ has the store layout; read-only use
    inspect, compare = InspectRun(view, view), CompareRuns(view, view)
    regenerate = ExportEvidence(inspect, compare, view, RedactionPolicy())
    return verify_evidence(files, compare, regenerate.execute)
