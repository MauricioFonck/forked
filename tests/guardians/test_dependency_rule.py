"""GUARDIAN: the hexagonal dependency rule (ADR-001, docs/05-architecture.md §5.3).

Reads the source code, not the behavior. It fails when:

1. ``forked.domain`` imports anything outside the standard library and ``forked.domain``;
2. ``forked.application`` imports anything outside the standard library, ``forked.domain``
   and ``forked.application`` (no Pydantic, Typer, adapters or bootstrap);
3. a concrete outbound adapter is imported from anywhere except ``forked.bootstrap`` or
   another outbound adapter.

If it fails: move the import outward, or introduce a port. An exception needs an ADR.
"""

import ast
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src" / "forked"
STDLIB = set(sys.stdlib_module_names) | {"__future__"}


def _module_name(path: Path) -> str:
    rel = path.relative_to(SRC.parent).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                raise AssertionError(f"{path}: relative imports are not allowed")
            if node.module:
                found.append(node.module)
    return found


def _files(package: str) -> list[Path]:
    return sorted((SRC / package.replace("forked.", "").replace(".", "/")).rglob("*.py"))


def _allowed(name: str, prefixes: tuple[str, ...]) -> bool:
    top = name.split(".")[0]
    return top in STDLIB or any(name == p or name.startswith(p + ".") for p in prefixes)


def test_guardian_sees_code() -> None:
    assert len(_files("forked.domain")) >= 5
    assert len(_files("forked.application")) >= 3


@pytest.mark.parametrize(
    ("package", "allowed"),
    [
        ("forked.domain", ("forked.domain",)),
        ("forked.application", ("forked.domain", "forked.application")),
    ],
)
def test_inner_layers_only_import_inward(package: str, allowed: tuple[str, ...]) -> None:
    violations = [
        f"{_module_name(path)} imports {name}"
        for path in _files(package)
        for name in _imports(path)
        if not _allowed(name, allowed)
    ]
    assert violations == [], "dependency rule violated:\n" + "\n".join(violations)


def test_outbound_adapters_are_wired_only_in_bootstrap() -> None:
    violations = []
    for path in sorted(SRC.rglob("*.py")):
        module = _module_name(path)
        if module.startswith(("forked.bootstrap", "forked.adapters.outbound")):
            continue
        for name in _imports(path):
            if name.startswith("forked.adapters.outbound"):
                violations.append(f"{module} imports {name}")
    assert violations == [], "concrete adapters imported outside bootstrap:\n" + "\n".join(
        violations
    )
