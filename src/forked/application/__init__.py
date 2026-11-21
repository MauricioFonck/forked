"""Application layer: use cases that orchestrate the domain through ports.

Rule: imports ``forked.domain`` and ``forked.application`` only — never adapters,
bootstrap, or third-party frameworks. Enforced by ``tests/guardians``.
"""
