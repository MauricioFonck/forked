## What and why

<!-- The problem, the change, and the decision behind it. Link the issue. -->

## Safety checklist

- [ ] No external write can execute in replay or branch mode (default deny).
- [ ] No secret, credential or raw sensitive data is persisted by default.
- [ ] No new claim of deterministic replay or causality beyond what tests prove.
- [ ] Domain/application import nothing from adapters or frameworks (guardian green).

## Evidence

- [ ] Tests for success, failure, unsafe operation and missing evidence.
- [ ] `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest` pass.
- [ ] Docs and examples updated; `contexto/` session log and impact analysis added.

<!-- Paste the commands you actually ran and their results. -->
