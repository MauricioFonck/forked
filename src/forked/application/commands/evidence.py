"""Use cases UC-05: export an evidence package, verify one offline.

Package layout (``forked-evidence/1``)::

    manifest.json              experiment, environment, policy, invariants, claim,
                               limitations, missing evidence, SHA-256 of every artifact
    comparison.json            full baseline-vs-branch comparison
    runs/<id>/events.jsonl     byte-for-byte copies from the store
    runs/<id>/run.json

The layout of ``runs/`` matches the store's, so the verifier can recompute the comparison
by opening the package itself as a read-only store.
"""

from dataclasses import dataclass

from forked.application.ports import ArtifactReader
from forked.application.queries.inspect_run import CompareRuns, InspectRun
from forked.domain.comparison.compare import Comparison
from forked.domain.evidence.package import (
    VALIDITY_NOTE,
    Integrity,
    build_package,
    check_claims,
    check_integrity,
    comparison_bytes,
)
from forked.domain.runs.redaction import RedactionPolicy
from forked.domain.shared.canonical import JsonValue
from forked.domain.shared.errors import ForkedError
from forked.domain.shared.identifiers import RunId

FORKED_LIMITATIONS = (
    "the manifest is not signed: hashes prove the files match it, not who produced them",
    "the comparison covers one recorded run pair; it is not a causal estimate",
    "only tool calls made through the FORKED SDK are observed",
)


class ExportEvidence:
    def __init__(
        self,
        inspect: InspectRun,
        compare: CompareRuns,
        reader: ArtifactReader,
        policy: RedactionPolicy,
    ) -> None:
        self._inspect = inspect
        self._compare = compare
        self._reader = reader
        self._policy = policy

    def execute(self, baseline: RunId, branch: RunId) -> dict[str, bytes]:
        comparison = self._compare.execute(baseline, branch)  # raises NotABranch
        reports = [self._inspect.execute(run_id) for run_id in (baseline, branch)]
        started = reports[1].events[0].payload
        lineage = started if isinstance(started, dict) else {}

        artifacts = {
            f"runs/{run_id.value}/{name}": data
            for run_id in (baseline, branch)
            for name, data in self._reader.raw_files(run_id).items()
        }
        artifacts["comparison.json"] = comparison_bytes(comparison)

        adapter_limits = [x for r in reports for x in r.snapshot.capabilities.limitations]
        limitations: list[JsonValue] = list(dict.fromkeys([*adapter_limits, *FORKED_LIMITATIONS]))
        env: list[dict[str, JsonValue]] = [
            {k: v for k, v in r.snapshot.environment.as_dict().items()} for r in reports
        ]
        meta: dict[str, JsonValue] = {
            "experiment": {
                "baseline": baseline.value,
                "branch": branch.value,
                "intervention": comparison.intervention,
                "effects_policy": lineage.get("effect_policy"),
            },
            "environment": {
                "baseline": env[0],
                "branch": env[1],
            },
            "invariants": [
                {"id": i.id, "verification": i.verification, "status": i.status.value}
                for i in comparison.invariants
            ],
            "claim": {"level": comparison.claim_level.value, "statement": comparison.statement},
            "limitations": limitations,
            "missing_evidence": list(comparison.missing_evidence),
        }
        return build_package(artifacts, meta, self._policy)


@dataclass(frozen=True, slots=True)
class Validity:
    evaluated: bool
    claim_level: str | None
    invariants: tuple[tuple[str, str], ...]
    problems: tuple[str, ...]
    note: str = VALIDITY_NOTE


@dataclass(frozen=True, slots=True)
class VerificationReport:
    integrity: Integrity
    validity: Validity

    @property
    def ok(self) -> bool:
        return self.integrity.ok and self.validity.evaluated and not self.validity.problems


def verify_evidence(files: dict[str, bytes], compare: CompareRuns) -> VerificationReport:
    """``compare`` must read from the package itself (see the module docstring)."""
    integrity = check_integrity(files)
    if not integrity.ok or integrity.manifest is None:
        skipped = Validity(False, None, (), ("not evaluated: integrity check failed",))
        return VerificationReport(integrity, skipped)

    experiment = integrity.manifest.get("experiment")
    ids = experiment if isinstance(experiment, dict) else {}
    try:
        recomputed: Comparison = compare.execute(
            RunId(str(ids.get("baseline"))), RunId(str(ids.get("branch")))
        )
    except ForkedError as exc:
        failed = Validity(True, None, (), (f"cannot recompute comparison: {exc}",))
        return VerificationReport(integrity, failed)
    return VerificationReport(
        integrity,
        Validity(
            evaluated=True,
            claim_level=recomputed.claim_level.value,
            invariants=tuple((i.id, i.status.value) for i in recomputed.invariants),
            problems=check_claims(integrity.manifest, recomputed),
        ),
    )
