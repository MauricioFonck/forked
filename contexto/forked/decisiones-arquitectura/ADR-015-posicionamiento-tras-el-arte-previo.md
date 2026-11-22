# ADR-015 — Posicionamiento tras la primera pasada de arte previo

↑ [Índice de ADR](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-22 |
| **Estado** | Vigente |
| **Refina** | `docs/12` §12.3 (puerta de arte previo), [ADR-014](ADR-014-documentacion-publica-y-puerta-de-release.md), [arte previo](../../investigacion/arte-previo.md) |

## Contexto

La primera pasada ([`docs/15`](../../../docs/15-prior-art-matrix.md)) leyó plataformas (LangGraph, Temporal, Phoenix,
OpenTelemetry), seis proyectos de código abierto y cinco artículos. Resultado incómodo y útil: **grabar, reproducir
desde observaciones, reemplazar un resultado de herramienta, hashing, redacción y bifurcar desde un checkpoint ya lo
hacen otros** (plataformas, proyectos pequeños y recientes, e investigación). Hasta ese momento el README comparaba
FORKED con *categorías* de herramientas usando «❌» absolutos que ese trabajo no sostenía.

## Decisión

1. **FORKED no se describe como «la herramienta de grabar y reproducir».** Se describe como una **capa de seguridad y
   de evidencia** para ejecuciones contrafactuales: política de efectos (clases + denegar por defecto), invariantes
   honestas (`verified/violated/unknown`, afirmación acotada por debajo de lo causal) y evidencia cuya **validez** se
   recalcula sin conexión.
2. **La diferencia se afirma solo como una combinación y solo dentro de lo leído**: «en las fuentes revisadas no
   encontramos…». «No encontrado» nunca se escribe como «no existe». Está en el README y en `docs/15`.
3. **La puerta sigue parcialmente abierta** (faltan OpenInference, W3C Trace Context, OCI/in-toto, patentes y comparar
   modelos de datos): las palabras de novedad siguen prohibidas y el guardián de documentación lo hace cumplir.
4. **Se acredita el trabajo previo**: Chronicle (replay por puntos de corte) y los artículos de intervención se citan
   donde FORKED habla de prefijo grabado + resto vivo e intervenciones.
5. **Los solapamientos se vigilan**: `agentreplay` (inyección + hash encadenado) y Chronicle. Si crecen hacia efectos o
   evidencia, la combinación se reduce y el posicionamiento se revisa.
6. **La matriz es un documento vivo con fecha**: se vuelve a pasar antes de cada release público y cuando se cierre la
   puerta; las correcciones externas que reducen la diferencia son las más valiosas.
7. **Ideas tomadas de lo leído, sin adoptarlas todavía**: registrar también las llamadas al modelo (varios proyectos lo
   hacen; FORKED no) y usar muchos runs controlados como sustrato de estimadores causales (CAR). Quedan como opciones del
   roadmap, no como compromisos.

## Alternativas descartadas

- **Seguir diciendo «primer/único»** — contradice la evidencia que acabamos de reunir.
- **Ocultar o minimizar lo que ya existe** — destruye la credibilidad que justifica el proyecto.
- **No publicar hasta cerrar toda la puerta** — la puerta completa exige leer cosas que requieren tiempo o a otras
  personas; se publica la primera pasada con sus límites y se declara parcial.
- **Comparar solo con plataformas** — dejaría fuera lo más cercano (los proyectos pequeños y la investigación).

## Consecuencias

- Menos «marketing» y más credibilidad: el valor se defiende con una combinación acotada y medible.
- El README admite lo que ya existe; un test impide quitar ese reconocimiento.
- Hay trabajo explícito pendiente para cerrar la puerta (ver [arte previo](../../investigacion/arte-previo.md)).
