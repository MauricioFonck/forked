# `modulos/` — Contextos acotados

↑ [Memoria central](../README.md)

Cada contexto acotado de [`docs/05`](../../docs/05-architecture.md) §5.5 es un **módulo lógico** del único paquete
`forked`, no un servicio. Solo tiene carpeta aquí cuando tiene código. Para documentar uno nuevo, usa la
[plantilla de contexto](../PLANTILLAS/plantilla-modulo.md).

| Contexto | README | Responsabilidad | Estado | Fase |
|---|---|---|---|---|
| Runs & Capture | [runs](runs/README.md) | Ciclo de vida, sobre de evento, orden, redacción, completitud, persistencia, SDK, CLI | ✅ implementado | 1 |
| Effects & Safety | [effects](effects/README.md) | Taxonomía de efectos (hecho); política default-deny y aprobaciones (pendiente) | 🟡 parcial | 1–3 |
| Replay | [replay](replay/README.md) | Cursor de observaciones y replay estricto; nunca ejecuta herramientas | ✅ implementado | 2 |
| Branches & Interventions | — | Linaje inmutable, referencias a checkpoint, intervenciones | ⏳ | 3 |
| Comparison & Invariants | — | Diferencias observadas, evaluación de invariantes, incertidumbre | ⏳ | 3 |
| Evidence | — | Manifiestos, hashes, exportación y verificación offline | ⏳ | 4 |
| Integrations | — | Contratos de adaptador e integraciones concretas (OTel, frameworks) | ⏳ | 5 |
| Interfaces | dentro de [runs](runs/README.md#cli) | CLI hoy; UI/API después | ✅ CLI | 1 |

Dependencias permitidas entre contextos: `runs` y `effects` no dependen de nadie (salvo `domain/shared`). Replay
depende de `runs` (y `effects` solo por la clase de efecto); branches de `runs`; comparison de `branches`; evidence de todos. Sin ciclos.
