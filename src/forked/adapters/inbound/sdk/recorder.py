"""Python SDK to instrument a workflow.

Example::

    with recorder.record(capabilities) as run:            # baseline: tools really execute
        rate = run.call_tool("get_exchange_rate", EffectClass.EXTERNAL_READ,
                             get_exchange_rate, base="USD", quote="EUR")
        run.set_outcome({"rate": rate})

    with recorder.replay(run_id, capabilities) as run:    # replay: tools never execute
        ...same workflow code...

During **recording** the SDK only observes inputs, outputs and errors. During **replay**
``fn`` is never called, whatever its effect class: each call returns the recorded
output (or re-raises the recorded error as ``RecordedToolError``). A call the recording
cannot answer fails closed.
"""

from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from typing import TypeVar, cast

from forked.application.commands.record_run import RecordingService, RecordingSession
from forked.application.commands.replay_run import ReplayService
from forked.domain.effects.effect_class import EffectClass
from forked.domain.replay.cursor import ReplayCursor, ReplayDivergence
from forked.domain.runs.capabilities import AdapterCapabilities
from forked.domain.runs.event import EventDraft, EventType
from forked.domain.shared.canonical import JsonValue
from forked.domain.shared.errors import ForkedError
from forked.domain.shared.identifiers import RunId

T = TypeVar("T", bound=JsonValue)

SDK_SOURCE = "forked.sdk"
REPLAY_SOURCE = "forked.replay"


class RecordedToolError(ForkedError):
    """Raised during replay where the recorded tool raised. Carries the recorded type name."""

    code = "recorded_tool_error"

    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(f"{error_type}: {message}")
        self.error_type = error_type


class RecordedRun:
    def __init__(self, session: RecordingSession, cursor: ReplayCursor | None = None) -> None:
        self._session = session
        self._cursor = cursor
        self._outcome: JsonValue = None

    @property
    def run_id(self) -> RunId:
        return self._session.run_id

    @property
    def is_replay(self) -> bool:
        return self._cursor is not None

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
        """Record ``tool.call``; then execute ``fn`` (record) or resolve it (replay)."""
        source = REPLAY_SOURCE if self._cursor else SDK_SOURCE
        call = self._session.capture(
            EventDraft(
                EventType.TOOL_CALL,
                source,
                {"inputs": dict(inputs)},
                tool_name=name,
                effect_class=effect,
            )
        )

        def outcome(event_type: EventType, payload: JsonValue) -> None:
            self._session.capture(
                EventDraft(
                    event_type,
                    source,
                    payload,
                    tool_name=name,
                    effect_class=effect,
                    parent_event_id=call.event_id,
                )
            )

        if self._cursor is not None:
            recorded = self._cursor.resolve(call)
            outcome(recorded.event_type, recorded.payload)
            payload = recorded.payload if isinstance(recorded.payload, dict) else {}
            if recorded.event_type is EventType.TOOL_ERROR:
                raise RecordedToolError(str(payload.get("error_type")), str(payload.get("message")))
            return cast(T, payload.get("output"))

        try:
            result = fn(**inputs)
        except Exception as exc:
            outcome(EventType.TOOL_ERROR, {"error_type": type(exc).__name__, "message": str(exc)})
            raise
        outcome(EventType.TOOL_RESULT, {"output": result})
        return result


class Recorder:
    def __init__(self, service: RecordingService, replayer: ReplayService | None = None) -> None:
        self._service = service
        self._replayer = replayer

    def record(self, capabilities: AdapterCapabilities) -> AbstractContextManager[RecordedRun]:
        """Record one run. An exception inside the block finalizes it as failed."""
        session = self._service.start(capabilities)
        return self._run(session, RecordedRun(session))

    def replay(
        self, source: RunId, capabilities: AdapterCapabilities
    ) -> AbstractContextManager[RecordedRun]:
        """Replay ``source`` as a new run. Unconsumed recorded calls fail the replay."""
        if self._replayer is None:
            raise ForkedError("this recorder was built without replay support")
        session, cursor = self._replayer.start(source, capabilities)
        return self._run(session, RecordedRun(session, cursor), cursor)

    @staticmethod
    @contextmanager
    def _run(
        session: RecordingSession, run: RecordedRun, cursor: ReplayCursor | None = None
    ) -> Iterator[RecordedRun]:
        try:
            yield run
            if cursor is not None and cursor.remaining:
                raise ReplayDivergence(
                    f"workflow finished after {cursor.consumed} of {cursor.expected} recorded "
                    "calls; the rest were never requested"
                )
        except BaseException as exc:
            try:
                session.fail(f"{type(exc).__name__}: {exc}")
            except ForkedError as fail_exc:
                exc.add_note(f"FORKED could not finalize run {session.run_id}: {fail_exc}")
            raise
        session.complete(run.outcome)
