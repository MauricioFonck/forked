# Impacto 2026-11-21 (c) — Fase 3: ramas, intervención, política y comparación

↑ [Índice de impacto](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-21 |
| **Sesión** | [`../sesiones/2026-11-21-c-fase-3-ramas.md`](../sesiones/2026-11-21-c-fase-3-ramas.md) |
| **Rama / commits** | `main` · commit de la Fase 3 |
| **Estado** | Verificado |

## 1. Qué se va a tocar

| Zona | Archivo / contrato | Otros consumidores |
|---|---|---|
| Cursor de replay | `ReplayCursor.resolve` partido en `match`/`try_resolve` | Replay (Fase 2) |
| Aplicación | `RecordingService.start(replay_of=)` → `start(lineage=)` | `ReplayService` (único llamador) |
| SDK | `RecordedRun(session, resolver, source)`; se quita `is_replay` (sin uso) | Recorder, demo |
| Demo | `run_toy_agent(replay_of=)` → `run_toy_agent(session=)`; captura `EffectDenied` | CLI, tests |
| Formato | Resultados en replay llevan `payload.forked`; `run.started` de rama lleva linaje | Inspector; esquema v0.1.0 sin cambios (payload libre) |

## 2. Qué funciona hoy y qué le podría pasar

| Id | Comportamiento | Qué le podría pasar | Riesgo | Mitigación |
|---|---|---|---|---|
| CP-022 | Replay no ejecuta herramientas | El resolutor único deja pasar `ALLOW` en replay | **Alto** | Replay solo produce `Resolution.replayed`; tests de replay + mutación previa en verde |
| CP-023…025 | Replay estricto | Refactor del cursor cambia mensajes o consumo | Medio | Mismos textos; 8 tests de replay sin cambios |
| CP-003…005 | Redacción | Valor de intervención con secreto llega a disco | **Alto** | Linaje y resultado pasan por `session.capture`; test con `sk-…` |
| CP-019 | CLI | `replay` roto por el cambio de firma del demo | Medio | Tests de CLI previos en verde |

## 3. Lo que se descubrió al analizar

- La mutación «la llamada del checkpoint no se compara con la del padre» **sobrevivió** a la primera suite: faltaba
  el test. Se añadió `test_checkpoint_call_must_match_parent_inputs` y ahora muerde.
- `docs/12` §12.2.2 (checkpoint portable) queda resuelto para el SDK por ADR-011; sigue abierto para adaptadores de
  framework (Fase 5).

## 4. Verificación posterior

| Id | Cómo se verificó | Resultado |
|---|---|---|
| Todos | `uv run pytest` | OK — 155 passed |
| CP-027 | Mutación: la política permite todo | OK — 7 rojos |
| CP-028 | Mutaciones: sin replay antes del checkpoint / checkpoint sin comparar | OK — 6 rojos / 1 rojo (tras test nuevo) |
| CP-030 | Mutaciones: digest siempre verificado / rama siempre finalizada | OK — 1 / 1 rojos |
| CP-031 | Mutación: nivel siempre controlado | OK — 2 rojos |
| CP-026/027 | Smoke real: `record` + `branch` + outbox | OK — outbox con 1 mensaje; 5 invariantes `verified` |
| Estáticos | ruff check · ruff format --check · mypy strict | OK |

## 5. Comportamientos nuevos que pasan a protegidos

CP-026 a CP-032 en [`comportamientos-protegidos.md`](comportamientos-protegidos.md).
