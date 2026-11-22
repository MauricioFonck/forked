"""OpenTelemetry bridge (ADR-013): FORKED runs <-> OTLP/JSON tool spans.

CIP does not redefine tracing (docs/06 §6.8). The bridge only maps:

* **export** — a run becomes one ``forked.run`` span with one child ``execute_tool <name>``
  span per tool call, using the GenAI semantic-convention attribute names where they exist
  and ``forked.*`` attributes for what tracing has no field for (effect class, capture
  status, policy decision). Ids are derived from FORKED ids, so export is deterministic.
  Payloads are **not** exported unless asked for (they may be sensitive; they are already
  redacted at capture, but an export leaves the machine);
* **import** — ``execute_tool`` spans become tool events. A trace says nothing about side
  effects, so every imported call is ``unknown`` (denied in branches) and completeness
  cannot be measured; both facts are declared as limitations of the import.
"""

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from forked.domain.runs.event import Event, EventType
from forked.domain.shared.canonical import JsonValue, digest
from forked.domain.shared.errors import DomainError
from forked.domain.shared.identifiers import RunId
from forked.domain.shared.schema import EVENT_SCHEMA_VERSION

MAX_SPANS = 10_000
_TRACE_ID = re.compile(r"[0-9a-f]{32}")
_SPAN_ID = re.compile(r"[0-9a-f]{16}")

TOOL_OPERATION = "execute_tool"
IMPORT_LIMITATIONS = (
    "imported from an OpenTelemetry trace: effect classes are unknown, so replay and "
    "branches deny any call whose inputs change",
    "capture completeness cannot be measured: the trace declares no capture points",
    "arguments and results exist only if the trace carried them",
    "event timestamps are the import time; original span times are kept in payload.otel",
)


class InvalidTrace(DomainError):
    code = "invalid_trace"


def _hex(seed: str, length: int) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()[:length]


def _nanos(event: Event) -> str:
    return str(int(event.timestamp.timestamp() * 1_000_000_000))


def _attr(key: str, value: str | int | float | bool) -> dict[str, JsonValue]:
    if isinstance(value, bool):
        wrapped: dict[str, JsonValue] = {"boolValue": value}
    elif isinstance(value, int):
        wrapped = {"intValue": str(value)}
    elif isinstance(value, float):
        wrapped = {"doubleValue": value}
    else:
        wrapped = {"stringValue": value}
    return {"key": key, "value": wrapped}


def _decision(payload: JsonValue) -> str | None:
    tag = payload.get("forked") if isinstance(payload, dict) else None
    decision = tag.get("decision") if isinstance(tag, dict) else None
    return decision if isinstance(decision, str) else None


def to_otlp(
    run_id: RunId,
    adapter: str,
    events: Sequence[Event],
    *,
    include_payloads: bool = False,
) -> dict[str, JsonValue]:
    if not events:
        raise InvalidTrace(f"run {run_id} has no events to export")
    trace_id = next((e.trace_id for e in events if e.trace_id), None) or _hex(run_id.value, 32)
    root_id = _hex(f"{run_id.value}/root", 16)
    outcomes = {
        e.parent_event_id: e
        for e in events
        if e.event_type in (EventType.TOOL_RESULT, EventType.TOOL_ERROR) and e.parent_event_id
    }
    spans: list[JsonValue] = []
    for call in (e for e in events if e.event_type is EventType.TOOL_CALL):
        outcome = outcomes.get(call.event_id)
        attrs: list[JsonValue] = [
            _attr("gen_ai.operation.name", TOOL_OPERATION),
            _attr("gen_ai.tool.name", call.tool_name or ""),
            _attr("forked.run_id", run_id.value),
            _attr("forked.sequence", call.sequence),
            _attr("forked.effect_class", call.effect_class.value if call.effect_class else ""),
            _attr("forked.call_capture_status", call.capture_status.value),
            _attr("forked.inputs_digest", digest(call.payload)),
        ]
        status: dict[str, JsonValue] = {"code": 0}
        if outcome is not None:
            attrs.append(_attr("forked.outcome_capture_status", outcome.capture_status.value))
            attrs.append(_attr("forked.outputs_digest", digest(outcome.payload)))
            body = outcome.payload if isinstance(outcome.payload, dict) else {}
            if outcome.event_type is EventType.TOOL_ERROR:
                status = {"code": 2, "message": str(body.get("message", ""))}
                attrs.append(_attr("error.type", str(body.get("error_type", "Error"))))
            else:
                status = {"code": 1}
        else:
            attrs.append(_attr("forked.outcome", "missing"))
        decision = _decision(outcome.payload) if outcome else None
        if decision:
            attrs.append(_attr("forked.decision", decision))
        if include_payloads:
            args = call.payload.get("inputs") if isinstance(call.payload, dict) else call.payload
            attrs.append(_attr("gen_ai.tool.call.arguments", json.dumps(args, sort_keys=True)))
            if outcome is not None and outcome.event_type is EventType.TOOL_RESULT:
                result = (
                    outcome.payload.get("output") if isinstance(outcome.payload, dict) else None
                )
                attrs.append(_attr("gen_ai.tool.call.result", json.dumps(result, sort_keys=True)))
        spans.append(
            {
                "traceId": trace_id,
                "spanId": call.span_id or _hex(call.event_id.value, 16),
                "parentSpanId": root_id,
                "name": f"{TOOL_OPERATION} {call.tool_name}",
                "kind": 1,
                "startTimeUnixNano": _nanos(call),
                "endTimeUnixNano": _nanos(outcome or call),
                "attributes": attrs,
                "status": status,
            }
        )
    first, last = events[0], events[-1]
    root: dict[str, JsonValue] = {
        "traceId": trace_id,
        "spanId": root_id,
        "name": f"forked.run {adapter}",
        "kind": 1,
        "startTimeUnixNano": _nanos(first),
        "endTimeUnixNano": _nanos(last),
        "attributes": [
            _attr("forked.run_id", run_id.value),
            _attr("forked.cip_version", EVENT_SCHEMA_VERSION),
            _attr("forked.payloads_included", include_payloads),
        ],
        "status": {"code": 2 if last.event_type is EventType.RUN_FAILED else 1},
    }
    return {
        "resourceSpans": [
            {
                "resource": {"attributes": [_attr("service.name", adapter)]},
                "scopeSpans": [{"scope": {"name": "forked"}, "spans": [root, *spans]}],
            }
        ]
    }


@dataclass(frozen=True, slots=True)
class ObservedToolCall:
    name: str
    arguments: JsonValue
    result: JsonValue
    failed: bool
    error_type: str | None
    message: str | None
    trace_id: str | None
    span_id: str | None
    start_unix_nano: str | None
    end_unix_nano: str | None
    has_arguments: bool
    has_result: bool


def _value(raw: object) -> str | int | float | bool | None:
    if not isinstance(raw, dict):
        return None
    for key in ("stringValue", "boolValue", "doubleValue"):
        if key in raw:
            found = raw[key]
            return found if isinstance(found, str | bool | float) else None
    if "intValue" in raw:
        try:
            return int(raw["intValue"])
        except (TypeError, ValueError):
            return None
    return None


def _attributes(span: Mapping[str, object]) -> dict[str, str | int | float | bool]:
    found: dict[str, str | int | float | bool] = {}
    raw = span.get("attributes", [])
    for item in raw if isinstance(raw, list) else []:
        if isinstance(item, dict) and isinstance(item.get("key"), str):
            value = _value(item.get("value"))
            if value is not None:
                found[str(item["key"])] = value
    return found


def _json_or_text(value: str | int | float | bool | None) -> JsonValue:
    if isinstance(value, str):
        try:
            parsed: JsonValue = json.loads(value)
        except json.JSONDecodeError:
            return value
        return parsed
    return value


def parse_tool_spans(document: object) -> list[ObservedToolCall]:
    """Extract ``execute_tool`` spans, ordered by start time (ties keep file order)."""
    if not isinstance(document, dict) or not isinstance(document.get("resourceSpans"), list):
        raise InvalidTrace("not an OTLP/JSON document: expected an object with resourceSpans")
    found: list[tuple[int, int, ObservedToolCall]] = []
    position = 0
    for resource in document["resourceSpans"]:
        scopes = resource.get("scopeSpans", []) if isinstance(resource, dict) else []
        for scope in scopes if isinstance(scopes, list) else []:
            spans = scope.get("spans", []) if isinstance(scope, dict) else []
            for span in spans if isinstance(spans, list) else []:
                if not isinstance(span, dict):
                    raise InvalidTrace("a span is not an object")
                attrs = _attributes(span)
                name = str(span.get("name", ""))
                if attrs.get("gen_ai.operation.name") != TOOL_OPERATION and not name.startswith(
                    f"{TOOL_OPERATION} "
                ):
                    continue
                position += 1
                if position > MAX_SPANS:
                    raise InvalidTrace(f"more than {MAX_SPANS} tool spans; refusing to import")
                tool = attrs.get("gen_ai.tool.name") or name.removeprefix(f"{TOOL_OPERATION} ")
                if not isinstance(tool, str) or not tool.strip():
                    raise InvalidTrace(f"span {position} has no tool name")
                status = span.get("status")
                failed = isinstance(status, dict) and status.get("code") in (2, "STATUS_CODE_ERROR")
                trace_id, span_id = span.get("traceId"), span.get("spanId")
                start = span.get("startTimeUnixNano")
                call = ObservedToolCall(
                    name=tool,
                    arguments=_json_or_text(attrs.get("gen_ai.tool.call.arguments")),
                    result=_json_or_text(attrs.get("gen_ai.tool.call.result")),
                    failed=failed,
                    error_type=str(attrs["error.type"]) if "error.type" in attrs else None,
                    message=str(status.get("message")) if isinstance(status, dict) else None,
                    trace_id=trace_id
                    if isinstance(trace_id, str) and _TRACE_ID.fullmatch(trace_id)
                    else None,
                    span_id=span_id
                    if isinstance(span_id, str) and _SPAN_ID.fullmatch(span_id)
                    else None,
                    start_unix_nano=str(start) if isinstance(start, str | int) else None,
                    end_unix_nano=str(e)
                    if isinstance(e := span.get("endTimeUnixNano"), str | int)
                    else None,
                    has_arguments="gen_ai.tool.call.arguments" in attrs,
                    has_result="gen_ai.tool.call.result" in attrs,
                )
                started = call.start_unix_nano or ""
                order = int(started) if started.isdigit() else 0
                found.append((order, position, call))
    if not found:
        raise InvalidTrace("no execute_tool spans found; nothing to import")
    return [call for _, _, call in sorted(found, key=lambda item: item[:2])]
