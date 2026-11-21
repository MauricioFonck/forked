# Claude Code project instructions — FORKED

You are the senior implementation assistant for FORKED. Treat the repository documentation as the product and engineering source of truth.

## Mission
Build a local-first, open-source research runtime for controlled counterfactual experiments over instrumented software workflows and AI-agent executions. The first release must demonstrate a narrow, honest, reproducible vertical slice—not a broad but fake platform.

## Read first
1. `contexto/README.md` — the project memory: where everything is, current state, what not to break
2. `contexto/forked/estado-actual.md` — what is implemented today and what is next
3. `README.md`
4. `docs/14-adr-001-hexagonal-architecture.md`
5. `docs/01-project-charter.md`
6. `docs/02-problem-and-research-hypotheses.md`
7. `docs/04-product-requirements.md`
8. `docs/05-architecture.md`
9. `docs/06-cip-protocol-draft.md`
10. `docs/07-security-and-privacy.md`
11. `docs/08-benchmarks-and-validation.md`
12. `docs/12-decisions-and-open-questions.md`
13. `contexto/forked/decisiones-arquitectura/README.md` — ADR-002+ refine the docs; where they differ, the ADR wins

## Architecture mandate — read before coding
- **Use Hexagonal Architecture (Ports & Adapters) inside a modular monolith.** `docs/05-architecture.md` and `docs/14-adr-001-hexagonal-architecture.md` are authoritative.
- Organize code by `domain`, `application`, `application/ports`, `adapters/inbound`, `adapters/outbound`, and `bootstrap` (composition root).
- Dependency direction is inward: domain imports no application/infrastructure/framework code; application depends on ports, never concrete adapters.
- Keep the core framework-, provider-, database-, CLI- and UI-independent.
- Use lightweight DDD for domain language, value objects, aggregates and invariants; do not introduce ceremony or abstractions without a use case.
- Use Strategy/Policy objects for effect decisions, explicit state machines for lifecycle transitions, and small pipeline stages for capture/redaction.
- Use Repository/Unit of Work only where persistence boundaries justify them. Use CQRS only if read/report needs become materially different. Do not call the whole system event-sourced.
- Wire concrete dependencies in one composition root. Prefer `typing.Protocol` and explicit constructors over a heavyweight DI framework.
- Add adapter contract tests and enforce dependency boundaries in CI where practical.
- Any architecture exception requires an ADR describing context, alternatives, consequences and migration.

## Non-negotiable engineering rules
- Do not claim deterministic replay for arbitrary programs.
- Distinguish replaying recorded observations from re-executing external operations.
- Never repeat external writes during replay by default.
- No real-world side effect may execute in an experimental branch unless an explicit, documented, user-approved policy permits it. Default is deny.
- Do not silently mock an external system and report the result as a real-world outcome.
- Every run must identify captured inputs, environment metadata, tool versions, and missing evidence.
- Mark each invariant as `verified`, `violated`, or `unknown`.
- Mark causal conclusions as `descriptive`, `conditional`, or `unsupported`; do not overstate causality.
- Redact secrets before persistence. Never store API keys, credentials, or raw sensitive data by default.
- Keep the core provider-neutral. Provider adapters belong behind interfaces.
- Prefer small modules, typed schemas, deterministic unit tests, and explicit errors.
- Do not add cloud dependencies to the local-first MVP.
- Do not introduce Kubernetes, distributed queues, or microservices before a measured need.
- Keep protocol schemas versioned and backward-compatibility tests.

## Required workflow for every task
1. Inspect the existing repository and current tests before changing code.
2. State the smallest implementation plan.
3. Implement one vertical slice at a time.
4. Add tests for success, failure, unsafe operation, and missing evidence.
5. Run formatting, linting, type checks, and tests.
6. Update relevant docs and examples.
7. Summarize files changed, tests run, known limitations, and next task.
8. Never mark a task complete if acceptance criteria are not met.

## First milestone
Implement a local event recorder and deterministic replay of recorded tool observations for a toy workflow. Then add branch metadata and a comparison report. No live external writes. No claim of general OS snapshotting.

## Architecture boundaries
- `domain`: pure business concepts, invariants, value objects and domain errors.
- `application`: use cases, commands/queries and DTOs.
- `application/ports`: interfaces required by use cases.
- `adapters/inbound`: CLI, SDK and future UI/API entry points.
- `adapters/outbound`: JSONL, SQLite, filesystem, OpenTelemetry and framework/provider integrations.
- `bootstrap`: composition root that wires implementations.
- Logical contexts include runs/capture, replay, branches/interventions, effects/safety, comparison/invariants and evidence.
- These are modules in one deployable package, not microservices. Do not create empty folders just to match a diagram.

## Definition of done
A feature is done only when it has:
- typed public interfaces;
- tests including negative and safety cases;
- documentation and runnable example;
- explicit failure behavior;
- no hidden network dependency;
- accurate statements about guarantees and limitations.

## Project memory: `contexto/` (NOT NEGOTIABLE)
`contexto/` is the engineering memory (written in Spanish; code and public docs stay in English). A change is not done until its memory is updated **in the same commit**.

Every session that touches code leaves two files:

| When | File | Content |
|---|---|---|
| **Before** editing | `contexto/impacto/YYYY-MM-DD-<topic>.md` | What will be touched and who else uses it; protected behaviors (`CP-nnn` from `contexto/impacto/comportamientos-protegidos.md`) at risk; risk and mitigation. At the end: how each row was verified |
| **During and at close** | `contexto/sesiones/YYYY-MM-DD-<topic>.md` | What was asked, what was found, **every** file changed and why, what was discarded, what is pending, and the verification commands actually run |

Also:
- A new architecture decision → `contexto/forked/decisiones-arquitectura/ADR-NNN-<topic>.md` + its row in the ADR index.
- A non-trivial failure fixed → a record in `contexto/errores/` (`bugs/B-nnn` for product, `errores/E-nnn` for environment) focused on the **concept** that was missing.
- A new behavior that must never break → a `CP-nnn` row with the test that protects it.
- A multi-task piece of work → `contexto/docs/superpowers/specs/NNN-<topic>/` with `spec.md`, `plan.md`, `tasks.md`.
- A bounded context gets implemented or changes → its README in `contexto/modulos/<context>/`.
- Every new document is linked from its folder index. The guardian `tests/guardians/test_context_graph.py` fails on broken links and orphan documents.
- Update `contexto/forked/estado-actual.md` whenever a phase advances.

## Commands
```bash
uv sync                                   # install (Python >= 3.11; uv fetches it if needed)
uv run ruff check . && uv run ruff format --check .
uv run mypy                               # strict, src + tests
uv run pytest                             # unit, contract, security, integration, acceptance, guardians
uv run forked record toy-agent            # demo; FORKED_STORE=<dir> to choose the store
uv run forked inspect <run_id> --events --strict
uv run python scripts/export_schemas.py   # regenerate spec/ after an intentional schema change
```

## Guardians (tests that read the source)
- `tests/guardians/test_dependency_rule.py` — hexagonal dependency direction.
- `tests/guardians/test_published_schema.py` — `spec/` matches the code; golden fixtures stay readable.
- `tests/guardians/test_context_graph.py` — `contexto/` has no broken links or orphan docs.
Never add an exception to a guardian without a written reason (and an ADR for architecture).
