"""Effect taxonomy from the CIP draft (docs/06-cip-protocol-draft.md §6.5)."""

from enum import StrEnum


class EffectClass(StrEnum):
    """What an operation can do to state outside the experiment boundary."""

    PURE_LOCAL = "pure_local"
    """No external state change expected; still subject to sandbox constraints."""

    RECORDED_READ = "recorded_read"
    """Result was captured and is replayed from evidence."""

    EXTERNAL_READ = "external_read"
    """Reads external state; needs a recorded response or an explicit policy."""

    EXTERNAL_WRITE = "external_write"
    """Changes external state; denied in replay and branches by default."""

    LOCAL_WRITE = "local_write"
    """Changes sandbox-local state; only allowed in disposable branch storage."""

    UNKNOWN = "unknown"
    """Cannot be classified; denied by default."""
