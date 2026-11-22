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
| S10 | Several adapters producing equivalent protocol artifacts | native SDK vs. the Pydantic AI and LangGraph adapters: equivalent tool events |

Baselines, **actually executed** against the same scenarios:

* **plain application logs** (S04, S06, S08, S09): a naive "replay" re-runs the tools; a tampered or
  truncated log still parses; the secret is in the log in clear;
* **LangGraph time travel** (S04 only): resuming from the checkpoint before `send_email` ran the
  email again (1 → 2). That is what LangGraph's documentation says nodes after a checkpoint do
  ("API requests … fire again"); it is a different tool for a different purpose (resuming and
  exploring state), so read it as a documented default, not a defect.

The plain-log "replay" is, by construction, re-running the tools: it shows what a log alone cannot do, not that
logging is badly engineered. A cold-start reviewer rightly called it weak as a comparison, which is one reason
LangGraph's time travel is executed too.

The other baselines named in `docs/08` §8.4 (generic OTel capture, Temporal, Phoenix) are **listed
with the reason they were not run** — not run, not claimed.

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

## Reproduction log

| Date | Who | Result | Independent? |
|---|---|---|---|
| 2026-11-22 | the author, clean clone | 10/10 `pass` | no |
| 2026-11-22 | an AI agent with no project context, following only the public docs (same machine) | 10/10 `pass`; `results.json` identical across two runs; a deliberate redaction bug made exactly S09 fail | **no**: not an independent human, so it does **not** satisfy the gate in `docs/08` §8.6 |

It told us the docs need a way to copy the run id, a note on which Python `uv` picks, and an ASCII-only
console output; all fixed. Add your own row through a
[reproduction report](https://github.com/MauricioFonck/forked/issues/new?template=reproduction_report.yml).

## Known limits

* Toy workflows; a scripted model; no real LLM, network or external system.
* Two executed baselines (LangGraph only for S04). No Temporal, Phoenix or generic-OTel comparison yet.
* Verification is exercised in a clean directory, not on a separate machine.
* Capture costs roughly 2–5 ms per tool call (two events, each flushed): the median was 2.4 ms on the
  author's Windows machine and 5.4 ms in a later run on the same machine under different load. Negligible
  next to an LLM call, but not free; measure your own workload.
