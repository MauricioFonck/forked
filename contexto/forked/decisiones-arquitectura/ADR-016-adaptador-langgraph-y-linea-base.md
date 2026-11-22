# ADR-016 — Adaptador de LangGraph y su viaje en el tiempo como línea base ejecutada

↑ [Índice de ADR](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-22 |
| **Estado** | Vigente |
| **Refina** | [ADR-013](ADR-013-framework-puente-otel-y-benchmark.md) (LangGraph era «segundo adaptador y línea base»), [ADR-015](ADR-015-posicionamiento-tras-el-arte-previo.md) |

## Contexto

El ADR-013 dejó LangGraph como segundo adaptador y como línea base natural. Probado el 2026-11-22 con
`langgraph 1.2.24` / `langchain-core 1.8.4`: `ToolNode` acepta `wrap_tool_call` y `awrap_tool_call`; un modelo
guionado (un nodo de función normal) corre sin red; y repetir desde el checkpoint previo a `send_email` **volvió a
enviar el email** (1 → 2), tal como dice su documentación.

## Decisión

1. **Una sola costura**: `forked_tool_node(tools, run, effects)` devuelve un `ToolNode` con el par
   `wrap`/`awrap` (`adapters/inbound/frameworks/langgraph_toolnode.py`), delegando en `RecordedRun.call_tool` /
   `acall_tool`. Extra opcional `forked-runtime[langgraph]`; error accionable si falta.
2. **Grabando se entrega al agente el `ToolMessage` original sin tocar** (conserva `artifact`, `status`…). **En replay se
   reconstruye desde el contenido grabado**: el `artifact` no está disponible (límite declarado y probado). Una mutación
   que descartaba el mensaje original sobrevivió a la primera suite y generó el test de fidelidad.
3. **Contenido = lo que produce LangGraph** (`"0.92"`, no `0.92`); la equivalencia con otros adaptadores se compara
   decodificando JSON de forma explícita (`parse_json_outputs`), y se dice en el informe.
4. **Llamadas paralelas de un paso**: se serializan con un candado y se graban en el orden en que `ToolNode` las
   programa; el replay exige el mismo orden (límite declarado).
5. **Un `Command` se rechaza** (`UnsupportedToolResult`); LangGraph ya rechaza los inválidos antes de llegar al
   envoltorio. Una herramienta sin clase de efecto es `unknown`. Las excepciones de herramienta se propagan como sin
   FORKED; reproducir un error grabado lanza `RecordedToolError`.
6. **`on_denied`** igual que en Pydantic AI: `raise` (por defecto) aborta el grafo; `report` devuelve un `ToolMessage`
   de error explícito. Nunca se finge un éxito.
7. **El viaje en el tiempo de LangGraph pasa a ser una línea base ejecutada del benchmark (solo S04)**, con la cita de
   su documentación y la advertencia de que es *otra herramienta con otro propósito* (retomar y explorar estado): se
   mide, no se acusa. El informe registra además las **versiones exactas** de los frameworks (`docs/08` §8.5).
8. **S10 compara tres adaptadores** (SDK, Pydantic AI, LangGraph); el segundo y tercero se omiten con aviso si su extra
   no está instalado.

## Alternativas descartadas

- **Envolver cada herramienta individualmente** — N costuras y fácil olvidar una; el gancho de `ToolNode` es uno.
- **Subclasificar o parchear `ToolNode`** — frágil frente a cambios de versión; el gancho es API pública.
- **Registrar el estado del grafo vía el checkpointer de LangGraph** — duplica lo que LangGraph ya persiste y amplía el
  alcance (y los límites de redacción); fuera de esta fase.
- **Declarar la línea base como «defecto»** — sería injusto: re-ejecutar es el comportamiento documentado.

## Consecuencias

- Dos frameworks distintos producen artefactos equivalentes sobre la misma tarea: evidencia razonable (no prueba) de
  que la costura es independiente del framework.
- La garantía de replay vale con nodos de modelo deterministas, igual que con Pydantic AI.
- Quien use LangGraph puede combinar ambos: su checkpointing para reanudar y FORKED para experimentos con efectos
  denegados por defecto. No se ha probado esa combinación más allá del benchmark.
