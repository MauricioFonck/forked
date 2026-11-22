# Spec 008 · Primera pasada de arte previo y segundo adaptador (LangGraph)

[Plan](plan.md) · [Tareas](tasks.md) · [Bitácora](../../../../sesiones/2026-11-22-g-arte-previo-langgraph-y-release.md) · [Impacto](../../../../impacto/2026-11-22-g-arte-previo-langgraph-y-release.md)

**Fecha:** 2026-11-22 · **Estado:** hecha (puerta de arte previo **parcialmente abierta**)

## Qué y por qué

Dos tareas que el dueño pidió ejecutar: (1) la **matriz de arte previo** que `docs/12` §12.3 exige antes de hablar de
novedad, y (2) un **segundo adaptador** (LangGraph) que, además, sirve de línea base medida para `docs/08` §8.4.

## Decisiones

[ADR-015](../../../../forked/decisiones-arquitectura/ADR-015-posicionamiento-tras-el-arte-previo.md) (posicionamiento) y
[ADR-016](../../../../forked/decisiones-arquitectura/ADR-016-adaptador-langgraph-y-linea-base.md) (LangGraph).

## Criterios de aceptación

| Criterio | Cómo se cumple |
|---|---|
| Matriz con URLs fechadas y confianza por fila | [`docs/15`](../../../../../docs/15-prior-art-matrix.md) (CP-055) |
| Lo que ya existe se reconoce; la diferencia se afirma solo como combinación acotada | README + guardián (CP-055) |
| Límites y lo no revisado se declaran | `docs/15` §1 y §7; [arte previo](../../../../investigacion/arte-previo.md) |
| Segundo adaptador por una costura única | `forked_tool_node` (CP-052…054) |
| LangGraph como línea base **medida**, no descrita | S04 del FCRB (CP-056) |
| Tres adaptadores equivalentes en S10; versiones de frameworks registradas | S10, `results.json` (CP-056) |

## Fuera de alcance

Cerrar la puerta de arte previo (OpenInference, W3C Trace Context, OCI/in-toto, patentes, modelos de datos), registrar
llamadas al modelo, registrar el estado del grafo, y una reproducción independiente.
