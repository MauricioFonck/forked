"""GUARDIAN: published schemas and golden fixtures stay compatible with the code.

* ``spec/cip/v0.1/*.schema.json`` must equal what the code generates. If the schema
  changes on purpose, regenerate with ``scripts/export_schemas.py`` and bump the schema
  version per docs/06-cip-protocol-draft.md §6.9.
* Every golden fixture in ``tests/fixtures/events/v0.1/`` must stay readable and
  round-trip unchanged. Never edit a published fixture: add a new one.
"""

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

from forked.adapters.outbound.persistence.filesystem.records import event_from_raw, event_to_json

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = sorted((ROOT / "tests" / "fixtures" / "events" / "v0.1").glob("*.json"))


def _exporter() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "export_schemas", ROOT / "scripts" / "export_schemas.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_published_schemas_match_code() -> None:
    exporter = _exporter()
    for filename, model in exporter.SCHEMAS.items():
        published = (exporter.SPEC_DIR / filename).read_text(encoding="utf-8")
        assert published == exporter.render(model), (
            f"{filename} drifted: run scripts/export_schemas.py"
        )


def test_there_are_golden_fixtures() -> None:
    assert len(FIXTURES) >= 5


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda p: p.stem)
def test_golden_fixture_round_trips(fixture: Path) -> None:
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    event = event_from_raw(raw)
    again = json.loads(event_to_json(event))
    expected = {k: v for k, v in raw.items() if v is not None}
    expected.setdefault("redacted_paths", [])
    assert again == expected
