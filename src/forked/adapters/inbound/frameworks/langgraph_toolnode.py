"""LangGraph adapter (ADR-016): route every ``ToolNode`` call through a FORKED ``RecordedRun``.

``ToolNode`` accepts ``wrap_tool_call`` / ``awrap_tool_call``, so one wrapper pair is the only
seam; recording, replay and branching share it::

    caps = langgraph_capabilities(EFFECTS)                 # EFFECTS: {tool name: EffectClass}
    with recorder.record(caps) as run:                     # or recorder.replay / recorder.branch
        tool_node = forked_tool_node(tools, run, EFFECTS)
        ...add tool_node to your StateGraph, then app.invoke(...)...
        run.set_outcome({"answer": ...})

Guarantees and limits (also declared in the adapter capabilities, so every report shows them):

* only calls handled by the wrapped ``ToolNode`` are observed — the model node, every other
  node and the graph state are **not** recorded;
* replay and branches re-run the graph: the other nodes (including the model) run again live, so
  they must request the same tool calls or the replay fails closed. This is different from
  LangGraph's own time travel, which re-executes the nodes after a checkpoint *including their
  tool calls*; here a replayed tool call is answered from the recording and never executes;
* a tool result must be a ``ToolMessage`` with JSON-serializable content; a ``Command`` result is
  rejected loudly;
* tool results come back as the **string/list content LangGraph produces** (e.g. ``"0.92"``),
  not as the original Python value. Recording hands the agent the *original* ``ToolMessage``
  untouched; a replayed result is rebuilt from the recorded **content only**, so
  ``artifact`` and other message fields are not available in replay;
* calls are serialized by a lock and recorded in the order ``ToolNode`` schedules them, so
  parallel calls of one step lose their concurrency, and a replay needs the same order;
* a tool without a declared effect class is ``unknown`` and denied in branches;
* an exception raised by a tool propagates exactly as it would without FORKED; replaying a
  recorded error raises ``RecordedToolError``;
* a call denied in a branch aborts the graph (``on_denied="raise"``, default) or is returned to the
  model as an explicit error message (``on_denied="report"``) — never faked as a success.
"""

import asyncio
import threading
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Literal

try:
    from langchain_core.messages import ToolMessage
    from langchain_core.tools import BaseTool
    from langgraph.prebuilt import ToolNode
    from langgraph.prebuilt.tool_node import ToolCallRequest
    from langgraph.types import Command
except ModuleNotFoundError as exc:  # the framework is an opt-in extra, never a core dependency
    raise ImportError(
        "the LangGraph adapter needs the optional extra: pip install 'forked-runtime[langgraph]'"
    ) from exc

from forked.adapters.inbound.sdk.recorder import RecordedRun, RecordedToolError
from forked.domain.effects.effect_class import EffectClass
from forked.domain.effects.policy import EffectDenied
from forked.domain.runs.capabilities import AdapterCapabilities, tool_capture_point

ADAPTER_NAME = "forked-langgraph"
ADAPTER_VERSION = "0.1.0"

LIMITATIONS = (
    "only calls handled by the wrapped ToolNode are observed; the model node, other nodes and "
    "the graph state are not recorded",
    "replay and branches re-run the graph: the other nodes run again live and must request the "
    "same tool calls, or the replay fails closed",
    "tool results are the string or list content LangGraph produces, not the original Python "
    "value; a replayed result carries content only (no artifact or other ToolMessage fields)",
    "calls are serialized and recorded in the order ToolNode schedules them",
    "a tool without a declared effect class is recorded as unknown and denied in branches",
)


class UnsupportedToolResult(TypeError):
    """A tool returned something other than a ``ToolMessage`` (for example a ``Command``)."""


def langgraph_capabilities(effects: Mapping[str, EffectClass]) -> AdapterCapabilities:
    return AdapterCapabilities(
        name=ADAPTER_NAME,
        version=ADAPTER_VERSION,
        capture_points=frozenset(tool_capture_point(tool) for tool in effects),
        limitations=LIMITATIONS,
    )


class ForkedToolCalls:
    """The ``wrap_tool_call`` / ``awrap_tool_call`` pair for one ``RecordedRun``."""

    def __init__(
        self,
        run: RecordedRun,
        effects: Mapping[str, EffectClass],
        *,
        on_denied: Literal["raise", "report"] = "raise",
    ) -> None:
        self._run = run
        self._effects = dict(effects)
        self._on_denied = on_denied
        self._lock = threading.Lock()
        self._alock = asyncio.Lock()

    # -- shared pieces -------------------------------------------------------------------

    def _target(self, request: ToolCallRequest) -> tuple[str, dict[str, Any], str, EffectClass]:
        call = request.tool_call
        name = call["name"]
        return (
            name,
            dict(call["args"]),
            str(call["id"]),
            self._effects.get(name, EffectClass.UNKNOWN),
        )

    @staticmethod
    def _require_message(result: object) -> ToolMessage:
        if not isinstance(result, ToolMessage):
            raise UnsupportedToolResult(
                "FORKED records ToolMessage results only; "
                f"the tool returned {type(result).__name__}"
            )
        return result

    def _outcome(
        self, held: list[ToolMessage], content: Any, name: str, call_id: str
    ) -> ToolMessage:
        if held:  # recorded live: hand back the original message (keeps artifact, status…)
            return held[0]
        return ToolMessage(content=content, tool_call_id=call_id, name=name)  # replayed

    def _denial(self, denied: EffectDenied, name: str, call_id: str) -> ToolMessage:
        if self._on_denied == "raise":
            raise denied
        text = f"denied by FORKED effect policy: {denied.reason}"
        return ToolMessage(content=text, tool_call_id=call_id, name=name, status="error")

    # -- the two seams -------------------------------------------------------------------

    def wrap(
        self, request: ToolCallRequest, execute: Callable[[ToolCallRequest], Any]
    ) -> ToolMessage | Command[Any]:
        name, args, call_id, effect = self._target(request)
        held: list[ToolMessage] = []

        def run_tool(**_inputs: Any) -> Any:
            message = self._require_message(execute(request))
            held.append(message)
            return message.content

        with self._lock:
            try:
                content = self._run.call_tool(name, effect, run_tool, **args)
            except EffectDenied as denied:
                return self._denial(denied, name, call_id)
        return self._outcome(held, content, name, call_id)

    async def awrap(
        self, request: ToolCallRequest, execute: Callable[[ToolCallRequest], Any]
    ) -> ToolMessage | Command[Any]:
        name, args, call_id, effect = self._target(request)
        held: list[ToolMessage] = []

        async def run_tool(**_inputs: Any) -> Any:
            message = self._require_message(await execute(request))
            held.append(message)
            return message.content

        async with self._alock:
            try:
                content = await self._run.acall_tool(name, effect, run_tool, **args)
            except EffectDenied as denied:
                return self._denial(denied, name, call_id)
        return self._outcome(held, content, name, call_id)


def forked_tool_node(
    tools: Sequence[BaseTool | Callable[..., Any]],
    run: RecordedRun,
    effects: Mapping[str, EffectClass],
    *,
    on_denied: Literal["raise", "report"] = "raise",
    **tool_node_kwargs: Any,
) -> ToolNode:
    """A ``ToolNode`` whose every call is recorded, replayed or branched through ``run``."""
    calls = ForkedToolCalls(run, effects, on_denied=on_denied)
    return ToolNode(
        tools, wrap_tool_call=calls.wrap, awrap_tool_call=calls.awrap, **tool_node_kwargs
    )


__all__ = [
    "ADAPTER_NAME",
    "ForkedToolCalls",
    "RecordedToolError",
    "UnsupportedToolResult",
    "forked_tool_node",
    "langgraph_capabilities",
]
