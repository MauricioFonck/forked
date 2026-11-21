"""Typed errors for expected failures.

Every expected failure in FORKED is a ``ForkedError`` with a stable ``code`` so that
callers (CLI, SDK, future API) can react without parsing messages. Third-party
exceptions are translated into these types at adapter boundaries.
"""


class ForkedError(Exception):
    """Base class for every expected FORKED failure."""

    code = "forked_error"


class DomainError(ForkedError):
    """A domain rule was violated."""

    code = "domain_error"


class InvalidIdentifier(DomainError):
    """An identifier does not match its required format."""

    code = "invalid_identifier"


class InvalidEvent(DomainError):
    """An event violates the event envelope invariants."""

    code = "invalid_event"


class IllegalTransition(DomainError):
    """A lifecycle transition is not allowed from the current state."""

    code = "illegal_transition"


class UnsupportedSchemaVersion(DomainError):
    """An artifact declares a schema major version this reader does not support."""

    code = "unsupported_schema_version"
