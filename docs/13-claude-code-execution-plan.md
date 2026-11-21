# 13. Claude Code Execution Plan

## Operating mode
Claude Code should work as a careful senior engineer, not autonomously expand scope. Implement one milestone at a time, inspect the repository, ask for confirmation only when a decision materially changes scope or creates external side effects, and never fabricate test results.

## First prompt (copy into Claude Code)

```text
You are the senior engineer for FORKED. Read README.md, CLAUDE.md, and all documents in docs/ before coding.

Your first task is NOT to implement the whole platform. Perform a repository readiness review. Architecture is mandatory: use Hexagonal Architecture (Ports & Adapters) inside a modular monolith, as specified in docs/05-architecture.md and ADR-001. Do not substitute a layered, microservices or framework-centric design.

Perform this review:
1. Summarize the problem and the exact v0 scope.
2. Identify contradictions, missing decisions, risky assumptions, and unsupported claims in the documentation.
3. Propose a minimal package structure for Phase 1 using domain/application/ports/adapters/bootstrap. Show the allowed dependency direction.
4. Define typed domain models for Run, Event, CaptureStatus, EffectClass, and AdapterCapabilities.
5. Propose the JSON event schema and 5 representative fixtures.
6. Define tests for ordering, schema validation, redaction, malformed events, and missing capture metadata.
7. Produce an implementation plan with small tasks and acceptance criteria.
8. Identify which interfaces are genuine outbound ports and which abstractions would be premature.
9. Propose a lightweight automated architecture-boundary check and adapter contract-test strategy.

Do not create cloud services, call external APIs, run real-world writes, or add a dashboard. Do not claim universal deterministic replay. Wait for review before implementing.
```

## Phase 1 implementation prompt

```text
Implement Phase 1 only: a local event recorder and reader for the toy workflow described in docs/04-product-requirements.md.

Requirements:
- Python package with typed models and the hexagonal boundaries defined in docs/05-architecture.md.
- Domain logic must not import Pydantic, Typer, SQLite, filesystem adapters or third-party framework SDKs.
- Application use cases depend on ports; concrete adapters are wired only in bootstrap.
- Append-only JSONL event storage.
- Stable sequence numbers and run IDs.
- Redaction before persistence.
- Explicit capture completeness status.
- CLI commands to record a demo and inspect a run.
- Unit tests and negative/security tests.
- Offline operation.
- Update README and usage docs.

Do not implement branching, causal analysis, cloud services, or a web UI yet. Run all tests and report exact commands and results.
```

## Phase 2 implementation prompt

```text
Implement replay of recorded observations only. Keep the use case independent of the JSONL/SQLite implementation through ports. Design a replay context that resolves a requested observation from the event store. If the observation is missing, fail closed. Prove with tests that replay mode cannot invoke external write adapters. Clearly label replay fidelity and unsupported behavior. Update docs and examples.
```

## Phase 3 implementation prompt

```text
Implement logical branch lineage and one intervention type. Keep branch rules in the domain and orchestration in application use cases: replacing a recorded tool observation in a branch. Parent artifacts must remain immutable. Add invariant checks for input dataset hash and adapter version. Report each invariant as verified, violated, or unknown. Do not call the result a causal proof.
```

## Phase 4 implementation prompt

```text
Implement evidence package export and offline verification through an ArtifactStore port. Keep manifest rules in the domain/application boundary and filesystem/archive mechanics in an outbound adapter. Use a versioned manifest and SHA-256 hashes. Prevent archive path traversal. Add tests for modified, missing, and unexpected files. Clearly distinguish artifact integrity from scientific validity.
```

## Code review prompt

```text
Review the current implementation against CLAUDE.md and all relevant docs. Look for:
- unsafe replay or accidental external writes;
- secret leakage;
- false claims of determinism or causality;
- mutable parent artifacts;
- schema/versioning problems;
- missing negative tests;
- unhandled partial capture;
- dependency and license concerns.
Return findings ranked by severity with file/line references. Do not modify code until findings are presented.
```

## Release checklist
- [ ] Tests pass from a clean environment.
- [ ] Type checks and lint pass.
- [ ] No credentials or sensitive fixtures.
- [ ] External writes denied in replay/branch modes.
- [ ] Incomplete capture clearly reported.
- [ ] Evidence verification tested offline.
- [ ] Docs match implementation.
- [ ] License and dependencies reviewed.
- [ ] Benchmark claims supported by published scripts.
