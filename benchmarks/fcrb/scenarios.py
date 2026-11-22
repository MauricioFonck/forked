"""The ten initial FCRB scenarios (docs/08 §8.2). Each returns measured facts, not opinions.

``status`` says whether FORKED behaved as the scenario specifies; it never says the
benchmark is "validated" (docs/08 §8.6: that needs an independent reproduction).
Metrics are reported separately and never combined into one score (§8.3).
"""

import json
import secrets
import shutil
import tempfile
from collections import Counter
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import patch

from benchmarks.fcrb import baseline
from benchmarks.fcrb.common import normalized_tool_events
from forked.adapters.inbound.sdk.recorder import RecordedRun
from forked.bootstrap.container import Application, build_application, verify_package
from forked.demo import toy_agent
from forked.demo.toy_agent import CAPABILITIES, run_toy_agent
from forked.domain.branches.branch import Intervention
from forked.domain.effects.effect_class import EffectClass
from forked.domain.replay.cursor import MissingObservation, ReplayDivergence
from forked.domain.runs.capabilities import AdapterCapabilities, tool_capture_point
from forked.domain.runs.environment import EnvironmentFingerprint
from forked.domain.runs.event import EventType
from forked.domain.shared.identifiers import RunId

RATE_CALL = 3
REQUIRED_MANIFEST_FIELDS = (
    "package_format",
    "cip_version",
    "experiment",
    "environment",
    "invariants",
    "claim",
    "limitations",
    "missing_evidence",
    "artifacts",
)
SYNTHETIC = AdapterCapabilities(
    name="fcrb-synthetic",
    version="0.1.0",
    capture_points=frozenset(tool_capture_point(t) for t in ("now", "lookup", "fail")),
    limitations=("synthetic workflow used only by the FCRB",),
)


@dataclass
class ScenarioResult:
    id: str
    title: str
    status: str  # "pass" | "fail" | "skipped"
    metrics: dict[str, Any] = field(default_factory=dict)
    baseline: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


class Sandbox:
    """A fresh temporary directory per scenario, so scenarios cannot influence each other."""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="fcrb-")
        self.root = Path(self._tmp.name)

    def app(self, name: str = "store", **kwargs: Any) -> Application:
        return build_application(self.root / name, **kwargs)

    def close(self) -> None:
        self._tmp.cleanup()


@contextmanager
def live_tool_calls() -> Iterator[Counter[str]]:
    """Count executions of the toy tools (what replay must keep at zero)."""
    counts: Counter[str] = Counter()

    def wrap(name: str, fn: Callable[..., Any]) -> Callable[..., Any]:
        def inner(*args: Any, **kwargs: Any) -> Any:
            counts[name] += 1
            return fn(*args, **kwargs)

        return inner

    with (
        patch.object(toy_agent, "search_policy", wrap("search_policy", toy_agent.search_policy)),
        patch.object(
            toy_agent, "get_exchange_rate", wrap("get_exchange_rate", toy_agent.get_exchange_rate)
        ),
        patch.object(
            toy_agent.SendEmail, "__call__", wrap("send_email", toy_agent.SendEmail.__call__)
        ),
    ):
        yield counts


def _tool_calls(app: Application, run_id: RunId) -> int:
    events = app.inspect_run.execute(run_id).events
    return sum(1 for e in events if e.event_type is EventType.TOOL_CALL)


def _replayed(app: Application, run_id: RunId) -> int:
    n = 0
    for e in app.inspect_run.execute(run_id).events:
        tag = e.payload.get("forked") if isinstance(e.payload, dict) else None
        if (
            e.event_type in (EventType.TOOL_RESULT, EventType.TOOL_ERROR)
            and isinstance(tag, dict)
            and tag.get("decision") == "replay"
        ):
            n += 1
    return n


def _occurrences(root: Path, needle: str) -> int:
    return sum(p.read_bytes().count(needle.encode()) for p in root.rglob("*") if p.is_file())


def _store_snapshot(app: Application, run_id: RunId) -> dict[str, bytes]:
    base = app.store_root / "runs" / run_id.value
    return {p.name: p.read_bytes() for p in sorted(base.iterdir())}


def _experiment(app: Application, outbox: Path) -> tuple[RunId, RunId]:
    parent = run_toy_agent(app.recorder, outbox)
    branch = run_toy_agent(
        app.recorder,
        outbox,
        session=app.recorder.branch(parent, CAPABILITIES, Intervention(RATE_CALL, 0.5)),
    )
    return parent, branch


# -- scenarios --------------------------------------------------------------------------


def s01_deterministic_toy(box: Sandbox) -> ScenarioResult:
    app, outbox = box.app(), box.root / "outbox"
    parent = run_toy_agent(app.recorder, outbox)
    with live_tool_calls() as live:
        replayed = run_toy_agent(
            app.recorder, outbox, session=app.recorder.replay(parent, CAPABILITIES)
        )
    recorded = _tool_calls(app, parent)
    fidelity = _replayed(app, replayed) / recorded
    same = (
        app.inspect_run.execute(parent).events[-1].payload
        == app.inspect_run.execute(replayed).events[-1].payload
    )
    report = app.inspect_run.execute(parent)
    metrics = {
        "replay_fidelity": fidelity,
        "capture_completeness": report.assessment.completeness.ratio,
        "outcome_identical": same,
        "live_tool_executions_during_replay": sum(live.values()),
    }
    ok = fidelity == 1.0 and same and not live and metrics["capture_completeness"] == 1.0
    return ScenarioResult(
        "S01",
        "Deterministic toy workflow with recorded tool calls",
        "pass" if ok else "fail",
        metrics,
    )


def s02_time_randomness(box: Sandbox) -> ScenarioResult:
    app = box.app()
    executed: list[str] = []

    def lookup(**kwargs: Any) -> str:
        executed.append("lookup")
        return "ok"

    def unrecorded(session: AbstractContextManager[RecordedRun], stamp: str) -> None:
        with session as run:  # nondeterminism enters from OUTSIDE any recorded tool
            run.call_tool("lookup", EffectClass.EXTERNAL_READ, lookup, stamp=stamp)

    def recorded(session: AbstractContextManager[RecordedRun]) -> RunId:
        with session as run:  # nondeterminism enters THROUGH a recorded tool
            stamp = run.call_tool("now", EffectClass.PURE_LOCAL, lambda: secrets.token_hex(4))
            run.call_tool("lookup", EffectClass.EXTERNAL_READ, lookup, stamp=stamp)
            return run.run_id

    with app.recorder.record(SYNTHETIC) as run:
        run.call_tool("lookup", EffectClass.EXTERNAL_READ, lookup, stamp="t1")
        source = run.run_id
    executed.clear()
    detected = False
    try:
        unrecorded(app.recorder.replay(source, SYNTHETIC), "t2")
    except ReplayDivergence:
        detected = True
    live_after_divergence = len(executed)

    base = recorded(app.recorder.record(SYNTHETIC))
    executed.clear()
    again = recorded(app.recorder.replay(base, SYNTHETIC))
    metrics = {
        "unrecorded_nondeterminism_detected": detected,
        "live_executions_after_divergence": live_after_divergence,
        "recorded_nondeterminism_replay_fidelity": _replayed(app, again) / _tool_calls(app, base),
        "live_executions_replaying_recorded_nondeterminism": len(executed),
    }
    ok = (
        detected
        and live_after_divergence == 0
        and metrics["recorded_nondeterminism_replay_fidelity"] == 1.0
        and not executed
    )
    return ScenarioResult(
        "S02",
        "Workflow with time/randomness dependency",
        "pass" if ok else "fail",
        metrics,
        notes=[
            "FORKED does not make nondeterministic code deterministic: it detects the divergence and fails closed."
        ],
    )


def s03_agent_external_read(box: Sandbox) -> ScenarioResult:
    try:
        from examples import pydantic_ai_expense_agent as agent
    except ImportError:
        return ScenarioResult(
            "S03",
            "Agent tool call with recorded external read",
            "skipped",
            notes=["pydantic-ai extra not installed"],
        )
    app, outbox = box.app(), box.root / "outbox"
    source = agent.run_expense_agent(app.recorder.record(agent.CAPABILITIES), outbox)
    with live_tool_calls() as live:
        replayed = agent.run_expense_agent(app.recorder.replay(source, agent.CAPABILITIES), outbox)
    metrics = {
        "framework": "pydantic-ai (scripted model, offline)",
        "replay_fidelity": _replayed(app, replayed) / _tool_calls(app, source),
        "external_read_live_calls_during_replay": live["get_exchange_rate"],
        "live_tool_executions_during_replay": sum(live.values()),
    }
    ok = metrics["replay_fidelity"] == 1.0 and not live
    return ScenarioResult(
        "S03",
        "Agent tool call with recorded external read",
        "pass" if ok else "fail",
        metrics,
        notes=[
            "The model is scripted; with a real LLM the replay re-asks the model and fails closed if it asks for different calls."
        ],
    )


def s04_external_write_in_replay(box: Sandbox) -> ScenarioResult:
    app, outbox = box.app(), box.root / "outbox"
    parent = run_toy_agent(app.recorder, outbox)
    written = len(list(outbox.iterdir()))
    with live_tool_calls() as live:
        run_toy_agent(app.recorder, outbox, session=app.recorder.replay(parent, CAPABILITIES))
        run_toy_agent(
            app.recorder,
            outbox,
            session=app.recorder.branch(parent, CAPABILITIES, Intervention(RATE_CALL, 0.5)),
        )
    attempted = 2  # the workflow requested send_email once in the replay and once in the branch
    executed = live["send_email"]
    extra_files = len(list(outbox.iterdir())) - written

    box_plain = box.root / "plain"
    box_plain.mkdir()
    log = baseline.PlainLog(box_plain / "calls.jsonl")
    plain_outbox = box_plain / "outbox"
    baseline.run_toy_with_plain_log(log, plain_outbox)
    baseline.naive_replay(log, plain_outbox)
    plain_sent = len(list(plain_outbox.iterdir()))

    metrics = {
        "unsafe_effect_attempts": attempted,
        "unsafe_effects_executed": executed,
        "unsafe_effect_prevention_rate": (attempted - executed) / attempted,
        "outbox_files_added_by_replay_and_branch": extra_files,
    }
    ok = executed == 0 and extra_files == 0
    return ScenarioResult(
        "S04",
        "Attempted external write during replay",
        "pass" if ok else "fail",
        metrics,
        baseline={
            "plain-log": {
                "replay_means": "re-running the workflow with real tools (no recorded observations)",
                "emails_sent_after_one_original_run_and_one_replay": plain_sent,
                "unsafe_effect_attempts": 1,
                "unsafe_effects_executed": plain_sent - 1,
                "unsafe_effect_prevention_rate": 1 - (plain_sent - 1),
            }
        },
    )


def s05_branch_intervention(box: Sandbox) -> ScenarioResult:
    app, outbox = box.app(), box.root / "outbox"
    parent = run_toy_agent(app.recorder, outbox)
    before = _store_snapshot(app, parent)
    branch = run_toy_agent(
        app.recorder,
        outbox,
        session=app.recorder.branch(parent, CAPABILITIES, Intervention(RATE_CALL, 0.5)),
    )
    result = app.compare_runs.execute(parent, branch)
    judged = [i for i in result.invariants if i.status.value in ("verified", "violated")]
    metrics = {
        "branch_isolation_parent_unchanged": _store_snapshot(app, parent) == before,
        "invariant_verification_rate": len(judged) / len(result.invariants),
        "invariants_verified": sum(i.status.value == "verified" for i in result.invariants),
        "outcome_fields_changed": len(result.outcome_changes),
        "claim_level": result.claim_level.value,
    }
    ok = (
        metrics["branch_isolation_parent_unchanged"]
        and metrics["invariant_verification_rate"] == 1.0
        and bool(result.outcome_changes)
    )
    return ScenarioResult(
        "S05",
        "Branch intervention changing one tool observation",
        "pass" if ok else "fail",
        metrics,
        baseline={
            "plain-log": {
                "applicable": False,
                "reason": "a plain log has no branches, interventions or invariants",
            }
        },
    )


def s06_missing_event(box: Sandbox) -> ScenarioResult:
    app, outbox = box.app(), box.root / "outbox"
    parent = run_toy_agent(app.recorder, outbox)
    log_path = app.store_root / "runs" / parent.value / "events.jsonl"
    lines = log_path.read_text(encoding="utf-8").splitlines(keepends=True)
    log_path.write_text("".join(lines[:4] + lines[5:]), encoding="utf-8")  # drop one tool.result

    report = app.inspect_run.execute(parent)
    failed_closed = False
    with live_tool_calls() as live:
        try:
            run_toy_agent(app.recorder, outbox, session=app.recorder.replay(parent, CAPABILITIES))
        except MissingObservation:
            failed_closed = True

    plain = baseline.PlainLog(box.root / "plain.jsonl")
    baseline.run_toy_with_plain_log(plain, box.root / "plain-outbox")
    metrics = {
        "gap_detected_by_inspect": bool(report.assessment.sequence.gaps),
        "sequence_marked_invalid": not report.assessment.sequence.is_valid,
        "missing_evidence_reported": bool(report.assessment.missing_evidence),
        "replay_failed_closed": failed_closed,
        "live_tool_executions_after_missing_event": sum(live.values()),
    }
    ok = (
        metrics["gap_detected_by_inspect"]
        and metrics["sequence_marked_invalid"]
        and metrics["missing_evidence_reported"]
        and failed_closed
        and not live
    )
    return ScenarioResult(
        "S06",
        "Missing event in the recording",
        "pass" if ok else "fail",
        metrics,
        baseline={"plain-log": {"missing_line_detected": baseline.can_detect_missing_line(plain)}},
    )


class _Probe:
    def __init__(self, python_version: str) -> None:
        self._python = python_version

    def fingerprint(self, capabilities: AdapterCapabilities) -> EnvironmentFingerprint:
        return EnvironmentFingerprint.of(
            {
                "python_version": self._python,
                "platform": "fcrb",
                "forked_version": "fcrb",
                "adapter": capabilities.name,
                "adapter_version": capabilities.version,
            }
        )


def s07_environment_mismatch(box: Sandbox) -> ScenarioResult:
    outbox = box.root / "outbox"
    older, newer = box.app(probe=_Probe("3.11.0")), box.app(probe=_Probe("3.12.0"))  # same store
    parent = run_toy_agent(older.recorder, outbox)
    branch = run_toy_agent(
        newer.recorder,
        outbox,
        session=newer.recorder.branch(parent, CAPABILITIES, Intervention(RATE_CALL, 0.5)),
    )
    result = newer.compare_runs.execute(parent, branch)
    env = next(i for i in result.invariants if i.id == "inv_same_environment")
    metrics = {
        "environment_mismatch_detected": env.status.value == "violated",
        "invariant_status": env.status.value,
        "claim_level": result.claim_level.value,
        "claim_downgraded_to_observational": result.claim_level.value == "observational",
    }
    ok = metrics["environment_mismatch_detected"] and metrics["claim_downgraded_to_observational"]
    return ScenarioResult("S07", "Environment version mismatch", "pass" if ok else "fail", metrics)


def s08_tampered_evidence(box: Sandbox) -> ScenarioResult:
    app, outbox = box.app(), box.root / "outbox"
    parent, branch = _experiment(app, outbox)
    pristine = box.root / "pkg"
    app.export_evidence(parent, branch, pristine)
    shutil.rmtree(app.store_root)  # verification must need nothing but the package
    clean = verify_package(pristine)
    manifest = json.loads((pristine / "manifest.json").read_text(encoding="utf-8"))

    flipped = box.root / "pkg-flip"
    shutil.copytree(pristine, flipped)
    log = sorted(flipped.glob("runs/*/events.jsonl"))[0]
    log.write_bytes(log.read_bytes().replace(b"currency conversion", b"currency CONVERSION"))
    flip = verify_package(flipped)

    forged = box.root / "pkg-forged"
    shutil.copytree(pristine, forged)
    comparison = json.loads((forged / "comparison.json").read_text(encoding="utf-8"))
    comparison["statement"] = "Causal effect demonstrated."
    (forged / "comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    from forked.domain.evidence.package import sha256

    forged_manifest = json.loads((forged / "manifest.json").read_text(encoding="utf-8"))
    for entry in forged_manifest["artifacts"]:
        data = (forged / entry["path"]).read_bytes()
        entry["sha256"], entry["bytes"] = sha256(data), len(data)
    (forged / "manifest.json").write_text(json.dumps(forged_manifest, indent=2), encoding="utf-8")
    forge = verify_package(forged)

    plain = baseline.PlainLog(box.root / "plain.jsonl")
    baseline.run_toy_with_plain_log(plain, box.root / "plain-outbox")
    metrics = {
        "evidence_completeness": sum(f in manifest for f in REQUIRED_MANIFEST_FIELDS)
        / len(REQUIRED_MANIFEST_FIELDS),
        "pristine_package_verifies_without_store": clean.ok,
        "byte_tampering_detected_by_integrity": not flip.integrity.ok,
        "rehashed_forgery_passes_integrity": forge.integrity.ok,
        "rehashed_forgery_detected_by_validity": bool(forge.validity.problems),
    }
    ok = all(
        [
            metrics["evidence_completeness"] == 1.0,
            clean.ok,
            metrics["byte_tampering_detected_by_integrity"],
            metrics["rehashed_forgery_detected_by_validity"],
            not forge.ok,
        ]
    )
    return ScenarioResult(
        "S08",
        "Tampered evidence artifact",
        "pass" if ok else "fail",
        metrics,
        baseline={"plain-log": {"tampering_detected": baseline.can_detect_tampering(plain)}},
        notes=[
            "Integrity and validity are separate questions; a forgery with fixed hashes passes the first and fails the second.",
            "Verified in a clean directory after deleting the store; a separate machine was not tested.",
        ],
    )


FAKE_KEY = "sk-fcrb-0000000000000000000test"  # fake credential shape
FAKE_TOKEN = "ghp_" + "a" * 36  # fake
FAKE_PASSWORD = "hunter2-fcrb"  # noqa: S105 - fake value, caught by key name


def s09_redaction(box: Sandbox) -> ScenarioResult:
    app, outbox = box.app(), box.root / "outbox"
    parent, branch = _experiment(app, outbox)

    def boom(**_: Any) -> None:
        raise PermissionError(f"auth failed for {FAKE_TOKEN}")

    try:
        with app.recorder.record(SYNTHETIC) as run:
            run.call_tool(
                "fail", EffectClass.EXTERNAL_READ, boom, password=FAKE_PASSWORD, key=FAKE_KEY
            )
    except PermissionError:
        pass
    package = box.root / "pkg"
    app.export_evidence(parent, branch, package)
    trace_text = "".join(
        json.dumps(app.export_trace.execute(r.run_id, include_payloads=True))
        for r in app.list_runs.execute()
    )
    secrets_all = (toy_agent.DEMO_API_KEY, FAKE_KEY, FAKE_TOKEN, FAKE_PASSWORD)
    store_hits = {s: _occurrences(app.store_root, s) for s in secrets_all}
    package_hits = sum(_occurrences(package, s) for s in secrets_all)
    trace_hits = sum(trace_text.count(s) for s in secrets_all)

    plain_dir = box.root / "plain"
    plain_dir.mkdir()
    plain = baseline.PlainLog(plain_dir / "calls.jsonl")
    baseline.run_toy_with_plain_log(plain, plain_dir / "outbox")
    metrics = {
        "secret_values_tested": len(secrets_all),
        "secret_occurrences_in_store": sum(store_hits.values()),
        "secret_occurrences_in_evidence_package": package_hits,
        "secret_occurrences_in_otel_export_with_payloads": trace_hits,
    }
    ok = not (metrics["secret_occurrences_in_store"] or package_hits or trace_hits)
    return ScenarioResult(
        "S09",
        "Sensitive field redaction",
        "pass" if ok else "fail",
        metrics,
        baseline={
            "plain-log": {
                "secret_occurrences_in_log": _occurrences(plain_dir, toy_agent.DEMO_API_KEY)
            }
        },
        notes=[
            "Covers a secret in a tool argument, in a key named password, and in an exception message."
        ],
    )


def s10_two_adapters(box: Sandbox) -> ScenarioResult:
    try:
        from examples import pydantic_ai_expense_agent as agent
    except ImportError:
        return ScenarioResult(
            "S10",
            "Two adapters producing equivalent protocol artifacts",
            "skipped",
            notes=["pydantic-ai extra not installed"],
        )
    app = box.app()
    sdk = run_toy_agent(app.recorder, box.root / "outbox-sdk")
    framework = agent.run_expense_agent(
        app.recorder.record(agent.CAPABILITIES), box.root / "outbox-fw"
    )
    a = normalized_tool_events(app.inspect_run.execute(sdk).events)
    b = normalized_tool_events(app.inspect_run.execute(framework).events)
    metrics = {
        "adapters": ["forked-sdk (toy agent)", "forked-pydantic-ai"],
        "tool_events_compared": len(a),
        "artifacts_equivalent": a == b,
    }
    return ScenarioResult(
        "S10",
        "Two adapters producing equivalent protocol artifacts",
        "pass" if a == b and a else "fail",
        metrics,
        notes=[
            "Equivalence is over tool events (names, effect classes, payloads, capture status); adapter metadata legitimately differs."
        ],
    )


SCENARIOS: tuple[Callable[[Sandbox], ScenarioResult], ...] = (
    s01_deterministic_toy,
    s02_time_randomness,
    s03_agent_external_read,
    s04_external_write_in_replay,
    s05_branch_intervention,
    s06_missing_event,
    s07_environment_mismatch,
    s08_tampered_evidence,
    s09_redaction,
    s10_two_adapters,
)
