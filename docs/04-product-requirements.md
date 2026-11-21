# 4. Product Requirements and Use Cases

## 4.1 Primary persona
AI application engineer using an agent that calls tools and external services. The engineer needs to understand why a run failed and test a changed decision without accidentally repeating production side effects.

## 4.2 Core user journeys

### UC-01: Capture an execution
1. Developer wraps a toy workflow with the FORKED recorder.
2. Recorder captures ordered events and metadata.
3. Sensitive fields are redacted according to policy.
4. Run is persisted locally.
5. User receives a run ID and capture completeness report.

Acceptance:
- Event order is stable.
- Missing capture fields are explicit.
- Secrets are not persisted in fixtures.
- Capture failure is visible, not silently ignored.

### UC-02: Replay recorded observations
1. User selects a captured run.
2. Replay engine feeds recorded tool responses to the workflow adapter.
3. External writes are not repeated.
4. Replay report identifies deterministic and non-deterministic boundaries.

Acceptance:
- Replay mode cannot invoke a write-capable adapter by default.
- Missing recorded observation fails closed.
- Replay does not claim exact reproduction beyond declared adapter guarantees.

### UC-03: Create a branch
1. User selects a supported checkpoint.
2. FORKED creates a branch with parent run/checkpoint references.
3. User declares an intervention.
4. The system records the intervention and inherited artifacts.
5. Branch runs inside the configured sandbox.

Acceptance:
- Branch lineage is immutable.
- Intervention is explicit and versioned.
- Branch cannot silently mutate parent artifacts.

### UC-04: Compare branches
1. User selects baseline and branch.
2. Comparison engine checks declared invariants.
3. It compares event sequences and selected outputs.
4. It classifies differences and missing evidence.
5. It generates a report.

Acceptance:
- Each invariant has `verified`, `violated`, or `unknown`.
- Reports distinguish observed difference from causal interpretation.
- No fabricated confidence score.

### UC-05: Export evidence
1. User exports an evidence package.
2. Manifest lists artifacts, hashes, schema version, environment metadata, and policies.
3. A verifier checks hashes and schema.
4. Verification result reports tampering, missing artifacts, and unsupported claims.

Acceptance:
- Package can be verified offline.
- Hash verification is independent of causal validity.
- Export excludes secrets by default.

## 4.3 Functional requirements
- FR-001: capture ordered typed events.
- FR-002: record execution metadata and adapter version.
- FR-003: redact configured sensitive fields.
- FR-004: store runs locally.
- FR-005: replay recorded observations without invoking external side effects.
- FR-006: create branch lineage from supported checkpoints.
- FR-007: represent interventions as typed, immutable records.
- FR-008: define and evaluate invariants.
- FR-009: classify effects as read, write, external, local, unknown.
- FR-010: default-deny effectful operations in experimental branches.
- FR-011: compare two or more runs.
- FR-012: export a portable evidence package.
- FR-013: verify package hashes and schema offline.
- FR-014: import/export OpenTelemetry trace context where available.
- FR-015: expose Python API and CLI for MVP.

## 4.4 Non-functional requirements
- Local-first operation.
- Python 3.11+ baseline (confirm during implementation).
- Typed schemas and versioned serialization.
- Clear error messages.
- No mandatory external network access.
- Structured logs.
- Test coverage for safety-critical code.
- Documentation for every public API.
- Reasonable performance overhead measured by benchmark rather than promised in advance.

## 4.5 MVP scope
In scope:
- toy tool-using workflow;
- JSONL event log;
- local SQLite metadata store;
- recorded-observation replay;
- branch lineage metadata;
- one intervention type (replace a recorded tool result or input value);
- invariant comparison;
- SHA-256 artifact manifest;
- CLI commands `record`, `inspect`, `replay`, `branch`, `compare`, `verify`;
- sample evidence package.

Out of scope:
- arbitrary process memory snapshots;
- transparent OS-level recording;
- multi-host distributed branching;
- production traffic shadowing;
- real-world write replay;
- sophisticated causal inference;
- hosted collaboration UI.
