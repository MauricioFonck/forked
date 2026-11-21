"""The event envelope (docs/06-cip-protocol-draft.md §6.4)."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from forked.domain.effects.effect_class import EffectClass
from forked.domain.runs.capabilities import tool_capture_point
from forked.domain.shared.canonical import JsonValue
from forked.domain.shared.errors import InvalidEvent
from forked.domain.shared.identifiers import EventId, RunId


class EventType(StrEnum):
    RUN_STARTED = "run.started"
    TOOL_CALL = "tool.call"
    TOOL_RESULT = "tool.result"
    TOOL_ERROR = "tool.error"
    RUN_COMPLETED = "run.completed"
    RUN_FAILED = "run.failed"


TOOL_EVENT_TYPES = frozenset({EventType.TOOL_CALL, EventType.TOOL_RESULT, EventType.TOOL_ERROR})


class CaptureStatus(StrEnum):
    """How faithfully the payload of one event was persisted."""

    CAPTURED = "captured"
    """Payload persisted as observed."""

    REDACTED = "redacted"
    """Payload persisted with sensitive values replaced; ``redacted_paths`` lists them."""

    OMITTED = "omitted"
    """Payload not persisted (e.g. over the size limit); only its digest is kept."""


@dataclass(frozen=True, slots=True)
class EventDraft:
    """What an adapter submits. Sequence, ids, time and redaction are added by FORKED."""

    event_type: EventType
    source: str
    payload: JsonValue = None
    tool_name: str | None = None
    effect_class: EffectClass | None = None
    parent_event_id: EventId | None = None
    trace_id: str | None = None
    span_id: str | None = None


@dataclass(frozen=True, slots=True)
class Event:
    """An immutable, ordered, typed observation about one run."""

    schema_version: str
    event_id: EventId
    run_id: RunId
    sequence: int
    event_type: EventType
    timestamp: datetime
    source: str
    capture_status: CaptureStatus
    payload: JsonValue = None
    payload_digest: str | None = None
    redacted_paths: tuple[str, ...] = ()
    tool_name: str | None = None
    effect_class: EffectClass | None = None
    parent_event_id: EventId | None = None
    trace_id: str | None = None
    span_id: str | None = None

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise InvalidEvent(f"sequence must be >= 0, got {self.sequence}")
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise InvalidEvent("timestamp must be timezone-aware")
        if not self.source.strip():
            raise InvalidEvent("source must not be empty")
        if self.event_type in TOOL_EVENT_TYPES:
            if not self.tool_name:
                raise InvalidEvent(f"{self.event_type} requires tool_name")
            if self.effect_class is None:
                raise InvalidEvent(f"{self.event_type} requires effect_class")
        if self.capture_status is CaptureStatus.OMITTED and (
            self.payload is not None or not self.payload_digest
        ):
            raise InvalidEvent("an omitted payload keeps only its digest")
        if self.capture_status is CaptureStatus.REDACTED and not self.redacted_paths:
            raise InvalidEvent("a redacted payload must list its redacted paths")
        if self.capture_status is CaptureStatus.CAPTURED and self.redacted_paths:
            raise InvalidEvent("a captured payload cannot list redacted paths")

    @property
    def capture_point(self) -> str | None:
        """Capture point this event evidences, if any."""
        if self.event_type in TOOL_EVENT_TYPES and self.tool_name:
            return tool_capture_point(self.tool_name)
        return None
