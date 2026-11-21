"""UC-03/UC-04 acceptance: branch with one intervention, default-deny effects, comparison."""

import dataclasses
import hashlib
from pathlib import Path

import pytest

from forked.bootstrap.container import Application
from forked.demo import toy_agent
from forked.demo.toy_agent import CAPABILITIES, run_toy_agent
from forked.domain.branches.branch import Intervention, InvalidCheckpoint
from forked.domain.comparison.compare import (
    ClaimLevel,
    InvariantStatus,
    NotABranch,
    RunEvidence,
    compare,
)
from forked.domain.effects.effect_class import EffectClass
from forked.domain.effects.policy import EffectDenied
from forked.domain.replay.cursor import ReplayDivergence
from forked.domain.runs.event import EventType
from forked.domain.runs.run import RunStatus
from forked.domain.shared.identifiers import RunId
from tests.conftest import CAPS

RATE_CALL = 3  # sequence of the get_exchange_rate tool.call in the toy agent


def _files(root: Path) -> dict[str, str]:
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def _branch(app: Application, outbox: Path, parent: RunId, value: object) -> RunId:
    return run_toy_agent(
        app.recorder,
        outbox,
        session=app.recorder.branch(parent, CAPABILITIES, Intervention(RATE_CALL, value)),  # type: ignore[arg-type]
    )


def _statuses(app: Application, base: RunId, branch: RunId) -> dict[str, InvariantStatus]:
    return {i.id: i.status for i in app.compare_runs.execute(base, branch).invariants}


def test_branch_changes_outcome_denies_write_and_keeps_parent_intact(
    app: Application, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    outbox = tmp_path / "outbox"
    parent = run_toy_agent(app.recorder, outbox)
    parent_dir = app.store_root / "runs" / parent.value
    before, sent = _files(parent_dir), sorted(outbox.iterdir())

    def boom(*_: object, **__: object) -> None:
        raise AssertionError("a non-pure tool executed in a branch")

    monkeypatch.setattr(toy_agent, "get_exchange_rate", boom)
    monkeypatch.setattr(toy_agent.SendEmail, "__call__", boom)
    branch = _branch(app, outbox, parent, 0.5)
    result = app.compare_runs.execute(parent, branch)

    assert _files(parent_dir) == before  # parent artifacts byte-identical
    assert sorted(outbox.iterdir()) == sent  # nothing sent
    assert [(s.tool, s.status, s.decision) for s in result.steps] == [
        ("search_policy", "same", "replay"),
        ("get_exchange_rate", "changed", "intervene"),
        ("send_email", "changed", "deny"),
    ]
    changes = {k: (a, b) for k, a, b in result.outcome_changes}
    assert changes["converted"] == (92.0, 50.0)
    assert changes["rate"] == (0.92, 0.5)
    assert all(i.status is InvariantStatus.VERIFIED for i in result.invariants)
    assert result.claim_level is ClaimLevel.CONTROLLED_COMPARISON
    assert "not a causal estimate" in result.statement
    assert result.intervention == {
        "id": "int_001",
        "target": "tool.result",
        "operation": "replace_recorded_observation",
        "checkpoint": RATE_CALL,
        "value": 0.5,
    }


def test_same_value_branch_replays_everything(app: Application, tmp_path: Path) -> None:
    parent = run_toy_agent(app.recorder, tmp_path / "outbox")
    branch = _branch(app, tmp_path / "outbox", parent, 0.92)
    result = app.compare_runs.execute(parent, branch)
    assert [s.decision for s in result.steps] == ["replay", "intervene", "replay"]
    assert result.outcome_changes == ()


def test_checkpoint_must_be_a_tool_call(app: Application, tmp_path: Path) -> None:
    parent = run_toy_agent(app.recorder, tmp_path / "outbox")
    runs = len(app.list_runs.execute())
    with pytest.raises(InvalidCheckpoint, match=r"not a tool\.call"):
        app.recorder.branch(parent, CAPABILITIES, Intervention(4, 0.5))
    assert len(app.list_runs.execute()) == runs  # no branch run was created


def test_prefix_divergence_fails_closed(app: Application, tmp_path: Path) -> None:
    with app.recorder.record(CAPS) as run:
        run.call_tool("echo", EffectClass.PURE_LOCAL, lambda x: x, x=1)
        run.call_tool("echo", EffectClass.PURE_LOCAL, lambda x: x, x=2)
        parent = run.run_id
    with (
        pytest.raises(ReplayDivergence, match="inputs differ"),
        app.recorder.branch(parent, CAPS, Intervention(3, 99)) as run,
    ):
        run.call_tool("echo", EffectClass.PURE_LOCAL, lambda x: x, x=7)


def _never(**_: object) -> int:
    raise AssertionError("executed")


@pytest.mark.parametrize(
    "effect",
    [
        EffectClass.EXTERNAL_READ,
        EffectClass.RECORDED_READ,
        EffectClass.EXTERNAL_WRITE,
        EffectClass.LOCAL_WRITE,
        EffectClass.UNKNOWN,
    ],
)
def test_changed_non_pure_call_after_checkpoint_is_denied(
    app: Application, effect: EffectClass
) -> None:
    with app.recorder.record(CAPS) as run:
        run.call_tool("echo", EffectClass.PURE_LOCAL, lambda x: x, x=1)
        run.call_tool("echo", effect, lambda x: x, x=2)
        parent = run.run_id
    with app.recorder.branch(parent, CAPS, Intervention(1, 10)) as run:
        assert run.call_tool("echo", EffectClass.PURE_LOCAL, _never, x=1) == 10
        with pytest.raises(EffectDenied):
            run.call_tool("echo", effect, _never, x=20)
        branch = run.run_id
    denied = [
        e for e in app.inspect_run.execute(branch).events if e.event_type is EventType.TOOL_ERROR
    ]
    assert denied[0].payload["error_type"] == "EffectDenied"  # type: ignore[index,call-overload]


def test_changed_pure_local_call_after_checkpoint_executes(app: Application) -> None:
    with app.recorder.record(CAPS) as run:
        run.call_tool("echo", EffectClass.PURE_LOCAL, lambda x: x, x=1)
        run.call_tool("echo", EffectClass.PURE_LOCAL, lambda x: x, x=2)
        parent = run.run_id
    with app.recorder.branch(parent, CAPS, Intervention(1, 10)) as run:
        first: int = run.call_tool("echo", EffectClass.PURE_LOCAL, _never, x=1)
        assert run.call_tool("echo", EffectClass.PURE_LOCAL, lambda x: x * 3, x=first) == 30


def test_tampered_parent_violates_invariant_and_downgrades_claim(
    app: Application, tmp_path: Path
) -> None:
    parent = run_toy_agent(app.recorder, tmp_path / "outbox")
    branch = _branch(app, tmp_path / "outbox", parent, 0.5)
    log = app.store_root / "runs" / parent.value / "events.jsonl"
    log.write_bytes(log.read_bytes().replace(b'"currency conversion"', b'"currency tampered!!"'))

    result = app.compare_runs.execute(parent, branch)

    statuses = {i.id: i.status for i in result.invariants}
    assert statuses["inv_parent_unchanged"] is InvariantStatus.VIOLATED
    assert result.claim_level is ClaimLevel.OBSERVATIONAL


def test_incomplete_branch_leaves_invariants_unknown_never_verified(
    app: Application, tmp_path: Path
) -> None:
    parent = run_toy_agent(app.recorder, tmp_path / "outbox")
    branch = _branch(app, tmp_path / "outbox", parent, 0.5)
    a, b = app.inspect_run.execute(parent), app.inspect_run.execute(branch)
    truncated = b.events[:4]  # log tail lost: intervention recorded, nothing after
    b_assessment = dataclasses.replace(b.assessment, effective_status=RunStatus.INCOMPLETE)

    result = compare(
        RunEvidence(a.snapshot, a.events, a.assessment),
        RunEvidence(b.snapshot, truncated, b_assessment),
    )

    statuses = {i.id: i.status for i in result.invariants}
    assert statuses["inv_prefix_replayed"] is InvariantStatus.UNKNOWN
    assert statuses["inv_no_live_side_effects"] is InvariantStatus.UNKNOWN
    assert result.claim_level is ClaimLevel.OBSERVATIONAL
    assert "outcome not comparable: a run has no run.completed event" in result.missing_evidence


def test_compare_requires_recorded_lineage(app: Application, tmp_path: Path) -> None:
    one = run_toy_agent(app.recorder, tmp_path / "outbox")
    two = run_toy_agent(app.recorder, tmp_path / "outbox")
    with pytest.raises(NotABranch):
        app.compare_runs.execute(one, two)


def test_secret_in_intervention_value_is_redacted(app: Application, tmp_path: Path) -> None:
    with app.recorder.record(CAPS) as run:
        run.call_tool("echo", EffectClass.PURE_LOCAL, lambda x: x, x=1)
        parent = run.run_id
    secret = "sk-live-abcdefghijklmnopqrstuvwxyz0123"  # noqa: S105 - fake, must be redacted
    with app.recorder.branch(parent, CAPS, Intervention(1, {"token": secret})) as run:
        run.call_tool("echo", EffectClass.PURE_LOCAL, _never, x=1)
    for path in (app.store_root / "runs").rglob("*"):
        if path.is_file():
            assert secret.encode() not in path.read_bytes()


def test_checkpoint_call_must_match_parent_inputs(app: Application) -> None:
    with app.recorder.record(CAPS) as run:
        run.call_tool("echo", EffectClass.PURE_LOCAL, lambda x: x, x=1)
        parent = run.run_id
    with (
        pytest.raises(ReplayDivergence, match="inputs differ"),
        app.recorder.branch(parent, CAPS, Intervention(1, 10)) as run,
    ):
        run.call_tool("echo", EffectClass.PURE_LOCAL, _never, x=99)
