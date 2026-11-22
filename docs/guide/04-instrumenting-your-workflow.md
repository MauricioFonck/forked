# 4. Instrumenting your workflow

You instrument **tool calls**. FORKED does not observe anything that does not go through
`call_tool`, and it says so in every report.

## The Python SDK

A complete, runnable version of this page is [`examples/minimal_sdk.py`](../../examples/minimal_sdk.py).

```python
from pathlib import Path

from forked.bootstrap.container import build_application
from forked.domain.effects.effect_class import EffectClass
from forked.domain.runs.capabilities import AdapterCapabilities, tool_capture_point

app = build_application(Path(".forked"))  # the composition root: picks the adapters

CAPABILITIES = AdapterCapabilities(
    name="my-workflow",
    version="1.0.0",
    capture_points=frozenset({tool_capture_point("price"), tool_capture_point("notify")}),
    limitations=("prices come from a fixed local table",),  # what you can NOT capture
)

with app.recorder.record(CAPABILITIES) as run:
    unit = run.call_tool("price", EffectClass.EXTERNAL_READ, price, item="widget")
    run.call_tool("notify", EffectClass.EXTERNAL_WRITE, notify, message=f"total {unit * 3}")
    run.set_outcome({"total": unit * 3})  # stored in run.completed
```

* `call_tool(name, effect, fn, **inputs)` records `tool.call`, runs `fn(**inputs)` and records the
  result (or the error, then re-raises). Tool **inputs and results must be JSON values**; anything
  else fails loudly and the run is marked `failed`.
* An exception inside the `with` block finalizes the run as `failed`. If the process dies, the run
  is reported as `incomplete`.
* `capture_points` are what the completeness figure is measured against. `limitations` are copied
  into every report.
* An async twin exists: `await run.acall_tool(name, effect, async_fn, **inputs)`.

### Replay and branch use the same workflow code

```python
from forked.domain.branches.branch import Intervention

with app.recorder.replay(baseline_id, CAPABILITIES) as run:  # nothing executes
    ...  # same code

with app.recorder.branch(baseline_id, CAPABILITIES, Intervention(checkpoint=1, value=12.5)) as run:
    ...  # same code
```

In a branch, a call the effect policy denies raises `EffectDenied` **without executing**. Handle it
like any other error:

```python
from forked.domain.effects.policy import EffectDenied

try:
    run.call_tool("notify", EffectClass.EXTERNAL_WRITE, notify, message=...)
except EffectDenied:
    ...  # the write was denied; the denial is recorded as a tool.error
```

Then compare and export from the same `app`:

```python
result = app.compare_runs.execute(baseline_id, branch_id)
app.export_evidence(baseline_id, branch_id, Path("evidence"))
```

## Choosing effect classes

Be honest and conservative: the class decides what a branch may do.

| Your tool | Class |
|---|---|
| computes from its arguments only | `pure_local` |
| reads from a service | `external_read` |
| sends, writes, charges, deletes | `external_write` |
| you are not sure | `unknown` (denied) |

## Pydantic AI

```bash
uv sync --locked                       # the dev group includes it; users: pip install 'forked-runtime[pydantic-ai]'
```

```python
from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

from forked.adapters.inbound.frameworks.pydantic_ai_toolset import (
    ForkedToolset,
    pydantic_ai_capabilities,
)

EFFECTS = {"search_policy": EffectClass.PURE_LOCAL, "send_email": EffectClass.EXTERNAL_WRITE}

with app.recorder.record(pydantic_ai_capabilities(EFFECTS)) as run:  # or .replay / .branch
    toolset = ForkedToolset(FunctionToolset(tools), run, EFFECTS)
    result = Agent(model, toolsets=[toolset]).run_sync(prompt)
```

One `WrapperToolset` is the only seam, so recording, replay and branching share it. A walkthrough
with a scripted model (no API key, no network) is in [`examples/README.md`](../../examples/README.md).

Know the limits before relying on it:

* only **tool calls** are recorded — not model requests or responses;
* replay and branches **re-run the agent**: the model must request the same tool calls with the same
  arguments, otherwise the replay **fails closed**. A real LLM sampled again usually will not; a
  scripted or deterministic model reproduces exactly;
* a tool you did not declare is `unknown`;
* a call denied in a branch aborts the agent (`on_denied="raise"`, default) or is reported to the
  model as an explicit denial (`on_denied="report"`). It is never faked as a success.

## LangGraph

```bash
uv sync --locked                       # the dev group includes it; users: pip install 'forked-runtime[langgraph]'
```

```python
from langgraph.graph import StateGraph

from forked.adapters.inbound.frameworks.langgraph_toolnode import (
    forked_tool_node,
    langgraph_capabilities,
)

EFFECTS = {"search_policy": EffectClass.PURE_LOCAL, "send_email": EffectClass.EXTERNAL_WRITE}

with app.recorder.record(langgraph_capabilities(EFFECTS)) as run:  # or .replay / .branch
    graph = StateGraph(MessagesState)
    graph.add_node("agent", my_model_node)
    graph.add_node("tools", forked_tool_node(tools, run, EFFECTS))  # instead of ToolNode(tools)
    ...  # edges as usual
    graph.compile().invoke({"messages": [...]})
```

`ToolNode` has `wrap_tool_call` / `awrap_tool_call` hooks, so one wrapper pair is the only seam.
A complete graph with a scripted model is [`examples/langgraph_expense_agent.py`](../../examples/langgraph_expense_agent.py).

How it differs from LangGraph's own time travel: LangGraph resumes from a checkpoint and
**re-executes the nodes after it, including their tool calls** (its documentation says so; the
benchmark's S04 measured the email being sent again). FORKED answers a replayed tool call from the
recording and never executes it. They solve different problems and can be used together.

Know the limits:

* only calls handled by the wrapped `ToolNode` are recorded — not the model node, other nodes or the
  graph state; replay and branches re-run those nodes live, so they must request the same tool calls
  or the replay **fails closed**;
* tool results are the **text/list content LangGraph produces** (`"0.92"`, not `0.92`). Recording
  returns the original `ToolMessage` untouched; a replayed result is rebuilt from the recorded
  **content only** (no `artifact`);
* the calls of one step are serialized by a lock and recorded in the order `ToolNode` schedules them;
* a tool that returns a `Command` is rejected loudly; an undeclared tool is `unknown`;
* a tool exception propagates as it would without FORKED; replaying it raises `RecordedToolError`;
* `on_denied="raise"` (default) aborts the graph on a denied call; `"report"` returns an explicit error
  `ToolMessage` to the model. It is never faked as a success;
* LangChain can send traces to LangSmith if you enable its tracing environment variables. FORKED does
  not enable it and sends nothing itself, but it cannot switch off a framework's own telemetry.

## OpenTelemetry

`forked otel-export` turns a run into tool spans; `forked otel-import` turns a trace into a run. An
imported run can be inspected, replayed and branched, but every call is `unknown`, so changed calls
are denied until you classify the tools. See [3. CLI reference](03-cli-reference.md).

## Writing an adapter for another framework

An adapter must: (1) route **every** tool call through `RecordedRun.call_tool`/`acall_tool`;
(2) declare each tool's effect class, defaulting to `unknown`; (3) declare its capture points and
limitations honestly; (4) never execute a tool when replaying. Keep the framework import inside the
adapter module and make it an optional extra — the core must stay framework-neutral. The Pydantic AI
adapter (`src/forked/adapters/inbound/frameworks/pydantic_ai_toolset.py`, about 80 lines) is the
reference; `tests/acceptance/test_pydantic_ai_adapter.py` shows the behavior an adapter must have.
