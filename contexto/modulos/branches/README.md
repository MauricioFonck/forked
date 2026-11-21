# Contextos `branches` y `comparison`

↑ [Contextos](../README.md) · [Memoria central](../../README.md)

> Bifurcar un run grabado en un `tool.call`, reemplazar ese resultado y re-ejecutar el flujo con la política
> default-deny; después, comparar base y rama con invariantes honestas. Decisión:
> [ADR-011](../../forked/decisiones-arquitectura/ADR-011-ramas-checkpoint-y-comparacion.md).

## Archivos

| Capa | Archivo | Qué hace |
|---|---|---|
| dominio | `src/forked/domain/branches/branch.py` | `Intervention`, `BranchResolver`, `Resolution`, `log_digest`, `InvalidCheckpoint` |
| dominio | `src/forked/domain/effects/policy.py` | `Decision`, `DefaultDenyPolicy` (`default-deny/1`), `EffectDenied` |
| dominio | `src/forked/domain/comparison/compare.py` | `compare()`, `InvariantStatus`, `ClaimLevel`, `Comparison`, `NotABranch` |
| dominio | `src/forked/domain/replay/cursor.py` | `match` / `try_resolve` reutilizados por la rama |
| aplicación | `src/forked/application/commands/replay_run.py` | `ReplayService.branch()`: valida checkpoint, registra linaje |
| aplicación | `src/forked/application/queries/inspect_run.py` | `CompareRuns` |
| SDK | `src/forked/adapters/inbound/sdk/recorder.py` | `Recorder.branch()`; `payload.forked = {decision, reason}` en cada resultado |
| CLI | `src/forked/adapters/inbound/cli/app.py` | `forked branch RUN --at SEQ --value JSON`, `forked compare BASE BRANCH [--json]` |

## Decisión por llamada (en orden)

| Posición | Coincide con el padre | Resultado |
|---|---|---|
| antes del checkpoint | sí | `replay` |
| antes del checkpoint | no | `ReplayDivergence`, rama `failed` |
| checkpoint | sí | `intervene` (valor declarado) |
| checkpoint | no | `ReplayDivergence` |
| después, aún alineado | sí | `replay` |
| después, distinto (o ya desalineado) | — | política: `pure_local` ⇒ `allow`; resto ⇒ `deny` (`EffectDenied`, no se ejecuta) |

## Invariantes

| Id | Método | `unknown` cuando |
|---|---|---|
| `inv_parent_unchanged` | digest del log del padre al crear la rama vs. ahora | no hay digest registrado |
| `inv_prefix_replayed` | inspección de eventos | rama no finalizada o intervención nunca aplicada |
| `inv_no_live_side_effects` | inspección de eventos | rama no finalizada |
| `inv_same_environment` | huella de entorno | falta algún hecho en cualquiera de los dos |
| `inv_same_adapter` | metadatos del adaptador | — |

`controlled_comparison` ⇔ las cinco `verified` y rama `completed`. Si no, `observational`. Nunca causal.

## Límites declarados

Ver «Consecuencias» del ADR-011: digest semántico (no de archivo), solo se observa lo que pasa por `call_tool`,
el entorno es el capturado, una sola intervención y una sola política.

## Comportamientos protegidos

CP-026 a CP-032 en [comportamientos protegidos](../../impacto/comportamientos-protegidos.md).
