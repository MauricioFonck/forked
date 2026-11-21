"""Branch resolution: replay up to a checkpoint, intervene there, apply policy after.

Checkpoint (ADR-011): the ``sequence`` of a ``tool.call`` event in the parent run.
The branch re-executes the workflow code; for each tool call, by position:

* before the checkpoint: strict replay (any divergence fails closed, like a replay);
* at the checkpoint: the call must still match the parent's (same inputs), and its
  result is replaced by the intervention value;
* after it: a call matching the parent's next recorded call is replayed; once a call
  differs, alignment is lost and every later call goes to the effect policy.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from forked.domain.effects.effect_class import EffectClass
from forked.domain.effects.policy import Decision, DefaultDenyPolicy
from forked.domain.replay.cursor import ReplayCursor
from forked.domain.runs.event import Event, EventType
from forked.domain.shared.canonical import JsonValue, digest
from forked.domain.shared.errors import DomainError
from forked.domain.shared.identifiers import RunId

INTERVENTION_ID = "int_001"


class InvalidCheckpoint(DomainError):
    code = "invalid_checkpoint"


@dataclass(frozen=True, slots=True)
class Intervention:
    """The one supported intervention type: replace a recorded tool result."""

    checkpoint: int
    value: JsonValue

    def as_dict(self) -> dict[str, JsonValue]:
        return {
            "id": INTERVENTION_ID,
            "target": "tool.result",
            "operation": "replace_recorded_observation",
            "checkpoint": self.checkpoint,
            "value": self.value,
        }


@dataclass(frozen=True, slots=True)
class Resolution:
    decision: Decision
    reason: str
    event_type: EventType | None = None  # set unless decision is ALLOW / DENY
    payload: JsonValue = None

    @classmethod
    def replayed(cls, recorded: Event) -> "Resolution":
        return cls(Decision.REPLAY, "recorded observation", recorded.event_type, recorded.payload)


def log_digest(events: Sequence[Event]) -> str:
    """Content digest of a parsed event log (ids, order, types, payloads)."""
    return digest(
        [
            [e.event_id.value, e.sequence, e.event_type.value, e.payload, e.payload_digest]
            for e in events
        ]
    )


class BranchResolver:
    def __init__(
        self,
        parent: RunId,
        events: Sequence[Event],
        intervention: Intervention,
        policy: DefaultDenyPolicy,
    ) -> None:
        calls = [e.sequence for e in events if e.event_type is EventType.TOOL_CALL]
        if intervention.checkpoint not in calls:
            raise InvalidCheckpoint(
                f"sequence {intervention.checkpoint} of {parent} is not a tool.call "
                f"(tool.call sequences: {calls})"
            )
        self._at = calls.index(intervention.checkpoint) + 1
        self._intervention = intervention
        self._policy = policy
        self._cursor = ReplayCursor(parent, events)
        self._position = 0
        self._aligned = True

    def resolve(self, call: Event) -> Resolution:
        self._position += 1
        if self._position < self._at:
            return Resolution.replayed(self._cursor.resolve(call))
        if self._position == self._at:
            self._cursor.match(call)
            return Resolution(
                Decision.INTERVENE,
                f"intervention {INTERVENTION_ID}",
                EventType.TOOL_RESULT,
                {"output": self._intervention.value},
            )
        # ponytail: positional alignment, no re-sync after the first differing call;
        # matching by content would need a diff algorithm and a reason to trust it.
        if self._aligned:
            recorded = self._cursor.try_resolve(call)
            if recorded is not None:
                return Resolution.replayed(recorded)
            self._aligned = False
        decided = self._policy.decide(call.effect_class or EffectClass.UNKNOWN)
        return Resolution(decided.decision, decided.reason)
