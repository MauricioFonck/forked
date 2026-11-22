"""Python SDK to instrument a workflow.

Example::

    with recorder.record(capabilities) as run:            # baseline: tools really execute
        rate = run.call_tool("get_exchange_rate", EffectClass.EXTERNAL_READ,
                             get_exchange_rate, base="USD", quote="EUR")
        run.set_outcome({"rate": rate})

    with recorder.replay(run_id, capabilities) as run:    # replay: tools never execute
        ...same workflow code...

    with recorder.branch(run_id, capabilities, Intervention(checkpoint=3, value=0.5)) as run:
        ...same workflow code...                          # fork with one declared change

During **recording** the SDK only observes inputs, outputs and errors. During **replay**
``fn`` is never called, whatever its effect class: each call returns the recorded
output (or re-raises the recorded error as ``RecordedToolError``). A call the recording
cannot answer fails closed. In a **branch**, calls before the checkpoint replay, the
checkpoint call gets the intervention value, and later calls replay if they match the
parent or go to the default-deny effect policy: only ``pure_local`` executes, anything
else raises ``EffectDenied`` (recorded as a ``tool.error``) without executing.
Every outcome in replay/branch mode carries ``payload.forked = {decision, reason}``.
"""

from collections.abc import Awaitable, Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from typing import TypeVar, cast

from forked.application.commands.record_run import RecordingService, RecordingSession
from forked.application.commands.replay_run import ReplayService
from forked.domain.branches.branch import Intervention, Resolution
from forked.domain.effects.effect_class import EffectClass
from forked.domain.effects.policy import Decision, EffectDenied
from forked.domain.replay.cursor import ReplayCursor, ReplayDivergence
from forked.domain.runs.capabilities import AdapterCapabilities
from forked.domain.runs.event import Event, EventDraft, EventType
from forked.domain.shared.canonical import JsonValue
from forked.domain.shared.errors import ForkedError
from forked.domain.shared.identifiers import RunId

T = TypeVar("T", bound=JsonValue)

SDK_SOURCE = "forked.sdk"
REPLAY_SOURCE = "forked.replay"
BRANCH_SOURCE = "forked.branch"

Resolver = Callable[[Event], Resolution]


class RecordedToolError(ForkedError):
    """Raised during replay where the recorded tool raised. Carries the recorded type name."""

    code = "recorded_tool_error"

    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(f"{error_type}: {message}")
        self.error_type = error_type
        self.message = message


class RecordedRun:
    def __init__(
        self,
        session: RecordingSession,
        resolver: Resolver | None = None,
        source: str = SDK_SOURCE,
    ) -> None:
        self._session = session
        self._resolver = resolver
        self._source = source
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

    def _begin(self, name: str, effect: EffectClass, inputs: dict[str, JsonValue]) -> "_Step":
        """Record ``tool.call`` and, in replay/branch mode, ask the resolver what to do."""
        source = self._source
        call = self._session.capture(
            EventDraft(
                EventType.TOOL_CALL,
                source,
                {"inputs": dict(inputs)},
                tool_name=name,
                effect_class=effect,
            )
        )

        def record(event_type: EventType, payload: JsonValue) -> None:
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

        step = _Step(record)
        if self._resolver is None:
            return step
        resolution = self._resolver(call)
        step.tag = {"forked": {"decision": resolution.decision.value, "reason": resolution.reason}}
        if resolution.decision is Decision.DENY:
            denied: dict[str, JsonValue] = {
                "error_type": "EffectDenied",
                "message": resolution.reason,
            }
            record(EventType.TOOL_ERROR, {**denied, **step.tag})
            raise EffectDenied(resolution.reason)
        if resolution.decision is not Decision.ALLOW and resolution.event_type is not None:
            body = dict(resolution.payload) if isinstance(resolution.payload, dict) else {}
            body.pop("forked", None)
            record(resolution.event_type, {**body, **step.tag})
            if resolution.event_type is EventType.TOOL_ERROR:
                raise RecordedToolError(str(body.get("error_type")), str(body.get("message")))
            step.answered, step.value = True, body.get("output")
        return step

    def call_tool(
        self,
        name: str,
        effect: EffectClass,
        fn: Callable[..., T],
        /,
        **inputs: JsonValue,
    ) -> T:
        """Record ``tool.call``; then execute ``fn`` or resolve it (replay/branch)."""
        step = self._begin(name, effect, inputs)
        if step.answered:
            return cast(T, step.value)
        try:
            result = fn(**inputs)
        except Exception as exc:
            step.fail(exc)
            raise
        step.ok(result)
        return result

    async def acall_tool(
        self,
        name: str,
        effect: EffectClass,
        fn: Callable[..., Awaitable[T]],
        /,
        **inputs: JsonValue,
    ) -> T:
        """Async twin of :meth:`call_tool` (same recording, replay and branch semantics)."""
        step = self._begin(name, effect, inputs)
        if step.answered:
            return cast(T, step.value)
        try:
            result = await fn(**inputs)
        except Exception as exc:
            step.fail(exc)
            raise
        step.ok(result)
        return result


class _Step:
    """One tool call in flight: how to record its outcome, and a replayed answer if any."""

    def __init__(self, record: Callable[[EventType, JsonValue], None]) -> None:
        self._record = record
        self.tag: dict[str, JsonValue] = {}
        self.answered = False
        self.value: object = None

    def ok(self, result: JsonValue) -> None:
        self._record(EventType.TOOL_RESULT, {"output": result, **self.tag})

    def fail(self, exc: Exception) -> None:
        error: dict[str, JsonValue] = {"error_type": type(exc).__name__, "message": str(exc)}
        self._record(EventType.TOOL_ERROR, {**error, **self.tag})


class Recorder:
    def __init__(self, service: RecordingService, replayer: ReplayService | None = None) -> None:
        self._service = service
        self._replayer = replayer

    def record(
        self, capabilities: AdapterCapabilities, *, source: str = SDK_SOURCE
    ) -> AbstractContextManager[RecordedRun]:
        """Record one run. An exception inside the block finalizes it as failed."""
        session = self._service.start(capabilities)
        return self._run(session, RecordedRun(session, source=source))

    def replay(
        self, source: RunId, capabilities: AdapterCapabilities
    ) -> AbstractContextManager[RecordedRun]:
        """Replay ``source`` as a new run. Unconsumed recorded calls fail the replay."""
        if self._replayer is None:
            raise ForkedError("this recorder was built without replay support")
        session, cursor = self._replayer.start(source, capabilities)

        def resolve(call: Event) -> Resolution:
            return Resolution.replayed(cursor.resolve(call))

        return self._run(session, RecordedRun(session, resolve, REPLAY_SOURCE), cursor)

    def branch(
        self, parent: RunId, capabilities: AdapterCapabilities, intervention: Intervention
    ) -> AbstractContextManager[RecordedRun]:
        """Fork ``parent`` at ``intervention.checkpoint`` as a new run (UC-03)."""
        if self._replayer is None:
            raise ForkedError("this recorder was built without replay support")
        session, resolver = self._replayer.branch(parent, capabilities, intervention)
        return self._run(session, RecordedRun(session, resolver.resolve, BRANCH_SOURCE))

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
