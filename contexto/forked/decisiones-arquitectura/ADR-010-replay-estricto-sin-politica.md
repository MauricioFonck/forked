# ADR-010 — Replay estricto que nunca ejecuta herramientas; la política de efectos pasa a la Fase 3

↑ [Índice de ADR](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-21 |
| **Estado** | Vigente |
| **Refina** | `docs/09` Fase 2 («default-deny effect policy»), `docs/05` §5.8 (`EvaluateEffect`) |

## Contexto

La spec 003 proponía, para la Fase 2, un `EffectPolicy` (Strategy) que devolviera `ALLOW | REPLAY | SIMULATE | DENY`
por llamada. Al implementar el replay se vio que **en un replay no existe ningún caso legítimo de `ALLOW`**: todo
resultado debe venir de la grabación. Una política con una sola respuesta posible es una abstracción sin caso de uso
(prohibida por `CLAUDE.md`) y, peor, un camino de código que *podría* devolver `ALLOW` por error.

La spec dejó dos preguntas al dueño; se tomaron sus propuestas por defecto (el dueño pidió avanzar sin esperar):
(1) el replay **re-ejecuta el código del flujo**; (2) una divergencia **aborta** el replay.

## Decisión

1. En modo replay el SDK **no tiene camino hacia `fn`**: `call_tool` resuelve contra `ReplayCursor` y devuelve la
   salida grabada o relanza el error grabado (`RecordedToolError`). Vale para cualquier clase de efecto.
2. Emparejamiento estricto y en orden: nombre, clase de efecto y entradas **redactadas** (payload + digest). Cualquier
   diferencia ⇒ `ReplayDivergence`; sin observación, sin resultado o resultado omitido ⇒ `MissingObservation`; llamadas
   grabadas que el flujo no pidió ⇒ `ReplayDivergence` al cerrar. Todo falla cerrado y el run de replay queda `failed`.
3. El replay es un **run nuevo** con `replay_of` en el payload de `run.started` (sin cambiar el esquema v0.1.0: el
   payload es libre). Se inspecciona como cualquier otro run.
4. Solo se reproduce un run del **mismo adaptador** (nombre).
5. El `EffectPolicy` con decisiones `ALLOW/DENY/SIMULATE` se implementa en la **Fase 3**, donde una rama sí puede
   necesitar ejecutar algo nuevo tras la intervención.

## Alternativas descartadas

- **Política en la Fase 2 con `REPLAY` fijo** — código muerto y superficie de error.
- **Emparejar por herramienta sin orden** — tolera reordenamientos que cambian la semántica; se revisará si un
  framework real lo exige.
- **Continuar tras divergencia en modo «solo reporte»** — un replay que sigue con datos que no corresponden produce
  conclusiones falsas. Si se necesita, será un modo explícito.

## Consecuencias

- La hipótesis H3 (ninguna escritura externa en replay) se garantiza por **ausencia de camino**, no por una decisión
  en tiempo de ejecución: CP-022 con mutación.
- Dos llamadas que solo difieren en un secreto redactado son indistinguibles: limitación declarada en el docstring del
  cursor y en el módulo.
- El replay no reproduce el entorno, solo las observaciones: un flujo no determinista *fuera* de las herramientas
  (azar, reloj) puede divergir y lo reportará como divergencia.
- `docs/09` Fase 2 queda cumplida salvo la política, que se mueve a la Fase 3 (README y roadmap actualizados).
