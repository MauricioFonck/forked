"""Security cases from docs/07-security-and-privacy.md §7.6 that apply to Phase 1."""

import json
from pathlib import Path

import pytest

from forked.adapters.outbound.persistence.filesystem.store import FileSystemRunStore
from forked.application.errors import CorruptRecording
from forked.bootstrap.container import Application
from forked.demo.toy_agent import DEMO_API_KEY, run_toy_agent
from forked.domain.shared.errors import InvalidIdentifier
from forked.domain.shared.identifiers import RunId


def _all_bytes(root: Path) -> bytes:
    return b"".join(p.read_bytes() for p in root.rglob("*") if p.is_file())


def test_demo_secret_never_reaches_disk(app: Application, tmp_path: Path) -> None:
    run_toy_agent(app.recorder, tmp_path / "outbox")
    persisted = _all_bytes(app.store_root)
    assert DEMO_API_KEY.encode() not in persisted
    assert b"[REDACTED]" in persisted


@pytest.mark.parametrize("bad", ["../escape", "run_../../x", "run_00000001/../../x", "/etc/passwd"])
def test_path_traversal_through_run_id_is_impossible(bad: str) -> None:
    with pytest.raises(InvalidIdentifier):
        RunId(bad)


def _write_log(tmp_path: Path, lines: list[bytes]) -> tuple[FileSystemRunStore, RunId]:
    run_id = RunId("run_00000001")
    directory = tmp_path / "store" / "runs" / run_id.value
    directory.mkdir(parents=True)
    (directory / "events.jsonl").write_bytes(b"".join(lines))
    return FileSystemRunStore(tmp_path / "store"), run_id


GOOD = (
    b'{"schema_version":"0.1.0","event_id":"evt_00000001","run_id":"run_00000001",'
    b'"sequence":0,"event_type":"run.started","timestamp":"2026-11-21T12:00:00Z",'
    b'"source":"t","capture_status":"captured"}\n'
)


@pytest.mark.parametrize(
    ("line", "message"),
    [
        (b"not json\n", "not valid JSON"),
        (b"\xff\xfe\n", "not valid JSON"),
        (b"[]\n", "schema_version"),
        (GOOD.replace(b'"0.1.0"', b'"9.0.0"'), "not supported"),
        (GOOD.replace(b'"run.started"', b'"run.exploded"'), "invalid event record"),
        (GOOD.replace(b'"sequence":0', b'"sequence":-3'), "invalid event record"),
        (GOOD.replace(b"12:00:00Z", b"12:00:00"), "invalid event record"),
        (GOOD.replace(b'"run_00000001"', b'"run_../../x"'), "invalid event record"),
        (GOOD.rstrip(b"\n"), "truncated"),
    ],
)
def test_malformed_lines_fail_closed_with_line_number(
    tmp_path: Path, line: bytes, message: str
) -> None:
    store, run_id = _write_log(tmp_path, [GOOD, line])
    with pytest.raises(CorruptRecording, match=message) as info:
        list(store.read(run_id))
    assert "line 2" in str(info.value)


def test_oversized_line_is_rejected(tmp_path: Path) -> None:
    run_id = RunId("run_00000001")
    directory = tmp_path / "store" / "runs" / run_id.value
    directory.mkdir(parents=True)
    huge = json.loads(GOOD)
    huge["payload"] = "x" * 2048
    (directory / "events.jsonl").write_text(json.dumps(huge) + "\n", encoding="utf-8")
    store = FileSystemRunStore(tmp_path / "store", max_line_bytes=1024)
    with pytest.raises(CorruptRecording, match="exceeds"):
        list(store.read(run_id))


def test_tampered_run_metadata_is_rejected(app: Application, tmp_path: Path) -> None:
    run_id = run_toy_agent(app.recorder, tmp_path / "outbox")
    meta = app.store_root / "runs" / run_id.value / "run.json"
    data = json.loads(meta.read_text(encoding="utf-8"))
    data["run_id"] = "run_00000999"
    meta.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CorruptRecording, match="belongs to"):
        app.inspect_run.execute(run_id)
