"""Ordering checks over a recorded event stream."""

from collections.abc import Iterable
from dataclasses import dataclass

from forked.domain.runs.event import Event
from forked.domain.shared.identifiers import RunId


@dataclass(frozen=True, slots=True)
class SequenceReport:
    """Result of checking that a stream is contiguous, ordered and single-run.

    Sequences must be exactly ``0, 1, 2, …`` in file order.
    """

    count: int
    gaps: tuple[int, ...]
    duplicates: tuple[int, ...]
    out_of_order: tuple[int, ...]
    foreign_events: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not (self.gaps or self.duplicates or self.out_of_order or self.foreign_events)


def check_sequence(events: Iterable[Event], run_id: RunId) -> SequenceReport:
    seen: set[int] = set()
    duplicates: list[int] = []
    out_of_order: list[int] = []
    foreign: list[str] = []
    previous = -1
    count = 0
    for event in events:
        count += 1
        if event.run_id != run_id:
            foreign.append(event.event_id.value)
        if event.sequence in seen:
            duplicates.append(event.sequence)
        elif event.sequence < previous:
            out_of_order.append(event.sequence)
        seen.add(event.sequence)
        previous = max(previous, event.sequence)
    expected = set(range(max(seen) + 1)) if seen else set()
    gaps = tuple(sorted(expected - seen))
    return SequenceReport(
        count=count,
        gaps=gaps,
        duplicates=tuple(duplicates),
        out_of_order=tuple(out_of_order),
        foreign_events=tuple(foreign),
    )
