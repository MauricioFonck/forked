# Changelog

All notable changes are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [SemVer](https://semver.org/) for the package; the CIP schema is versioned separately.

## [Unreleased]

### Added
- Phase 0: repository foundation — hexagonal package layout, CI (Linux/Windows/macOS,
  Python 3.11–3.14), Apache-2.0 license, security/contribution/governance policies.
- Phase 1: local event recorder and inspector.
  - Typed domain: `Run` aggregate with lifecycle state machine, event envelope, effect
    taxonomy, adapter capabilities, environment fingerprint.
  - Capture pipeline: JSON validation → secret redaction → size limit (oversized payloads
    are omitted and represented by a SHA-256 digest, never truncated).
  - Filesystem store: append-only JSONL events + atomically replaced run metadata.
  - Inspection: ordering checks, capture completeness against declared capture points,
    explicit missing-evidence list; interrupted runs are reported as incomplete.
  - Python SDK (`Recorder`) and CLI: `forked record toy-agent`, `forked inspect`, `forked runs`.
  - Event schema v0.1.0 published in `spec/cip/v0.1/` with golden fixtures.
  - Guardians: hexagonal dependency rule, published-schema drift, `contexto/` link graph.

### Not implemented yet
- Replay, branching, interventions, invariants, comparison, evidence export/verification.
