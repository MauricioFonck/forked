"""Effect policy for experimental branches (docs/07 §7.5, ADR-011).

The policy is consulted only when **no recorded observation applies** to a call. A
recorded observation that matches is always replayed instead; that is not a policy
decision, it is the absence of a live call.
"""

from dataclasses import dataclass
from enum import StrEnum

from forked.domain.effects.effect_class import EffectClass
from forked.domain.shared.errors import DomainError


class Decision(StrEnum):
    REPLAY = "replay"  # answered from the parent recording
    INTERVENE = "intervene"  # answered with the declared intervention value
    ALLOW = "allow"  # executed live
    DENY = "deny"  # not executed; the workflow receives EffectDenied


class EffectDenied(DomainError):
    code = "effect_denied"

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True, slots=True)
class EffectDecision:
    decision: Decision
    reason: str


class DefaultDenyPolicy:
    """Allow only declared ``pure_local`` calls; deny everything else.

    ponytail: the only policy. User-approved policies (e.g. allow a specific
    ``local_write`` into a disposable workspace) need a Protocol + config; add then.
    """

    version = "default-deny/1"

    def decide(self, effect: EffectClass) -> EffectDecision:
        if effect is EffectClass.PURE_LOCAL:
            return EffectDecision(
                Decision.ALLOW, "pure_local with new inputs: executed (declared side-effect free)"
            )
        return EffectDecision(
            Decision.DENY,
            f"{effect}: no recorded observation for these inputs and the default policy "
            "denies live execution in a branch",
        )
