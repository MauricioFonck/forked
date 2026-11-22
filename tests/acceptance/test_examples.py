"""The documented examples must keep working: they are the first thing a newcomer runs."""

from pathlib import Path

import pytest

from examples import minimal_sdk


def test_minimal_sdk_example_records_replays_branches_and_denies(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    minimal_sdk.NOTIFICATIONS.clear()

    minimal_sdk.main(tmp_path)

    out = capsys.readouterr().out
    assert "notifications sent: 1" in out
    assert "replayed  nothing executed; notifications sent: 1" in out
    assert "notified: True -> False" in out
    assert "total: 30.0 -> 37.5" in out
    assert "claim     controlled_comparison" in out
    assert len(minimal_sdk.NOTIFICATIONS) == 1  # the replay and the branch sent nothing new
