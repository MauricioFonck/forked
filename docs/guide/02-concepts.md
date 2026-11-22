# 2. Concepts

FORKED asks one question: *if I change one thing about a recorded execution, what changes — and
what do we honestly know about why?* These are the ideas it is built from.

## Run and event

A **run** is one recorded execution. It is an ordered list of **events**: `run.started`,
`tool.call`, `tool.result` / `tool.error`, then `run.completed` or `run.failed`. Events are numbered
`0, 1, 2…` with no gaps. A run that is never finalized (the process died) is reported as
**incomplete**, never as complete.

Each tool event has a **capture status**:

| Status | Meaning |
|---|---|
| `captured` | stored as is |
| `redacted` | stored, but secret-shaped values were replaced by `[REDACTED]` before reaching disk |
| `omitted` | too large (over 64 KiB): not stored, only its SHA-256 digest — **never truncated** |

Every report lists **missing evidence** explicitly. "None detected" means what it says, not that
nothing could be missing.

## Effect class

Every tool call carries what it can do to the world outside the experiment:

| Class | Replay and branches |
|---|---|
| `pure_local` | may run again in a branch (it touches nothing outside) |
| `recorded_read` / `external_read` | answered from the recording; denied if inputs changed |
| `external_write` | **never repeated**; denied if its inputs changed |
| `local_write` | denied (no disposable branch workspace yet) |
| `unknown` | denied |

The default is **deny**. A tool you did not classify is `unknown`.

## Replay

Replay re-runs your workflow, but every tool call is answered from the recording instead of being
executed. It is **strict**: a call with different inputs, an extra call, a missing observation, or a
recorded call your code never asks for stops the replay with an error. It reproduces recorded
*observations*, not the original environment — it is not general deterministic replay.

## Branch and intervention

A **branch** forks a run at a **checkpoint** — the `sequence` number of a `tool.call` (see
`forked inspect --events`) — and applies one **intervention**: replace that call's recorded result
with a value you choose. Calls before the checkpoint replay. Calls after it replay if they are
unchanged; a call whose inputs changed goes to the effect policy above. The parent run is only ever
read.

## Comparison, invariants and claim level

`compare` lines up baseline and branch step by step, lists the outcome fields that changed, and
checks five **invariants**, each `verified`, `violated` or `unknown`:

| Invariant | Checks |
|---|---|
| `inv_parent_unchanged` | the baseline's log is the same as when the branch was created |
| `inv_prefix_replayed` | everything before the checkpoint came from the recording |
| `inv_no_live_side_effects` | nothing but declared `pure_local` tools ran live in the branch |
| `inv_same_environment` | the captured environment facts are equal |
| `inv_same_adapter` | same adapter and version |

Missing evidence makes an invariant `unknown`, **never** `verified`. The **claim level** is
`controlled_comparison` only when all five are verified and the branch completed; otherwise
`observational`. FORKED never produces a causal claim: one run pair cannot support one. There is
no confidence score.

## Evidence package

`export` writes a folder: a `manifest.json` (experiment, environment, policy, invariants, claim,
limitations, SHA-256 of every file), `comparison.json` and the run files. The same runs always
produce the same bytes. `verify` answers two **separate** questions:

* **Integrity** — do the files match the manifest? (changed, missing or extra files)
* **Validity** — recompute everything from the packaged runs: is each claim in the manifest what the
  evidence actually supports?

The manifest is **not signed**: hashes show internal consistency, not who made it. Compare the
`package_digest` that `verify` prints with a copy you got through another channel.

## Adapter

An **adapter** connects FORKED to your code: the Python SDK, a framework adapter (Pydantic AI), or
the OpenTelemetry importer. It declares its **capture points** and its **limitations**; both appear
in every report.
