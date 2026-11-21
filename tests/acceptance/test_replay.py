"""UC-02 acceptance: replay a recorded run from observations, never executing tools."""

import contextlib
from pathlib import Path

import pytest

from forked.adapters.inbound.sdk.recorder import RecordedToolError
from forked.bootstrap.container import Application
from forked.demo import toy_agent
from forked.demo.toy_agent import CAPABILITIES, run_toy_agent
from forked.domain.effects.effect_class import EffectClass
from forked.domain.replay.cursor import MissingObservation, ReplayDivergence
from forked.domain.runs.event import EventType
from forked.domain.runs.run import RunStatus
from forked.domain.shared.canonical import JsonValue
from forked.domain.shared.identifiers import RunId
from tests.conftest import CAPS


def _payload(app: Application, run_id: RunId, index: int) -> dict[str, JsonValue]:
    events = app.inspect_run.execute(run_id).events
    payload = events[index].payload
    assert isinstance(payload, dict)
    return payload


def test_replay_reproduces_outcome_without_executing_any_tool(
    app: Application, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    outbox = tmp_path / "outbox"
    source = run_toy_agent(app.recorder, outbox)
    sent = sorted(p.name for p in outbox.iterdir())

    def boom(*_: object, **__: object) -> None:
        raise AssertionError("a tool executed during replay")

    for name in ("search_policy", "get_exchange_rate"):
        monkeypatch.setattr(toy_agent, name, boom)
    monkeypatch.setattr(toy_agent.SendEmail, "__call__", boom)

    replayed = run_toy_agent(
        app.recorder, outbox, session=app.recorder.replay(source, CAPABILITIES)
    )

    assert replayed != source
    assert sorted(p.name for p in outbox.iterdir()) == sent  # external write not repeated
    assert _payload(app, replayed, -1) == _payload(app, source, -1)
    report = app.inspect_run.execute(replayed)
    assert report.events[-1].event_type is EventType.RUN_COMPLETED
    assert report.assessment.missing_evidence == ()
    assert _payload(app, replayed, 0)["replay_of"] == source.value
    assert {e.source for e in report.events if e.tool_name} == {"forked.replay"}


def test_changed_input_diverges_and_fails_the_replay(app: Application, tmp_path: Path) -> None:
    source = run_toy_agent(app.recorder, tmp_path / "outbox")
    with pytest.raises(ReplayDivergence, match=r"#3 \(send_email\): inputs differ"):
        run_toy_agent(
            app.recorder,
            tmp_path / "outbox",
            amount=999.0,
            session=app.recorder.replay(source, CAPABILITIES),
        )
    failed = app.list_runs.execute()[-1]
    assert failed.status is RunStatus.FAILED


def _record_echo(app: Application, *, calls: int, fail: bool = False) -> RunId:
    def echo(x: int) -> int:
        if fail:
            raise ValueError("bad x")
        return x

    with app.recorder.record(CAPS) as run:
        for i in range(calls):
            with contextlib.suppress(ValueError):
                run.call_tool("echo", EffectClass.PURE_LOCAL, echo, x=i)
        return run.run_id


def _never(**_: object) -> int:
    raise AssertionError("executed")


def test_extra_call_has_no_observation(app: Application) -> None:
    source = _record_echo(app, calls=1)
    with pytest.raises(MissingObservation), app.recorder.replay(source, CAPS) as run:  # noqa: PT012
        run.call_tool("echo", EffectClass.PURE_LOCAL, _never, x=0)
        run.call_tool("echo", EffectClass.PURE_LOCAL, _never, x=1)


def test_unrequested_recorded_calls_fail_the_replay(app: Application) -> None:
    source = _record_echo(app, calls=2)
    with pytest.raises(ReplayDivergence, match="1 of 2"), app.recorder.replay(source, CAPS) as run:
        run.call_tool("echo", EffectClass.PURE_LOCAL, _never, x=0)


def test_effect_class_change_diverges(app: Application) -> None:
    source = _record_echo(app, calls=1)
    with (
        pytest.raises(ReplayDivergence, match="effect_class"),
        app.recorder.replay(source, CAPS) as run,
    ):
        run.call_tool("echo", EffectClass.EXTERNAL_WRITE, _never, x=0)


def test_recorded_error_is_replayed_as_error(app: Application) -> None:
    source = _record_echo(app, calls=1, fail=True)
    with app.recorder.replay(source, CAPS) as run:
        with pytest.raises(RecordedToolError) as info:
            run.call_tool("echo", EffectClass.PURE_LOCAL, _never, x=0)
        assert info.value.error_type == "ValueError"


def test_other_adapters_run_cannot_be_replayed(app: Application, tmp_path: Path) -> None:
    source = _record_echo(app, calls=1)
    with pytest.raises(ReplayDivergence, match="adapter"):
        app.recorder.replay(source, CAPABILITIES)


def test_omitted_result_cannot_be_replayed(tmp_path: Path) -> None:
    from forked.application.capture import CaptureLimits
    from forked.bootstrap.container import build_application

    app = build_application(tmp_path / "s", limits=CaptureLimits(max_payload_bytes=64))
    with app.recorder.record(CAPS) as run:
        run.call_tool("echo", EffectClass.PURE_LOCAL, lambda x: "y" * 200, x=0)
        source = run.run_id
    with (
        pytest.raises(MissingObservation, match="omitted"),
        app.recorder.replay(source, CAPS) as run,
    ):
        run.call_tool("echo", EffectClass.PURE_LOCAL, _never, x=0)
