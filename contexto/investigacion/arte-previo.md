# Arte previo (puerta obligatoria)

↑ [Investigación](README.md) · [Memoria central](../README.md)

[`docs/12`](../../docs/12-decisions-and-open-questions.md) §12.3 exige, antes de llamar **novedoso** al CIP o
proponerlo como estándar, publicar una matriz de arte previo con URLs fechadas y nivel de confianza.

**Estado al 2026-11-22: primera pasada publicada, puerta PARCIALMENTE ABIERTA.** La matriz pública es
[`docs/15-prior-art-matrix.md`](../../docs/15-prior-art-matrix.md). Mientras la puerta no cierre, **no** se usa
«novedoso», «primero», «único» ni «estándar» (lo impide el guardián de documentación,
[ADR-014](../forked/decisiones-arquitectura/ADR-014-documentacion-publica-y-puerta-de-release.md)).

| Paso exigido por §12.3 | Estado al 2026-11-22 |
|---|---|
| Literatura académica | 🟡 5 trabajos leídos **a nivel de resumen** (CAR, Chronicle, DoVer, CausalFlow, ReplayRCA); sin evaluar métodos ni código |
| GitHub y registros de paquetes | 🟡 6 proyectos de código abierto leídos a nivel de README; sin auditoría de código; sin registros de paquetes (solo se vio que `forked` está ocupado en PyPI, [ADR-002](../forked/decisiones-arquitectura/ADR-002-nombre-distribucion.md)) |
| OpenTelemetry | 🟡 registro de atributos GenAI leído (los atributos «se movieron» a otro repositorio); estabilidad de la especificación **no verificada** |
| OpenInference, W3C Trace Context, OCI, protocolos de workflow | ⏳ sin revisar |
| Plataformas (LangGraph, Temporal, Phoenix) | ✅ páginas oficiales leídas, con cita literal (LangGraph y Temporal) |
| Patentes | ⏳ (solo si hay comercialización) |
| Comparar modelos de datos y semántica, no solo nombres | ⏳ se compararon **capacidades**, no esquemas |
| Matriz publicada con URLs fechadas y confianza | ✅ primera pasada |

## Lo que encontró la primera pasada

1. **Lo básico ya existe**: grabar, reproducir desde observaciones, reemplazar un resultado de herramienta, hashing,
   redacción y bifurcar desde un checkpoint lo hacen plataformas, varios proyectos pequeños y la investigación reciente.
   FORKED **no** lo reclama como nuevo.
2. **Lo que no se encontró en las fuentes leídas** es la *combinación* de (a) clases de efecto con denegación por
   defecto, (b) invariantes `verified/violated/unknown` con un nivel de afirmación acotado por debajo de lo causal y
   (c) un paquete portable cuya **validez** se recalcula sin conexión. Es una afirmación sobre una combinación y está
   limitada a lo leído; «no encontrado» **no** es «no existe».
3. Un proyecto (`hassanzafarr/AgentReplay`) declara como límite que las escrituras no se aíslan en replay y como
   trabajo futuro un replay «sandboxed» para herramientas con efectos de escritura: señal de que el hueco es real.
4. **Solapamientos a vigilar**: `agentreplay` (inyección + hash encadenado) y Chronicle (replay por puntos de corte).
5. La investigación (CAR y compañía) persigue **otro objetivo** (atribuir causa por muestreo con intervalos de
   confianza); FORKED se detiene deliberadamente en «comparación controlada de un par de runs».

## Qué falta para cerrar la puerta

Revisar OpenInference, W3C Trace Context, OCI/in-toto/SLSA (procedencia y atestación), W3C PROV, LangSmith, Langfuse,
AgentOps, Braintrust, Inspect AI, MLflow/DVC, depuradores de grabar-reproducir (rr/Pernosco), `langchain-replay`;
leer los artículos completos; comparar **modelos de datos**; y, si se comercializa, patentes. Hasta entonces, cualquier
afirmación sobre esos sistemas está **sin respaldo**.
