# 5. Guarantees and limits

What FORKED promises, what it does not, and how each promise is checked. Every row of "guarantees"
is covered by a test in this repository; the limits are listed because they are as important.

## Guarantees (within the tool calls you route through the SDK)

| Guarantee | How it is checked |
|---|---|
| Replay and branches **never execute an `external_write`**, and never run a tool outside `pure_local` when its inputs changed | acceptance tests with the tools patched to explode; the benchmark's S04; the CI smoke test checks the outbox |
| A replay that cannot answer a call **fails closed** instead of calling the real tool | replay tests for every failure mode |
| Secrets are redacted **before** anything is written (arguments, keys named `password`/`token`/…, error messages) | security tests; the benchmark's S09 searches the store, the evidence package and an OTel export |
| An oversized payload is **omitted with a digest**, never truncated | capture tests |
| A partial recording is never reported as complete | lifecycle and completeness tests |
| A malformed or truncated recording **fails closed**, with the line number | store contract tests |
| Missing evidence makes an invariant `unknown`, **never `verified`** | comparison tests and mutation checks |
| No causal claim, no confidence score | comparison tests; the claim level is `observational` or `controlled_comparison` |
| A branch **never modifies its parent** | byte-for-byte test of the parent's files |
| `export` is deterministic; `verify` needs only the package and rejects a forged manifest even when its hashes are fixed | evidence tests, the benchmark's S08 |
| The core has no network dependency; recording, replay, branching and verification run offline | acceptance tests with `socket.connect` blocked |

## Limits — read these

* **Not deterministic replay.** FORKED replays recorded *observations*. Nondeterminism that enters
  from outside a recorded tool (time, randomness) makes the replay diverge, and it then stops. It
  does not make your code deterministic.
* **Only instrumented calls are observed.** Code that does not go through `call_tool` can do
  anything; the `inv_no_live_side_effects` invariant only sees what the SDK sees. There is no process
  sandbox.
* **Pydantic AI and LangGraph:** model requests (and, in LangGraph, every non-tool node and the graph
  state) are not recorded, and a real LLM usually diverges on replay. See
  [4. Instrumenting your workflow](04-instrumenting-your-workflow.md).
* **The frameworks you instrument may have their own telemetry.** FORKED never sends data anywhere,
  and its tests and benchmark run with the network blocked. A framework you wrap may: for example,
  LangChain/LangGraph can send traces to LangSmith if you set its tracing environment variables.
  Check your framework's settings; FORKED's local-first guarantee does not extend to it.
* **Redaction is pattern-based.** It catches secret-shaped values and sensitive key names; it can miss
  a secret in an unusual form and may over-redact. Do not rely on it for regulated data.
* **The evidence manifest is not signed.** Integrity means internal consistency, not authorship.
* **Validity is checked against FORKED's own rules** (five fixed invariants), not against whether
  your experiment was well designed. Hash integrity never implies scientific validity.
* **One intervention type** (replace a tool result), **one effect policy** (`default-deny/1`), one
  experiment (baseline + one branch) per package. No user-approved policies yet.
* **Capture costs time:** about 2–3 ms per tool call on the author's Windows machine (two events,
  each flushed). Negligible next to an LLM call, but measure your own workload.
* **Pre-alpha.** Formats may change before 1.0 (the event schema is versioned and has golden
  fixtures; the package format is `forked-evidence/1`). The benchmark that exercises all this is
  provisional and **has not been independently reproduced**.

## Reporting a problem

* A behavior that breaks a guarantee above is a bug: open a
  [bug report](https://github.com/MauricioFonck/forked/issues/new?template=bug_report.yml).
* A way to **bypass** a guarantee (leak a secret, run a denied write, make `verify` accept a forgery)
  is a vulnerability: follow [SECURITY.md](../../SECURITY.md) and do not open a public issue.
