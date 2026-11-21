# Spec 002 · Grabador local e inspector (Fase 1)

[Plan](plan.md) · [Tareas](tasks.md) · [Bitácora](../../../../sesiones/2026-11-21-arranque-fase-0-y-1.md) · [Impacto](../../../../impacto/2026-11-21-arranque-fase-0-y-1.md) · [Contexto `runs`](../../../../modulos/runs/README.md)

**Fecha:** 2026-11-21 · **Estado:** hecha

## Qué y por qué

UC-01 de [`docs/04`](../../../../../docs/04-product-requirements.md): envolver un flujo de juguete, capturar eventos
ordenados y tipados con metadatos, redactar secretos, persistir localmente y devolver un id de run con un reporte de
completitud. Es la base de todo lo demás: sin grabación fiable no hay replay ni ramas.

## Criterios de aceptación

| Criterio (`docs/04` UC-01 · `docs/09` Fase 1 · `docs/13`) | Cómo se cumple |
|---|---|
| El orden de eventos es estable | Secuencia asignada solo por `Run` (CP-001, CP-002) |
| Los campos de captura faltantes son explícitos | `assess()` → lista de evidencia faltante (CP-007, CP-010, CP-011) |
| Los secretos no se persisten | Pipeline de redacción antes de `append` (CP-003…CP-005) |
| Un fallo de captura es visible, no se ignora | `CaptureFailed` + run `incomplete` (CP-008, CP-009) |
| Eventos malformados fallan claro | `CorruptRecording` con número de línea (CP-012) |
| Grabar e inspeccionar offline | Test de aceptación con red bloqueada (CP-017) |
| Dominio sin Pydantic/Typer/SQLite/FS | Guardián de dependencias (CP-015) |
| CLI para grabar el demo e inspeccionar | `forked record toy-agent`, `forked inspect`, `forked runs` (CP-019) |

## Fuera de alcance

Replay, ramas, análisis causal, servicios en la nube, UI web, SQLite ([ADR-004](../../../../forked/decisiones-arquitectura/ADR-004-persistencia-fase-1.md)).
