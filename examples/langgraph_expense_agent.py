"""The same expense agent as a LangGraph graph, run through FORKED.

The "model" is a plain scripted node, so the run is deterministic and needs no API key and no
network. The tools are the shared local stand-ins in ``examples/expense_tools.py``.

    uv run python -m examples.langgraph_expense_agent
"""

import json
import tempfile
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.graph import END, START, MessagesState, StateGraph

from examples.expense_tools import EFFECTS, RATE_CALL, build_tools
from forked.adapters.inbound.frameworks.langgraph_toolnode import (
    forked_tool_node,
    langgraph_capabilities,
)
from forked.adapters.inbound.sdk.recorder import RecordedRun
from forked.demo import toy_agent
from forked.domain.shared.identifiers import RunId

CAPABILITIES = langgraph_capabilities(EFFECTS)


def _decode(content: Any) -> Any:
    """LangGraph hands tool results back as text: ``"0.92"`` -> ``0.92``; plain text stays text."""
    if not isinstance(content, str):
        return content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return content


def _scripted_agent(amount: float, state_out: dict[str, Any]) -> Any:
    """A deterministic 'model' node: asks for the three tools in order, then answers."""

    def call(tool: str, args: dict[str, Any], number: int) -> dict[str, Any]:
        tool_call = {"name": tool, "args": args, "id": f"call_{number}", "type": "tool_call"}
        return {"messages": [AIMessage(content="", tool_calls=[tool_call])]}

    def agent(state: MessagesState) -> dict[str, Any]:
        got = {m.name: _decode(m.content) for m in state["messages"] if isinstance(m, ToolMessage)}
        if "search_policy" not in got:
            return call("search_policy", {"query": "currency conversion"}, 1)
        hits = got["search_policy"]
        state_out["policy_hits"] = len(hits) if isinstance(hits, list) else 0
        if "get_exchange_rate" not in got:
            args = {"base": "USD", "quote": "EUR", "api_key": toy_agent.DEMO_API_KEY}
            return call("get_exchange_rate", args, 2)
        rate = got["get_exchange_rate"]
        if not isinstance(rate, int | float):
            return {"messages": [AIMessage(content=f"Cannot convert: {rate}")]}
        state_out["rate"], state_out["converted"] = rate, round(amount * rate, 2)
        if "send_email" not in got:
            converted = state_out["converted"]
            body = f"{amount:.2f} USD = {converted:.2f} EUR (rate {rate}, source: toy stub)."
            args = {"to": "finance@example.com", "subject": "Conversion USD->EUR", "body": body}
            return call("send_email", args, 3)
        state_out["email"] = got["send_email"]
        text = f"Converted {amount:.2f} USD to {state_out['converted']:.2f} EUR."
        return {"messages": [AIMessage(content=text)]}

    return agent


def run_expense_agent(
    session: AbstractContextManager[RecordedRun], outbox: Path, *, amount: float = 100.0
) -> RunId:
    """Run the graph inside ``recorder.record(...)``, ``.replay(...)`` or ``.branch(...)``."""
    state: dict[str, Any] = {}
    with session as run:
        tools = [StructuredTool.from_function(fn) for fn in build_tools(outbox)]
        graph = StateGraph(MessagesState)
        graph.add_node("agent", _scripted_agent(amount, state))
        graph.add_node("tools", forked_tool_node(tools, run, EFFECTS, on_denied="report"))
        graph.add_edge(START, "agent")
        graph.add_conditional_edges(
            "agent", lambda s: "tools" if s["messages"][-1].tool_calls else END, ["tools", END]
        )
        graph.add_edge("tools", "agent")
        result = graph.compile().invoke(
            {"messages": [HumanMessage(f"Convert {amount:.2f} USD to EUR and email finance.")]}
        )
        state["answer"] = result["messages"][-1].content
        run.set_outcome(state)
        return run.run_id


def main() -> None:
    from forked.bootstrap.container import build_application
    from forked.domain.branches.branch import Intervention

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        app = build_application(root / "store")
        outbox = root / "outbox"

        baseline = run_expense_agent(app.recorder.record(CAPABILITIES), outbox)
        print(f"1. recorded  {baseline}  outbox files: {len(list(outbox.iterdir()))}")
        replayed = run_expense_agent(app.recorder.replay(baseline, CAPABILITIES), outbox)
        sent = len(list(outbox.iterdir()))
        print(f"2. replayed  {replayed}  outbox files: {sent}  (nothing executed)")
        branch = run_expense_agent(
            app.recorder.branch(baseline, CAPABILITIES, Intervention(RATE_CALL, 0.5)), outbox
        )
        comparison = app.compare_runs.execute(baseline, branch)
        for step in comparison.steps:
            print(f"3. #{step.index} {step.tool}: {step.status} [{step.decision}]")
        print(
            f"   claim level: {comparison.claim_level}; outbox files: {len(list(outbox.iterdir()))}"
        )


if __name__ == "__main__":
    main()
