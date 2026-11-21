"""Schema versioning rules for persisted artifacts.

Semantic versioning: readers reject an unsupported **major** version; a newer minor
version may only add optional fields (docs/06-cip-protocol-draft.md §6.9).
"""

from forked.domain.shared.errors import UnsupportedSchemaVersion

EVENT_SCHEMA_VERSION = "0.1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({0})


def ensure_supported(version: str) -> None:
    """Raise ``UnsupportedSchemaVersion`` unless ``version`` has a supported major."""
    parts = version.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise UnsupportedSchemaVersion(f"schema version is not MAJOR.MINOR.PATCH: {version!r}")
    if int(parts[0]) not in SUPPORTED_MAJOR_VERSIONS:
        raise UnsupportedSchemaVersion(
            f"schema major version {parts[0]} is not supported "
            f"(supported: {sorted(SUPPORTED_MAJOR_VERSIONS)})"
        )
