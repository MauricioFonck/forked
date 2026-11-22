# Changelog

All notable changes are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [SemVer](https://semver.org/) for the package; the CIP schema is versioned separately.

## [Unreleased]

### Fixed (after 0.1.0a1, unreleased)
- Console output is ASCII (a decorative em dash turned into mojibake on Windows); guarded by tests.
- Getting started: how to keep the run id in a shell variable and how to choose the Python interpreter;
  the capture-cost figure is now "roughly 2-5 ms, varies with load".
- Benchmark README: a reproduction log (author; a cold-start AI agent, explicitly **not** independent).

## [0.1.0a1] - 2026-11-22

First public alpha. Pre-alpha quality: see the [release notes](docs/release-notes/v0.1.0a1.md).

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
- Phase 2: replay of recorded observations.
  - `Recorder.replay(run_id, capabilities)` and `forked replay RUN_ID`: re-run the workflow
    with every tool call answered from the recording; tools are never executed.
  - Strict, fail-closed matching (tool name, effect class, redacted inputs, order):
    `ReplayDivergence` / `MissingObservation`; recorded tool errors re-raise as
    `RecordedToolError`.
  - A replay is a new run whose `run.started` payload carries `replay_of`.
- Phase 3: branches, one intervention, effect policy, comparison.
  - `Recorder.branch(parent, capabilities, Intervention(checkpoint, value))` and
    `forked branch RUN_ID --at SEQ --value JSON`: the checkpoint is the sequence of a
    `tool.call`; earlier calls replay strictly, the checkpoint call's result is replaced,
    later calls replay if unchanged or go to the effect policy.
  - `DefaultDenyPolicy` (`default-deny/1`): only declared `pure_local` calls execute;
    everything else raises `EffectDenied`, recorded as a `tool.error`, never executed.
  - Lineage (`branch_of`, `parent_log_digest`, intervention, policy version) is recorded
    in the branch's `run.started`; parent artifacts are only read.
  - `forked compare BASELINE BRANCH [--json]`: per-step diff, outcome changes, five
    invariants (`verified`/`violated`/`unknown`), claim level (`observational` or
    `controlled_comparison`; never causal), missing evidence.
- Phase 4: evidence packages.
  - `forked export BASE BRANCH --out DIR`: deterministic `forked-evidence/1` package —
    `manifest.json` (experiment, environment, policy, invariants, claim, limitations, missing
    evidence, SHA-256 + size of every artifact), `comparison.json`, byte-for-byte run files.
    Refuses non-empty targets, unsafe paths and credential-shaped values.
  - `forked verify DIR [--json]`: offline, needs only the package. Reports integrity
    (changed / missing / unexpected files, manifest problems) separately from validity
    (comparison recomputed from the packaged runs; inflated or mismatched claims are
    `unsupported`; the whole manifest is regenerated from the packaged runs and must match
    exactly, and `comparison.json` must equal the recomputed comparison). Rejects symlinks.
    Exit 1 if either fails.

- Phase 5: first framework adapter, OpenTelemetry bridge, FCRB benchmark.
  - Pydantic AI adapter (`pip install forked-runtime[pydantic-ai]`): one `ForkedToolset` routes
    every tool call through a `RecordedRun`, so recording, replay and branching share one seam.
    `RecordedRun.acall_tool` is the async twin of `call_tool`. ADR-013 records why this framework
    was chosen first.
  - `forked otel-export RUN [--include-payloads]`: OTLP/JSON `forked.run` span plus one
    `execute_tool` span per call (GenAI attribute names, `forked.*` for effect class, capture
    status, policy decision). Deterministic; payloads left out unless requested.
  - `forked otel-import FILE`: tool spans become a run; every effect is `unknown`, completeness is
    unknown, malformed or oversized traces are rejected.
  - `python -m benchmarks.fcrb`: ten scenarios from docs/08, an executed plain-log baseline,
    capture overhead, `results.json` + `REPORT.md`. Provisional and not validated.
  - `build_application(probe=...)`; `examples/pydantic_ai_expense_agent.py`.

- LangGraph adapter (`pip install forked-runtime[langgraph]`): `forked_tool_node(tools, run, effects)`
  returns a `ToolNode` whose `wrap_tool_call` / `awrap_tool_call` route every call through a
  `RecordedRun`. Recording returns the original `ToolMessage`; replay answers from the recording and
  never executes the tool; tool results are the text LangGraph produces; a `Command` result is
  rejected; parallel calls of one step are serialized. `examples/langgraph_expense_agent.py`.
- FCRB: LangGraph time travel is now an **executed** baseline for S04 (resuming from the checkpoint
  before `send_email` sent the email again, as its documentation says); S10 compares three adapters;
  the report records framework versions.
- `docs/15-prior-art-matrix.md`: first-pass prior-art review (platforms, six open-source projects, five
  papers) with sources, dates and confidence; the README comparison was rewritten from it.

### Not implemented yet
- More framework adapters, independent reproduction of the benchmark, a docs site; user-approved effect policies; more intervention types; signed manifests.
