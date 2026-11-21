# AGENTS.md

Instructions for any AI coding agent (Codex, Gemini, Cursor, Claude Code, …) working on FORKED.

The single source of truth is [`CLAUDE.md`](CLAUDE.md) — read it completely before acting.
It applies to every agent, not only Claude. Then read [`contexto/README.md`](contexto/README.md).

Non-negotiables, repeated here because they matter most:

- Never execute a real external write in replay or branch mode. Default is deny.
- Never persist secrets; redaction runs before persistence.
- Never claim deterministic replay or causality beyond what tests prove.
- `domain` imports only the standard library; `application` depends on ports; adapters are
  wired only in `bootstrap`.
- Every session that touches code writes `contexto/impacto/…` (before) and
  `contexto/sesiones/…` (at close) in the same commit.
