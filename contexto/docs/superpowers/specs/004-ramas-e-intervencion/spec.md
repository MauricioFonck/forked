# Spec 004 · Ramas, una intervención, política de efectos y comparación (Fase 3)

[Plan](plan.md) · [Tareas](tasks.md) · [Bitácora](../../../../sesiones/2026-11-21-c-fase-3-ramas.md) · [Impacto](../../../../impacto/2026-11-21-c-fase-3-ramas.md) · [Contexto `branches`](../../../../modulos/branches/README.md)

**Fecha:** 2026-11-21 · **Estado:** hecha

## Qué y por qué

UC-03 y UC-04 de [`docs/04`](../../../../../docs/04-product-requirements.md): bifurcar un run en un checkpoint con
una intervención explícita y versionada, ejecutar la rama sin efectos reales por defecto y comparar base y rama con
invariantes `verified/violated/unknown`, distinguiendo diferencia observada de interpretación causal. Prueba la
hipótesis [H2/H4](../../../../investigacion/hipotesis.md) en el demo y habilita el escenario FCRB de «resultado de
herramienta alterado».

## Decisiones

Todas en [ADR-011](../../../../forked/decisiones-arquitectura/ADR-011-ramas-checkpoint-y-comparacion.md): checkpoint
= `sequence` de un `tool.call`; intervención `replace_recorded_observation`; política `default-deny/1`; linaje en
`run.started`; cinco invariantes fijas; `controlled_comparison` u `observational`.

## Criterios de aceptación

| Criterio (`docs/04` UC-03/04 · `docs/09` Fase 3) | Cómo se cumple |
|---|---|
| Linaje inmutable; la rama no muta artefactos del padre | Linaje en el log append-only de la rama; padre byte a byte igual (CP-026) |
| Intervención explícita y versionada, presente en la evidencia | `run.started.intervention` + `effect_policy` (CP-029) |
| La rama corre sin efectos reales por defecto | `default-deny/1`; herramientas parcheadas para explotar en el test (CP-027) |
| Cada invariante `verified/violated/unknown`; lo desconocido nunca `verified` | CP-030 |
| El reporte distingue diferencia observada de interpretación causal; sin puntaje | `statement` + `claim_level`, nunca causal (CP-031) |
| Checkpoint inválido falla claro | `InvalidCheckpoint` antes de crear el run (CP-032) |

## Fuera de alcance

Más tipos de intervención, invariantes declaradas por el usuario, políticas aprobadas por el usuario, `SIMULATE`,
sandbox de procesos, paquete de evidencia (Fase 4).
