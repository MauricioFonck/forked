# Spec 004 · Plan

[Spec](spec.md) · [Tareas](tasks.md) · [Bitácora](../../../../sesiones/2026-11-21-c-fase-3-ramas.md)

1. **Cursor**: separar `match` (coincidencia, lanza), `try_resolve` (sin lanzar) y `resolve` (replay estricto).
2. **Dominio**: `DefaultDenyPolicy` + `Decision` + `EffectDenied`; `Intervention`, `BranchResolver`, `Resolution`,
   `log_digest`; `compare()` con pasos, cambios de resultado, 5 invariantes y nivel de afirmación.
3. **Aplicación**: `RecordingService.start(lineage=)` generaliza `replay_of`; `ReplayService.branch()` valida antes
   de abrir el run; `CompareRuns`.
4. **SDK**: un solo `Resolver` para replay y rama; `DENY` ⇒ `tool.error` + `EffectDenied`; decisión en
   `payload.forked`.
5. **Demo / CLI / CI**: `run_toy_agent(session=...)`; el demo captura `EffectDenied` al enviar; `forked branch`,
   `forked compare`; smoke de CI con rama y outbox intacto.
6. **Tests y mutaciones** sobre cada regla de seguridad y de honestidad.
