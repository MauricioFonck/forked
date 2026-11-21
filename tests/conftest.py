from pathlib import Path

import pytest

from forked.application.capture import CaptureLimits, CapturePipeline
from forked.application.commands.record_run import RecordingDependencies, RecordingService
from forked.bootstrap.container import Application, build_application
from forked.domain.runs.capabilities import AdapterCapabilities, tool_capture_point
from forked.domain.runs.redaction import RedactionPolicy
from tests.fakes import InMemoryRunStore, SequentialIds, StaticProbe, SteppingClock

CAPS = AdapterCapabilities(
    name="test-adapter",
    version="1.0.0",
    capture_points=frozenset({tool_capture_point("echo")}),
    limitations=("test adapter",),
)


def make_deps(
    store: InMemoryRunStore | None = None,
    *,
    limits: CaptureLimits | None = None,
    probe: StaticProbe | None = None,
) -> RecordingDependencies:
    store = store if store is not None else InMemoryRunStore()
    effective = limits or CaptureLimits()
    return RecordingDependencies(
        events=store,
        runs=store,
        clock=SteppingClock(),
        ids=SequentialIds(),
        probe=probe or StaticProbe(),
        pipeline=CapturePipeline(RedactionPolicy(), effective),
        limits=effective,
    )


@pytest.fixture
def store() -> InMemoryRunStore:
    return InMemoryRunStore()


@pytest.fixture
def service(store: InMemoryRunStore) -> RecordingService:
    return RecordingService(make_deps(store))


@pytest.fixture
def app(tmp_path: Path) -> Application:
    return build_application(tmp_path / "store", clock=SteppingClock(), ids=SequentialIds())
