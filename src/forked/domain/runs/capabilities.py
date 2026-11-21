"""What a workflow adapter declares about itself before capture starts."""

from dataclasses import dataclass, field

from forked.domain.shared.errors import DomainError


@dataclass(frozen=True, slots=True)
class AdapterCapabilities:
    """Declaration made by the adapter that instruments a workflow.

    ``capture_points`` are the points the adapter promises to record (for tools:
    ``"tool:<name>"``). Capture completeness is measured against this declaration, so an
    adapter that declares nothing cannot claim a complete capture.
    ``limitations`` are free-text statements copied into every report, e.g.
    ``"get_exchange_rate is a local stub; no network call is made"``.
    """

    name: str
    version: str
    capture_points: frozenset[str] = field(default_factory=frozenset)
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise DomainError("adapter name must not be empty")
        if not self.version.strip():
            raise DomainError("adapter version must not be empty")
        for point in self.capture_points:
            if not point.strip():
                raise DomainError("capture points must not be empty strings")


def tool_capture_point(tool_name: str) -> str:
    """Capture point identifier for a tool invocation."""
    return f"tool:{tool_name}"
