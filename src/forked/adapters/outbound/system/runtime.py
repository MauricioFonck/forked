"""Real clock, id generator and environment probe."""

import platform
import secrets
from datetime import UTC, datetime

from forked import __version__
from forked.domain.runs.capabilities import AdapterCapabilities
from forked.domain.runs.environment import EnvironmentFingerprint
from forked.domain.shared.identifiers import EventId, RunId


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class RandomIdGenerator:
    """128-bit random ids. Not time-ordered: ordering lives in ``sequence``."""

    def new_run_id(self) -> RunId:
        return RunId(RunId.PREFIX + secrets.token_hex(16))

    def new_event_id(self) -> EventId:
        return EventId(EventId.PREFIX + secrets.token_hex(16))


class PlatformProbe:
    """Captures interpreter and OS facts.

    Deliberately excludes hostname, user name, paths and environment variables: they are
    identifying and not needed to explain a divergent replay at this stage.
    """

    def fingerprint(self, capabilities: AdapterCapabilities) -> EnvironmentFingerprint:
        return EnvironmentFingerprint.of(
            {
                "python_version": platform.python_version() or None,
                "python_implementation": platform.python_implementation() or None,
                "platform": platform.platform(terse=True) or None,
                "forked_version": __version__,
                "adapter": capabilities.name,
                "adapter_version": capabilities.version,
            }
        )
