"""GUARDIAN: ``contexto/`` is a connected graph with no broken links.

``contexto/`` is the project memory. A document nobody links to does not exist for the
next reader, and a broken link sends them nowhere. Rules (one test each):

1. Every relative ``](target)`` link resolves to an existing file or folder, with exact
   letter case (Windows and macOS forgive case; Linux CI does not).
2. Every ``.md`` under ``contexto/`` is reachable from ``contexto/README.md`` following
   relative ``.md`` links that stay inside ``contexto/``.
3. No ``*-package.md`` files (temporary subagent context bundles).
4. Every ``docs/superpowers/specs/NNN-*`` folder has a row in ``docs/superpowers/README.md``.

Ignored: fenced code blocks, inline code, ``http(s):``/``mailto:`` links, bare anchors and
``.obsidian/``. If it fails, link the document from its index or fix the path. An entry
in ``EXCEPTIONS`` needs its reason on the same line.
"""

import os
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
CONTEXT = ROOT / "contexto"
GRAPH_ROOT = CONTEXT / "README.md"
SPECS_INDEX = CONTEXT / "docs" / "superpowers" / "README.md"
SPECS_DIR = CONTEXT / "docs" / "superpowers" / "specs"

EXCEPTIONS: dict[str, str] = {}

_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
_INLINE_CODE = re.compile(r"(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)")
_LINK = re.compile(r"\]\(([^)]*)\)")


def _markdown_files() -> list[Path]:
    return sorted(p for p in CONTEXT.rglob("*.md") if ".obsidian" not in p.parts)


def _without_code(text: str) -> str:
    out: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        match = _FENCE.match(line)
        if fence:
            if match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence):
                fence = None
            out.append("")
            continue
        if match:
            fence = match.group(1)
            out.append("")
            continue
        out.append(_INLINE_CODE.sub("", line))
    return "\n".join(out)


def _links(path: Path) -> list[tuple[str, Path]]:
    found = []
    for match in _LINK.finditer(_without_code(path.read_text(encoding="utf-8"))):
        target = match.group(1).strip()
        if target.startswith("<"):
            target = target[1 : target.find(">")] if ">" in target else target[1:]
        else:
            target = re.sub(r"\s+[\"'(].*$", "", target)
        if not target or target.startswith("#") or re.match(r"^(https?|mailto):", target, re.I):
            continue
        clean = unquote(target.split("#")[0])
        if clean:
            # normpath, not resolve(): on Windows resolve() silently fixes letter case,
            # which would hide a link that is broken on case-sensitive Linux CI.
            found.append((target, Path(os.path.normpath(path.parent / clean))))
    return found


def _exists_exact_case(path: Path) -> bool:
    """True if ``path`` exists with exactly this letter case in every component."""
    if not path.exists():
        return False
    relative = path.relative_to(ROOT) if path.is_relative_to(ROOT) else None
    if relative is None:
        return True  # outside the repo (should not happen); existence is enough
    current = ROOT
    for part in relative.parts:
        if part not in {child.name for child in current.iterdir()}:
            return False
        current = current / part
    return True


def _rel(path: Path) -> str:
    return path.relative_to(CONTEXT).as_posix()


def test_guardian_reads_something() -> None:
    assert GRAPH_ROOT.is_file()
    assert len(_markdown_files()) > 20


def test_1_every_relative_link_resolves() -> None:
    broken = [
        f"{_rel(path)} -> {original}"
        for path in _markdown_files()
        if _rel(path) not in EXCEPTIONS
        for original, target in _links(path)
        if not _exists_exact_case(target)
    ]
    assert broken == [], "broken links:\n" + "\n".join(broken)


def test_2_every_document_is_reachable_from_the_root() -> None:
    seen = {GRAPH_ROOT}
    pending = [GRAPH_ROOT]
    while pending:
        current = pending.pop()
        for _, target in _links(current):
            inside = CONTEXT in target.parents
            if inside and target.suffix == ".md" and target.is_file() and target not in seen:
                seen.add(target)
                pending.append(target)
    orphans = [_rel(p) for p in _markdown_files() if p not in seen and _rel(p) not in EXCEPTIONS]
    assert orphans == [], "documents not reachable from contexto/README.md:\n" + "\n".join(orphans)


def test_3_no_temporary_package_files() -> None:
    assert [_rel(p) for p in _markdown_files() if p.name.endswith("-package.md")] == []


def test_4_every_spec_folder_is_indexed() -> None:
    index = SPECS_INDEX.read_text(encoding="utf-8")
    missing = [
        folder.name
        for folder in sorted(SPECS_DIR.iterdir())
        if folder.is_dir()
        and re.match(r"^\d{3}-", folder.name)
        and f"specs/{folder.name}/" not in index
    ]
    assert missing == [], "spec folders without a row in the specs index: " + ", ".join(missing)
