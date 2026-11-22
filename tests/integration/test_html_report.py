"""The HTML report: complete, deterministic, and safe to open even if the data is hostile."""

import html
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from forked.adapters.inbound.cli.app import app as cli
from forked.bootstrap.container import build_application
from forked.domain.effects.effect_class import EffectClass
from tests.conftest import CAPS

runner = CliRunner()


def _record_pair(store: Path) -> tuple[str, str]:
    recorded = runner.invoke(cli, ["record", "toy-agent", "--store", str(store)])
    run = recorded.output.split()[1]
    branched = runner.invoke(
        cli, ["branch", run, "--at", "3", "--value", "0.5", "--store", str(store)]
    )
    match = re.search(r"as (run_[0-9a-f]+)", branched.output)
    assert match
    return run, match.group(1)


def test_report_for_one_run(tmp_path: Path) -> None:
    store, out = tmp_path / "store", tmp_path / "r.html"
    run, _ = _record_pair(store)

    result = runner.invoke(cli, ["report", run, "--out", str(out), "--store", str(store)])

    assert result.exit_code == 0, result.output
    page = out.read_text(encoding="utf-8")
    assert run in page
    for expected in (
        "get_exchange_rate",
        "external_write",
        "pure_local",
        "redacted",
        "tool.result",
    ):
        assert expected in page
    assert "Baseline vs branch" not in page  # no branch asked


def test_report_for_a_branch_shows_the_fork_the_invariants_and_the_evidence(tmp_path: Path) -> None:
    store, out = tmp_path / "store", tmp_path / "r.html"
    run, branch = _record_pair(store)

    result = runner.invoke(cli, ["report", run, branch, "--out", str(out), "--store", str(store)])

    assert result.exit_code == 0, result.output
    page = out.read_text(encoding="utf-8")
    assert "<svg" in page
    for decision in ("dec-deny", "dec-intervene", "dec-replay"):
        assert decision in page
    assert "controlled_comparison" in page
    assert "inv_parent_unchanged" in page
    assert "st-verified" in page
    assert "Evidence package" in page
    assert "package_digest" in page
    assert "not a causal estimate" in page.lower()
    assert "denied" in page  # the denied email's recorded reason is visible


def test_report_is_deterministic(tmp_path: Path) -> None:
    store = tmp_path / "store"
    run, branch = _record_pair(store)
    a, b = tmp_path / "a.html", tmp_path / "b.html"
    for target in (a, b):
        assert (
            runner.invoke(
                cli, ["report", run, branch, "--out", str(target), "--store", str(store)]
            ).exit_code
            == 0
        )
    assert a.read_bytes() == b.read_bytes()


def test_report_loads_nothing_and_runs_no_script(tmp_path: Path) -> None:
    store, out = tmp_path / "store", tmp_path / "r.html"
    run, branch = _record_pair(store)
    runner.invoke(cli, ["report", run, branch, "--out", str(out), "--store", str(store)])
    page = out.read_text(encoding="utf-8")

    decoded = html.unescape(page)  # the policy sits in an attribute, so its quotes are entities
    assert "Content-Security-Policy" in decoded
    assert "default-src 'none'" in decoded
    assert "script-src" not in decoded  # nothing may run: default-src 'none' covers it
    assert "<script" not in page.lower()
    assert not re.search(r"""(?:src|href|action)\s*=\s*["']?(?:https?:)?//""", page)
    assert "url(" not in page
    assert "@import" not in page


def test_hostile_recorded_data_is_escaped(tmp_path: Path) -> None:
    store, out = tmp_path / "store", tmp_path / "r.html"
    app = build_application(store)
    attack = "<script>alert(1)</script>"
    with app.recorder.record(CAPS) as run:
        run.call_tool(
            'echo"><img src=x onerror=alert(2)>',
            EffectClass.PURE_LOCAL,
            lambda q: f"<b>{q}</b>",
            q=attack,
        )
        run_id = run.run_id

    result = runner.invoke(cli, ["report", run_id.value, "--out", str(out), "--store", str(store)])

    assert result.exit_code == 0, result.output
    page = out.read_text(encoding="utf-8")
    assert "<script" not in page.lower()
    assert "<img" not in page.lower()
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page
    assert (
        "onerror=alert(2)" not in page.replace("&gt;", "").replace("&quot;", "")
        or "<img" not in page
    )
    assert "&lt;img src=x onerror=alert(2)&gt;" in page


def test_unknown_run_and_non_branch_exit_2(tmp_path: Path) -> None:
    store, out = tmp_path / "store", tmp_path / "r.html"
    run, _ = _record_pair(store)
    other = runner.invoke(cli, ["record", "toy-agent", "--store", str(store)]).output.split()[1]

    missing = runner.invoke(
        cli, ["report", "run_deadbeefdeadbeef", "--out", str(out), "--store", str(store)]
    )
    not_branch = runner.invoke(
        cli, ["report", run, other, "--out", str(out), "--store", str(store)]
    )

    assert missing.exit_code == 2
    assert "error[run_not_found]" in missing.output
    assert not_branch.exit_code == 2
    assert "error[not_a_branch]" in not_branch.output
    assert not out.exists()


def test_open_flag_opens_the_file_in_the_browser(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened: list[str] = []

    def fake_open(url: str) -> bool:
        opened.append(url)
        return True

    monkeypatch.setattr("webbrowser.open", fake_open)
    store, out = tmp_path / "store", tmp_path / "r.html"
    run, _ = _record_pair(store)

    runner.invoke(cli, ["report", run, "--out", str(out), "--open", "--store", str(store)])

    assert opened == [out.resolve().as_uri()]
