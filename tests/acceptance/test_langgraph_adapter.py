"""LangGraph adapter acceptance: record, replay, branch and deny through one ToolNode seam."""

import asyncio
import socket
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("langgraph")

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import StructuredTool, tool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.types import Command

from benchmarks.fcrb.common import normalized_tool_events
from examples import expense_tools as shared
from examples import langgraph_expense_agent as expense
from forked.adapters.inbound.frameworks.langgraph_toolnode import (
    ForkedToolCalls,
    UnsupportedToolResult,
    forked_tool_node,
    langgraph_capabilities,
)
from forked.adapters.inbound.sdk.recorder import RecordedToolError
from forked.bootstrap.container import Application
from forked.demo import toy_agent
from forked.domain.branches.branch import Intervention
from forked.domain.effects.effect_class import EffectClass
from forked.domain.effects.policy import EffectDenied
from forked.domain.runs.event import EventType
from forked.domain.runs.run import RunStatus


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    real = socket.socket.connect

    def guard(self: socket.socket, address: Any) -> None:
        host = address[0] if isinstance(address, tuple) else address
        if host not in ("127.0.0.1", "::1", "localhost"):  # loopback = the event loop itself
            raise AssertionError(f"network access attempted: {address}")
        real(self, address)

    monkeypatch.setattr(socket.socket, "connect", guard)


def _record(app: Application, outbox: Path) -> Any:
    return expense.run_expense_agent(app.recorder.record(expense.CAPABILITIES), outbox)


def _graph(
    run: Any, tools: list[Any], effects: dict[str, EffectClass], script: Any, **kw: Any
) -> Any:
    graph = StateGraph(MessagesState)
    graph.add_node("agent", script)
    graph.add_node("tools", forked_tool_node(tools, run, effects, **kw))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent", lambda s: "tools" if s["messages"][-1].tool_calls else END, ["tools", END]
    )
    graph.add_edge("tools", "agent")
    return graph.compile()


def _one_call(tool_name: str, args: dict[str, Any]) -> Any:
    def agent(state: MessagesState) -> dict[str, Any]:
        if any(isinstance(m, ToolMessage) for m in state["messages"]):
            return {"messages": [AIMessage(content="done")]}
        call = {"name": tool_name, "args": args, "id": "c1", "type": "tool_call"}
        return {"messages": [AIMessage(content="", tool_calls=[call])]}

    return agent


def test_record_captures_every_tool_call_with_effect_class(
    app: Application, tmp_path: Path
) -> None:
    run_id = _record(app, tmp_path / "outbox")
    report = app.inspect_run.execute(run_id)

    assert report.snapshot.status is RunStatus.COMPLETED
    assert report.assessment.completeness.ratio == 1.0
    assert report.assessment.missing_evidence == ()
    calls = [
        (e.tool_name, e.effect_class) for e in report.events if e.event_type is EventType.TOOL_CALL
    ]
    assert calls == [
        ("search_policy", EffectClass.PURE_LOCAL),
        ("get_exchange_rate", EffectClass.EXTERNAL_READ),
        ("send_email", EffectClass.EXTERNAL_WRITE),
    ]
    assert report.assessment.redacted_events == 1
    stored = b"".join(p.read_bytes() for p in (app.store_root / "runs").rglob("*") if p.is_file())
    assert toy_agent.DEMO_API_KEY.encode() not in stored


def test_replay_executes_no_tool(
    app: Application, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    outbox = tmp_path / "outbox"
    source = _record(app, outbox)
    sent = sorted(outbox.iterdir())

    def boom(*_: object, **__: object) -> None:
        raise AssertionError("a tool executed during replay")

    monkeypatch.setattr(toy_agent, "search_policy", boom)
    monkeypatch.setattr(toy_agent, "get_exchange_rate", boom)
    monkeypatch.setattr(toy_agent.SendEmail, "__call__", boom)

    replayed = expense.run_expense_agent(app.recorder.replay(source, expense.CAPABILITIES), outbox)

    assert sorted(outbox.iterdir()) == sent
    original, again = (app.inspect_run.execute(r).events for r in (source, replayed))
    assert original[-1].payload == again[-1].payload


def test_branch_denies_the_changed_email_and_tells_the_model(
    app: Application, tmp_path: Path
) -> None:
    outbox = tmp_path / "outbox"
    baseline = _record(app, outbox)
    branch = expense.run_expense_agent(
        app.recorder.branch(baseline, expense.CAPABILITIES, Intervention(shared.RATE_CALL, 0.5)),
        outbox,
    )
    result = app.compare_runs.execute(baseline, branch)

    assert len(list(outbox.iterdir())) == 1
    assert [(s.tool, s.decision) for s in result.steps] == [
        ("search_policy", "replay"),
        ("get_exchange_rate", "intervene"),
        ("send_email", "deny"),
    ]
    assert result.claim_level.value == "controlled_comparison"
    email_after = {k: b for k, _, b in result.outcome_changes}["email"]
    assert isinstance(email_after, str)
    assert email_after.startswith("denied by FORKED effect policy")


def test_denial_can_abort_the_graph_instead(app: Application, tmp_path: Path) -> None:
    outbox = tmp_path / "outbox"
    baseline = _record(app, outbox)
    tools = [StructuredTool.from_function(f) for f in shared.build_tools(outbox)]
    script = expense._scripted_agent(100.0, {})

    with (
        pytest.raises(EffectDenied),
        app.recorder.branch(
            baseline, expense.CAPABILITIES, Intervention(shared.RATE_CALL, 0.5)
        ) as run,
    ):
        _graph(run, tools, shared.EFFECTS, script, on_denied="raise").invoke(
            {"messages": [HumanMessage("go")]}
        )

    assert app.list_runs.execute()[-1].status is RunStatus.FAILED
    assert len(list(outbox.iterdir())) == 1


def test_tool_error_propagates_and_is_replayed_as_recorded_error(app: Application) -> None:
    @tool
    def flaky(x: int) -> str:
        """Always fails."""
        raise ValueError("bad x")

    effects = {"flaky": EffectClass.PURE_LOCAL}
    caps = langgraph_capabilities(effects)
    inputs = {"messages": [HumanMessage("go")]}

    with pytest.raises(ValueError, match="bad x"), app.recorder.record(caps) as run:
        _graph(run, [flaky], effects, _one_call("flaky", {"x": 1})).invoke(inputs)
    source = app.list_runs.execute()[-1]
    assert source.status is RunStatus.FAILED
    kinds = [e.event_type for e in app.inspect_run.execute(source.run_id).events]
    assert EventType.TOOL_ERROR in kinds

    with (
        pytest.raises(RecordedToolError, match="ValueError: bad x"),
        app.recorder.replay(source.run_id, caps) as run,
    ):
        _graph(run, [flaky], effects, _one_call("flaky", {"x": 1})).invoke(inputs)


def test_command_result_is_rejected_loudly(app: Application) -> None:
    """A valid ``Command`` reaches the wrapper (LangGraph rejects invalid ones earlier)."""
    effects = {"jump": EffectClass.PURE_LOCAL}
    caps = langgraph_capabilities(effects)
    request = ToolCallRequest(
        tool_call={"name": "jump", "args": {}, "id": "c1", "type": "tool_call"},
        tool=None,
        state={},
        runtime=None,  # type: ignore[arg-type]
    )

    def execute(_: Any) -> Any:
        return Command(update={"messages": [ToolMessage("ok", tool_call_id="c1")]})

    with (
        pytest.raises(UnsupportedToolResult, match="ToolMessage results only"),
        app.recorder.record(caps) as run,
    ):
        ForkedToolCalls(run, effects).wrap(request, execute)
    assert app.list_runs.execute()[-1].status is RunStatus.FAILED


def test_undeclared_tool_is_unknown_and_answered_by_the_intervention(app: Application) -> None:
    @tool
    def mystery(name: str, fn: str) -> str:  # parameter names that collide with SDK internals
        """Mystery."""
        return f"{name}-{fn}"

    caps = langgraph_capabilities({})
    args = {"name": "x", "fn": "a"}
    inputs = {"messages": [HumanMessage("go")]}
    with app.recorder.record(caps) as run:
        _graph(run, [mystery], {}, _one_call("mystery", args)).invoke(inputs)
        parent = run.run_id
    first = next(
        e for e in app.inspect_run.execute(parent).events if e.event_type is EventType.TOOL_CALL
    )
    assert first.effect_class is EffectClass.UNKNOWN

    with app.recorder.branch(parent, caps, Intervention(first.sequence, "replaced")) as run:
        result = _graph(run, [mystery], {}, _one_call("mystery", args), on_denied="report").invoke(
            inputs
        )
    message = next(m for m in result["messages"] if isinstance(m, ToolMessage))
    assert message.content == "replaced"  # answered by the intervention, never executed


def test_async_path_records_and_replays(app: Application, tmp_path: Path) -> None:
    outbox = tmp_path / "outbox"

    async def go(session: Any) -> Any:
        with session as run:
            tools = [StructuredTool.from_function(f) for f in shared.build_tools(outbox)]
            graph = _graph(
                run, tools, shared.EFFECTS, expense._scripted_agent(100.0, {}), on_denied="report"
            )
            await graph.ainvoke({"messages": [HumanMessage("go")]})
            return run.run_id

    source = asyncio.run(go(app.recorder.record(expense.CAPABILITIES)))
    replayed = asyncio.run(go(app.recorder.replay(source, expense.CAPABILITIES)))

    assert len(list(outbox.iterdir())) == 1  # the replay executed nothing
    a, b = (app.inspect_run.execute(r).events for r in (source, replayed))
    assert [(e.tool_name, e.event_type) for e in a] == [(e.tool_name, e.event_type) for e in b]


def test_three_adapters_produce_equivalent_tool_artifacts(app: Application, tmp_path: Path) -> None:
    sdk = toy_agent.run_toy_agent(app.recorder, tmp_path / "o1")
    framework = _record(app, tmp_path / "o2")
    a = normalized_tool_events(app.inspect_run.execute(sdk).events, parse_json_outputs=True)
    b = normalized_tool_events(app.inspect_run.execute(framework).events, parse_json_outputs=True)
    assert a == b


def test_missing_extra_gives_an_actionable_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib
    import sys

    import forked.adapters.inbound.frameworks.langgraph_toolnode as module

    # submodules are already cached, so block each of them, not only the top-level package
    for name in [n for n in sys.modules if n.startswith(("langgraph", "langchain_core"))]:
        monkeypatch.setitem(sys.modules, name, None)
    with pytest.raises(ImportError, match=r"forked-runtime\[langgraph\]"):
        importlib.reload(module)
    monkeypatch.undo()
    importlib.reload(module)


def test_parallel_tool_calls_in_one_step_keep_a_valid_sequence(app: Application) -> None:
    """ToolNode may schedule the calls of one step concurrently; the adapter serializes them."""

    @tool
    def lookup(key: str) -> str:
        """Lookup."""
        return key.upper()

    effects = {"lookup": EffectClass.EXTERNAL_READ}
    caps = langgraph_capabilities(effects)

    def agent(state: MessagesState) -> dict[str, Any]:
        if any(isinstance(m, ToolMessage) for m in state["messages"]):
            return {"messages": [AIMessage(content="done")]}
        calls = [
            {"name": "lookup", "args": {"key": f"k{i}"}, "id": f"c{i}", "type": "tool_call"}
            for i in range(6)
        ]
        return {"messages": [AIMessage(content="", tool_calls=calls)]}

    with app.recorder.record(caps) as run:
        _graph(run, [lookup], effects, agent).invoke({"messages": [HumanMessage("go")]})
        run_id = run.run_id

    report = app.inspect_run.execute(run_id)
    assert report.assessment.sequence.is_valid
    calls = [e for e in report.events if e.event_type is EventType.TOOL_CALL]
    results = [e for e in report.events if e.event_type is EventType.TOOL_RESULT]
    assert len(calls) == len(results) == 6
    assert {e.parent_event_id for e in results} == {e.event_id for e in calls}  # each result pairs


def test_recording_hands_the_agent_the_original_message_and_replay_content_only(
    app: Application,
) -> None:
    @tool(response_format="content_and_artifact")
    def with_artifact(x: int) -> tuple[str, dict[str, int]]:
        """Returns content plus an artifact the model never sees."""
        return f"x={x}", {"raw": x}

    effects = {"with_artifact": EffectClass.PURE_LOCAL}
    caps = langgraph_capabilities(effects)
    inputs = {"messages": [HumanMessage("go")]}

    def messages_of(session: Any) -> tuple[Any, list[ToolMessage]]:
        with session as run:
            result = _graph(
                run, [with_artifact], effects, _one_call("with_artifact", {"x": 3})
            ).invoke(inputs)
            return run.run_id, [m for m in result["messages"] if isinstance(m, ToolMessage)]

    source, recorded = messages_of(app.recorder.record(caps))
    assert recorded[0].artifact == {"raw": 3}  # identical to what the agent gets without FORKED
    assert recorded[0].content == "x=3"

    _, replayed = messages_of(app.recorder.replay(source, caps))
    assert replayed[0].content == "x=3"
    assert replayed[0].artifact is None  # declared limit: replay carries content only
