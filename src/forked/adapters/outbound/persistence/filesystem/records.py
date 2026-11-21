"""Wire format (schema v0.1) for events and run metadata, and its mapping to the domain.

Pydantic lives here, at the boundary, and never inside ``forked.domain``. Unknown fields
are ignored on read so that a newer *minor* schema version stays readable; an unknown
*major* version is rejected before validation.
"""

from typing import Any

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, JsonValue, ValidationError

from forked.application.errors import CorruptRecording
from forked.domain.effects.effect_class import EffectClass
from forked.domain.runs.capabilities import AdapterCapabilities
from forked.domain.runs.environment import EnvironmentFingerprint
from forked.domain.runs.event import CaptureStatus, Event, EventType
from forked.domain.runs.run import RunSnapshot, RunStatus
from forked.domain.shared.errors import DomainError
from forked.domain.shared.identifiers import EventId, RunId
from forked.domain.shared.schema import EVENT_SCHEMA_VERSION, ensure_supported


class _Record(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True, strict=True)


class EventRecord(_Record):
    """One line of ``events.jsonl``."""

    model_config = ConfigDict(
        extra="ignore",
        frozen=True,
        strict=True,
        title="FORKED event envelope",
        json_schema_extra={"$id": "https://forked.dev/schema/cip/0.1/event.schema.json"},
    )

    schema_version: str
    event_id: str
    run_id: str
    sequence: int = Field(ge=0)
    event_type: EventType
    timestamp: AwareDatetime
    source: str
    capture_status: CaptureStatus
    payload: JsonValue = None
    payload_digest: str | None = None
    redacted_paths: list[str] = Field(default_factory=list)
    tool_name: str | None = None
    effect_class: EffectClass | None = None
    parent_event_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None


class AdapterRecord(_Record):
    name: str
    version: str
    capture_points: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class RunRecord(_Record):
    """Content of ``run.json``."""

    schema_version: str
    run_id: str
    status: RunStatus
    started_at: AwareDatetime
    finished_at: AwareDatetime | None = None
    reason: str | None = None
    next_sequence: int = Field(ge=0)
    adapter: AdapterRecord
    environment: dict[str, str | None]


def _check_version(raw: Any) -> None:
    if not isinstance(raw, dict) or not isinstance(raw.get("schema_version"), str):
        raise CorruptRecording("record has no string schema_version")
    ensure_supported(raw["schema_version"])


def event_to_json(event: Event) -> str:
    record = EventRecord(
        schema_version=event.schema_version,
        event_id=event.event_id.value,
        run_id=event.run_id.value,
        sequence=event.sequence,
        event_type=event.event_type,
        timestamp=event.timestamp,
        source=event.source,
        capture_status=event.capture_status,
        payload=event.payload,
        payload_digest=event.payload_digest,
        redacted_paths=list(event.redacted_paths),
        tool_name=event.tool_name,
        effect_class=event.effect_class,
        parent_event_id=event.parent_event_id.value if event.parent_event_id else None,
        trace_id=event.trace_id,
        span_id=event.span_id,
    )
    return record.model_dump_json(exclude_none=True)


def event_from_raw(raw: Any) -> Event:
    """Validate a decoded JSON object and build a domain ``Event``."""
    _check_version(raw)
    try:
        record = EventRecord.model_validate(raw, strict=False)
        return Event(
            schema_version=record.schema_version,
            event_id=EventId(record.event_id),
            run_id=RunId(record.run_id),
            sequence=record.sequence,
            event_type=record.event_type,
            timestamp=record.timestamp,
            source=record.source,
            capture_status=record.capture_status,
            payload=record.payload,
            payload_digest=record.payload_digest,
            redacted_paths=tuple(record.redacted_paths),
            tool_name=record.tool_name,
            effect_class=record.effect_class,
            parent_event_id=EventId(record.parent_event_id) if record.parent_event_id else None,
            trace_id=record.trace_id,
            span_id=record.span_id,
        )
    except (ValidationError, DomainError) as exc:
        raise CorruptRecording(f"invalid event record: {exc}") from exc


def snapshot_to_json(snapshot: RunSnapshot) -> str:
    caps = snapshot.capabilities
    record = RunRecord(
        schema_version=EVENT_SCHEMA_VERSION,
        run_id=snapshot.run_id.value,
        status=snapshot.status,
        started_at=snapshot.started_at,
        finished_at=snapshot.finished_at,
        reason=snapshot.reason,
        next_sequence=snapshot.next_sequence,
        adapter=AdapterRecord(
            name=caps.name,
            version=caps.version,
            capture_points=sorted(caps.capture_points),
            limitations=list(caps.limitations),
        ),
        environment=snapshot.environment.as_dict(),
    )
    return record.model_dump_json(indent=2)


def snapshot_from_raw(raw: Any) -> RunSnapshot:
    _check_version(raw)
    try:
        record = RunRecord.model_validate(raw, strict=False)
        return RunSnapshot(
            run_id=RunId(record.run_id),
            capabilities=AdapterCapabilities(
                name=record.adapter.name,
                version=record.adapter.version,
                capture_points=frozenset(record.adapter.capture_points),
                limitations=tuple(record.adapter.limitations),
            ),
            environment=EnvironmentFingerprint.of(record.environment),
            status=record.status,
            started_at=record.started_at,
            next_sequence=record.next_sequence,
            finished_at=record.finished_at,
            reason=record.reason,
        )
    except (ValidationError, DomainError) as exc:
        raise CorruptRecording(f"invalid run record: {exc}") from exc
