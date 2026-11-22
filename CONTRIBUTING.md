# Contributing to FORKED

Thanks for considering a contribution. FORKED is pre-alpha research software: the most
valuable contributions right now are **honest bug reports, adversarial test cases, review
of the CIP draft, and reproductions of our claims**.

## Ground rules

1. **Evidence before claims.** A PR that adds a guarantee adds the test that proves it.
   Never describe a behavior as deterministic, causal or validated unless tests show it.
2. **Safe by default.** Nothing may execute a real external write in replay or branch mode
   unless an explicit, documented, user-approved policy allows it. Default is deny.
3. **No secrets.** Do not commit credentials, real traces, or personal data — fixtures are
   synthetic. Redaction runs before persistence.
4. **Hexagonal boundaries.** `domain` imports only the standard library; `application`
   depends on ports; concrete adapters are wired only in `bootstrap`. A guardian test
   enforces it. Exceptions need an ADR.
5. **Small slices.** One vertical slice per PR, with tests for success, failure, unsafe
   operation and missing evidence.

## Development setup

```bash
# requires uv (https://docs.astral.sh/uv/) — it installs Python if needed
uv sync
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
uv run forked record toy-agent
```

## Workflow

- Open an issue (bug, proposal or [reproduction report](.github/ISSUE_TEMPLATE/reproduction_report.yml)) describing the problem and acceptance criteria.
- Branch from `main`, keep commits focused, and fill in the PR template's checklists.
- Protocol or schema changes: regenerate `spec/` with `uv run python scripts/export_schemas.py`,
  add new golden fixtures (never edit published ones) and follow the versioning rules in
  [`docs/06-cip-protocol-draft.md`](docs/06-cip-protocol-draft.md).
- Maintainers keep an internal engineering memory in [`contexto/`](contexto/README.md)
  (Spanish): session logs, impact analyses, ADRs and failure records. Contributors are
  welcome to read it; you do not need to write to it.

## Where help is most useful

Concrete, scoped work, roughly in order of value. Open an issue first so we agree on acceptance
criteria (including failure and unsafe cases):

1. **Reproduce the benchmark** and file a [reproduction report](docs/guide/06-reproducing-and-reviewing.md).
   The release gate in [`docs/08`](docs/08-benchmarks-and-validation.md) needs someone independent.
2. **Try to break a guarantee** ([guarantees](docs/guide/05-guarantees-and-limits.md)); report bypasses
   privately via [SECURITY.md](SECURITY.md).
3. **A second framework adapter** (LangGraph is the natural next one, and also the natural baseline).
   The contract is in [instrumenting your workflow](docs/guide/04-instrumenting-your-workflow.md#writing-an-adapter-for-another-framework).
4. **A prior-art matrix** with dated URLs and a confidence level for each claim
   ([`docs/12`](docs/12-decisions-and-open-questions.md) §12.3). No claim of novelty until it exists.
5. **More benchmark scenarios or baselines** — especially ones that could make FORKED look bad.
6. **Docs:** anything that confused you on your first run is a bug in the docs.

## Licensing

By contributing you agree your code is licensed under Apache-2.0 and your documentation
under CC BY 4.0 (see [`LICENSE`](LICENSE) and [`GOVERNANCE.md`](GOVERNANCE.md)).
