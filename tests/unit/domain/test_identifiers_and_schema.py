import pytest

from forked.domain.shared.canonical import canonical_json, digest
from forked.domain.shared.errors import InvalidIdentifier, UnsupportedSchemaVersion
from forked.domain.shared.identifiers import EventId, RunId
from forked.domain.shared.schema import ensure_supported


def test_valid_identifiers() -> None:
    assert RunId("run_0123456789abcdef").value == "run_0123456789abcdef"
    assert str(EventId("evt_abcdef01")) == "evt_abcdef01"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "run_",
        "run_short",
        "evt_0123456789abcdef",
        "run_0123456789ABCDEF",
        "run_../../etc/passwd",
        "run_0123456789abcdef/x",
        "run_0123456789abcdef\\x",
        "run_" + "a" * 65,
    ],
)
def test_invalid_run_ids_are_rejected(value: str) -> None:
    with pytest.raises(InvalidIdentifier):
        RunId(value)


def test_schema_major_zero_is_supported() -> None:
    ensure_supported("0.1.0")
    ensure_supported("0.9.3")


@pytest.mark.parametrize("version", ["1.0.0", "2.1.0", "0.1", "v0.1.0", "x.y.z", ""])
def test_unsupported_or_malformed_schema_versions_are_rejected(version: str) -> None:
    with pytest.raises(UnsupportedSchemaVersion):
        ensure_supported(version)


def test_canonical_json_is_order_independent() -> None:
    assert canonical_json({"b": 1, "a": [1, "x"]}) == canonical_json({"a": [1, "x"], "b": 1})
    assert digest({"a": 1}).startswith("sha256:")
    assert digest({"a": 1}) == digest({"a": 1})
    assert digest({"a": 1}) != digest({"a": 2})


def test_canonical_json_rejects_nan() -> None:
    with pytest.raises(ValueError, match="Out of range"):
        canonical_json(float("nan"))
