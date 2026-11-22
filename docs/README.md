# FORKED documentation

Two sets of documents live here. Pick by what you need.

## User guide — how to use FORKED

Start here if you want to run it or instrument your own code. These pages describe what the software
**does today**, and what it does not.

| Page | What it covers |
|---|---|
| [1. Getting started](guide/01-getting-started.md) | Install from source, your first minute, where data lives |
| [2. Concepts](guide/02-concepts.md) | Run, event, effect class, replay, branch, invariants, claim level, evidence |
| [3. CLI reference](guide/03-cli-reference.md) | Every command, its options and the exit codes |
| [4. Instrumenting your workflow](guide/04-instrumenting-your-workflow.md) | Python SDK, Pydantic AI, OpenTelemetry, writing an adapter |
| [5. Guarantees and limits](guide/05-guarantees-and-limits.md) | What is promised, how it is checked, what is **not** promised |
| [6. Reproducing and reviewing](guide/06-reproducing-and-reviewing.md) | Reproduce the benchmark, review the project, report back |

Runnable examples: [`examples/`](../examples/README.md). Benchmark: [`benchmarks/`](../benchmarks/README.md).
Release notes: [`release-notes/`](release-notes/v0.1.0-alpha.1.md) and the [CHANGELOG](../CHANGELOG.md).

## Design documents — why it is built this way

The project proposal (v0.2) and the decisions that refine it. They describe intent and rationale;
where they differ from the user guide, the guide describes the current behavior.

| Document | Topic |
|---|---|
| [01 Charter](01-project-charter.md) · [02 Problem & hypotheses](02-problem-and-research-hypotheses.md) | Mission, scope, falsifiable hypotheses H1–H5 |
| [03 Competitive landscape](03-competitive-landscape.md) | LangGraph, Temporal, Phoenix, OpenTelemetry GenAI, LangSmith |
| [04 Requirements](04-product-requirements.md) · [05 Architecture](05-architecture.md) · [14 ADR-001](14-adr-001-hexagonal-architecture.md) | Use cases, hexagonal modular monolith |
| [06 CIP protocol draft](06-cip-protocol-draft.md) · [07 Security & privacy](07-security-and-privacy.md) | Event envelope, effect taxonomy, claim levels, threat model |
| [08 Benchmarks & validation](08-benchmarks-and-validation.md) · [09 Roadmap](09-roadmap-and-backlog.md) | FCRB, phases |
| [10 Governance](10-governance-and-open-source.md) · [11 Partnerships](11-partnership-strategy.md) · [12 Decisions & open questions](12-decisions-and-open-questions.md) | Project and community |
| [13 Claude Code execution plan](13-claude-code-execution-plan.md) · [Diagrams](diagrams.md) · [References](references.md) | |
