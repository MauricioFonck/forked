"""Pydantic AI adapter (ADR-013): route every tool call through a FORKED ``RecordedRun``.

One ``WrapperToolset`` is the only seam, so recording, replay and branching share it::

    caps = pydantic_ai_capabilities(EFFECTS)               # EFFECTS: {tool name: EffectClass}
    with recorder.record(caps) as run:                     # or recorder.replay / recorder.branch
        toolset = ForkedToolset(FunctionToolset(tools), run, EFFECTS)
        result = Agent(model, toolsets=[toolset]).run_sync(prompt)
        run.set_outcome({"output": result.output})

Guarantees and limits (also declared in the adapter capabilities, so every report shows them):

* only tool calls are observed — model requests and responses are **not** recorded;
* replay and branches re-run the agent: the model must ask for the same tool calls with
  the same arguments, otherwise the replay fails closed (a real LLM sampled again usually
  will not; a scripted or deterministic model will);
* tool arguments and results must be JSON values, otherwise capture fails loudly;
* a tool without a declared effect class is recorded as ``unknown`` and denied in branches;
* a call denied in a branch aborts the agent run (``on_denied="raise"``, default) or is
  reported to the model as an explicit denial (``on_denied="report"``) — never faked.
"""

from collections.abc import Mapping
from typing import Any, Literal

try:
    from pydantic_ai import RunContext
    from pydantic_ai.tools import AgentDepsT
    from pydantic_ai.toolsets import AbstractToolset, ToolsetTool, WrapperToolset
except ModuleNotFoundError as exc:  # the framework is an opt-in extra, never a core dependency
    raise ImportError(
        "the Pydantic AI adapter needs the optional extra: "
        "pip install 'forked-runtime[pydantic-ai]'"
    ) from exc

from forked.adapters.inbound.sdk.recorder import RecordedRun
from forked.domain.effects.effect_class import EffectClass
from forked.domain.effects.policy import EffectDenied
from forked.domain.runs.capabilities import AdapterCapabilities, tool_capture_point

ADAPTER_NAME = "forked-pydantic-ai"
ADAPTER_VERSION = "0.1.0"

LIMITATIONS = (
    "only tool calls are observed; model requests and responses are not recorded",
    "replay and branches re-run the agent: the model must request the same tool calls with "
    "the same arguments or the replay fails closed",
    "tool arguments and results must be JSON values",
    "a tool without a declared effect class is recorded as unknown and denied in branches",
)


def pydantic_ai_capabilities(effects: Mapping[str, EffectClass]) -> AdapterCapabilities:
    return AdapterCapabilities(
        name=ADAPTER_NAME,
        version=ADAPTER_VERSION,
        capture_points=frozenset(tool_capture_point(tool) for tool in effects),
        limitations=LIMITATIONS,
    )


class ForkedToolset(WrapperToolset[AgentDepsT]):
    def __init__(
        self,
        wrapped: AbstractToolset[AgentDepsT],
        run: RecordedRun,
        effects: Mapping[str, EffectClass],
        *,
        on_denied: Literal["raise", "report"] = "raise",
    ) -> None:
        super().__init__(wrapped)
        self._run = run
        self._effects = dict(effects)
        self._on_denied = on_denied

    async def call_tool(
        self,
        name: str,
        tool_args: dict[str, Any],
        ctx: RunContext[AgentDepsT],
        tool: ToolsetTool[AgentDepsT],
    ) -> Any:
        inner = super().call_tool

        async def execute(**inputs: Any) -> Any:
            return await inner(name, inputs, ctx, tool)

        effect = self._effects.get(name, EffectClass.UNKNOWN)
        try:
            return await self._run.acall_tool(name, effect, execute, **tool_args)
        except EffectDenied as denied:
            if self._on_denied == "raise":
                raise
            return {"denied": True, "reason": denied.reason}
