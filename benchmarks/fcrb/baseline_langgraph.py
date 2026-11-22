"""Baseline: LangGraph's own time travel (docs/08 §8.4), executed — not described.

LangGraph's documentation says replay and fork resume from a prior checkpoint and that
"nodes after the checkpoint re-execute, including any LLM calls, API requests, and
interrupts" (https://docs.langchain.com/oss/python/langgraph/use-time-travel, retrieved
2026-11-22). This module *measures* what that means for the expense workflow: a plain
``ToolNode`` (no FORKED), an in-memory checkpointer, and a replay from the checkpoint that
precedes the ``send_email`` tool call.

Applicability, stated plainly: this baseline is only meaningful for the scenario about
repeating an external write (S04). It is a different tool with a different purpose — resuming
and exploring state — not a failing one; the number below describes a default behavior, not a
defect.
"""

from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from examples import langgraph_expense_agent as agent
from examples.expense_tools import build_tools


def time_travel_repeats_external_write(outbox: Path) -> dict[str, Any]:
    tools = [StructuredTool.from_function(fn) for fn in build_tools(outbox)]
    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent._scripted_agent(100.0, {}))
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent", lambda s: "tools" if s["messages"][-1].tool_calls else END, ["tools", END]
    )
    graph.add_edge("tools", "agent")
    app = graph.compile(checkpointer=InMemorySaver())
    config: Any = {"configurable": {"thread_id": "fcrb"}}

    app.invoke({"messages": [HumanMessage("go")]}, config)
    after_original = len(list(outbox.iterdir()))

    def pending_send_email(snapshot: Any) -> bool:
        last = snapshot.values["messages"][-1] if snapshot.values.get("messages") else None
        return (
            snapshot.next == ("tools",)
            and isinstance(last, AIMessage)
            and any(call["name"] == "send_email" for call in last.tool_calls)
        )

    checkpoint = next(s for s in app.get_state_history(config) if pending_send_email(s))
    app.invoke(None, checkpoint.config)  # "replay from this checkpoint"
    after_replay = len(list(outbox.iterdir()))
    executed = after_replay - after_original
    return {
        "replay_means": "resume from a checkpoint; nodes after it re-execute (documented)",
        "emails_after_original_run_and_one_replay": after_replay,
        "unsafe_effect_attempts": 1,
        "unsafe_effects_executed": executed,
        "unsafe_effect_prevention_rate": 1 - executed,
    }
