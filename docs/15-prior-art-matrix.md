# 15. Prior-art matrix (first pass)

> **Retrieved 2026-11-22. A first pass, not a complete survey.** It answers one question honestly:
> *what already exists, and what — if anything — is left that FORKED adds?* Every row has a source
> and a confidence level. "Not found" means "not found in the sources we read", **never** "does not
> exist". Corrections are welcome: open a
> [proposal](https://github.com/MauricioFonck/forked/issues/new?template=proposal.yml).

## Short answer

* **Recording a run, replaying it from recorded observations, replacing a tool result and
  continuing, hashing, redaction and branching from a checkpoint are all already done** — by
  platforms (LangGraph, Temporal), by several small open-source projects and by recent research.
  FORKED does not claim any of these as new.
* In the sources we reviewed, we **did not find** a tool that combines all three of:
  1. **effect classes with a default-deny policy** for what a replay or branch may execute;
  2. **invariants reported as `verified` / `violated` / `unknown`**, with a claim level deliberately
     capped below causal;
  3. a **portable evidence package** whose validity (not only its hashes) is **recomputed offline**.

  That is a statement about a *combination*, limited to what we read. One of the projects below lists
  "sandboxed replay for write-side-effect tools" as future work, which suggests the gap is real, not
  that nobody noticed it.
* Research on counterfactual replay of agents (see §3) pursues a **different goal**: estimating *which
  step caused a failure*, with distributions and confidence intervals. FORKED deliberately stops at
  "controlled comparison of one run pair" and says so.

## 1. Method and limits

| | |
|---|---|
| Date | 2026-11-22 |
| Sources | official documentation pages, project READMEs and GitHub metadata (`gh api`), arXiv abstract pages |
| **Confidence** | **High**: read the primary page and quote it · **Medium**: README or abstract level · **Low**: search snippet only |
| What was *not* done | no code audit of any project; papers were read at abstract level only; no patent search; no commercial-product trials |
| Bias to watch | the author of this matrix also wrote FORKED; every "not found" is a place to prove us wrong |

Searches run (web): LangGraph time travel/checkpoint fork; Temporal replay and side effects; Phoenix
span replay; OpenTelemetry GenAI `execute_tool`; "counterfactual replay LLM agents"; "agent trajectory
record replay tool observations". Then each hit was read at its source.

## 2. Platforms and standards

| System | What it does (as documented) | Source (retrieved 2026-11-22) | Relation to FORKED | Conf. |
|---|---|---|---|---|
| **LangGraph** time travel | *Replay* and *fork* resume from a prior checkpoint. "Nodes after the checkpoint re-execute, including any LLM calls, API requests, and interrupts." "Replay re-executes nodes — it doesn't just read from cache." Fork = `update_state` on a prior checkpoint. | [docs.langchain.com/oss/python/langgraph/use-time-travel](https://docs.langchain.com/oss/python/langgraph/use-time-travel) | Closest *runtime* feature. It re-executes later nodes, so external writes after the checkpoint can run again; no per-call effect policy is described. **We measured it** (benchmark S04, 2026-11-22): resuming from the checkpoint before `send_email` sent the email again (1 → 2). That is documented behavior of a tool built for resuming and exploring state, not a defect. FORKED keeps recorded observations and denies re-execution; it also ships a LangGraph adapter, so the two can be combined. | High |
| **Temporal** | Workflow code is replayed against the recorded Event History. "A Side Effect does not re-execute during a Replay. Instead, it returns the recorded result." Activity results are recorded too. | [Side Effects – Go SDK](https://docs.temporal.io/develop/go/workflows/side-effects.md) · [Event History](https://docs.temporal.io/encyclopedia/event-history/event-history-python) | Durable execution with deterministic workflow code; a different problem (resuming), not counterfactual experiments or evidence packages. | High (side effects) / Medium (rest) |
| **Arize Phoenix** span replay | "Replay LLM spans from your application in the Prompt Playground." | [arize.com/docs/phoenix/…/span-replay](https://www.arize.com/docs/phoenix/prompt-engineering/overview-prompts/span-replay.md) | Re-runs a single LLM call with an edited prompt; not a whole-run replay with tool observations. | Medium |
| **OpenTelemetry GenAI** conventions | Registry lists the operation `execute_tool` and the attributes `gen_ai.tool.name`, `gen_ai.tool.call.arguments`, `gen_ai.tool.call.result`; the page notes they were **moved** to a dedicated GenAI semantic-conventions repository. | [attributes-registry/gen-ai](https://opentelemetry.io/docs/specs/semconv/attributes-registry/gen-ai/) | FORKED's OTLP bridge reuses these names and **does not redefine tracing**. Names may change (they moved); we have not verified the spec's stability status. | Medium |

## 3. Research

Read at **abstract level** (confidence: Medium) — we have not evaluated the papers' methods or code.

| Work | What it does | Relation to FORKED |
|---|---|---|
| **Causal Agent Replay** — [arXiv 2606.08275](https://arxiv.org/abs/2606.08275) (2026-06-06) | Models a run as a structural causal model, applies an intervention to one step and re-executes under the same stochastic policy; reports effects with **confidence intervals**. | Different aim: *causal attribution of failures by resampling*. FORKED reports **no** causal claim from one pair. Complementary: many FORKED branches could feed such an estimator. |
| **Chronicle** — [arXiv 2609.20625](https://arxiv.org/abs/2609.20625) (2026-09-17) | Records at non-deterministic boundaries as immutable envelopes; **cut-point replay** serves some boundaries from the record and runs others live with new code, as a CI regression test. Its mutation study mentions "guarded tools" and "the recorded unsafe action". | Closest *design*: record boundaries, replay a prefix, run the rest live. Overlaps with FORKED's prefix replay + live `pure_local`. Not evaluated: its safety model, whether it has effect classes or evidence packages (abstract does not say). |
| **DoVer** — [arXiv 2512.06749](https://arxiv.org/abs/2512.06749) (2025-12-07) | Intervention-driven debugging: edits messages or plans in a failed multi-agent trace and checks whether the failure is repaired. | Same family (interventions on traces); aimed at debugging and repair. |
| **CausalFlow** — [arXiv 2605.25338](https://arxiv.org/abs/2605.25338) (2026-05-25) | Step-level counterfactual interventions to score responsibility and generate minimal repairs. | Same family; aimed at attribution and repair. |
| **ReplayRCA** — [arXiv 2610.41025](https://arxiv.org/abs/2610.41025) (2026-10-29) | A benchmark that scores failure diagnoses by restoring the state before a step, substituting an action and continuing, against a placebo replay. | Evaluation of diagnosers, using counterfactual replay as the measuring device. |

## 4. Open-source record/replay projects

README level (confidence: **Medium**); GitHub metadata fetched 2026-11-22. All are recent and small
(0 stars at retrieval) — that is a fact about visibility, not about quality.

| Project | Created · license | Record / replay | Inject a result | Redaction | Hashing | Effect handling | Invariants · verification · claim levels |
|---|---|---|---|---|---|---|---|
| [Intermountainh8ter/agentreplay](https://github.com/Intermountainh8ter/agentreplay) (Rust) | 2026-10-14 · MIT | yes (initial scaffold) | **yes**, "rewind, inject, continue" | not mentioned | chained SHA-256 | not mentioned | not found |
| [hassanzafarr/AgentReplay](https://github.com/hassanzafarr/AgentReplay) (LangGraph) | 2026-06-27 · MIT | yes, 148 tests | not mentioned | not mentioned | hashes used to match calls | **states a limit**: "Write side effects are not sandboxed during replay"; lists "Sandboxed replay for write-side-effect tools" as planned | not found |
| [jahnavi-1019/agent-replay](https://github.com/jahnavi-1019/agent-replay) (TypeScript) | 2026-10-28 · no license file | yes (cassettes) | not mentioned | **yes**, secrets and PII | canonical SHA-256 of state | not mentioned | divergence localization; no invariants found |
| [RockENZO/trajectory-replay](https://github.com/RockENZO/trajectory-replay) | 2026-11-01 · MIT | yes (cassettes) | not mentioned | not mentioned | no | not mentioned | trajectory-match scoring, not invariants |
| [Davsooonowy/pytest-agent-trace](https://github.com/Davsooonowy/pytest-agent-trace) | 2026-08-16 · MIT | yes (pytest plugin, LangGraph) | partial (mentions) | mentioned | no | not mentioned | trajectory tests, not invariants |
| [aman-abeb/agent-tape](https://github.com/aman-abeb/agent-tape) (TypeScript) | 2026-10-29 · MIT | yes (JSON fixtures) | not mentioned | not mentioned | no | not mentioned | not found |

## 5. Capability matrix

`✔` documented in the sources read · `◐` partial, or documented as a limitation · `—` not found in
the sources read · `n/a` outside the system's goal. **Read it with §1's limits.**

| Capability | LangGraph | Temporal | Phoenix | OSS tools (§4) | Research (§3) | FORKED |
|---|---|---|---|---|---|---|
| Records tool calls and results | ◐ graph state | ✔ | ✔ spans | ✔ | ✔ | ✔ |
| Replays from recorded observations **without re-executing** tools | — (re-executes) | ✔ (activities, side effects) | ◐ one LLM span | ✔ | ✔ | ✔ |
| Branches with a replaced observation | ✔ (re-executes after) | — | ◐ prompt edit | ◐ one project | ✔ | ✔ |
| **Effect classes + default-deny for replay/branch** | — | ◐ (activities vs workflow code) | — | — (one lists it as a limit) | not read | ✔ |
| Secrets redacted before persistence | not read | not read | not read | ◐ some projects | not read | ✔ |
| Integrity hashes on records | not read | not read | not read | ◐ some projects | not read | ✔ |
| **Invariants as `verified` / `violated` / `unknown`** | — | — | — | — | — | ✔ |
| **Claim levels capped below causal** | n/a | n/a | n/a | — | opposite goal (estimates with CIs) | ✔ |
| **Portable package, validity recomputed offline** | — | — | — | — | — | ✔ |
| OpenTelemetry bridge | not read | not read | not read | — | — | ◐ (tool spans only) |
| Runs fully offline, no hosted service | not read | not read | not read | ✔ (READMEs describe offline use) | not read | ✔ |

## 6. What this means for FORKED

* **Positioning.** FORKED is **not** "the record/replay tool". The defensible description is narrower:
  a *safety and evidence layer* for counterfactual runs — effect policy, honest invariants, and
  evidence that can be re-verified. The README and the guide now say that and avoid superlatives.
* **Credit.** Chronicle's cut-point replay and the intervention papers are the nearest ideas; they
  should be cited wherever FORKED discusses prefix replay and interventions.
* **A real overlap to watch.** `agentreplay` already combines inject + chained hashing; if its
  effect or evidence story grows, the combination above shrinks.
* **Complementarity, not competition.** CAR-style estimators need many controlled runs; FORKED's
  invariants and packages could be the substrate. We have not tested that.
* **Our own weak spots this review exposed.** Recorded runs of a real LLM agent mostly diverge on
  replay (FORKED fails closed and says so); several projects above record the *model* calls too,
  which FORKED does not.

## 7. Not yet reviewed

LangSmith, Langfuse, AgentOps, Braintrust, Inspect AI, MLflow/DVC (experiment tracking), VCR.py-style
cassette libraries, rr/Pernosco (record-and-replay debuggers), deterministic simulation testing,
W3C PROV and in-toto/SLSA (provenance and attestation), `langchain-replay`, patents. Anything we
claim about these is **unsupported until reviewed**.

## 8. How to correct this document

Open a [proposal](https://github.com/MauricioFonck/forked/issues/new?template=proposal.yml) with the
tool, a link, a date and what we got wrong. Corrections that shrink FORKED's claimed difference are
the most valuable ones.
