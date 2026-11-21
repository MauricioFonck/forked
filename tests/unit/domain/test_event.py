from dataclasses import replace
from datetime import datetime

import pytest

from forked.domain.effects.effect_class import EffectClass
from forked.domain.runs.event import CaptureStatus, Event, EventType
from forked.domain.shared.errors import InvalidEvent
from forked.domain.shared.identifiers import EventId, RunId
from tests.fakes import T0

BASE = Event(
    schema_version="0.1.0",
    event_id=EventId("evt_00000001"),
    run_id=RunId("run_00000001"),
    sequence=0,
    event_type=EventType.TOOL_CALL,
    timestamp=T0,
    source="test",
    capture_status=CaptureStatus.CAPTURED,
    payload={"inputs": {}},
    tool_name="echo",
    effect_class=EffectClass.PURE_LOCAL,
)


def test_valid_event_exposes_capture_point() -> None:
    assert BASE.capture_point == "tool:echo"
    assert replace(BASE, event_type=EventType.RUN_STARTED).capture_point is None


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"sequence": -1}, "sequence"),
        ({"timestamp": datetime(2026, 1, 1)}, "timezone-aware"),
        ({"source": "  "}, "source"),
        ({"tool_name": None}, "tool_name"),
        ({"effect_class": None}, "effect_class"),
        ({"capture_status": CaptureStatus.OMITTED}, "digest"),
        ({"capture_status": CaptureStatus.REDACTED}, "redacted paths"),
        ({"redacted_paths": ("$.x",)}, "captured payload"),
    ],
)
def test_event_invariants(changes: dict[str, object], message: str) -> None:
    with pytest.raises(InvalidEvent, match=message):
        replace(BASE, **changes)  # type: ignore[arg-type]


def test_omitted_event_keeps_only_digest() -> None:
    event = replace(
        BASE, capture_status=CaptureStatus.OMITTED, payload=None, payload_digest="sha256:ab"
    )
    assert event.payload is None


def test_events_are_immutable() -> None:
    with pytest.raises(AttributeError):
        BASE.sequence = 5  # type: ignore[misc]
