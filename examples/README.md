# End-to-end use case: an expense agent (Pydantic AI + FORKED)

An agent built with [Pydantic AI](https://pydantic.dev/docs/ai/) converts an amount between
currencies, checks an expense policy and emails finance. FORKED records it, replays it, forks it with
one changed observation, compares the two runs, and exports evidence anyone can verify offline.

Everything is local and deterministic: the model is scripted (`FunctionModel`), so no API key, no
network. The tools are the toy agent's local stand-ins: the exchange rate is a fixed table, and the
"email" is a JSON file in a local outbox.

```bash
git clone https://github.com/MauricioFonck/forked && cd forked
uv sync --locked
uv run python -m examples.pydantic_ai_expense_agent
```

```text
1. record the agent (tools really run; the email goes to a local outbox)
   run_…  outbox files: 1
2. replay it: every tool answers from the recording, nothing executes
   run_…  outbox files: 1
3. branch: replace the exchange rate (tool call #3) with 0.5
   #1 search_policy: same [replay]
   #2 get_exchange_rate: changed [intervene]
   #3 send_email: changed [deny]
   claim level: controlled_comparison
   outbox files: 1  (the changed email was denied, not sent)
4. export an evidence package and verify it offline
   integrity ok: True; claims supported: True
```

## How the integration works

```python
from forked.adapters.inbound.frameworks.pydantic_ai_toolset import (
    ForkedToolset,
    pydantic_ai_capabilities,
)

EFFECTS = {
    "search_policy": EffectClass.PURE_LOCAL,
    "get_exchange_rate": EffectClass.EXTERNAL_READ,
    "send_email": EffectClass.EXTERNAL_WRITE,
}

with recorder.record(pydantic_ai_capabilities(EFFECTS)) as run:  # or .replay(...) / .branch(...)
    toolset = ForkedToolset(FunctionToolset(tools), run, EFFECTS)
    result = Agent(model, toolsets=[toolset]).run_sync(prompt)
```

One `WrapperToolset` is the only seam: every tool call passes through it, so recording, replay and
branching share it. You declare each tool's **effect class**; an undeclared tool is `unknown` and is
denied in branches.

## What it does *not* do

* Only **tool calls** are recorded — model requests and responses are not.
* Replay and branches **re-run the agent**. The model must ask for the same tool calls with the same
  arguments; a real LLM sampled again usually will not, and the replay then **fails closed** rather
  than calling the real tool. A scripted or deterministic model reproduces exactly.
* Tool arguments and results must be JSON values; anything else fails loudly.
* A call denied in a branch either aborts the agent (`on_denied="raise"`, default) or is reported to
  the model as an explicit denial (`on_denied="report"`, used here). It is never faked as a success.
* The `comparison` describes one recorded run pair. It is not a causal estimate.

See [`benchmarks/`](../benchmarks/README.md) for the scenarios that exercise this adapter (S03, S10).

## The same agent as a LangGraph graph

```bash
uv run python -m examples.langgraph_expense_agent
```

`forked_tool_node(tools, run, EFFECTS)` returns a `ToolNode` whose `wrap_tool_call` /
`awrap_tool_call` route every call through FORKED; the "model" is a scripted node, so it is
deterministic and offline. Output:

```text
1. recorded  run_…  outbox files: 1
2. replayed  run_…  outbox files: 1  (nothing executed)
3. #1 search_policy: same [replay]
3. #2 get_exchange_rate: changed [intervene]
3. #3 send_email: changed [deny]
   claim level: controlled_comparison; outbox files: 1
```

Different from LangGraph's own time travel, which **re-executes** the nodes after a checkpoint
(including tool calls): here a replayed call is answered from the recording and never runs.
Limits: only `ToolNode` calls are observed (not the model node or graph state); tool results are the
text LangGraph produces; a replayed result carries content only (no `artifact`); parallel calls of one
step are serialized; a `Command` result is rejected. See
[the guide](../docs/guide/04-instrumenting-your-workflow.md#langgraph).
