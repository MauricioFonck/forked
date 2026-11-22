"""Use cases for the OpenTelemetry bridge: export a run's tool spans, import a trace as a run."""

from collections.abc import Sequence

from forked.application.commands.record_run import RecordingService
from forked.application.queries.inspect_run import InspectRun
from forked.domain.effects.effect_class import EffectClass
from forked.domain.runs.capabilities import AdapterCapabilities
from forked.domain.runs.event import EventDraft, EventType
from forked.domain.shared.canonical import JsonValue
from forked.domain.shared.errors import ForkedError
from forked.domain.shared.identifiers import RunId
from forked.domain.telemetry.otlp import (
    IMPORT_LIMITATIONS,
    InvalidTrace,
    ObservedToolCall,
    to_otlp,
)

IMPORT_SOURCE = "forked.otel-import"
IMPORT_ADAPTER = "forked-otel-import"


class ExportTrace:
    def __init__(self, inspect: InspectRun) -> None:
        self._inspect = inspect

    def execute(self, run_id: RunId, *, include_payloads: bool = False) -> dict[str, JsonValue]:
        report = self._inspect.execute(run_id)
        if not report.events:
            raise InvalidTrace(f"run {run_id} has no events to export")
        return to_otlp(
            run_id,
            report.snapshot.capabilities.name,
            report.events,
            include_payloads=include_payloads,
        )


class ImportTrace:
    def __init__(self, recording: RecordingService) -> None:
        self._recording = recording

    def execute(self, calls: Sequence[ObservedToolCall]) -> RunId:
        capabilities = AdapterCapabilities(
            name=IMPORT_ADAPTER,
            version="0.1.0",
            capture_points=frozenset(),  # a trace declares none: completeness stays unknown
            limitations=IMPORT_LIMITATIONS,
        )
        session = self._recording.start(capabilities)
        try:
            for item in calls:
                provenance: dict[str, JsonValue] = {
                    "start_unix_nano": item.start_unix_nano,
                    "end_unix_nano": item.end_unix_nano,
                    "inputs_present": item.has_arguments,
                    "result_present": item.has_result,
                }
                call = session.capture(
                    EventDraft(
                        EventType.TOOL_CALL,
                        IMPORT_SOURCE,
                        {
                            "inputs": item.arguments
                        },  # same shape as the SDK, so imported runs can replay
                        tool_name=item.name,
                        effect_class=EffectClass.UNKNOWN,
                        trace_id=item.trace_id,
                        span_id=item.span_id,
                    )
                )
                kind = EventType.TOOL_ERROR if item.failed else EventType.TOOL_RESULT
                body: JsonValue = (
                    {
                        "error_type": item.error_type or "Error",
                        "message": item.message or "",
                        "otel": provenance,
                    }
                    if item.failed
                    else {"output": item.result, "otel": provenance}
                )
                session.capture(
                    EventDraft(
                        kind,
                        IMPORT_SOURCE,
                        body,
                        tool_name=item.name,
                        effect_class=EffectClass.UNKNOWN,
                        parent_event_id=call.event_id,
                        trace_id=item.trace_id,
                        span_id=item.span_id,
                    )
                )
        except BaseException as exc:
            try:
                session.fail(f"{type(exc).__name__}: {exc}")
            except ForkedError as fail_exc:
                exc.add_note(f"FORKED could not finalize run {session.run_id}: {fail_exc}")
            raise
        session.complete({"imported_tool_calls": len(calls)})
        return session.run_id
