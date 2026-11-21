# Roadmap

↑ [Memoria central](../README.md)

> Fuente: [`docs/09-roadmap-and-backlog.md`](../../docs/09-roadmap-and-backlog.md). Aquí se anota el estado real y lo
> que se aprendió. Estado vivo en [`estado-actual.md`](estado-actual.md).

**Regla:** no se empieza P2/P3 mientras fallen criterios de aceptación de P0/P1.

| Fase | Entregables | Criterio de salida | Estado |
|---|---|---|---|
| 0 · Cimientos | Andamiaje, carta, arquitectura, modelo de amenazas, borrador de esquema, CI | Decisiones registradas; README sin afirmaciones sin sustento | ✅ 2026-11-21 ([spec 001](../docs/superpowers/specs/001-cimientos-del-repositorio/spec.md)). Pendiente: revisión de arte previo del nombre del protocolo ([arte previo](../investigacion/arte-previo.md)) |
| 1 · Grabador | Modelos `Run`/`Event`, JSONL, validación de secuencia, redacción, adaptador de juguete, `record`/`inspect` | Grabar e inspeccionar offline; eventos malformados fallan claro; redacción probada | ✅ 2026-11-21 ([spec 002](../docs/superpowers/specs/002-grabador-local/spec.md)) |
| 2 · Replay | Búsqueda de observaciones, contexto de replay, sustitución de resultados, fallo cerrado, sin camino de escritura | El demo reproduce la salida grabada; un test prueba que el adaptador de escritura no se invocó | ⏳ [spec 003](../docs/superpowers/specs/003-replay-de-observaciones/spec.md) en borrador |
| 3 · Ramas | Linaje inmutable, una intervención, stream por rama, comparación, invariantes | Padre intacto; intervención en la evidencia; desconocido nunca se marca verificado | ⏳ |
| 4 · Evidencia | Manifiesto, SHA-256, exportación determinista, verificador offline | Detecta artefactos cambiados/faltantes; separa integridad de validez | ⏳ |
| 5 · Adaptador y benchmark | Puente OTel, un adaptador de framework, escenarios FCRB, runner reproducible | Un caso end-to-end documentado; reproducción independiente | ⏳ |
| 6 · Alfa pública | Sitio de docs, repo de ejemplo, plantillas, notas de versión, feedback | — | ⏳ (adelantado: CONTRIBUTING, SECURITY, plantillas de issues y PR) |

## Adelantos hechos fuera de orden (y por qué)

- **Políticas OSS** (Fase 6 en el plan original) se hicieron en la Fase 0: un repositorio público sin `SECURITY.md` ni
  canal privado de reporte invita a reportar vulnerabilidades en issues públicos.
- **Taxonomía de efectos** (Fase 2) se adelantó como vocabulario: la Fase 1 ya registra la clase de efecto de cada
  herramienta, así los runs grabados hoy servirán para el replay de mañana.
