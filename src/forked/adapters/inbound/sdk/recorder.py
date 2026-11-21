"""Python SDK to instrument a workflow.

Example::

    with recorder.record(capabilities) as run:
        rate = run.call_tool("get_exchange_rate", EffectClass.EXTERNAL_READ,
                             get_exchange_rate, base="USD", quote="EUR")
        run.set_outcome({"rate": rate})

During **recording** the tool really executes: a baseline run is a real run. The SDK only
observes inputs, outputs and errors. Replay (Phase 2) will substitute recorded outputs
instead of executing tools.
"""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import TypeVar

from forked.application.commands.record_run import RecordingService, RecordingSession
from forked.domain.effects.effect_class import EffectClass
from forked.domain.runs.capabilities import AdapterCapabilities
from forked.domain.runs.event import EventDraft, EventType
from forked.domain.shared.canonical import JsonValue
from forked.domain.shared.errors import ForkedError
from forked.domain.shared.identifiers import RunId

T = TypeVar("T", bound=JsonValue)

SDK_SOURCE = "forked.sdk"


class RecordedRun:
    def __init__(self, session: RecordingSession) -> None:
        self._session = session
        self._outcome: JsonValue = None

    @property
    def run_id(self) -> RunId:
        return self._session.run_id

    def set_outcome(self, outcome: JsonValue) -> None:
        """Value stored in the ``run.completed`` event."""
        self._outcome = outcome

    @property
    def outcome(self) -> JsonValue:
        return self._outcome

    def call_tool(
        self,
        name: str,
        effect: EffectClass,
        fn: Callable[..., T],
        /,
        **inputs: JsonValue,
    ) -> T:
        """Record ``tool.call``, execute ``fn(**inputs)``, record ``tool.result``/``tool.error``."""
        call = self._session.capture(
            EventDraft(
                EventType.TOOL_CALL,
                SDK_SOURCE,
                {"inputs": dict(inputs)},
                tool_name=name,
                effect_class=effect,
            )
        )
        try:
            result = fn(**inputs)
        except Exception as exc:
            self._session.capture(
                EventDraft(
                    EventType.TOOL_ERROR,
                    SDK_SOURCE,
                    {"error_type": type(exc).__name__, "message": str(exc)},
                    tool_name=name,
                    effect_class=effect,
                    parent_event_id=call.event_id,
                )
            )
            raise
        self._session.capture(
            EventDraft(
                EventType.TOOL_RESULT,
                SDK_SOURCE,
                {"output": result},
                tool_name=name,
                effect_class=effect,
                parent_event_id=call.event_id,
            )
        )
        return result


class Recorder:
    def __init__(self, service: RecordingService) -> None:
        self._service = service

    @contextmanager
    def record(self, capabilities: AdapterCapabilities) -> Iterator[RecordedRun]:
        """Record one run. An exception inside the block finalizes it as failed."""
        session = self._service.start(capabilities)
        run = RecordedRun(session)
        try:
            yield run
        except BaseException as exc:
            try:
                session.fail(f"{type(exc).__name__}: {exc}")
            except ForkedError as fail_exc:
                exc.add_note(f"FORKED could not finalize run {session.run_id}: {fail_exc}")
            raise
        session.complete(run.outcome)
