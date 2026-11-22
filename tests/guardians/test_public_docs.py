"""Guardian: the public documentation cannot rot silently (Phase 6).

* every CLI command is documented in the CLI reference, and nothing documented is invented;
* relative links in the README and the user-facing pages resolve to real files;
* every ``forked <command>`` mentioned in those pages is a real command;
* every Python snippet in the guide at least parses.
"""

import ast
import re
from pathlib import Path

import pytest
import typer.main

from forked.adapters.inbound.cli.app import app

ROOT = Path(__file__).resolve().parents[2]
PAGES = [
    ROOT / "README.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "RELEASING.md",
    ROOT / "docs" / "README.md",
    ROOT / "docs" / "15-prior-art-matrix.md",
    ROOT / "examples" / "README.md",
    ROOT / "benchmarks" / "README.md",
    *sorted((ROOT / "docs" / "guide").glob("*.md")),
    *sorted((ROOT / "docs" / "release-notes").glob("*.md")),
]
COMMANDS = set(typer.main.get_command(app).commands)  # type: ignore[attr-defined]
LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)\)")
FORKED_CMD = re.compile(r"\bforked ([a-z][a-z-]*)")
FENCE = re.compile(r"```python\n(.*?)```", re.DOTALL)


def _local_links(page: Path) -> list[tuple[str, Path]]:
    found = []
    for target in LINK.findall(page.read_text(encoding="utf-8")):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        clean = target.split("#")[0]
        if clean:
            found.append((target, (page.parent / clean).resolve()))
    return found


def test_every_command_is_documented_and_nothing_is_invented() -> None:
    text = (ROOT / "docs" / "guide" / "03-cli-reference.md").read_text(encoding="utf-8")
    documented = set(re.findall(r"^### forked ([a-z-]+)$", text, re.MULTILINE))
    assert documented == COMMANDS, f"CLI reference out of sync: {documented ^ COMMANDS}"


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_relative_links_resolve(page: Path) -> None:
    broken = [t for t, path in _local_links(page) if not path.exists()]
    assert broken == [], f"{page.name}: broken links {broken}"


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_documented_commands_exist(page: Path) -> None:
    text = re.sub(r"```python.*?```", "", page.read_text(encoding="utf-8"), flags=re.DOTALL)
    mentioned = set(FORKED_CMD.findall(text))
    # words that follow "forked" in prose, not commands
    prose = {"runtime", "is", "does", "never", "will", "has", "and", "can", "in", "from", "writes"}
    unknown = {m for m in mentioned if m not in COMMANDS and m not in prose}
    assert unknown == set(), f"{page.name}: unknown commands {unknown}"


@pytest.mark.parametrize(
    "page", sorted((ROOT / "docs" / "guide").glob("*.md")), ids=lambda p: p.name
)
def test_python_snippets_parse(page: Path) -> None:
    for number, block in enumerate(FENCE.findall(page.read_text(encoding="utf-8")), start=1):
        try:
            ast.parse(block)
        except SyntaxError as exc:
            pytest.fail(f"{page.name}: python snippet #{number} does not parse: {exc}")


def test_readme_comparison_points_to_the_evidence_and_admits_what_already_exists() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/15-prior-art-matrix.md" in text
    assert "already done" in text  # recording and replay are not claimed as new
    assert "not found in what we read" in text  # a gap in our reading, not proof of absence
    assert "Nothing here claims FORKED is first, unique or a standard" in text


def test_prior_art_matrix_states_its_limits() -> None:
    text = (ROOT / "docs" / "15-prior-art-matrix.md").read_text(encoding="utf-8")
    assert "A first pass, not a complete survey" in text
    assert "not found in the sources we read" in text.lower() or "Not found" in text
    assert "Not yet reviewed" in text
    assert "https://" in text
    assert "retrieved" in text.lower()


OVERCLAIMS = re.compile(
    r"\b(novel|unique|state[- ]of[- ]the[- ]art|revolutionary|breakthrough|world[- ]first|"
    r"first[- ]ever|industry[- ]standard|de facto standard|the first (open|tool|runtime|framework)|"
    r"the only (tool|runtime|framework))\b",
    re.IGNORECASE,
)


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_no_novelty_or_superlative_claims_while_prior_art_is_unreviewed(page: Path) -> None:
    # Prose that *forbids* such claims quotes the words; those quoted lines are exempt.
    lines = [
        line
        for line in page.read_text(encoding="utf-8").splitlines()
        if not re.search(r"(first, unique or a standard|never[^.]*(first|novel)|treat\s*$)", line)
    ]
    hits = [m.group(0) for line in lines for m in OVERCLAIMS.finditer(line)]
    assert hits == [], f"{page.name}: unreviewed novelty claim {hits} (prior-art gate is open)"
