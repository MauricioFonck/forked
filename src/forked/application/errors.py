"""Application-level failures. Adapters translate their own exceptions into these."""

from forked.domain.shared.errors import ForkedError


class RunNotFound(ForkedError):
    code = "run_not_found"


class CorruptRecording(ForkedError):
    """A persisted artifact cannot be parsed or violates its schema."""

    code = "corrupt_recording"


class StorageFailure(ForkedError):
    """The storage adapter could not read or write."""

    code = "storage_failure"


class CaptureFailed(ForkedError):
    """An event could not be captured. The run is marked incomplete when possible."""

    code = "capture_failed"
