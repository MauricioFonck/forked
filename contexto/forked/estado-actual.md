# Estado actual

↑ [Memoria central](../README.md)

> Documento **vivo**: se actualiza cada vez que una fase avanza. Última revisión: **2026-11-21**
> ([sesión de arranque](../sesiones/2026-11-21-arranque-fase-0-y-1.md)).

## Resumen

| Fase | Alcance | Estado | Spec |
|---|---|---|---|
| 0 | Cimientos del repositorio, CI, políticas OSS, guardianes | ✅ Hecha | [001](../docs/superpowers/specs/001-cimientos-del-repositorio/spec.md) |
| 1 | Grabador local + inspector + CLI `record`/`inspect`/`runs` | ✅ Hecha | [002](../docs/superpowers/specs/002-grabador-local/spec.md) |
| 2 | Replay de observaciones grabadas + política default-deny | ⏳ Spec en borrador | [003](../docs/superpowers/specs/003-replay-de-observaciones/spec.md) |
| 3 | Ramas, una intervención, invariantes | ⏳ Pendiente | — |
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
- **123 tests** (unidad, contrato, seguridad, integración, aceptación, guardianes) + ruff + mypy strict en verde, y
  11 mutaciones dirigidas detectadas. Comandos y salida en la [bitácora](../sesiones/2026-11-21-arranque-fase-0-y-1.md#6-cómo-verificar).

## Qué NO funciona todavía

- No hay replay, ramas, intervenciones, invariantes, comparación ni paquete de evidencia.
- La política de efectos no existe: hoy la clase de efecto solo se **declara y registra**.
- No hay índice SQLite: listar runs recorre el directorio ([ADR-004](decisiones-arquitectura/ADR-004-persistencia-fase-1.md)).
- El CI está escrito pero **no ha corrido en GitHub** (el repositorio remoto aún no existe).

## Próximo paso

Fase 2 según la [spec 003](../docs/superpowers/specs/003-replay-de-observaciones/spec.md): plan, tareas e implementación
del replay que falla cerrado y prueba que ninguna escritura externa es alcanzable.
