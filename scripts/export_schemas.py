"""Regenerate the published JSON Schemas under ``spec/cip/v0.1/``.

Usage: ``uv run python scripts/export_schemas.py``. The guardian
``tests/guardians/test_published_schema.py`` fails if the files drift from the code.
"""

import json
from pathlib import Path

from forked.adapters.outbound.persistence.filesystem.records import EventRecord, RunRecord

SPEC_DIR = Path(__file__).resolve().parents[1] / "spec" / "cip" / "v0.1"
SCHEMAS = {"event.schema.json": EventRecord, "run.schema.json": RunRecord}


def render(model: type[EventRecord] | type[RunRecord]) -> str:
    return (
        json.dumps(model.model_json_schema(mode="serialization"), indent=2, sort_keys=True) + "\n"
    )


def main() -> None:
    SPEC_DIR.mkdir(parents=True, exist_ok=True)
    for filename, model in SCHEMAS.items():
        (SPEC_DIR / filename).write_text(render(model), encoding="utf-8", newline="\n")
        print(f"wrote {SPEC_DIR / filename}")


if __name__ == "__main__":
    main()
