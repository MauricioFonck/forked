"""The FCRB must run, be reproducible, and — crucially — be able to fail."""

import json
from pathlib import Path
from typing import Any

import pytest

from benchmarks.fcrb import runner
from forked.domain.effects.effect_class import EffectClass
from forked.domain.effects.policy import Decision, DefaultDenyPolicy, EffectDecision


@pytest.fixture(scope="module")
def results() -> dict[str, Any]:
    return runner.run_all(with_overhead=False)


def test_all_scenarios_run_and_none_fails(results: dict[str, Any]) -> None:
    scenarios = results["scenarios"]
    assert [s["id"] for s in scenarios] == [f"S{n:02d}" for n in range(1, 11)]
    assert [s["id"] for s in scenarios if s["status"] == "fail"] == []
    assert {s["status"] for s in scenarios} <= {"pass", "skipped"}


def test_deterministic_part_is_reproducible(results: dict[str, Any]) -> None:
    again = runner.run_all(with_overhead=False)
    assert runner.deterministic_view(results) == runner.deterministic_view(again)


def test_no_combined_score_and_limitations_are_stated(results: dict[str, Any]) -> None:
    assert "score" not in json.dumps(results).replace("never combined into one score", "")
    assert any("not that the approach is validated" in x for x in results["limitations"])
    assert set(results["baselines"]["executed"]) == {"plain-log", "langgraph-time-travel"}
    assert set(results["baselines"]["not_executed"]) >= {"temporal-replay", "phoenix-experiments"}
    assert "langgraph-checkpoints" not in results["baselines"]["not_executed"]  # it IS executed now


def test_baseline_is_measured_not_assumed(results: dict[str, Any]) -> None:
    by_id = {s["id"]: s for s in results["scenarios"]}
    assert by_id["S04"]["baseline"]["plain-log"]["unsafe_effects_executed"] == 1
    # LangGraph's own time travel re-executes the nodes after a checkpoint (documented): measured
    assert by_id["S04"]["baseline"]["langgraph-time-travel"]["unsafe_effects_executed"] == 1
    assert by_id["S04"]["metrics"]["unsafe_effects_executed"] == 0  # FORKED: nothing re-executed
    assert by_id["S10"]["metrics"]["equivalent_per_adapter"] == {
        "forked-pydantic-ai": True,
        "forked-langgraph": True,
    }
    assert by_id["S06"]["baseline"]["plain-log"]["missing_line_detected"] is False
    assert by_id["S08"]["baseline"]["plain-log"]["tampering_detected"] is False
    assert by_id["S09"]["baseline"]["plain-log"]["secret_occurrences_in_log"] >= 1


def test_benchmark_can_fail_when_an_unsafe_effect_is_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def allow_everything(self: DefaultDenyPolicy, effect: EffectClass) -> EffectDecision:
        return EffectDecision(Decision.ALLOW, "mutant")

    monkeypatch.setattr(DefaultDenyPolicy, "decide", allow_everything)
    broken = {s["id"]: s["status"] for s in runner.run_all(with_overhead=False)["scenarios"]}
    assert broken["S04"] == "fail"


def test_overhead_is_measured_without_asserting_speed() -> None:
    over = runner.measure_overhead(warmup=2, measured=10)
    assert over["measured_calls"] == 10
    assert over["warmup_calls_discarded"] == 2
    assert over["recorded_call"]["median_us"] > 0
    assert over["storage_bytes_per_event"] > 0
    assert over["cpu_and_memory"] == "not measured"


def test_runner_writes_results_and_report(tmp_path: Path) -> None:
    code = runner.main(["--out", str(tmp_path), "--no-overhead"])
    assert code == 0
    data = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    report = (tmp_path / "REPORT.md").read_text(encoding="utf-8")
    assert data["benchmark"] == "FCRB"
    assert "Not validated" in report or "**Not validated**" in report
    assert "## Baselines not executed" in report


def test_a_crashing_scenario_is_reported_as_failed_not_raised(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def s99_exploding(box: Any) -> Any:
        raise RuntimeError("boom")

    monkeypatch.setattr(runner, "SCENARIOS", (s99_exploding,))
    only = runner.run_all(with_overhead=False)["scenarios"]
    assert [(s["id"], s["status"]) for s in only] == [("S99", "fail")]
    assert "RuntimeError: boom" in only[0]["notes"][0]
