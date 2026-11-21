"""A deterministic toy agent used to demonstrate recording.

Task: "convert an amount between currencies, check the expense policy, and email the
summary to finance".

Honesty notes (also declared as adapter limitations, so they appear in every report):

* ``get_exchange_rate`` is classified ``external_read`` but is a **local stub** with a
  fixed table. No network call is made. Its result is not a real-world rate.
* ``send_email`` is classified ``external_write`` but writes a JSON file to a local
  ``outbox`` directory standing in for a mail server. No email is sent.
* The fake API key exists only to demonstrate redaction; it is not a credential.
"""

import json
from pathlib import Path

from forked.adapters.inbound.sdk.recorder import Recorder
from forked.domain.effects.effect_class import EffectClass
from forked.domain.runs.capabilities import AdapterCapabilities, tool_capture_point
from forked.domain.shared.canonical import JsonValue
from forked.domain.shared.identifiers import RunId

ADAPTER_NAME = "forked-toy-agent"
ADAPTER_VERSION = "0.1.0"
TOOLS = ("search_policy", "get_exchange_rate", "send_email")

CAPABILITIES = AdapterCapabilities(
    name=ADAPTER_NAME,
    version=ADAPTER_VERSION,
    capture_points=frozenset(tool_capture_point(t) for t in TOOLS),
    limitations=(
        "get_exchange_rate is a local stub with a fixed rate table; no network call is made",
        "send_email writes to a local outbox directory; no email is sent",
        "the demo api_key is fake and exists only to demonstrate redaction",
    ),
)

DEMO_API_KEY = "sk-toy-0000000000000000000demo"  # fake, see module docstring

_RATES = {("USD", "EUR"): 0.92, ("EUR", "USD"): 1.087, ("USD", "COP"): 4100.0}
_POLICY = (
    "Expenses above 500 USD require manager approval.",
    "Currency conversions must cite the rate source.",
    "Finance summaries are sent to finance@example.com.",
)


def search_policy(query: str) -> list[JsonValue]:
    words = {w.lower() for w in query.split()}
    return [line for line in _POLICY if words & {w.lower().strip(".") for w in line.split()}]


def get_exchange_rate(base: str, quote: str, api_key: str) -> float:
    if not api_key:
        raise PermissionError("missing api key")
    try:
        return _RATES[(base, quote)]
    except KeyError:
        raise LookupError(f"no rate for {base}/{quote}") from None


def make_send_email(outbox: Path) -> "SendEmail":
    return SendEmail(outbox)


class SendEmail:
    """Local stand-in for a mail server: one JSON file per message."""

    def __init__(self, outbox: Path) -> None:
        self._outbox = outbox

    def __call__(self, to: str, subject: str, body: str) -> dict[str, JsonValue]:
        self._outbox.mkdir(parents=True, exist_ok=True)
        index = len(list(self._outbox.glob("message-*.json"))) + 1
        path = self._outbox / f"message-{index:04d}.json"
        path.write_text(
            json.dumps({"to": to, "subject": subject, "body": body}, indent=2), encoding="utf-8"
        )
        return {"accepted": True, "message_file": path.name}


def run_toy_agent(
    recorder: Recorder,
    outbox: Path,
    *,
    amount: float = 100.0,
    base: str = "USD",
    quote: str = "EUR",
) -> RunId:
    """Execute and record the toy agent once. Returns the run id."""
    send_email = make_send_email(outbox)
    with recorder.record(CAPABILITIES) as run:
        policy = run.call_tool(
            "search_policy", EffectClass.PURE_LOCAL, search_policy, query="currency conversion"
        )
        rate = run.call_tool(
            "get_exchange_rate",
            EffectClass.EXTERNAL_READ,
            get_exchange_rate,
            base=base,
            quote=quote,
            api_key=DEMO_API_KEY,
        )
        converted = round(amount * rate, 2)
        body = f"{amount:.2f} {base} = {converted:.2f} {quote} (rate {rate}, source: toy stub)."
        receipt = run.call_tool(
            "send_email",
            EffectClass.EXTERNAL_WRITE,
            send_email,
            to="finance@example.com",
            subject=f"Conversion {base}->{quote}",
            body=body,
        )
        run.set_outcome(
            {"converted": converted, "rate": rate, "policy_hits": len(policy), "email": receipt}
        )
        return run.run_id
