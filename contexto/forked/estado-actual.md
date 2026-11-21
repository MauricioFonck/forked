# Estado actual

↑ [Memoria central](../README.md)

> Documento **vivo**: se actualiza cada vez que una fase avanza. Última revisión: **2026-11-21**
> ([sesión de la Fase 4](../sesiones/2026-11-21-d-fase-4-evidencia.md)).

## Resumen

| Fase | Alcance | Estado | Spec |
|---|---|---|---|
| 0 | Cimientos del repositorio, CI, políticas OSS, guardianes | ✅ Hecha | [001](../docs/superpowers/specs/001-cimientos-del-repositorio/spec.md) |
| 1 | Grabador local + inspector + CLI `record`/`inspect`/`runs` | ✅ Hecha | [002](../docs/superpowers/specs/002-grabador-local/spec.md) |
| 2 | Replay de observaciones grabadas, fallo cerrado | ✅ Hecha | [003](../docs/superpowers/specs/003-replay-de-observaciones/spec.md) |
| 3 | Ramas, una intervención, política default-deny, invariantes, comparación | ✅ Hecha | [004](../docs/superpowers/specs/004-ramas-e-intervencion/spec.md) |
| 4 | Paquete de evidencia + verificador offline | ✅ Hecha | [005](../docs/superpowers/specs/005-paquete-de-evidencia/spec.md) |
| 5 | Puente OpenTelemetry, primer adaptador de framework, FCRB | ⏳ Siguiente | — |
| 6 | Alfa pública y comunidad | ⏳ Pendiente | — |

## Qué funciona hoy (verificado)

- `forked record toy-agent` graba un agente de juguete con 3 herramientas (`pure_local`, `external_read`,
  `external_write`), redacta su API key falsa y reporta 100 % de completitud, 0 evidencia faltante.
- `forked inspect <run> [--events] [--json] [--strict]` reporta estado efectivo, validez de secuencia, completitud contra
  puntos declarados, eventos redactados/omitidos y la lista de evidencia faltante.
- Un run interrumpido (metadatos en `recording`, cola del log perdida) se reporta como `incomplete` con cada punto de
  captura no observado.
- Esquema de evento v0.1.0 publicado en [`spec/cip/v0.1/`](../../spec/cip/v0.1/event.schema.json) con 5 fixtures dorados.
- `forked replay <run>` re-ejecuta el flujo contestando cada herramienta con lo grabado: **0 herramientas
  ejecutadas**, outbox intacto, mismo resultado; cualquier divergencia u observación faltante falla cerrado
  ([contexto `replay`](../modulos/replay/README.md)).
- `forked branch <run> --at 3 --value 0.5` bifurca en un `tool.call`, reemplaza su resultado y re-ejecuta: antes
  del checkpoint replay, después replay si no cambió o política default-deny (el email nuevo se **deniega**).
  `forked compare` da diferencias por paso y de resultado, 5 invariantes y el nivel de afirmación
  ([contexto `branches`](../modulos/branches/README.md)).
- `forked export <base> <rama> --out DIR` y `forked verify DIR`: paquete determinista con SHA-256 por artefacto;
  el verificador funciona solo con el paquete y separa integridad de validez, recalculando la comparación
  ([contexto `evidence`](../modulos/evidence/README.md)).
- **189 tests** (1 se salta en Windows: symlinks) (unidad, contrato, seguridad, integración, aceptación, guardianes) + ruff + mypy strict en verde, y
  34 mutaciones dirigidas detectadas (una sobrevivió y generó un test nuevo, ver la
  [bitácora de la Fase 3](../sesiones/2026-11-21-c-fase-3-ramas.md#6-cómo-verificar)). Comandos en las bitácoras
  ([Fases 0–1](../sesiones/2026-11-21-arranque-fase-0-y-1.md#6-cómo-verificar),
  [Fase 2](../sesiones/2026-11-21-b-publicacion-y-fase-2.md#6-cómo-verificar)).
- Repositorio público en GitHub (`MauricioFonck/forked`), CI en verde en Linux 3.11–3.14, Windows y macOS.

## Qué NO funciona todavía

- El manifiesto no está firmado: la integridad es consistencia interna ([ADR-012](decisiones-arquitectura/ADR-012-paquete-de-evidencia.md)).
- No hay adaptadores de framework ni puente OpenTelemetry (Fase 5).
- Una sola intervención (`replace_recorded_observation`) y una sola política (`default-deny/1`), sin
  aprobaciones del usuario.
- No hay índice SQLite: listar runs recorre el directorio ([ADR-004](decisiones-arquitectura/ADR-004-persistencia-fase-1.md)).

## Próximo paso

Fase 5: adaptador y benchmark — mapeo a OpenTelemetry, primer adaptador de framework y los 10 escenarios FCRB de
[`docs/08`](../../docs/08-benchmarks-and-validation.md). Antes de elegir framework: revisar
[arte previo](../investigacion/arte-previo.md) y decidir cuál (decisión del dueño).
