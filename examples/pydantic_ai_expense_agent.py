"""End-to-end use case: an expense agent built with Pydantic AI, run through FORKED.

Task: "convert an amount between currencies, check the expense policy, email finance".
The model is scripted (``FunctionModel``), so the whole run is deterministic and needs no
API key and no network. The tools are the same local stand-ins as the toy agent:

* ``get_exchange_rate`` is ``external_read`` but a fixed local table — not a real rate;
* ``send_email`` is ``external_write`` but writes a JSON file to a local outbox — no email.

Run it::

    uv run python -m examples.pydantic_ai_expense_agent          # walks through the four steps
"""

import os
import tempfile
from collections.abc import Callable
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.toolsets import FunctionToolset

from forked.adapters.inbound.frameworks.pydantic_ai_toolset import (
    ForkedToolset,
    pydantic_ai_capabilities,
)
from forked.adapters.inbound.sdk.recorder import RecordedRun
from forked.demo import toy_agent
from forked.domain.effects.effect_class import EffectClass
from forked.domain.shared.identifiers import RunId

EFFECTS = {
    "search_policy": EffectClass.PURE_LOCAL,
    "get_exchange_rate": EffectClass.EXTERNAL_READ,
    "send_email": EffectClass.EXTERNAL_WRITE,
}
CAPABILITIES = pydantic_ai_capabilities(EFFECTS)
RATE_CALL = 3  # sequence of the get_exchange_rate tool.call in a recorded run


def build_tools(outbox: Path) -> list[Callable[..., Any]]:
    send = toy_agent.make_send_email(outbox)

    def search_policy(query: str) -> list[str]:
        """Search the expense policy."""
        return [str(line) for line in toy_agent.search_policy(query)]

    def get_exchange_rate(base: str, quote: str, api_key: str) -> float:
        """Exchange rate (local stub table)."""
        return toy_agent.get_exchange_rate(base, quote, api_key)

    def send_email(to: str, subject: str, body: str) -> dict[str, Any]:
        """Send the summary to finance (writes a file to a local outbox)."""
        return dict(send(to, subject, body))

    return [search_policy, get_exchange_rate, send_email]


def _script(
    amount: float, state: dict[str, Any]
) -> Callable[[list[ModelMessage], AgentInfo], ModelResponse]:
    """A deterministic 'model': asks for the three tools in order, then answers."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        got = {
            part.tool_name: part.content
            for message in messages
            for part in message.parts
            if isinstance(part, ToolReturnPart)
        }
        if "search_policy" not in got:
            return _call("search_policy", {"query": "currency conversion"})
        hits = got["search_policy"]
        state["policy_hits"] = len(hits) if isinstance(hits, list) else 0
        if "get_exchange_rate" not in got:
            args = {"base": "USD", "quote": "EUR", "api_key": toy_agent.DEMO_API_KEY}
            return _call("get_exchange_rate", args)
        rate = got["get_exchange_rate"]
        if not isinstance(rate, int | float):
            return ModelResponse(parts=[TextPart(f"Cannot convert: {rate}")])
        state["rate"], state["converted"] = rate, round(amount * rate, 2)
        if "send_email" not in got:
            body = (
                f"{amount:.2f} USD = {state['converted']:.2f} EUR (rate {rate}, source: toy stub)."
            )
            return _call(
                "send_email",
                {"to": "finance@example.com", "subject": "Conversion USD->EUR", "body": body},
            )
        state["email"] = got["send_email"]
        return ModelResponse(
            parts=[TextPart(f"Converted {amount:.2f} USD to {state['converted']:.2f} EUR.")]
        )

    return respond


def _call(tool: str, args: dict[str, Any]) -> ModelResponse:
    return ModelResponse(parts=[ToolCallPart(tool, args)])


def run_expense_agent(
    session: AbstractContextManager[RecordedRun],
    outbox: Path,
    *,
    amount: float = 100.0,
) -> RunId:
    """Run the agent inside ``recorder.record(...)``, ``.replay(...)`` or ``.branch(...)``."""
    state: dict[str, Any] = {}
    with session as run:
        toolset = ForkedToolset(
            FunctionToolset(build_tools(outbox)), run, EFFECTS, on_denied="report"
        )
        agent = Agent(FunctionModel(_script(amount, state)), toolsets=[toolset])
        result = agent.run_sync(f"Convert {amount:.2f} USD to EUR and email finance.")
        state["answer"] = result.output
        run.set_outcome(state)
        return run.run_id


def main() -> None:
    os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
    from forked.bootstrap.container import build_application, verify_package
    from forked.domain.branches.branch import Intervention

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        app = build_application(root / "store")
        outbox = root / "outbox"

        print("1. record the agent (tools really run; the email goes to a local outbox)")
        baseline = run_expense_agent(app.recorder.record(CAPABILITIES), outbox)
        print(f"   {baseline}  outbox files: {len(list(outbox.iterdir()))}")

        print("2. replay it: every tool answers from the recording, nothing executes")
        replayed = run_expense_agent(app.recorder.replay(baseline, CAPABILITIES), outbox)
        print(f"   {replayed}  outbox files: {len(list(outbox.iterdir()))}")

        print("3. branch: replace the exchange rate (tool call #3) with 0.5")
        branch = run_expense_agent(
            app.recorder.branch(baseline, CAPABILITIES, Intervention(RATE_CALL, 0.5)), outbox
        )
        comparison = app.compare_runs.execute(baseline, branch)
        for step in comparison.steps:
            print(f"   #{step.index} {step.tool}: {step.status} [{step.decision}]")
        print(f"   claim level: {comparison.claim_level}")
        sent = len(list(outbox.iterdir()))
        print(f"   outbox files: {sent}  (the changed email was denied, not sent)")

        print("4. export an evidence package and verify it offline")
        package = root / "evidence"
        app.export_evidence(baseline, branch, package)
        report = verify_package(package)
        supported = not report.validity.problems
        print(f"   integrity ok: {report.integrity.ok}; claims supported: {supported}")
        print(f"   {report.validity.note}")


if __name__ == "__main__":
    main()
