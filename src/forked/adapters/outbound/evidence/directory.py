"""Evidence packages as plain directories (no archive: nothing to extract, nothing to traverse)."""

from pathlib import Path

from forked.application.errors import StorageFailure
from forked.domain.evidence.package import UnsafePackagePath, is_safe_path


def write_package(target: Path, files: dict[str, bytes]) -> None:
    """Write ``files`` under ``target``. Refuses a non-empty target: never overwrite evidence."""
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise StorageFailure(f"refusing to write into existing non-empty path {target}")
    for path, data in sorted(files.items()):
        if not is_safe_path(path):
            raise UnsafePackagePath(f"refusing package path {path!r}")
        dest = target / path
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        except OSError as exc:
            raise StorageFailure(f"cannot write {path}: {exc}") from exc


def read_package(root: Path) -> dict[str, bytes]:
    """Read every file under ``root``. Symlinks are rejected *before* anything is resolved."""
    if not root.is_dir() or root.is_symlink():
        raise StorageFailure(f"{root} is not an evidence package directory")
    files: dict[str, bytes] = {}
    # ponytail: whole package in memory; stream if packages grow past a few hundred MB.
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise UnsafePackagePath(f"symlink in package: {rel}")
        if path.is_file():
            files[rel] = path.read_bytes()
    return files
