"""Secret redaction applied before anything is persisted.

Two independent detectors:

* **Key names** — a mapping key whose normalized name contains a sensitive fragment
  (``api_key``, ``Authorization``, ``x-auth-token`` …) has its value replaced.
* **Value shapes** — a string that looks like a well-known credential format
  (``sk-…``, ``ghp_…``, ``AKIA…``, ``Bearer …``, PEM private keys) is replaced wherever
  it appears.

Over-redaction is the accepted failure mode: ``token_count`` is redacted because it
contains ``token``. A leaked secret cannot be un-leaked; an over-redacted counter can
be allow-listed later. Redaction is best effort and does not prove the absence of
sensitive data — see docs/07-security-and-privacy.md.
"""

import re
from dataclasses import dataclass, field

from forked.domain.shared.canonical import JsonValue

REDACTED = "[REDACTED]"

DEFAULT_SENSITIVE_KEY_FRAGMENTS = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "token",
        "apikey",
        "authorization",
        "cookie",
        "credential",
        "privatekey",
        "accesskey",
        "sessionid",
    }
)

DEFAULT_SECRET_VALUE_PATTERNS = (
    r"sk-[A-Za-z0-9_\-]{16,}",
    r"gh[pousr]_[A-Za-z0-9]{20,}",
    r"github_pat_[A-Za-z0-9_]{20,}",
    r"AKIA[0-9A-Z]{16}",
    r"xox[abprs]-[A-Za-z0-9\-]{10,}",
    r"(?i)bearer\s+[A-Za-z0-9._~+/\-]{8,}=*",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
)


def _normalize(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())


@dataclass(frozen=True, slots=True)
class RedactionPolicy:
    sensitive_key_fragments: frozenset[str] = DEFAULT_SENSITIVE_KEY_FRAGMENTS
    secret_value_patterns: tuple[str, ...] = DEFAULT_SECRET_VALUE_PATTERNS
    _compiled: tuple[re.Pattern[str], ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "_compiled", tuple(re.compile(p) for p in self.secret_value_patterns)
        )

    def is_sensitive_key(self, key: str) -> bool:
        normalized = _normalize(key)
        return any(fragment in normalized for fragment in self.sensitive_key_fragments)

    def looks_like_secret(self, value: str) -> bool:
        return any(pattern.search(value) for pattern in self._compiled)


@dataclass(frozen=True, slots=True)
class RedactionResult:
    payload: JsonValue
    redacted_paths: tuple[str, ...]


def redact(payload: JsonValue, policy: RedactionPolicy) -> RedactionResult:
    """Return a redacted copy of ``payload`` and the JSONPath-like paths that changed."""
    paths: list[str] = []

    def walk(value: JsonValue, path: str) -> JsonValue:
        if isinstance(value, dict):
            out: dict[str, JsonValue] = {}
            for key, item in value.items():
                child = f"{path}.{key}"
                if policy.is_sensitive_key(key) and item is not None:
                    paths.append(child)
                    out[key] = REDACTED
                else:
                    out[key] = walk(item, child)
            return out
        if isinstance(value, list):
            return [walk(item, f"{path}[{index}]") for index, item in enumerate(value)]
        if isinstance(value, str) and policy.looks_like_secret(value):
            paths.append(path)
            return REDACTED
        return value

    return RedactionResult(payload=walk(payload, "$"), redacted_paths=tuple(paths))
