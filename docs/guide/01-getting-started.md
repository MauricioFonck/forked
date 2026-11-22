# 1. Getting started

> **FORKED is pre-alpha.** It runs on toy workflows and one framework adapter. It is a research
> runtime, not a production tool, and it is **not on PyPI yet**: install from source.

## Install

You need [uv](https://docs.astral.sh/uv/) (it installs Python for you) or Python 3.11+.

```bash
git clone https://github.com/MauricioFonck/forked && cd forked
uv sync --locked          # core + dev tools; pinned by uv.lock
uv run forked --version
```

The core depends only on `pydantic` and `typer`. Framework adapters are **optional extras**
(`forked-runtime[pydantic-ai]`); the core never imports them.

## Your first minute

```bash
uv run forked record toy-agent
```

This runs a small scripted "agent" (convert a currency, check a policy, email finance) and records
every tool call. Copy the run id it prints, then:

```bash
uv run forked inspect <run_id> --events     # every event, its effect class and capture status
uv run forked replay <run_id>               # re-run it from the recording: 0 tools execute
uv run forked branch <run_id> --at 3 --value 0.5   # fork: replace the exchange-rate result
uv run forked compare <run_id> <branch_id>  # what changed, which invariants hold, claim level
uv run forked export <run_id> <branch_id> --out evidence/
uv run forked verify evidence/              # offline: integrity and validity, separately
```

What just happened, and what to notice:

* `record` ran the tools for real — but they are local stand-ins: the exchange rate is a fixed
  table and the "email" is a JSON file under `.forked/toy-outbox/`. **No network, no real email.**
* `replay` answered every call from the recording. The outbox did not grow.
* `branch` replaced one observation. The email body changed, so that write was **denied**, not
  sent, and not faked. `compare` says so (`decision: deny`).
* `verify` needs only the `evidence/` folder. Delete `.forked/` and it still works.

Where things live: `.forked/runs/<run_id>/events.jsonl` (append-only) and `run.json`. Change the
location with `--store` or the `FORKED_STORE` environment variable. Nothing is sent anywhere.

## Instrument your own code

The CLI's `record`, `replay` and `branch` run the **built-in demo**. For your own workflow use the
Python SDK — see [4. Instrumenting your workflow](04-instrumenting-your-workflow.md). A complete
30-line example is [`examples/minimal_sdk.py`](../../examples/minimal_sdk.py):

```bash
uv run python -m examples.minimal_sdk
```

## Where next

* Understand the vocabulary: [2. Concepts](02-concepts.md)
* Every command: [3. CLI reference](03-cli-reference.md)
* What FORKED does and does **not** promise: [5. Guarantees and limits](05-guarantees-and-limits.md)
