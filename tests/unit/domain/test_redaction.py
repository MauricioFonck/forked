import json

import pytest
from hypothesis import given
from hypothesis import strategies as st

from forked.domain.runs.redaction import REDACTED, RedactionPolicy, redact
from forked.domain.shared.canonical import JsonValue

POLICY = RedactionPolicy()


@pytest.mark.parametrize(
    "key",
    [
        "api_key",
        "API-KEY",
        "apiKey",
        "password",
        "Authorization",
        "x-auth-token",
        "client_secret",
        "session_id",
        "AWS_ACCESS_KEY_ID",
        "private_key",
        "Cookie",
    ],
)
def test_sensitive_keys_are_redacted(key: str) -> None:
    result = redact({key: "value", "keep": "visible"}, POLICY)
    assert result.payload == {key: REDACTED, "keep": "visible"}
    assert result.redacted_paths == (f"$.{key}",)


@pytest.mark.parametrize(
    "value",
    [
        "sk-proj-abcdefghijklmnop1234",
        "ghp_" + "a" * 36,
        "github_pat_" + "B" * 30,
        "AKIAABCDEFGHIJKLMNOP",
        "xoxb-1234567890-abcdef",
        "Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig",
        "-----BEGIN RSA PRIVATE KEY-----\nMII...",
    ],
)
def test_secret_shaped_values_are_redacted_anywhere(value: str) -> None:
    result = redact({"notes": ["harmless", {"deep": value}]}, POLICY)
    assert result.payload == {"notes": ["harmless", {"deep": REDACTED}]}
    assert result.redacted_paths == ("$.notes[1].deep",)


def test_null_sensitive_value_is_not_reported_as_redacted() -> None:
    result = redact({"password": None}, POLICY)
    assert result.payload == {"password": None}
    assert result.redacted_paths == ()


def test_over_redaction_is_the_accepted_failure_mode() -> None:
    # documented trade-off: 'token_count' contains 'token'
    assert redact({"token_count": 12}, POLICY).payload == {"token_count": REDACTED}


def test_redaction_does_not_mutate_input() -> None:
    original: JsonValue = {"api_key": "x", "list": [{"password": "y"}]}
    snapshot = json.dumps(original)
    redact(original, POLICY)
    assert json.dumps(original) == snapshot


json_values = st.recursive(
    st.none() | st.booleans() | st.integers() | st.text(max_size=20),
    lambda children: (
        st.lists(children, max_size=4) | st.dictionaries(st.text(max_size=10), children, max_size=4)
    ),
    max_leaves=20,
)


@given(json_values)
def test_redaction_is_idempotent(value: JsonValue) -> None:
    once = redact(value, POLICY)
    twice = redact(once.payload, POLICY)
    assert twice.payload == once.payload


@given(json_values, st.sampled_from(["api_key", "password", "token"]), st.text(min_size=1))
def test_secret_under_sensitive_key_never_survives(value: JsonValue, key: str, secret: str) -> None:
    payload: JsonValue = {"wrapper": [value, {key: secret}]}
    result = redact(payload, POLICY)
    assert result.payload["wrapper"][1][key] == REDACTED  # type: ignore[index,call-overload]
