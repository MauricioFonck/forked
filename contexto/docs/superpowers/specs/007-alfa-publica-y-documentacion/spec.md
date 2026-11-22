# Spec 007 · Alfa pública: documentación, ejemplos, empaquetado y feedback (Fase 6)

[Plan](plan.md) · [Tareas](tasks.md) · [Bitácora](../../../../sesiones/2026-11-22-f-fase-6-alfa-publica.md) · [Impacto](../../../../impacto/2026-11-22-f-fase-6-alfa-publica.md)

**Fecha:** 2026-11-22 · **Estado:** preparada; **el release está pendiente de decisión del dueño**

## Qué y por qué

[`docs/09`](../../../../../docs/09-roadmap-and-backlog.md) Fase 6: documentación, repositorio de ejemplos, guía de
contribución, plantillas de issues, notas de versión y feedback/revisión externa. Objetivo real: que una persona que
no es el autor pueda **instalar, ejecutar, entender, reproducir y reportar** sin ayuda, y que nada de lo que lea sea
más fuerte que la evidencia.

## Decisiones

[ADR-014](../../../../forked/decisiones-arquitectura/ADR-014-documentacion-publica-y-puerta-de-release.md).

## Criterios de aceptación

| Criterio | Cómo se cumple |
|---|---|
| Documentación bien organizada | `docs/README.md` + `docs/guide/01…06` (CP-047, CP-048) |
| Ejemplos ejecutables | `examples/minimal_sdk.py` (sin framework) y `examples/pydantic_ai_expense_agent.py` (CP-051) |
| Guía de contribución y plantillas | CONTRIBUTING con «dónde ayudar»; plantillas bug/proposal/**reproduction_report** |
| Notas de versión | `docs/release-notes/v0.1.0-alpha.1.md` (**borrador**) |
| Feedback y revisión externa | guía 06, plantilla de reproducción, etiquetas |
| Instalable y ejecutable fuera del repo | paso de CI con la rueda construida (CP-050) |
| Sin promesas más fuertes que la evidencia | guardián de sobre-afirmaciones + aviso en el README (CP-049) |

## Fuera de alcance (decisión del dueño)

Etiquetar `v0.1.0-alpha.1`, crear el GitHub Release, publicar `forked-runtime` en PyPI, habilitar Discussions, anunciar.
Tampoco: la matriz de arte previo (sigue abierta) ni la reproducción independiente (requiere a otra persona).
