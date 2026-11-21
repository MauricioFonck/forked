"""Filesystem implementation of ``EventLog`` and ``RunRepository``.

Layout under ``root``::

    runs/<run_id>/events.jsonl   append-only, one event per line, LF endings
    runs/<run_id>/run.json       metadata, replaced atomically (write temp + rename)

Durability: each event line is flushed on append; ``run.json`` is fsync'd before the
rename. A crash can leave a truncated last line, which ``read`` reports as
``CorruptRecording`` instead of silently dropping it.
"""

import json
import os
from collections.abc import Iterator
from pathlib import Path

from forked.adapters.outbound.persistence.filesystem.records import (
    event_from_raw,
    event_to_json,
    snapshot_from_raw,
    snapshot_to_json,
)
from forked.application.errors import CorruptRecording, RunNotFound, StorageFailure
from forked.domain.runs.event import Event
from forked.domain.runs.run import RunSnapshot
from forked.domain.shared.errors import InvalidIdentifier, UnsupportedSchemaVersion
from forked.domain.shared.identifiers import RunId

EVENTS_FILE = "events.jsonl"
RUN_FILE = "run.json"
DEFAULT_MAX_LINE_BYTES = 1024 * 1024


class FileSystemRunStore:
    def __init__(self, root: Path, max_line_bytes: int = DEFAULT_MAX_LINE_BYTES) -> None:
        self._root = root.resolve()
        self._runs = self._root / "runs"
        self._max_line_bytes = max_line_bytes

    # -- paths -------------------------------------------------------------------------

    def _run_dir(self, run_id: RunId) -> Path:
        path = (self._runs / run_id.value).resolve()
        # RunId's pattern already forbids separators; this is defense in depth.
        if path.parent != self._runs.resolve():
            raise StorageFailure(f"run directory escapes the store: {run_id}")
        return path

    # -- EventLog ----------------------------------------------------------------------

    def append(self, event: Event) -> None:
        line = event_to_json(event) + "\n"
        try:
            directory = self._run_dir(event.run_id)
            directory.mkdir(parents=True, exist_ok=True)
            with (directory / EVENTS_FILE).open("a", encoding="utf-8", newline="\n") as fh:
                fh.write(line)
                fh.flush()
        except OSError as exc:
            raise StorageFailure(f"cannot append event: {exc}") from exc

    def read(self, run_id: RunId) -> Iterator[Event]:
        path = self._run_dir(run_id) / EVENTS_FILE
        if not path.is_file():
            raise RunNotFound(f"no event log for run {run_id}")
        try:
            with path.open("rb") as fh:
                for number, raw_line in enumerate(fh, start=1):
                    yield self._parse_line(raw_line, number)
        except OSError as exc:
            raise StorageFailure(f"cannot read event log: {exc}") from exc

    def _parse_line(self, raw_line: bytes, number: int) -> Event:
        if len(raw_line) > self._max_line_bytes:
            raise CorruptRecording(f"line {number} exceeds {self._max_line_bytes} bytes")
        if not raw_line.endswith(b"\n"):
            raise CorruptRecording(f"line {number} is truncated (no line terminator)")
        try:
            raw = json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CorruptRecording(f"line {number} is not valid JSON: {exc}") from exc
        try:
            return event_from_raw(raw)
        except UnsupportedSchemaVersion as exc:
            raise CorruptRecording(f"line {number}: {exc}") from exc
        except CorruptRecording as exc:
            raise CorruptRecording(f"line {number}: {exc}") from exc

    # -- RunRepository -----------------------------------------------------------------

    def save(self, snapshot: RunSnapshot) -> None:
        try:
            directory = self._run_dir(snapshot.run_id)
            directory.mkdir(parents=True, exist_ok=True)
            target = directory / RUN_FILE
            temp = directory / (RUN_FILE + ".tmp")
            with temp.open("w", encoding="utf-8", newline="\n") as fh:
                fh.write(snapshot_to_json(snapshot) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(temp, target)
        except OSError as exc:
            raise StorageFailure(f"cannot save run metadata: {exc}") from exc

    def get(self, run_id: RunId) -> RunSnapshot:
        path = self._run_dir(run_id) / RUN_FILE
        if not path.is_file():
            raise RunNotFound(f"run {run_id} not found")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise StorageFailure(f"cannot read run metadata: {exc}") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CorruptRecording(f"{RUN_FILE} is not valid JSON: {exc}") from exc
        try:
            snapshot = snapshot_from_raw(raw)
        except UnsupportedSchemaVersion as exc:
            raise CorruptRecording(f"{RUN_FILE}: {exc}") from exc
        if snapshot.run_id != run_id:
            raise CorruptRecording(f"{RUN_FILE} belongs to {snapshot.run_id}, not {run_id}")
        return snapshot

    def list_ids(self) -> list[RunId]:
        if not self._runs.is_dir():
            return []
        ids: list[RunId] = []
        for child in self._runs.iterdir():
            if not (child / RUN_FILE).is_file():
                continue
            try:
                ids.append(RunId(child.name))
            except InvalidIdentifier:
                continue
        return sorted(ids, key=lambda run_id: run_id.value)
