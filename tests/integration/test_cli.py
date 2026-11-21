import json
import re
from pathlib import Path

from typer.testing import CliRunner

from forked import __version__
from forked.adapters.inbound.cli.app import app

runner = CliRunner()


def _record(store: Path) -> str:
    result = runner.invoke(app, ["record", "toy-agent", "--store", str(store)])
    assert result.exit_code == 0, result.output
    match = re.search(r"recorded (run_[0-9a-f]+)", result.output)
    assert match
    return match.group(1)


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_record_inspect_and_list(tmp_path: Path) -> None:
    store = tmp_path / "store"
    run_id = _record(store)

    listed = runner.invoke(app, ["runs", "--store", str(store)])
    assert run_id in listed.output

    human = runner.invoke(app, ["inspect", run_id, "--store", str(store), "--events"])
    assert human.exit_code == 0
    assert "missing evidence: none detected" in human.output
    assert "get_exchange_rate [external_read] (redacted)" in human.output

    machine = runner.invoke(app, ["inspect", run_id, "--store", str(store), "--json", "--strict"])
    assert machine.exit_code == 0
    data = json.loads(machine.output)
    assert data["effective_status"] == "completed"
    assert data["capture_completeness"]["ratio"] == 1.0
    assert data["missing_evidence"] == []


def test_strict_exits_1_when_evidence_is_missing(tmp_path: Path) -> None:
    store = tmp_path / "store"
    run_id = _record(store)
    meta_path = store / "runs" / run_id / "run.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["environment"]["platform"] = None
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    result = runner.invoke(app, ["inspect", run_id, "--store", str(store), "--strict"])
    assert result.exit_code == 1
    assert "environment fact not captured: platform" in result.output


def test_errors_are_explicit_with_code(tmp_path: Path) -> None:
    store = str(tmp_path / "store")
    missing = runner.invoke(app, ["inspect", "run_00000404", "--store", store])
    assert missing.exit_code == 2
    assert "error[run_not_found]" in missing.output

    bad_id = runner.invoke(app, ["inspect", "../../etc", "--store", store])
    assert bad_id.exit_code == 2
    assert "error[invalid_identifier]" in bad_id.output

    unknown = runner.invoke(app, ["record", "rm-rf", "--store", store])
    assert unknown.exit_code == 2
    assert "error[unknown_workflow]" in unknown.output


def test_empty_store(tmp_path: Path) -> None:
    result = runner.invoke(app, ["runs", "--store", str(tmp_path / "empty")])
    assert result.exit_code == 0
    assert "no runs" in result.output


def test_replay_does_not_touch_the_outbox(tmp_path: Path) -> None:
    store = tmp_path / "store"
    run_id = _record(store)
    before = sorted((store / "toy-outbox").iterdir())

    result = runner.invoke(app, ["replay", run_id, "--store", str(store)])

    assert result.exit_code == 0, result.output
    assert f"replayed {run_id} as run_" in result.output
    assert "missing evidence: none detected" in result.output
    assert sorted((store / "toy-outbox").iterdir()) == before


def test_replay_of_unknown_run_exits_2(tmp_path: Path) -> None:
    result = runner.invoke(app, ["replay", "run_deadbeefdeadbeef", "--store", str(tmp_path)])
    assert result.exit_code == 2
    assert "error[run_not_found]" in result.output


def test_branch_and_compare(tmp_path: Path) -> None:
    store = tmp_path / "store"
    run_id = _record(store)

    branched = runner.invoke(
        app, ["branch", run_id, "--at", "3", "--value", "0.5", "--store", str(store)]
    )
    assert branched.exit_code == 0, branched.output
    assert "claim      controlled_comparison" in branched.output
    branch_id = re.search(r"as (run_[0-9a-f]+)", branched.output).group(1)  # type: ignore[union-attr]
    assert len(list((store / "toy-outbox").iterdir())) == 1

    report = runner.invoke(app, ["compare", run_id, branch_id, "--json", "--store", str(store)])
    data = json.loads(report.output)
    assert data["claim_level"] == "controlled_comparison"
    assert {i["status"] for i in data["invariants"]} == {"verified"}
    assert data["intervention"]["operation"] == "replace_recorded_observation"


def test_branch_rejects_bad_value_and_bad_checkpoint(tmp_path: Path) -> None:
    store = tmp_path / "store"
    run_id = _record(store)
    bad_json = runner.invoke(
        app, ["branch", run_id, "--at", "3", "--value", "{", "--store", str(store)]
    )
    assert bad_json.exit_code == 2
    assert "error[invalid_value]" in bad_json.output
    bad_at = runner.invoke(
        app, ["branch", run_id, "--at", "0", "--value", "1", "--store", str(store)]
    )
    assert bad_at.exit_code == 2
    assert "error[invalid_checkpoint]" in bad_at.output
