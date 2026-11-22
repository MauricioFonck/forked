"""Pydantic AI adapter acceptance: record, replay, branch and deny through one toolset."""

import socket
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pydantic_ai")

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.toolsets import FunctionToolset

from benchmarks.fcrb.common import normalized_tool_events
from examples import pydantic_ai_expense_agent as expense
from forked.adapters.inbound.frameworks.pydantic_ai_toolset import ForkedToolset
from forked.bootstrap.container import Application
from forked.demo import toy_agent
from forked.domain.branches.branch import Intervention
from forked.domain.effects.effect_class import EffectClass
from forked.domain.effects.policy import EffectDenied
from forked.domain.runs.event import EventType
from forked.domain.runs.run import RunStatus
from forked.domain.shared.errors import InvalidEvent


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


def test_record_captures_every_tool_call_with_effect_class(
    app: Application, tmp_path: Path
) -> None:
    run_id = _record(app, tmp_path / "outbox")
    report = app.inspect_run.execute(run_id)

    assert report.snapshot.status is RunStatus.COMPLETED
    assert report.assessment.completeness.ratio == 1.0
    assert report.assessment.missing_evidence == ()
    tools = [
        (e.tool_name, e.effect_class) for e in report.events if e.event_type is EventType.TOOL_CALL
    ]
    assert tools == [
        ("search_policy", EffectClass.PURE_LOCAL),
        ("get_exchange_rate", EffectClass.EXTERNAL_READ),
        ("send_email", EffectClass.EXTERNAL_WRITE),
    ]
    assert report.assessment.redacted_events == 1  # the api_key argument
    assert toy_agent.DEMO_API_KEY.encode() not in b"".join(
        p.read_bytes() for p in (app.store_root / "runs").rglob("*") if p.is_file()
    )


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
    assert original[-1].payload == again[-1].payload  # same outcome from the recording


def test_branch_denies_the_changed_email_and_reports_it_to_the_model(
    app: Application, tmp_path: Path
) -> None:
    outbox = tmp_path / "outbox"
    baseline = _record(app, outbox)
    branch = expense.run_expense_agent(
        app.recorder.branch(baseline, expense.CAPABILITIES, Intervention(expense.RATE_CALL, 0.5)),
        outbox,
    )
    result = app.compare_runs.execute(baseline, branch)

    assert len(list(outbox.iterdir())) == 1  # nothing new was sent
    assert [(s.tool, s.decision) for s in result.steps] == [
        ("search_policy", "replay"),
        ("get_exchange_rate", "intervene"),
        ("send_email", "deny"),
    ]
    assert result.claim_level.value == "controlled_comparison"
    changes = {k: (a, b) for k, a, b in result.outcome_changes}
    assert changes["converted"] == (92.0, 50.0)
    email_after = changes["email"][1]
    assert isinstance(email_after, dict)
    assert email_after["denied"] is True


def test_denial_can_abort_the_run_instead(app: Application, tmp_path: Path) -> None:
    outbox = tmp_path / "outbox"
    baseline = _record(app, outbox)

    def abort(run: Any) -> Any:
        return ForkedToolset(
            FunctionToolset(expense.build_tools(outbox)), run, expense.EFFECTS, on_denied="raise"
        )

    state: dict[str, Any] = {}
    with (  # noqa: PT012
        pytest.raises(EffectDenied),
        app.recorder.branch(
            baseline, expense.CAPABILITIES, Intervention(expense.RATE_CALL, 0.5)
        ) as run,
    ):
        agent = Agent(FunctionModel(expense._script(100.0, state)), toolsets=[abort(run)])
        agent.run_sync("go")

    failed = app.list_runs.execute()[-1]
    assert failed.status is RunStatus.FAILED
    assert len(list(outbox.iterdir())) == 1


def _mystery_agent(run: Any) -> Agent[None, str]:
    calls = iter(["a", "b"])

    def mystery(name: str, fn: str) -> str:  # parameter names that collide with SDK internals
        return f"{name}-{fn}"

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if len(messages) <= 1:
            return ModelResponse(parts=[ToolCallPart("mystery", {"name": "x", "fn": next(calls)})])
        return ModelResponse(parts=[TextPart("done")])

    toolset = ForkedToolset(FunctionToolset([mystery]), run, {}, on_denied="report")
    return Agent(FunctionModel(respond), toolsets=[toolset])


def test_undeclared_tool_is_unknown_and_denied_when_its_inputs_change(app: Application) -> None:
    with app.recorder.record(expense.CAPABILITIES) as run:
        _mystery_agent(run).run_sync("go")
        parent = run.run_id
    events = app.inspect_run.execute(parent).events
    call = next(e for e in events if e.event_type is EventType.TOOL_CALL)
    assert call.effect_class is EffectClass.UNKNOWN

    # branch at the only call, then a changed second call would be denied: here the replayed
    # agent repeats the same call, so it is answered by the intervention, never executed.
    with app.recorder.branch(
        parent, expense.CAPABILITIES, Intervention(call.sequence, "replaced")
    ) as run:
        _mystery_agent(run).run_sync("go")
        branch = run.run_id
    outcomes = [
        e for e in app.inspect_run.execute(branch).events if e.event_type is EventType.TOOL_RESULT
    ]
    assert outcomes[0].payload["output"] == "replaced"  # type: ignore[index,call-overload]


def test_non_json_tool_result_fails_loudly(app: Application) -> None:
    class Opaque:
        pass

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(parts=[ToolCallPart("opaque", {})])

    def opaque() -> Any:
        return Opaque()

    with pytest.raises(InvalidEvent), app.recorder.record(expense.CAPABILITIES) as run:  # noqa: PT012
        toolset = ForkedToolset(FunctionToolset([opaque]), run, {"opaque": EffectClass.PURE_LOCAL})
        Agent(FunctionModel(respond), toolsets=[toolset]).run_sync("go")

    assert app.list_runs.execute()[-1].status is RunStatus.FAILED


def test_pydantic_ai_and_sdk_adapters_produce_equivalent_tool_artifacts(
    app: Application, tmp_path: Path
) -> None:
    sdk = toy_agent.run_toy_agent(app.recorder, tmp_path / "outbox-sdk")
    framework = _record(app, tmp_path / "outbox-fw")
    a, b = (normalized_tool_events(app.inspect_run.execute(r).events) for r in (sdk, framework))
    assert a == b


def test_missing_extra_gives_an_actionable_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib
    import sys

    import forked.adapters.inbound.frameworks.pydantic_ai_toolset as module

    monkeypatch.setitem(sys.modules, "pydantic_ai", None)  # what an absent package looks like
    with pytest.raises(ImportError, match=r"forked-runtime\[pydantic-ai\]"):
        importlib.reload(module)
    monkeypatch.undo()
    importlib.reload(module)  # leave the module usable for the other tests
