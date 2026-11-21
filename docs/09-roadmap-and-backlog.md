# 9. Roadmap and Engineering Backlog

## Phase 0 — Specification and repository foundation
Deliverables:
- repository scaffold;
- charter and architecture;
- threat model;
- event schema draft;
- protocol naming and prior-art review;
- CI skeleton.

Exit criteria:
- architecture decisions recorded;
- no unsupported claims in README;
- schema review completed.

## Phase 1 — Recorder and local event store
Tasks:
- define typed Run and Event models;
- implement JSONL writer/reader;
- implement sequence validation;
- implement redaction pipeline;
- create toy workflow adapter;
- add SQLite metadata index if needed;
- add fixtures and CLI `record`/`inspect`.

Exit criteria:
- events can be recorded and inspected offline;
- malformed events fail clearly;
- secret-redaction tests pass.

## Phase 2 — Recorded-observation replay
Tasks:
- define observation lookup interface;
- implement replay context;
- add adapter hook to substitute recorded tool results;
- deny missing observations;
- ensure no external write path is reachable in replay mode;
- add replay report.

Exit criteria:
- demo replay returns recorded tool output;
- replay test proves write adapter was not invoked;
- limitations are documented.

## Phase 3 — Branching and interventions
Tasks:
- immutable branch lineage model;
- parent run/checkpoint references;
- one intervention type;
- branch-specific event stream;
- comparison of baseline vs branch;
- invariant statuses.

Exit criteria:
- parent artifacts remain unchanged;
- intervention appears in evidence;
- unknown invariants are not marked verified.

## Phase 4 — Evidence package
Tasks:
- manifest schema;
- SHA-256 artifact hashing;
- deterministic package export;
- offline verifier;
- tamper and missing-file tests.

Exit criteria:
- independent verifier detects changed/missing artifacts;
- verification report separates hash integrity from scientific validity.

## Phase 5 — Adapter and benchmark
Tasks:
- OpenTelemetry ingestion/export bridge;
- one framework adapter selected based on user demand and feasibility;
- FCRB scenarios;
- baseline comparison;
- reproducible benchmark runner.

Exit criteria:
- one end-to-end use case documented;
- independent reproduction instructions work.

## Phase 6 — Public alpha and community
Tasks:
- docs site or well-organized Markdown docs;
- example repository;
- contribution guide;
- issue templates;
- release notes;
- community feedback and external review.

## Prioritized backlog
P0: domain models, event schema, recorder, redaction, replay from recorded observations, default-deny effects, tests.
P1: branch lineage, intervention record, invariant checker, evidence manifest, offline verifier, CLI.
P2: OpenTelemetry bridge, first framework adapter, benchmark runner, Studio prototype.
P3: additional adapters, performance optimization, collaboration features, hosted services.

## Rule
Do not start P2/P3 while P0/P1 acceptance criteria are failing.
