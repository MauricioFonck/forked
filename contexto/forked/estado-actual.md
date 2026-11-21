# Estado actual

↑ [Memoria central](../README.md)

> Documento **vivo**: se actualiza cada vez que una fase avanza. Última revisión: **2026-11-21**
> ([sesión de publicación y Fase 2](../sesiones/2026-11-21-b-publicacion-y-fase-2.md)).

## Resumen

| Fase | Alcance | Estado | Spec |
|---|---|---|---|
| 0 | Cimientos del repositorio, CI, políticas OSS, guardianes | ✅ Hecha | [001](../docs/superpowers/specs/001-cimientos-del-repositorio/spec.md) |
| 1 | Grabador local + inspector + CLI `record`/`inspect`/`runs` | ✅ Hecha | [002](../docs/superpowers/specs/002-grabador-local/spec.md) |
| 2 | Replay de observaciones grabadas, fallo cerrado | ✅ Hecha | [003](../docs/superpowers/specs/003-replay-de-observaciones/spec.md) |
| 3 | Ramas, una intervención, política default-deny, invariantes | ⏳ Siguiente | — |
| 4 | Paquete de evidencia + verificador offline | ⏳ Pendiente | — |
| 5 | Puente OpenTelemetry, primer adaptador de framework, FCRB | ⏳ Pendiente | — |
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
- **138 tests** (unidad, contrato, seguridad, integración, aceptación, guardianes) + ruff + mypy strict en verde, y
  17 mutaciones dirigidas detectadas. Comandos en las bitácoras
  ([Fases 0–1](../sesiones/2026-11-21-arranque-fase-0-y-1.md#6-cómo-verificar),
  [Fase 2](../sesiones/2026-11-21-b-publicacion-y-fase-2.md#6-cómo-verificar)).
- Repositorio público en GitHub (`MauricioFonck/forked`), CI en verde en Linux 3.11–3.14, Windows y macOS.

## Qué NO funciona todavía

- No hay ramas, intervenciones, invariantes, comparación ni paquete de evidencia.
- La política de efectos no existe: la clase de efecto se **declara, registra y se compara en replay**; decidir
  `allow/deny` llega con las ramas ([ADR-010](decisiones-arquitectura/ADR-010-replay-estricto-sin-politica.md)).
- No hay índice SQLite: listar runs recorre el directorio ([ADR-004](decisiones-arquitectura/ADR-004-persistencia-fase-1.md)).

## Próximo paso

Fase 3: spec 004 (ramas e intervención). Bloqueo abierto: definir qué es un checkpoint portable (`docs/12` §12.2.2,
[revisión](../revisiones/2026-11-21-revision-de-preparacion.md)). Propuesta: checkpoint = índice de secuencia en el
log; la rama re-ejecuta en replay hasta ese índice y aplica la intervención después.
