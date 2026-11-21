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

- Open an issue (bug or proposal) describing the problem and acceptance criteria.
- Branch from `main`, keep commits focused, and fill in the PR template's checklists.
- Protocol or schema changes: regenerate `spec/` with `uv run python scripts/export_schemas.py`,
  add new golden fixtures (never edit published ones) and follow the versioning rules in
  [`docs/06-cip-protocol-draft.md`](docs/06-cip-protocol-draft.md).
- Maintainers keep an internal engineering memory in [`contexto/`](contexto/README.md)
  (Spanish): session logs, impact analyses, ADRs and failure records. Contributors are
  welcome to read it; you do not need to write to it.

## Licensing

By contributing you agree your code is licensed under Apache-2.0 and your documentation
under CC BY 4.0 (see [`LICENSE`](LICENSE) and [`GOVERNANCE.md`](GOVERNANCE.md)).
