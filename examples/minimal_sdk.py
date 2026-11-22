"""The smallest useful FORKED example: instrument your own workflow with the Python SDK.

No framework, no model, no network. Two tools: a price lookup (an external *read*) and a
notification (an external *write*, here just appended to a list). Run it::

    uv run python -m examples.minimal_sdk
"""

import tempfile
from contextlib import AbstractContextManager
from pathlib import Path

from forked.adapters.inbound.sdk.recorder import RecordedRun
from forked.bootstrap.container import build_application
from forked.domain.branches.branch import Intervention
from forked.domain.effects.effect_class import EffectClass
from forked.domain.effects.policy import EffectDenied
from forked.domain.runs.capabilities import AdapterCapabilities, tool_capture_point
from forked.domain.shared.identifiers import RunId

# What this workflow can capture, and what it cannot — shown in every report.
CAPABILITIES = AdapterCapabilities(
    name="minimal-workflow",
    version="1.0.0",
    capture_points=frozenset({tool_capture_point("price"), tool_capture_point("notify")}),
    limitations=("prices come from a fixed local table", "notify only appends to a list"),
)

PRICES = {"widget": 10.0}
NOTIFICATIONS: list[str] = []


def price(item: str) -> float:
    return PRICES[item]


def notify(message: str) -> bool:
    NOTIFICATIONS.append(message)
    return True


def workflow(session: AbstractContextManager[RecordedRun]) -> RunId:
    """Your code, unchanged except that tool calls go through ``run.call_tool``."""
    with session as run:
        unit = run.call_tool("price", EffectClass.EXTERNAL_READ, price, item="widget")
        total = unit * 3
        try:
            run.call_tool("notify", EffectClass.EXTERNAL_WRITE, notify, message=f"total {total}")
            sent = True
        except EffectDenied:  # in a branch, a changed write is denied: handle it like any error
            sent = False
        run.set_outcome({"total": total, "notified": sent})
        return run.run_id


def main(workdir: Path | None = None) -> None:
    root = workdir or Path(tempfile.mkdtemp(prefix="forked-minimal-"))
    app = build_application(root / "store")

    baseline = workflow(app.recorder.record(CAPABILITIES))
    print(f"recorded  {baseline}  notifications sent: {len(NOTIFICATIONS)}")

    workflow(app.recorder.replay(baseline, CAPABILITIES))
    print(f"replayed  nothing executed; notifications sent: {len(NOTIFICATIONS)}")

    # sequence 1 is the `price` tool.call (see `forked inspect <run> --events`)
    intervention = Intervention(checkpoint=1, value=12.5)
    branch = workflow(app.recorder.branch(baseline, CAPABILITIES, intervention))
    result = app.compare_runs.execute(baseline, branch)
    for field, before, after in result.outcome_changes:
        print(f"branch    {field}: {before} -> {after}")
    print(f"claim     {result.claim_level} (one run pair; not a causal estimate)")
    print(f"sent      {len(NOTIFICATIONS)} notification(s) in total — the branch's was denied")


if __name__ == "__main__":
    main()
