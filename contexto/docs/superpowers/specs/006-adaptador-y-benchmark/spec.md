# Spec 006 · Primer adaptador de framework, puente OpenTelemetry y benchmark FCRB (Fase 5)

[Plan](plan.md) · [Tareas](tasks.md) · [Bitácora](../../../../sesiones/2026-11-22-e-fase-5-adaptador-y-benchmark.md) · [Impacto](../../../../impacto/2026-11-22-e-fase-5-adaptador-y-benchmark.md) · [Contexto `integrations`](../../../../modulos/integrations/README.md) · [Contexto `benchmarks`](../../../../modulos/benchmarks/README.md)

**Fecha:** 2026-11-22 · **Estado:** hecha (sin reproducción independiente)

## Qué y por qué

[`docs/09`](../../../../../docs/09-roadmap-and-backlog.md) Fase 5: puente de ingestión/exportación OpenTelemetry, **un**
adaptador de framework, escenarios FCRB, comparación con una línea base y un runner reproducible. Criterios de salida:
un caso de uso de punta a punta documentado y reproducción independiente. Valida la hipótesis
[H1/H5](../../../../investigacion/hipotesis.md) sobre un framework real y deja la base medible para la Fase 6.

## Decisiones

[ADR-013](../../../../forked/decisiones-arquitectura/ADR-013-framework-puente-otel-y-benchmark.md): Pydantic AI primero (por factibilidad, **sin datos de demanda**), puente OTLP/JSON sin el SDK de OTel, diseño
del benchmark (métricas separadas, línea base ejecutada, debe poder fallar).

## Criterios de aceptación

| Criterio (`docs/09` Fase 5 · `docs/08`) | Cómo se cumple |
|---|---|
| Puente OTel de ingestión/exportación | `forked otel-export` / `otel-import` (CP-043, CP-044) |
| Un adaptador de framework | `ForkedToolset` para Pydantic AI (CP-040…042) |
| Escenarios FCRB | S01…S10 en `benchmarks/fcrb/scenarios.py` |
| Comparación con línea base | logs simples **ejecutados**; el resto listado con su motivo (CP-046) |
| Runner reproducible | `python -m benchmarks.fcrb`; parte determinista exigida por test (CP-045) |
| Un caso de uso de punta a punta documentado | `examples/README.md` + `examples/pydantic_ai_expense_agent.py` |
| Instrucciones de reproducción independientes | `benchmarks/README.md`; probadas desde un clon limpio (por el mismo autor) |
| Sin puntaje opaco, límites y fallos reportados (§8.3, §8.5) | `REPORT.md` con limitaciones; escenarios `fail` visibles |

## Fuera de alcance

Segundo framework (LangGraph), reproducción independiente real, líneas base de Temporal/Phoenix/LangGraph/OTel
genérico, CPU y memoria, modelos de lenguaje reales, firma de manifiestos.
