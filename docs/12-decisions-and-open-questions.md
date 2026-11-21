# 12. Architecture Decisions and Open Questions

## 12.1 Provisional decisions
- D-011: Adopt Hexagonal Architecture (Ports & Adapters) within a modular monolith; see ADR-001.
- D-012: Enforce inward dependency direction: domain → no outer layers; application → ports; adapters implement ports.
- D-013: Use lightweight DDD, explicit composition root, effect-policy strategies and lifecycle state machines.
- D-014: Defer microservices, full CQRS, full event sourcing and third-party plugin execution until measurable needs exist.
- D-001: Start with a modular Python core.
- D-002: Local-first, offline-capable MVP.
- D-003: JSONL event artifacts plus SQLite metadata index.
- D-004: Replay recorded observations; do not repeat external operations by default.
- D-005: External writes and unknown effects are denied by default.
- D-006: CLI before Studio.
- D-007: Integrate with OpenTelemetry rather than replace it.
- D-008: Use SHA-256 for artifact integrity in MVP.
- D-009: Do not claim universal deterministic replay or automatic causal proof.
- D-010: Proposed software license Apache-2.0, subject to review.

## 12.2 Open questions requiring evidence
1. Which first adapter yields the strongest demonstration with the least framework-specific complexity?
2. What is the minimum useful checkpoint contract across frameworks?
3. How should large event payloads be externalized and encrypted?
4. Which invariants can be verified generically, and which require adapter-specific verifiers?
5. How should stochastic model calls be represented: exact recorded output, repeated sampling, or both?
6. What is the right representation for time, randomness, and environment variables?
7. How should we compare branches when an intervention changes the downstream event topology?
8. What overhead is acceptable for capture and hashing?
9. Which baseline tools provide a fair comparison for each benchmark scenario?
10. Is CIP a useful distinct protocol, or should it be an extension/profile over existing formats?

## 12.3 Mandatory prior-art gate
Before calling CIP novel or proposing it as a standard:
- search academic literature;
- search GitHub and package registries;
- review OpenTelemetry, OpenInference, W3C Trace Context, OCI, and relevant workflow protocols;
- search patents if commercialization requires it;
- compare data models and semantics, not only product names;
- publish a prior-art matrix with dated URLs and confidence levels.

## 12.4 Naming
FORKED, CIP, and FCRB are working names. Check package-name, domain, trademark, and repository availability before public launch.
