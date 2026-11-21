# FORKED — Contexto general

↑ [Memoria central](../README.md)

> **Visión general del proyecto.** La puerta de entrada es la [memoria central](../README.md); este documento da la
> visión global y enlaza al detalle. La fuente original es la propuesta técnica en [`docs/`](../../docs/01-project-charter.md)
> (inglés), resumida y anotada aquí.

## 1. Qué es FORKED

**FORKED (Open Counterfactual Computing Infrastructure)** es infraestructura open source para experimentar de forma
confiable con alternativas de ejecución: *¿qué habría pasado si…?* aplicado a flujos de software y agentes de IA.

Lema: **Explore what could have happened. Verify what changed.**

Se distribuye como un paquete Python (`forked-runtime`, import `forked`) con SDK y CLI. Corre en la máquina del
usuario; no hay servicio hospedado.

## 2. Problema que resuelve

Una ejecución de un agente depende de mucho más que su prompt o su código: muestreo del modelo, respuestas de APIs,
estado de bases de datos, hora, aleatoriedad, archivos, versiones de paquetes, credenciales. Si alguien cambia una
decisión y compara dos ejecuciones, la diferencia puede venir de **otra** cosa que también cambió. Y re-ejecutar puede
**repetir escrituras externas** (un correo, un pago, un `DELETE`).

FORKED investiga si una infraestructura reutilizable puede volver más disciplinados esos experimentos: registrar la
procedencia, declarar invariantes, representar intervenciones, controlar efectos secundarios y **reportar límites**.
Detalle y vocabulario: [`docs/02`](../../docs/02-problem-and-research-hypotheses.md) · [hipótesis](../investigacion/hipotesis.md).

## 3. Usuarios

1. Ingenieros de aplicaciones de IA que depuran agentes que usan herramientas (**persona principal**).
2. Ingenieros de plataforma que prueban cambios de flujo.
3. Investigadores de evaluación de IA que comparan intervenciones.
4. Mantenedores de frameworks que buscan artefactos de experimento interoperables.
5. Equipos de seguridad y confiabilidad que necesitan garantizar que un experimento no repite efectos de producción.

## 4. Qué responde FORKED (propuesta de valor)

¿Qué se capturó? ¿Qué se cambió? ¿Qué se mantuvo constante? ¿Qué se reprodujo desde observaciones grabadas? ¿Qué se
simuló, bloqueó o re-ejecutó? ¿Qué invariantes se verificaron, violaron o quedaron desconocidos? ¿Qué conclusiones se
sostienen y qué sigue incierto?

## 5. Qué NO es (v0)

Ni un modelo fundacional ni un framework de agentes · ni un orquestador de producción · ni una garantía de replay
determinista para software arbitrario · ni un oráculo causal · ni un reemplazo de OpenTelemetry, Temporal, LangGraph,
Phoenix o LangSmith. Fuera de v0: snapshots de máquina completa, captura transparente de llamadas al SO, prueba causal
automática, experimentación autónoma en producción, re-ejecución automática de escrituras, SaaS, ranking de modelos.

## 6. Reglas no negociables

Copiadas de [`CLAUDE.md`](../../CLAUDE.md) porque gobiernan todo diseño:

- No afirmar replay determinista para programas arbitrarios; distinguir **reproducir observaciones grabadas** de
  **re-ejecutar operaciones externas**.
- Nunca repetir escrituras externas en replay por defecto. Ningún efecto real en una rama experimental sin una
  política explícita, documentada y aprobada por el usuario. **Por defecto: denegar.**
- No simular un sistema externo en silencio y reportarlo como resultado real.
- Todo run identifica entradas capturadas, metadatos de entorno, versiones y **evidencia faltante**.
- Invariantes: `verified` · `violated` · `unknown`. Conclusiones: niveles de afirmación sin exagerar causalidad.
- Redactar secretos antes de persistir. Núcleo neutral respecto de proveedores. Sin dependencias de nube en el MVP.

## 7. Dónde seguir

| Tema | Documento |
|---|---|
| Qué funciona hoy | [Estado actual](estado-actual.md) |
| Cómo está construido | [Arquitectura](arquitectura.md) · [ADR-001](../../docs/14-adr-001-hexagonal-architecture.md) |
| Cómo se escribe código aquí | [Convenciones](convenciones.md) |
| Con qué | [Tecnologías](tecnologias.md) |
| Qué viene | [Roadmap](roadmap.md) |
| Por qué es así | [Decisiones de arquitectura](decisiones-arquitectura/README.md) |
| Competencia y posicionamiento | [`docs/03`](../../docs/03-competitive-landscape.md) · [arte previo](../investigacion/arte-previo.md) |
| Gobierno, licencias y alianzas | [`docs/10`](../../docs/10-governance-and-open-source.md) · [`docs/11`](../../docs/11-partnership-strategy.md) |
