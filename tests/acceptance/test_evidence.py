"""UC-05 acceptance: export an evidence package and verify it offline."""

import json
import os
import shutil
from pathlib import Path

import pytest

from forked.application.errors import StorageFailure
from forked.bootstrap.container import Application, verify_package
from forked.demo.toy_agent import CAPABILITIES, run_toy_agent
from forked.domain.branches.branch import Intervention
from forked.domain.comparison.compare import NotABranch
from forked.domain.evidence.package import (
    MANIFEST,
    SecretInPackage,
    UnsafePackagePath,
    build_package,
    sha256,
)
from forked.domain.runs.redaction import RedactionPolicy
from forked.domain.shared.identifiers import RunId


def _experiment(app: Application, tmp_path: Path) -> tuple[RunId, RunId]:
    parent = run_toy_agent(app.recorder, tmp_path / "outbox")
    branch = run_toy_agent(
        app.recorder,
        tmp_path / "outbox",
        session=app.recorder.branch(parent, CAPABILITIES, Intervention(3, 0.5)),
    )
    return parent, branch


@pytest.fixture
def package(app: Application, tmp_path: Path) -> Path:
    parent, branch = _experiment(app, tmp_path)
    out = tmp_path / "pkg"
    app.export_evidence(parent, branch, out)
    return out


def _manifest(pkg: Path) -> dict:  # type: ignore[type-arg]
    return json.loads((pkg / MANIFEST).read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def _rewrite_manifest(pkg: Path, manifest: dict) -> None:  # type: ignore[type-arg]
    (pkg / MANIFEST).write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _events(pkg: Path) -> Path:
    return sorted(pkg.glob("runs/*/events.jsonl"))[0]


def test_exported_package_verifies_without_the_store(app: Application, package: Path) -> None:
    shutil.rmtree(app.store_root)  # verification needs nothing but the package

    report = verify_package(package)

    assert report.ok
    assert report.integrity.ok
    assert report.validity.claim_level == "controlled_comparison"
    assert dict(report.validity.invariants)["inv_parent_unchanged"] == "verified"
    manifest = _manifest(package)
    assert set(
        manifest
    ) == {  # forked-evidence/1 schema: contexto/protocolo/paquete-de-evidencia.md
        "package_format",
        "cip_version",
        "experiment",
        "environment",
        "invariants",
        "claim",
        "limitations",
        "missing_evidence",
        "artifacts",
    }
    assert set(manifest["experiment"]) == {"baseline", "branch", "intervention", "effects_policy"}
    assert set(manifest["artifacts"][0]) == {"path", "sha256", "bytes"}
    assert manifest["package_format"] == "forked-evidence/1"
    assert manifest["experiment"]["intervention"]["operation"] == "replace_recorded_observation"
    assert manifest["experiment"]["effects_policy"] == "default-deny/1"
    assert {a["path"] for a in manifest["artifacts"]} == {
        p.relative_to(package).as_posix() for p in package.rglob("*") if p.is_file()
    } - {MANIFEST}
    assert any("not signed" in item for item in manifest["limitations"])


def test_export_is_deterministic(app: Application, tmp_path: Path) -> None:
    parent, branch = _experiment(app, tmp_path)
    one = app.export_evidence(parent, branch, tmp_path / "one")
    two = app.export_evidence(parent, branch, tmp_path / "two")
    assert one == two


def test_changed_artifact_fails_integrity_and_skips_validity(package: Path) -> None:
    log = _events(package)
    log.write_bytes(log.read_bytes().replace(b"currency conversion", b"currency CONVERSION"))

    report = verify_package(package)

    assert not report.ok
    assert report.integrity.changed == (log.relative_to(package).as_posix(),)
    assert not report.validity.evaluated


def test_missing_and_unexpected_files_are_reported(package: Path) -> None:
    (package / "comparison.json").unlink()
    (package / "notes.txt").write_text("planted", encoding="utf-8")

    report = verify_package(package)

    assert report.integrity.missing == ("comparison.json",)
    assert report.integrity.unexpected == ("notes.txt",)
    assert not report.ok


def test_inflated_claim_with_intact_hashes_is_unsupported(package: Path) -> None:
    manifest = _manifest(package)
    manifest["claim"]["level"] = "conditional_causal"
    _rewrite_manifest(package, manifest)

    report = verify_package(package)

    assert report.integrity.ok  # hashes say nothing about claims
    assert not report.ok
    assert any("causal claim" in p for p in report.validity.problems)


def test_rehashed_tampering_is_caught_by_recomputation(package: Path) -> None:
    """An attacker edits the parent log AND fixes its hash: integrity passes, claims do not."""
    original_digest = verify_package(package).integrity.package_digest
    log = _events(package)  # first run sorted is not necessarily the parent: tamper both
    manifest = _manifest(package)
    for path in package.glob("runs/*/events.jsonl"):
        path.write_bytes(path.read_bytes().replace(b"currency conversion", b"currency CONVERSION"))
    for entry in manifest["artifacts"]:
        data = (package / entry["path"]).read_bytes()
        entry["sha256"], entry["bytes"] = sha256(data), len(data)
    _rewrite_manifest(package, manifest)

    report = verify_package(package)

    assert log.exists()
    assert report.integrity.ok
    assert report.integrity.package_digest != original_digest  # detectable out of band
    assert not report.ok
    assert report.validity.claim_level == "observational"
    assert any("inv_parent_unchanged" in p and "unsupported" in p for p in report.validity.problems)


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (lambda m: m.update(package_format="other/9"), "unsupported package_format"),
        (lambda m: m.update(cip_version="9.0.0"), "major version 9"),
        (
            lambda m: m["artifacts"].append({"path": "../escape", "sha256": "x", "bytes": 1}),
            "unsafe",
        ),
        (lambda m: m["artifacts"].append(m["artifacts"][0]), "listed twice"),
        (lambda m: m.update(artifacts=[]), "no artifacts"),
    ],
)
def test_bad_manifest_fails_integrity(package: Path, mutate, expected: str) -> None:
    manifest = _manifest(package)
    mutate(manifest)
    _rewrite_manifest(package, manifest)
    report = verify_package(package)
    assert not report.integrity.ok
    assert any(expected in p for p in report.integrity.problems)


def test_unparseable_or_missing_manifest(package: Path) -> None:
    (package / MANIFEST).write_text("{not json", encoding="utf-8")
    assert "not valid JSON" in verify_package(package).integrity.problems[0]
    (package / MANIFEST).unlink()
    assert verify_package(package).integrity.problems == ("manifest.json is missing",)


def test_symlink_in_package_is_rejected(package: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("x", encoding="utf-8")
    try:
        os.symlink(outside, package / "link.txt")
    except OSError:
        pytest.skip("symlinks not permitted on this system")
    with pytest.raises(UnsafePackagePath):
        verify_package(package)


def test_export_refuses_non_empty_target(app: Application, tmp_path: Path) -> None:
    parent, branch = _experiment(app, tmp_path)
    target = tmp_path / "busy"
    target.mkdir()
    (target / "keep.txt").write_text("mine", encoding="utf-8")
    with pytest.raises(StorageFailure, match="non-empty"):
        app.export_evidence(parent, branch, target)
    assert (target / "keep.txt").read_text(encoding="utf-8") == "mine"


def test_export_requires_a_branch_of_the_baseline(app: Application, tmp_path: Path) -> None:
    one = run_toy_agent(app.recorder, tmp_path / "outbox")
    two = run_toy_agent(app.recorder, tmp_path / "outbox")
    with pytest.raises(NotABranch):
        app.export_evidence(one, two, tmp_path / "pkg")
    assert not (tmp_path / "pkg").exists()


def test_credential_shaped_value_blocks_export() -> None:
    leaked = b'{"payload": "token sk-live-abcdefghijklmnopqrstuvwxyz"}\n'
    with pytest.raises(SecretInPackage):
        build_package({"runs/run_x/events.jsonl": leaked}, {}, RedactionPolicy())


@pytest.mark.parametrize("path", ["../x", "/abs", "a/../b", "a\\b", "C:/x", "./a", MANIFEST])
def test_unsafe_artifact_paths_are_refused(path: str) -> None:
    with pytest.raises(UnsafePackagePath):
        build_package({path: b"x"}, {}, RedactionPolicy())
