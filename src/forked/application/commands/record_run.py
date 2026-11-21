"""Use case UC-01: capture an execution.

A ``RecordingSession`` owns one ``Run`` aggregate while the workflow executes:

1. ``start`` persists metadata in ``RECORDING`` state and writes ``run.started``.
2. ``capture`` runs the capture pipeline, assigns the next sequence and appends.
3. ``complete`` / ``fail`` write the terminal event and persist the final status.

If the process dies mid-run, metadata stays in ``RECORDING`` and every later inspection
reports the run as incomplete — a partial run is never mistaken for a complete one.
"""

import contextlib
from dataclasses import dataclass

from forked.application.capture import CaptureLimits, CapturePipeline
from forked.application.errors import CaptureFailed
from forked.application.ports import Clock, EnvironmentProbe, EventLog, IdGenerator, RunRepository
from forked.domain.runs.capabilities import AdapterCapabilities
from forked.domain.runs.event import Event, EventDraft, EventType
from forked.domain.runs.run import Run, RunSnapshot, RunStatus
from forked.domain.shared.canonical import JsonValue
from forked.domain.shared.errors import ForkedError
from forked.domain.shared.identifiers import RunId

RECORDER_SOURCE = "forked.recorder"


@dataclass(frozen=True, slots=True)
class RecordingDependencies:
    events: EventLog
    runs: RunRepository
    clock: Clock
    ids: IdGenerator
    probe: EnvironmentProbe
    pipeline: CapturePipeline
    limits: CaptureLimits


class RecordingSession:
    def __init__(self, run: Run, deps: RecordingDependencies) -> None:
        self._run = run
        self._deps = deps

    @property
    def run_id(self) -> RunId:
        return self._run.run_id

    @property
    def status(self) -> RunStatus:
        return self._run.status

    def capture(self, draft: EventDraft) -> Event:
        """Redact, sequence and persist one event. Raises on any failure; never drops."""
        snapshot = self._run.snapshot()
        if (
            self._run.status is RunStatus.RECORDING
            and snapshot.next_sequence >= self._deps.limits.max_events_per_run
        ):
            self._abort(f"event limit of {self._deps.limits.max_events_per_run} reached")
            raise CaptureFailed(
                f"run {self.run_id} exceeded {self._deps.limits.max_events_per_run} events"
            )
        prepared = self._deps.pipeline.prepare(draft.payload)
        event = self._run.append(
            draft, prepared, self._deps.ids.new_event_id(), self._deps.clock.now()
        )
        try:
            self._deps.events.append(event)
        except ForkedError as exc:
            self._abort(f"event {event.sequence} could not be persisted: {exc}")
            raise CaptureFailed(f"could not persist event {event.sequence}: {exc}") from exc
        return event

    def complete(self, outcome: JsonValue = None) -> RunSnapshot:
        self.capture(EventDraft(EventType.RUN_COMPLETED, RECORDER_SOURCE, outcome))
        self._run.complete(self._deps.clock.now())
        self._deps.runs.save(self._run.snapshot())
        return self._run.snapshot()

    def fail(self, reason: str) -> RunSnapshot:
        """Finalize as failed. ``reason`` is redacted before it reaches any artifact."""
        safe_reason = self._safe_text(reason)
        self.capture(EventDraft(EventType.RUN_FAILED, RECORDER_SOURCE, {"reason": safe_reason}))
        self._run.fail(self._deps.clock.now(), safe_reason)
        self._deps.runs.save(self._run.snapshot())
        return self._run.snapshot()

    def _safe_text(self, text: str) -> str:
        """Run free text through the capture pipeline (exception messages leak secrets)."""
        prepared = self._deps.pipeline.prepare({"text": text})
        if isinstance(prepared.payload, dict):
            safe = prepared.payload.get("text")
            if isinstance(safe, str):
                return safe
        return "[omitted: text exceeded the payload size limit]"

    def _abort(self, reason: str) -> None:
        """Best effort: mark the run incomplete so the failure stays visible."""
        if self._run.status is RunStatus.RECORDING:
            self._run.mark_incomplete(self._deps.clock.now(), self._safe_text(reason))
            # If this save fails, metadata stays RECORDING on disk, which inspection
            # already reports as incomplete. The original error is raised by the caller.
            with contextlib.suppress(ForkedError):
                self._deps.runs.save(self._run.snapshot())


class RecordingService:
    def __init__(self, deps: RecordingDependencies) -> None:
        self._deps = deps

    def start(
        self, capabilities: AdapterCapabilities, *, lineage: dict[str, JsonValue] | None = None
    ) -> RecordingSession:
        """Start a run. ``lineage`` (replay/branch metadata) is merged into ``run.started``."""
        run = Run.start(
            run_id=self._deps.ids.new_run_id(),
            capabilities=capabilities,
            environment=self._deps.probe.fingerprint(capabilities),
            started_at=self._deps.clock.now(),
        )
        self._deps.runs.save(run.snapshot())
        session = RecordingSession(run, self._deps)
        started: dict[str, JsonValue] = {
            "adapter": capabilities.name,
            "adapter_version": capabilities.version,
            "limitations": list(capabilities.limitations),
        }
        started.update(lineage or {})
        session.capture(EventDraft(EventType.RUN_STARTED, RECORDER_SOURCE, started))
        return session
