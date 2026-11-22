"""Helpers shared by the FCRB scenarios and the tests."""

import contextlib
import json
from collections.abc import Sequence

from forked.domain.runs.event import Event, EventType
from forked.domain.shared.canonical import JsonValue

# run.started/run.completed payloads legitimately differ between adapters (adapter name,
# limitations, outcome shape); tool events are what must be equivalent.
_TOOL_EVENTS = {EventType.TOOL_CALL, EventType.TOOL_RESULT, EventType.TOOL_ERROR}


def _comparable(payload: JsonValue, *, parse_json_outputs: bool) -> str:
    """``repr`` of the payload; optionally decode a tool ``output`` a framework stringified.

    LangGraph hands tool results back as text (``"0.92"``), so equivalence with an adapter that
    keeps the Python value (``0.92``) holds *up to that stringification*. Opt-in, and said so.
    """
    if parse_json_outputs and isinstance(payload, dict) and isinstance(payload.get("output"), str):
        with contextlib.suppress(json.JSONDecodeError):
            payload = {**payload, "output": json.loads(str(payload["output"]))}
    return repr(payload)


def normalized_tool_events(
    events: Sequence[Event], *, parse_json_outputs: bool = False
) -> list[tuple[object, ...]]:
    """Adapter-independent view of a run: no ids, timestamps, sources or adapter metadata."""
    return [
        (
            e.sequence,
            e.event_type.value,
            e.tool_name,
            e.effect_class.value if e.effect_class else None,
            e.capture_status.value,
            e.redacted_paths,
            _comparable(e.payload, parse_json_outputs=parse_json_outputs),
        )
        if e.event_type in _TOOL_EVENTS
        else (e.sequence, e.event_type.value)
        for e in events
    ]
