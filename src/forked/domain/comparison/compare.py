"""Compare a baseline run with a branch of it (UC-04).

Rules (CLAUDE.md, CIP §6.6 and §6.7, ADR-003):

* every invariant ends ``verified``, ``violated`` or ``unknown``; missing evidence is
  ``unknown``, never ``verified``;
* the claim level is ``controlled_comparison`` only when every invariant is verified
  and the branch completed; otherwise ``observational``. This module never produces a
  causal claim: a single run pair cannot support one;
* no confidence score is computed.
"""

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum

from forked.domain.branches.branch import log_digest
from forked.domain.effects.effect_class import EffectClass
from forked.domain.effects.policy import Decision
from forked.domain.runs.completeness import RunAssessment
from forked.domain.runs.event import Event, EventType
from forked.domain.runs.run import RunSnapshot, RunStatus
from forked.domain.shared.canonical import JsonValue
from forked.domain.shared.errors import DomainError
from forked.domain.shared.schema import EVENT_SCHEMA_VERSION


class NotABranch(DomainError):
    code = "not_a_branch"


class InvariantStatus(StrEnum):
    VERIFIED = "verified"
    VIOLATED = "violated"
    UNKNOWN = "unknown"


class ClaimLevel(StrEnum):
    OBSERVATIONAL = "observational"
    CONTROLLED_COMPARISON = "controlled_comparison"
    CONDITIONAL_CAUSAL = "conditional_causal"  # never produced here
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class InvariantResult:
    id: str
    description: str
    verification: str
    status: InvariantStatus
    evidence: str


@dataclass(frozen=True, slots=True)
class RunEvidence:
    snapshot: RunSnapshot
    events: tuple[Event, ...]
    assessment: RunAssessment


@dataclass(frozen=True, slots=True)
class Step:
    index: int
    tool: str | None
    baseline: JsonValue
    branch: JsonValue
    decision: str
    status: str  # same | changed | only_baseline | only_branch


@dataclass(frozen=True, slots=True)
class Comparison:
    baseline_id: str
    branch_id: str
    branch_status: RunStatus
    intervention: JsonValue
    steps: tuple[Step, ...]
    outcome_changes: tuple[tuple[str, JsonValue, JsonValue], ...]
    invariants: tuple[InvariantResult, ...]
    claim_level: ClaimLevel
    statement: str
    missing_evidence: tuple[str, ...]

    def as_dict(self) -> dict[str, JsonValue]:
        return {
            "cip_version": EVENT_SCHEMA_VERSION,
            "baseline": self.baseline_id,
            "branch": self.branch_id,
            "branch_status": self.branch_status.value,
            "intervention": self.intervention,
            "steps": [asdict(s) for s in self.steps],
            "outcome_changes": [
                {"field": k, "baseline": a, "branch": b} for k, a, b in self.outcome_changes
            ],
            "invariants": [{**asdict(i), "status": i.status.value} for i in self.invariants],
            "claim_level": self.claim_level.value,
            "statement": self.statement,
            "missing_evidence": list(self.missing_evidence),
        }


def _forked(payload: JsonValue) -> dict[str, JsonValue]:
    tag = payload.get("forked") if isinstance(payload, dict) else None
    return tag if isinstance(tag, dict) else {}


StepData = tuple[str | None, JsonValue, str, EffectClass | None]
_OUTCOMES = (EventType.TOOL_RESULT, EventType.TOOL_ERROR)


def _steps(events: Sequence[Event]) -> list[StepData]:
    """(tool, output or error body, decision, effect class) per tool call, in order."""
    outcomes = {e.parent_event_id: e for e in events if e.event_type in _OUTCOMES}
    steps: list[StepData] = []
    for call in (e for e in events if e.event_type is EventType.TOOL_CALL):
        out = outcomes.get(call.event_id)
        if out is None:
            steps.append((call.tool_name, None, "no outcome recorded", call.effect_class))
            continue
        body = dict(out.payload) if isinstance(out.payload, dict) else {}
        decision = str(_forked(out.payload).get("decision", "executed"))
        body.pop("forked", None)
        value: JsonValue = body.get("output") if out.event_type is EventType.TOOL_RESULT else body
        steps.append((call.tool_name, value, decision, call.effect_class))
    return steps


def _completed_payload(events: Sequence[Event]) -> dict[str, JsonValue] | None:
    last = events[-1] if events else None
    if last is None or last.event_type is not EventType.RUN_COMPLETED:
        return None
    return last.payload if isinstance(last.payload, dict) else {"value": last.payload}


def _invariants(
    base: RunEvidence, branch: RunEvidence, lineage: dict[str, JsonValue]
) -> list[InvariantResult]:
    ok, bad, unk = InvariantStatus.VERIFIED, InvariantStatus.VIOLATED, InvariantStatus.UNKNOWN
    results = []
    finalized = (
        branch.assessment.effective_status in (RunStatus.COMPLETED, RunStatus.FAILED)
        and branch.assessment.sequence.is_valid
    )

    stored, current = lineage.get("parent_log_digest"), log_digest(base.events)
    status = unk if not isinstance(stored, str) else (ok if stored == current else bad)
    results.append(
        InvariantResult(
            "inv_parent_unchanged",
            "parent run log is unchanged since the branch was created",
            "content_digest",
            status,
            f"branch run.started parent_log_digest={stored}; current={current}",
        )
    )

    steps = _steps(branch.events)
    at = next((i for i, s in enumerate(steps) if s[2] == Decision.INTERVENE), None)
    if not finalized or at is None:
        status, why = unk, "branch not finalized or intervention never applied"
    elif all(s[2] == Decision.REPLAY for s in steps[:at]):
        status, why = ok, f"{at} call(s) before the checkpoint answered from the recording"
    else:
        status, why = bad, "a call before the checkpoint was not answered from the recording"
    results.append(
        InvariantResult(
            "inv_prefix_replayed",
            "every call before the checkpoint was answered from the parent recording",
            "event_inspection",
            status,
            why,
        )
    )

    live = [
        s
        for s in steps
        if s[2] not in (Decision.REPLAY, Decision.INTERVENE, Decision.DENY)
        and not (s[2] == Decision.ALLOW and s[3] is EffectClass.PURE_LOCAL)
    ]
    status = unk if not finalized else (bad if live else ok)
    results.append(
        InvariantResult(
            "inv_no_live_side_effects",
            "no tool other than a declared pure_local one executed live in the branch",
            "event_inspection",
            status,
            "branch not finalized" if not finalized else f"{len(live)} live non-pure_local call(s)",
        )
    )

    a, b = base.snapshot.environment, branch.snapshot.environment
    if a.missing() or b.missing():
        status, why = unk, f"facts not captured: {sorted(set(a.missing()) | set(b.missing()))}"
    else:
        diff = sorted(k for k, v in a.as_dict().items() if b.as_dict().get(k) != v)
        status, why = (bad, f"differs: {diff}") if diff else (ok, "all captured facts equal")
    results.append(
        InvariantResult(
            "inv_same_environment",
            "baseline and branch ran with the same captured environment facts",
            "environment_fingerprint",
            status,
            why,
        )
    )

    ca, cb = base.snapshot.capabilities, branch.snapshot.capabilities
    same = (ca.name, ca.version) == (cb.name, cb.version)
    results.append(
        InvariantResult(
            "inv_same_adapter",
            "baseline and branch were produced by the same adapter version",
            "adapter_metadata",
            ok if same else bad,
            f"{ca.name} {ca.version} vs {cb.name} {cb.version}",
        )
    )
    return results


def compare(base: RunEvidence, branch: RunEvidence) -> Comparison:
    first = branch.events[0] if branch.events else None
    lineage = first.payload if first and isinstance(first.payload, dict) else {}
    if lineage.get("branch_of") != base.snapshot.run_id.value:
        raise NotABranch(
            f"{branch.snapshot.run_id} is not a recorded branch of {base.snapshot.run_id}"
        )

    a, b = _steps(base.events), _steps(branch.events)
    steps = []
    for i in range(max(len(a), len(b))):
        sa, sb = (a[i] if i < len(a) else None), (b[i] if i < len(b) else None)
        if sa is None or sb is None:
            status = "only_branch" if sa is None else "only_baseline"
        else:
            status = "same" if (sa[0], sa[1]) == (sb[0], sb[1]) else "changed"
        ref = sb or sa
        steps.append(
            Step(
                i + 1,
                ref[0] if ref else None,
                sa[1] if sa else None,
                sb[1] if sb else None,
                sb[2] if sb else "-",
                status,
            )
        )

    before, after = _completed_payload(base.events), _completed_payload(branch.events)
    changes: list[tuple[str, JsonValue, JsonValue]] = []
    if before is not None and after is not None:
        changes = [
            (k, before.get(k), after.get(k))
            for k in sorted(before.keys() | after.keys())
            if before.get(k) != after.get(k)
        ]

    invariants = _invariants(base, branch, lineage)
    unverified = [r.id for r in invariants if r.status is not InvariantStatus.VERIFIED]
    controlled = not unverified and branch.assessment.effective_status is RunStatus.COMPLETED
    changed = ", ".join(k for k, _, _ in changes) or "nothing"
    if controlled:
        level = ClaimLevel.CONTROLLED_COMPARISON
        statement = (
            f"Observed with all {len(invariants)} invariants verified: after the intervention, "
            f"outcome fields changed: {changed}. This describes one recorded run pair; it is "
            "not a causal estimate."
        )
    else:
        level = ClaimLevel.OBSERVATIONAL
        statement = (
            f"Observed differences only (outcome fields changed: {changed}). Not a controlled "
            f"comparison: unverified invariants {unverified or '-'}, branch status "
            f"{branch.assessment.effective_status}."
        )

    missing = tuple(f"baseline: {m}" for m in base.assessment.missing_evidence) + tuple(
        f"branch: {m}" for m in branch.assessment.missing_evidence
    )
    if before is None or after is None:
        missing += ("outcome not comparable: a run has no run.completed event",)
    return Comparison(
        baseline_id=base.snapshot.run_id.value,
        branch_id=branch.snapshot.run_id.value,
        branch_status=branch.assessment.effective_status,
        intervention=lineage.get("intervention"),
        steps=tuple(steps),
        outcome_changes=tuple(changes),
        invariants=tuple(invariants),
        claim_level=level,
        statement=statement,
        missing_evidence=missing,
    )
