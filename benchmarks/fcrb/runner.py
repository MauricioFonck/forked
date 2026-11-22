"""Reproducible FCRB runner: scenarios + overhead -> results.json and REPORT.md.

    uv run python -m benchmarks.fcrb --out benchmarks/results

Everything except ``overhead`` and ``environment`` is deterministic: two runs produce the
same ``deterministic_view``. Timings are machine-dependent by nature (docs/08 §8.5):
warm-up runs are discarded, the measured runs are summarized as median and p95, and the
raw numbers are kept in ``results.json``.
"""

import argparse
import dataclasses
import json
import os
import platform
import statistics
import sys
import time
from pathlib import Path
from typing import Any

from benchmarks.fcrb import baseline
from benchmarks.fcrb.scenarios import SCENARIOS, Sandbox, ScenarioResult
from forked import __version__
from forked.bootstrap.container import build_application
from forked.domain.effects.effect_class import EffectClass
from forked.domain.runs.capabilities import AdapterCapabilities, tool_capture_point

FCRB_VERSION = "0.1"
OVERHEAD_CAPS = AdapterCapabilities(
    name="fcrb-overhead",
    version="0.1.0",
    capture_points=frozenset({tool_capture_point("noop")}),
    limitations=("synthetic no-op tool",),
)
LIMITATIONS = (
    "The workflows are toy and scripted; no real LLM, network or external system is involved.",
    "Results show FORKED behaves as specified on these scenarios, not that the approach is "
    "validated: that needs an independent reproduction (docs/08 §8.6).",
    "Only a plain-log baseline is executed; the others are listed with the reason they were not.",
    "Overhead is measured for capture only (latency, storage); CPU and memory are not measured.",
    "Verification was exercised in a clean directory, not on a separate machine.",
)


def measure_overhead(warmup: int, measured: int) -> dict[str, Any]:
    def noop(**kwargs: Any) -> int:
        return 1

    def bare() -> list[float]:
        out = []
        for i in range(measured + warmup):
            start = time.perf_counter()
            noop(x=i)
            out.append(time.perf_counter() - start)
        return out[warmup:]

    box = Sandbox()
    try:
        app = build_application(box.root / "store")
        with app.recorder.record(OVERHEAD_CAPS) as run:
            samples = []
            for i in range(measured + warmup):
                start = time.perf_counter()
                run.call_tool("noop", EffectClass.PURE_LOCAL, noop, x=i)
                samples.append(time.perf_counter() - start)
            run_id = run.run_id
        recorded = samples[warmup:]
        log = app.store_root / "runs" / run_id.value / "events.jsonl"
        events = len(log.read_text(encoding="utf-8").splitlines())
        size = log.stat().st_size
    finally:
        box.close()

    def summary(values: list[float]) -> dict[str, float]:
        ordered = sorted(values)
        return {
            "median_us": round(statistics.median(ordered) * 1e6, 2),
            "p95_us": round(ordered[int(len(ordered) * 0.95) - 1] * 1e6, 2),
        }

    bare_values = bare()
    return {
        "warmup_calls_discarded": warmup,
        "measured_calls": measured,
        "bare_call": summary(bare_values),
        "recorded_call": summary(recorded),
        "storage_bytes_per_event": round(size / events, 1),
        "events_per_tool_call": 2,
        "raw_recorded_seconds": [round(v, 9) for v in recorded],
        "cpu_and_memory": "not measured",
    }


def run_all(*, with_overhead: bool = True, warmup: int = 20, measured: int = 200) -> dict[str, Any]:
    os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
    results: list[ScenarioResult] = []
    for scenario in SCENARIOS:
        box = Sandbox()
        try:
            results.append(scenario(box))
        except Exception as exc:  # a benchmark reports a broken behavior, it does not abort
            name = scenario.__name__
            results.append(
                ScenarioResult(
                    name.split("_")[0].upper(),
                    name.split("_", 1)[1].replace("_", " "),
                    "fail",
                    notes=[f"scenario raised {type(exc).__name__}: {exc}"],
                )
            )
        finally:
            box.close()
    return {
        "benchmark": "FCRB",
        "fcrb_version": FCRB_VERSION,
        "note": "name provisional; metrics are reported separately and never combined into one score",
        "forked_version": __version__,
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(terse=True),
        },
        "scenarios": [dataclasses.asdict(r) for r in results],
        "baselines": {"executed": ["plain-log"], "not_executed": baseline.NOT_EXECUTED},
        "overhead": measure_overhead(warmup, measured) if with_overhead else None,
        "limitations": list(LIMITATIONS),
    }


def deterministic_view(results: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in results.items() if k not in ("overhead", "environment")}


def _cell(value: Any) -> str:
    return f"{value:.2f}" if isinstance(value, float) else str(value)


def render_report(results: dict[str, Any]) -> str:
    lines = [
        f"# FCRB report (v{results['fcrb_version']}, FORKED {results['forked_version']})",
        "",
        "> Provisional benchmark name. Pre-alpha. **Not validated**: no independent reproduction yet.",
        "> Metrics are reported separately and never combined into one score.",
        "",
        "## Scenarios",
        "",
        "| Id | Scenario | Result | Measured by FORKED | Plain-log baseline (measured) |",
        "|---|---|---|---|---|",
    ]
    for s in results["scenarios"]:
        metrics = "; ".join(f"{k}={_cell(v)}" for k, v in s["metrics"].items()) or "—"
        base = (
            "; ".join(f"{k}={_cell(v)}" for k, v in (s["baseline"].get("plain-log") or {}).items())
            or "—"
        )
        lines.append(f"| {s['id']} | {s['title']} | **{s['status']}** | {metrics} | {base} |")
    lines += ["", "### Notes", ""]
    lines += [f"- **{s['id']}**: {n}" for s in results["scenarios"] for n in s["notes"]]
    over = results["overhead"]
    if over:
        lines += [
            "",
            "## Overhead (machine-dependent)",
            "",
            f"- environment: {results['environment']}",
            f"- {over['measured_calls']} measured calls after {over['warmup_calls_discarded']} warm-up calls",
            f"- bare call: median {over['bare_call']['median_us']} µs, p95 {over['bare_call']['p95_us']} µs",
            f"- recorded call: median {over['recorded_call']['median_us']} µs, "
            f"p95 {over['recorded_call']['p95_us']} µs ({over['events_per_tool_call']} events per call, each flushed)",
            f"- storage: {over['storage_bytes_per_event']} bytes per event",
            "- the ratio to a bare call is not meaningful for a no-op; the absolute cost per tool "
            "call is what matters. It is dominated by opening and flushing the log once per event; "
            "batching is a possible optimization if a workload ever needs it (none measured yet)",
            f"- CPU and memory: {over['cpu_and_memory']}",
        ]
    lines += ["", "## Baselines not executed", ""]
    lines += [f"- **{k}**: {v}" for k, v in results["baselines"]["not_executed"].items()]
    lines += ["", "## Limitations", ""] + [f"- {item}" for item in results["limitations"]]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m benchmarks.fcrb", description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("benchmarks/results"))
    parser.add_argument("--no-overhead", action="store_true", help="skip the timing measurements")
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--runs", type=int, default=200, help="measured calls for the overhead")
    args = parser.parse_args(argv)

    results = run_all(with_overhead=not args.no_overhead, warmup=args.warmup, measured=args.runs)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.out / "REPORT.md").write_text(render_report(results), encoding="utf-8")
    for s in results["scenarios"]:
        print(f"{s['id']} {s['status']:<8} {s['title']}")
    print(f"wrote {args.out / 'results.json'} and {args.out / 'REPORT.md'}")
    return 1 if any(s["status"] == "fail" for s in results["scenarios"]) else 0


if __name__ == "__main__":
    sys.exit(main())
