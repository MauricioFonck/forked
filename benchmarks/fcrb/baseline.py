"""Baseline: plain application logs (docs/08 §8.4), executed — not described.

A plain-log setup is what many agent projects have today: each tool call appends
``{tool, args, result}`` to a JSONL file. "Replay" from such a log means running the
workflow again with the real tools, because the log has no mechanism to answer a call
from a recorded observation. No hashes, no sequence numbers, no redaction, no effect
classes: every number measured here is measured against those facts, not assumed.
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from forked.demo import toy_agent


class PlainLog:
    def __init__(self, path: Path) -> None:
        self.path = path

    def call(self, name: str, fn: Callable[..., Any], **kwargs: Any) -> Any:
        result = fn(**kwargs)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"tool": name, "args": kwargs, "result": result}) + "\n")
        return result


def run_toy_with_plain_log(log: PlainLog, outbox: Path) -> None:
    """The toy workflow with plain logging instead of FORKED. Same tools, same inputs."""
    send_email = toy_agent.make_send_email(outbox)
    log.call("search_policy", toy_agent.search_policy, query="currency conversion")
    rate = log.call(
        "get_exchange_rate",
        toy_agent.get_exchange_rate,
        base="USD",
        quote="EUR",
        api_key=toy_agent.DEMO_API_KEY,
    )
    body = f"100.00 USD = {round(100 * rate, 2):.2f} EUR (rate {rate}, source: toy stub)."
    log.call(
        "send_email",
        send_email,
        to="finance@example.com",
        subject="Conversion USD->EUR",
        body=body,
    )


def naive_replay(log: PlainLog, outbox: Path) -> None:
    """What 'replay' means with only a plain log: run the workflow again, tools included."""
    run_toy_with_plain_log(log, outbox)


def can_detect_tampering(log: PlainLog) -> bool:
    """Flip a value in the log and run the only check a plain-log consumer has: parse it."""
    text = log.path.read_text(encoding="utf-8")
    tampered = text.replace('"EUR"', '"XXX"', 1)
    if tampered == text:
        raise RuntimeError("tamper probe did not change the log")
    try:
        for line in tampered.splitlines():
            json.loads(line)
    except json.JSONDecodeError:
        return True
    return False  # still parses: the tampering went unnoticed


def can_detect_missing_line(log: PlainLog) -> bool:
    """Drop a line and look for any evidence of it: there is no sequence or count to compare."""
    lines = log.path.read_text(encoding="utf-8").splitlines()
    remaining = lines[:1] + lines[2:]
    try:
        for line in remaining:
            json.loads(line)
    except json.JSONDecodeError:
        return True
    return False


NOT_EXECUTED = {
    "otel-trace-capture": "FORKED's OTel bridge exports to it; a generic capture has no effect "
    "classes, branches or integrity manifest, so most scenarios have no counterpart. Not run.",
    "temporal-replay": "requires a Temporal deployment and deterministic workflow code; not "
    "applicable to the toy workflows used here. Not run.",
    "phoenix-experiments": "requires a Phoenix deployment and an LLM application; not applicable "
    "to offline scripted workflows. Not run.",
}
