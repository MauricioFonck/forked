"""Canonical JSON and content digests.

Canonical form: UTF-8, sorted keys, no insignificant whitespace, no NaN/Infinity.
The digest of a payload is ``sha256:<hex>`` over that form. A digest proves that bytes
did not change; it says nothing about whether an experiment is valid.
"""

import hashlib
import json
from typing import TypeAlias

JsonValue: TypeAlias = bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"] | None


def canonical_json(value: JsonValue) -> bytes:
    """Serialize ``value`` deterministically. Raises ``ValueError`` on NaN/Infinity."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def digest(value: JsonValue) -> str:
    """Return ``sha256:<hex>`` of the canonical JSON form of ``value``."""
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()
