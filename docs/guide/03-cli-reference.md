# 3. CLI reference

`forked [--version] COMMAND [ARGS]`. Every command except `verify` accepts
`--store DIR` (default `.forked`, or the `FORKED_STORE` environment variable).

**Exit codes** (a contract): `0` success · `1` a check failed (`inspect --strict` with missing
evidence, `verify` with a failed integrity or validity check) · `2` an error, printed as
`error[code]: message` on stderr (unknown run, corrupt recording, divergence, denied effect, invalid
input…).

> `record`, `replay` and `branch` operate on the **built-in demo workflow** (`toy-agent`). To record
> your own workflow use the Python SDK ([4. Instrumenting your workflow](04-instrumenting-your-workflow.md)).
> `inspect`, `runs`, `compare`, `export`, `verify` and the OpenTelemetry commands work on any run.

### forked record

`forked record toy-agent` — run the demo agent and record it. Prints the run id and a report.

### forked runs

`forked runs` — list recorded runs: id, status, adapter and start time.

### forked inspect

`forked inspect RUN_ID [--events] [--json] [--strict]`

Status, event count, sequence validity, capture completeness against the adapter's declared capture
points, redacted/omitted counts, the adapter's limitations and the list of missing evidence.
`--events` lists every event, `--json` is machine-readable, `--strict` exits `1` if any evidence is
missing.

### forked replay

`forked replay RUN_ID` — re-run the demo workflow from the recording. **No tool executes.** A call
the recording cannot answer fails the replay (exit `2`) instead of calling the real tool. The replay
is itself a new run (its `run.started` carries `replay_of`).

### forked branch

`forked branch RUN_ID --at SEQUENCE --value JSON`

Fork a run. `--at` is the `sequence` of a `tool.call` (see `inspect --events`); `--value` is the JSON
that replaces that call's result, e.g. `--value 0.5` or `--value '{"ok": false}'`. Prints the
comparison. A checkpoint that is not a `tool.call` is rejected before anything is created.

### forked compare

`forked compare BASELINE BRANCH [--json]` — step-by-step differences, outcome changes, the five
invariants (`verified` / `violated` / `unknown`), the claim level and any missing evidence. `BRANCH`
must be a recorded branch of `BASELINE`.

### forked export

`forked export BASELINE BRANCH --out DIR` — write an evidence package. `DIR` must be new or empty
(evidence is never overwritten). Refuses to include anything shaped like a credential.

### forked verify

`forked verify PACKAGE [--json]` — verify a package **offline**; it needs nothing but the folder.
Reports integrity (changed / missing / unexpected files, manifest problems) and validity (every claim
recomputed from the packaged runs) separately, plus the `package_digest` to compare out of band.
Exit `0` only if both hold. Symlinks inside a package are rejected.

### forked otel-export

`forked otel-export RUN_ID [--out FILE] [--include-payloads]` — OTLP/JSON: one `forked.run` span and
one `execute_tool <name>` span per tool call, with GenAI attribute names plus `forked.*` attributes
(effect class, capture status, policy decision). Deterministic. Arguments and results are **left out**
unless you pass `--include-payloads` (they are already redacted, but an export leaves your machine).

### forked otel-import

`forked otel-import FILE` — record the `execute_tool` spans of an OTLP/JSON trace as a run. A trace
says nothing about side effects, so **every imported call is `unknown`** (denied in branches when its
inputs change) and capture completeness is unknown. Files over 5 MiB, traces with more than 10 000
tool spans, and malformed traces are rejected.
