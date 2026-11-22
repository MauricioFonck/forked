# Security policy

FORKED records executions that may contain prompts, tool inputs and outputs, and
environment details. We treat leaks, unsafe replays and integrity bypasses as
security issues.

## Reporting a vulnerability

**Do not open a public issue.** Use GitHub's private vulnerability reporting:
<https://github.com/MauricioFonck/forked/security/advisories/new>.

Please include a minimal reproduction with synthetic data. We will acknowledge reports on
a best-effort basis; this is a pre-alpha project maintained by volunteers and we do not
promise a response SLA yet.

## In scope

- secrets or sensitive values persisted despite redaction;
- any path where replay or a branch executes an external write by default;
- path traversal or symlink escapes when reading or importing artifacts;
- tampered or malformed artifacts that are accepted silently;
- reports that claim more than the evidence supports (e.g. a partial run shown as complete).

## Current guarantees and limits (v0.1.0a1)

The full list, with how each guarantee is tested, is in
[docs/guide/05-guarantees-and-limits.md](docs/guide/05-guarantees-and-limits.md). In short:

- **Replay and branches never execute an `external_write`** and never run a tool outside `pure_local`
  when its inputs changed; a replay that cannot answer a call fails closed. This holds for the tool
  calls routed through the SDK, **not** for code that bypasses it: there is no process sandbox.
- **Evidence packages** are verified offline: integrity (hashes) and validity (everything recomputed)
  are separate checks. The manifest is **not signed**: hashes show internal consistency, not authorship.
- Redaction is best effort (key names + common credential formats). It does not prove
  that no sensitive data was captured. Review stores before sharing them.
- Stores are local, unencrypted files. Protect them like source code with secrets.
- FORKED sends no data anywhere. A framework you wrap may (for example LangChain tracing to
  LangSmith when enabled by its environment variables); that is outside FORKED's control.

## Reporting a bypass

A way to defeat any guarantee above — leak a secret, run a denied write, make `verify` accept a
forged package, escape the store with a crafted path — is a vulnerability: use the private channel
above, with synthetic data.
