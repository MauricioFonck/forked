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

## Current guarantees and limits (v0.1.0.dev0)

- Redaction is best effort (key names + common credential formats). It does not prove
  that no sensitive data was captured. Review stores before sharing them.
- Stores are local, unencrypted files. Protect them like source code with secrets.
- Replay, branching and evidence export are **not implemented yet**.
