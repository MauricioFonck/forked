# FCRB — FORKED Counterfactual Reliability Benchmark

> **Provisional name. Pre-alpha. Not validated.** The scenarios show FORKED behaving as specified on
> toy, scripted workflows. They are **not** evidence that the approach works on real agents, and
> nobody independent has reproduced them yet (that is the release gate in
> [`docs/08`](../docs/08-benchmarks-and-validation.md) §8.6).

## What it measures

Ten scenarios from [`docs/08`](../docs/08-benchmarks-and-validation.md) §8.2, each returning
**measured facts**, plus capture overhead. Metrics are reported **separately and never combined into
one score**.

| Id | Scenario | What is measured |
|---|---|---|
| S01 | Deterministic toy workflow with recorded tool calls | replay fidelity, capture completeness, live tool executions during replay |
| S02 | Workflow with time/randomness dependency | nondeterminism outside a tool is *detected*; recorded nondeterminism replays |
| S03 | Agent tool call with recorded external read | Pydantic AI agent: replay fidelity, live external reads (must be 0) |
| S04 | Attempted external write during replay | unsafe effects attempted / executed / prevented |
| S05 | Branch intervention changing one tool observation | branch isolation, invariant verification rate, claim level |
| S06 | Missing event in the recording | gap detected, evidence reported, replay fails closed |
| S07 | Environment version mismatch | mismatch detected, claim downgraded |
| S08 | Tampered evidence artifact | byte tampering vs. re-hashed forgery; integrity vs. validity; evidence completeness |
| S09 | Sensitive field redaction | secret occurrences in the store, the evidence package and an OTel export |
| S10 | Two adapters producing equivalent protocol artifacts | native SDK vs. Pydantic AI adapter: equivalent tool events |

Baseline: **plain application logs**, actually executed against the same scenarios (a naive
"replay" re-runs the tools; a tampered or truncated log still parses). The other baselines named in
`docs/08` §8.4 are **listed with the reason they were not run** — not run, not claimed.

Overhead: capture latency (median and p95 after a discarded warm-up), storage per event. CPU and
memory are **not** measured.

## Reproduce it from a clean clone

Needs [uv](https://docs.astral.sh/uv/) and nothing else: no API key, no network, no model.

```bash
git clone https://github.com/MauricioFonck/forked && cd forked
uv sync --locked                                   # pinned by uv.lock
uv run python -m benchmarks.fcrb --out results/    # exit 0 = no scenario failed
```

It writes `results/results.json` (raw numbers) and `results/REPORT.md` (the table). Everything
except `overhead` and `environment` is deterministic: two runs give identical results, which the
test suite checks. Timings depend on your machine; the report states the environment.

```bash
uv run python -m benchmarks.fcrb --out results/ --runs 1000 --warmup 100   # tighter timings
uv run python -m benchmarks.fcrb --out results/ --no-overhead              # skip timings
```

## Reading a result

* `pass` means FORKED behaved as the scenario specifies. `fail` means it did not — including when a
  scenario crashes (reported, not aborted). `skipped` means an optional extra is missing.
* The benchmark is able to fail: breaking FORKED on purpose (redaction off, replay executing tools,
  claims always "controlled", gaps not reported, hashes not compared, …) makes the matching
  scenario fail; `tests/benchmarks/test_fcrb.py` keeps one such check in the suite.

## Known limits

* Toy workflows; a scripted model; no real LLM, network or external system.
* One executed baseline. No Temporal, LangGraph, Phoenix or generic-OTel comparison yet.
* Verification is exercised in a clean directory, not on a separate machine.
* Capture costs about 2–3 ms per tool call on the author's Windows machine (two events, each
  flushed) — negligible next to an LLM call, but not free.
