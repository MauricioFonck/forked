"""Capture pipeline: the ordered stages a payload passes before it can be persisted.

    validate (JSON-serializable) ─▶ redact ─▶ enforce size limit ─▶ PreparedPayload

Redaction runs *before* the size check, so the digest of an omitted payload is computed
over redacted content: a digest of a secret would let anyone confirm a guessed secret.
"""

from dataclasses import dataclass

from forked.domain.runs.event import CaptureStatus
from forked.domain.runs.redaction import RedactionPolicy, redact
from forked.domain.runs.run import PreparedPayload
from forked.domain.shared.canonical import JsonValue, canonical_json, digest
from forked.domain.shared.errors import InvalidEvent

DEFAULT_MAX_PAYLOAD_BYTES = 64 * 1024


@dataclass(frozen=True, slots=True)
class CaptureLimits:
    max_payload_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES
    max_events_per_run: int = 100_000


class CapturePipeline:
    def __init__(self, policy: RedactionPolicy, limits: CaptureLimits) -> None:
        self._policy = policy
        self._limits = limits

    def prepare(self, payload: JsonValue) -> PreparedPayload:
        try:
            canonical_json(payload)
        except (TypeError, ValueError) as exc:
            raise InvalidEvent(f"payload is not JSON-serializable: {exc}") from exc

        result = redact(payload, self._policy)
        size = len(canonical_json(result.payload))
        if size > self._limits.max_payload_bytes:
            return PreparedPayload(
                payload=None,
                capture_status=CaptureStatus.OMITTED,
                redacted_paths=result.redacted_paths,
                payload_digest=digest(result.payload),
            )
        if result.redacted_paths:
            return PreparedPayload(
                payload=result.payload,
                capture_status=CaptureStatus.REDACTED,
                redacted_paths=result.redacted_paths,
            )
        return PreparedPayload(payload=result.payload, capture_status=CaptureStatus.CAPTURED)
