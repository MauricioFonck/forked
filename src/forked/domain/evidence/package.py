"""Evidence package: deterministic manifest, integrity check and claim check (UC-05, ADR-012).

Two separate questions, never merged into one verdict:

* **integrity** — do the files match the manifest? (SHA-256 + size of every artifact,
  nothing missing, nothing extra). This says nothing about the experiment's quality.
* **validity** — do the manifest's claims follow from the packaged evidence? Checked by
  recomputing the comparison; a claim stronger than the evidence is ``unsupported``.

Limitation: the manifest is not signed. Integrity shows internal consistency; whoever
can rewrite the files can rewrite the manifest. Compare ``package_digest`` with a copy
obtained through another channel to detect that.
"""

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass

from forked.domain.comparison.compare import ClaimLevel, Comparison, InvariantStatus
from forked.domain.runs.redaction import RedactionPolicy
from forked.domain.shared.canonical import JsonValue
from forked.domain.shared.errors import DomainError, UnsupportedSchemaVersion
from forked.domain.shared.schema import EVENT_SCHEMA_VERSION, ensure_supported

PACKAGE_FORMAT = "forked-evidence/1"
MANIFEST = "manifest.json"
VALIDITY_NOTE = (
    "Hash integrity shows the files match the manifest. It does not show that the "
    "experiment was well designed, that its invariants were sufficient, or that any "
    "difference is causal."
)

_SAFE_PATH = re.compile(r"[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+)*")


class UnsafePackagePath(DomainError):
    code = "unsafe_package_path"


class SecretInPackage(DomainError):
    code = "secret_in_package"


def sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def is_safe_path(path: str) -> bool:
    """Relative POSIX path, no ``..``/``.`` parts, no drive, no backslash, plain characters."""
    return bool(_SAFE_PATH.fullmatch(path)) and not any(
        part in (".", "..") for part in path.split("/")
    )


def _dump(value: JsonValue) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def build_package(
    artifacts: Mapping[str, bytes], meta: Mapping[str, JsonValue], policy: RedactionPolicy
) -> dict[str, bytes]:
    """Return every file of the package, ``manifest.json`` included. Same input, same bytes."""
    for path, data in artifacts.items():
        if not is_safe_path(path) or path == MANIFEST:
            raise UnsafePackagePath(f"refusing artifact path {path!r}")
        if policy.looks_like_secret(data.decode("utf-8", errors="replace")):
            raise SecretInPackage(f"{path} contains a value shaped like a credential; not exported")
    entries: list[JsonValue] = [
        {"path": path, "sha256": sha256(data), "bytes": len(data)}
        for path, data in sorted(artifacts.items())
    ]
    manifest: dict[str, JsonValue] = {
        **meta,
        "package_format": PACKAGE_FORMAT,
        "cip_version": EVENT_SCHEMA_VERSION,
        "artifacts": entries,
    }
    return {**artifacts, MANIFEST: _dump(manifest)}


def comparison_bytes(comparison: Comparison) -> bytes:
    return _dump(comparison.as_dict())


@dataclass(frozen=True, slots=True)
class Integrity:
    ok: bool
    package_digest: str | None
    changed: tuple[str, ...]
    missing: tuple[str, ...]
    unexpected: tuple[str, ...]
    problems: tuple[str, ...]
    manifest: dict[str, JsonValue] | None


def check_integrity(files: Mapping[str, bytes]) -> Integrity:
    raw = files.get(MANIFEST)
    problems: list[str] = []
    changed: list[str] = []
    missing: list[str] = []
    listed: set[str] = set()
    manifest: dict[str, JsonValue] | None = None

    if raw is None:
        problems.append("manifest.json is missing")
    else:
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            parsed = None
            problems.append(f"manifest.json is not valid JSON: {exc}")
        if parsed is not None and not isinstance(parsed, dict):
            problems.append("manifest.json is not a JSON object")
        elif isinstance(parsed, dict):
            manifest = parsed

    if manifest is not None:
        if manifest.get("package_format") != PACKAGE_FORMAT:
            problems.append(f"unsupported package_format {manifest.get('package_format')!r}")
        try:
            ensure_supported(str(manifest.get("cip_version")))
        except UnsupportedSchemaVersion as exc:
            problems.append(str(exc))
        entries = manifest.get("artifacts")
        if not isinstance(entries, list) or not entries:
            problems.append("manifest lists no artifacts")
            entries = []
        for entry in entries:
            if not (
                isinstance(entry, dict)
                and isinstance(entry.get("path"), str)
                and isinstance(entry.get("sha256"), str)
                and isinstance(entry.get("bytes"), int)
            ):
                problems.append(f"malformed artifact entry: {entry!r}")
                continue
            path = str(entry["path"])
            if not is_safe_path(path) or path == MANIFEST:
                problems.append(f"unsafe artifact path in manifest: {path!r}")
                continue
            if path in listed:
                problems.append(f"artifact listed twice: {path}")
            listed.add(path)
            data = files.get(path)
            if data is None:
                missing.append(path)
            elif sha256(data) != entry["sha256"] or len(data) != entry["bytes"]:
                changed.append(path)

    unexpected = sorted(set(files) - listed - {MANIFEST})
    return Integrity(
        ok=not (problems or changed or missing or unexpected),
        package_digest=sha256(raw) if raw is not None else None,
        changed=tuple(sorted(changed)),
        missing=tuple(sorted(missing)),
        unexpected=tuple(unexpected),
        problems=tuple(problems),
        manifest=manifest,
    )


def check_claims(manifest: Mapping[str, JsonValue], recomputed: Comparison) -> tuple[str, ...]:
    """Problems where the manifest claims more than (or differently from) the evidence."""
    problems: list[str] = []
    claim = manifest.get("claim")
    level = claim.get("level") if isinstance(claim, dict) else None
    if level not in {c.value for c in ClaimLevel}:
        problems.append(f"unsupported claim: unknown claim level {level!r}")
    elif level == ClaimLevel.CONDITIONAL_CAUSAL:
        problems.append("unsupported claim: a causal claim cannot follow from one run pair")
    elif level != recomputed.claim_level:
        problems.append(
            f"unsupported claim: manifest says {level}, packaged evidence supports "
            f"{recomputed.claim_level}"
        )
    declared = manifest.get("invariants")
    stated = {
        str(i.get("id")): i.get("status")
        for i in (declared if isinstance(declared, list) else [])
        if isinstance(i, dict)
    }
    for inv in recomputed.invariants:
        if inv.id not in stated:
            problems.append(f"invariant {inv.id} missing from manifest")
        elif stated[inv.id] != inv.status:
            kind = "unsupported claim" if stated[inv.id] == InvariantStatus.VERIFIED else "mismatch"
            problems.append(
                f"{kind}: {inv.id} is {stated[inv.id]!r} in manifest, evidence gives {inv.status}"
            )
    return tuple(problems)
