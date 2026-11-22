"""The expense agent's three tools, shared by every framework example.

Local stand-ins (no network, no real email): a fixed rate table, a policy search, and a "mail
server" that writes a JSON file to an outbox directory.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from forked.demo import toy_agent
from forked.domain.effects.effect_class import EffectClass

EFFECTS = {
    "search_policy": EffectClass.PURE_LOCAL,
    "get_exchange_rate": EffectClass.EXTERNAL_READ,
    "send_email": EffectClass.EXTERNAL_WRITE,
}
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
