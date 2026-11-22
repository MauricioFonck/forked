"""Helpers shared by the FCRB scenarios and the tests."""

from collections.abc import Sequence

from forked.domain.runs.event import Event, EventType

# run.started/run.completed payloads legitimately differ between adapters (adapter name,
# limitations, outcome shape); tool events are what must be equivalent.
_TOOL_EVENTS = {EventType.TOOL_CALL, EventType.TOOL_RESULT, EventType.TOOL_ERROR}


def normalized_tool_events(events: Sequence[Event]) -> list[tuple[object, ...]]:
    """Adapter-independent view of a run: no ids, timestamps, sources or adapter metadata."""
    return [
        (
            e.sequence,
            e.event_type.value,
            e.tool_name,
            e.effect_class.value if e.effect_class else None,
            e.capture_status.value,
            e.redacted_paths,
            repr(e.payload),
        )
        if e.event_type in _TOOL_EVENTS
        else (e.sequence, e.event_type.value)
        for e in events
    ]
