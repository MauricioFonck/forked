"""Environment fingerprint: the facts about where a run happened."""

from dataclasses import dataclass

REQUIRED_FACTS = ("python_version", "platform", "forked_version", "adapter", "adapter_version")


@dataclass(frozen=True, slots=True)
class EnvironmentFingerprint:
    """Sorted ``(name, value)`` pairs. ``None`` means the fact could not be captured.

    A missing fact is never invented: it stays ``None`` and is reported as missing
    evidence.
    """

    facts: tuple[tuple[str, str | None], ...]

    @classmethod
    def of(cls, facts: dict[str, str | None]) -> "EnvironmentFingerprint":
        merged: dict[str, str | None] = {name: None for name in REQUIRED_FACTS}
        merged.update(facts)
        return cls(tuple(sorted(merged.items())))

    def as_dict(self) -> dict[str, str | None]:
        return dict(self.facts)

    def missing(self) -> tuple[str, ...]:
        """Names of facts whose value could not be captured."""
        return tuple(name for name, value in self.facts if value is None)
