"""Strict, in-order resolution of tool calls against a recorded run.

Contract (fail closed, docs/04 UC-02):

* The n-th tool call of the replay must match the n-th recorded ``tool.call``: same tool
  name, same effect class, same *redacted* inputs. Otherwise ``ReplayDivergence``.
* A recorded call with no outcome, or whose outcome payload was omitted, cannot be
  replayed: ``MissingObservation``. Nothing ever falls back to a live call.
* Inputs are compared after redaction, so two calls that differ only in a redacted
  secret are indistinguishable. That is a declared limitation, not a bug.
"""

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass

from forked.domain.runs.event import CaptureStatus, Event, EventType
from forked.domain.shared.errors import DomainError
from forked.domain.shared.identifiers import RunId


class MissingObservation(DomainError):
    code = "missing_observation"


class ReplayDivergence(DomainError):
    code = "replay_divergence"


@dataclass(frozen=True, slots=True)
class Observation:
    call: Event
    outcome: Event | None  # tool.result / tool.error, None if the recording lost it


def _observations(events: Sequence[Event]) -> list[Observation]:
    outcomes = {
        e.parent_event_id: e
        for e in events
        if e.event_type in (EventType.TOOL_RESULT, EventType.TOOL_ERROR) and e.parent_event_id
    }
    return [
        Observation(e, outcomes.get(e.event_id))
        for e in events
        if e.event_type is EventType.TOOL_CALL
    ]


class ReplayCursor:
    def __init__(self, source_run_id: RunId, events: Sequence[Event]) -> None:
        self.source_run_id = source_run_id
        self._pending = deque(_observations(events))
        self.expected = len(self._pending)

    @property
    def remaining(self) -> int:
        return len(self._pending)

    @property
    def consumed(self) -> int:
        return self.expected - self.remaining

    def resolve(self, call: Event) -> Event:
        """Return the recorded outcome for ``call`` (the live, already-redacted call)."""
        position = self.consumed + 1
        if not self._pending:
            raise MissingObservation(
                f"call #{position} ({call.tool_name}) has no recorded observation in "
                f"{self.source_run_id} (it recorded {self.expected} calls)"
            )
        recorded = self._pending[0]
        for field in ("tool_name", "effect_class"):
            live, then = getattr(call, field), getattr(recorded.call, field)
            if live != then:
                raise ReplayDivergence(f"call #{position}: {field} is {live!r}, recorded {then!r}")
        if (call.payload, call.payload_digest) != (
            recorded.call.payload,
            recorded.call.payload_digest,
        ):
            raise ReplayDivergence(
                f"call #{position} ({call.tool_name}): inputs differ from the recording"
            )
        outcome = recorded.outcome
        if outcome is None:
            raise MissingObservation(
                f"call #{position} ({call.tool_name}) has no recorded result "
                f"in {self.source_run_id}"
            )
        if outcome.capture_status is CaptureStatus.OMITTED:
            raise MissingObservation(
                f"call #{position} ({call.tool_name}): recorded result was omitted "
                "(over the size limit); only its digest exists"
            )
        self._pending.popleft()
        return outcome
