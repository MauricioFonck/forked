"""Identifier value objects.

Identifiers are validated against a strict pattern. Besides typing, this is a security
control: a run id becomes a directory name in filesystem adapters, so a value such as
``../../etc`` must be impossible to construct.
"""

import re
from dataclasses import dataclass

from forked.domain.shared.errors import InvalidIdentifier

_BODY = re.compile(r"^[0-9a-z]{8,64}$")


def _validate(value: str, prefix: str) -> None:
    if not isinstance(value, str) or not value.startswith(prefix):
        raise InvalidIdentifier(f"identifier must start with {prefix!r}: {value!r}")
    if not _BODY.fullmatch(value[len(prefix) :]):
        raise InvalidIdentifier(
            f"identifier body must be 8-64 lowercase alphanumeric characters: {value!r}"
        )


@dataclass(frozen=True, slots=True)
class RunId:
    """Identifier of one recorded execution, e.g. ``run_3f9a...``."""

    value: str

    PREFIX = "run_"

    def __post_init__(self) -> None:
        _validate(self.value, self.PREFIX)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class EventId:
    """Identifier of one event, e.g. ``evt_9c1d...``."""

    value: str

    PREFIX = "evt_"

    def __post_init__(self) -> None:
        _validate(self.value, self.PREFIX)

    def __str__(self) -> str:
        return self.value
