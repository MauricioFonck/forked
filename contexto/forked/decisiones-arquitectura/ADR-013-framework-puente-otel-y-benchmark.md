# ADR-013 — Primer framework (Pydantic AI), puente OpenTelemetry y diseño del benchmark FCRB

↑ [Índice de ADR](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-22 |
| **Estado** | Vigente |
| **Refina** | `docs/09` Fase 5 («un adaptador elegido por demanda de usuarios y factibilidad»), `docs/06` §6.8, `docs/08` §8.2–8.6, [ADR-010](ADR-010-replay-estricto-sin-politica.md), [ADR-011](ADR-011-ramas-checkpoint-y-comparacion.md) |

## Contexto

La Fase 5 pide un puente OpenTelemetry, **un** adaptador de framework, los escenarios FCRB y un runner reproducible.
El criterio de `docs/09` es «demanda de usuarios y factibilidad»: **no hay datos de demanda** (el repositorio acaba de
publicarse), así que la elección se hizo solo por factibilidad y por las reglas del propio proyecto. El dueño pidió
escoger el mejor según la lógica del negocio.

## Decisión 1 — Pydantic AI es el primer adaptador

Se probaron los tres candidatos en un entorno aislado antes de decidir:

| Criterio (de dónde sale) | Pydantic AI | LangGraph | OpenAI Agents SDK |
|---|---|---|---|
| Corre **sin red ni API key**, benchmark reproducible por un tercero (`docs/08` §8.5–8.6, `CLAUDE.md`: «sin dependencia de red oculta») | ✅ `FunctionModel`/`TestModel` incluidos; verificado con `connect` bloqueado | ⚠️ requiere construir un modelo falso | ⚠️ pensado para el proveedor |
| Un **único punto** por el que pasa toda llamada a herramienta (grabar, replay y rama comparten la costura) | ✅ `WrapperToolset.call_tool` | ⚠️ por nodo / herramienta de LangChain | ⚠️ por decorador |
| Paquetes de terceros instalados (cadena de suministro, `docs/07`) | **17** | 38 | 39 |
| Núcleo **neutral al proveedor** (`CLAUDE.md`) | ✅ | ✅ | ❌ acoplado a un proveedor |
| Reusa lo que ya usamos (Pydantic, OpenTelemetry API) | ✅ | ❌ | ❌ |

LangGraph tiene viaje en el tiempo propio (`docs/03`): es la **línea base** natural para comparar y el **segundo**
adaptador, no el primero, para no difuminar qué aporta FORKED. Es una elección por factibilidad; si aparece demanda
real distinta, se revisa.

Reglas del adaptador (`adapters/inbound/frameworks/pydantic_ai_toolset.py`):

- Dependencia **opcional** (`forked-runtime[pydantic-ai]`); el núcleo no la importa (el guardián de dependencias lo
  cubre porque `domain`/`application` no pueden importar adaptadores).
- Una sola costura: `ForkedToolset(WrapperToolset)` delega en `RecordedRun.acall_tool` (gemelo asíncrono de
  `call_tool`, misma lógica compartida por `_begin`/`_Step`).
- Cada herramienta declara su clase de efecto; **sin declarar ⇒ `unknown`** (denegada en ramas).
- `on_denied="raise"` (por defecto) aborta el agente; `"report"` entrega al modelo una denegación **explícita**
  (`{"denied": true, "reason": …}`) y queda registrada como `tool.error`. Nunca se finge un éxito.
- Solo se observan llamadas a herramientas; **no** las peticiones al modelo. Replay y ramas **re-ejecutan el
  agente**: un LLM real muestreado de nuevo suele pedir otras llamadas y el replay **falla cerrado**. Un modelo
  guionado reproduce exacto.
- Argumentos y resultados deben ser JSON; si no, falla ruidosamente (`InvalidEvent`) y el run queda `failed`.

## Decisión 2 — Puente OpenTelemetry en OTLP/JSON puro, sin el SDK de OTel

`domain/telemetry/otlp.py` mapea sin añadir dependencias (CIP no redefine trazas, `docs/06` §6.8):

- **Exportar:** un span `forked.run` y un span hijo `execute_tool <nombre>` por llamada, con atributos GenAI donde
  existen (`gen_ai.operation.name`, `gen_ai.tool.name`, `gen_ai.tool.call.arguments/result`) y `forked.*` para lo que
  el tracing no modela (clase de efecto, estado de captura, decisión de política, digests). Ids derivados de ids de
  FORKED ⇒ **determinista**. **Los payloads no se exportan** salvo `--include-payloads` (una exportación sale de la
  máquina; ya están redactados, pero es opt-in).
- **Importar:** spans `execute_tool` ⇒ eventos con clase **`unknown`** (un trace no dice nada de efectos), sin puntos
  de captura declarados (completitud **desconocida**, no 100 %), y la procedencia (`start/end_unix_nano`,
  `inputs_present`) en el payload **del resultado**, no de la llamada.
- Límites duros: 5 MiB de archivo, 10 000 spans; JSON malformado o sin spans de herramienta ⇒ `InvalidTrace`.

Un defecto de diseño se detectó **antes de publicar**, con un test propio: la primera versión guardaba la
procedencia dentro del payload de la llamada, así que un run importado nunca podía reproducirse (las entradas jamás
coincidían), y el export anidaba `inputs` dos veces. Se corrigió: el payload de la llamada importada tiene la misma
forma que el del SDK y el export entrega los argumentos tal cual.

## Decisión 3 — Diseño del benchmark

- Paquete `benchmarks/` en la raíz, **fuera** del paquete instalado; se ejecuta con `python -m benchmarks.fcrb`.
- Cada escenario devuelve **hechos medidos** y `status` (`pass`/`fail`/`skipped`); **no hay puntaje único**
  (`docs/08` §8.3). Un escenario que revienta se reporta `fail`, no aborta el runner.
- **Línea base ejecutada de verdad**: logs simples (replay = re-ejecutar las herramientas; un log alterado o
  truncado sigue siendo parseable). Las demás líneas base (OTel genérico, LangGraph, Temporal, Phoenix) se listan
  **con el motivo de no ejecutarse**; no se inventa una comparación injusta (`docs/08` §8.4).
- Solo `overhead` y `environment` varían entre corridas; el resto es determinista y un test lo exige.
- El benchmark **debe poder fallar**: se rompió FORKED a propósito (redacción apagada, replay que ejecuta,
  afirmaciones siempre «controladas», huecos no reportados, hashes sin comparar, entorno sin comparar, rama que muta
  al padre) y cada defecto hizo fallar el escenario correspondiente. Ese control encontró un escenario débil (S06
  solo miraba la lista de huecos y no si la secuencia queda inválida) y el runner abortaba en vez de reportar; ambos
  corregidos.

## Alternativas descartadas

- **LangGraph primero** — más usado, pero 38 paquetes, sin modelo offline listo, y su time travel nativo mezclaría
  «baseline» con «adaptador». Segundo adaptador.
- **OpenAI Agents SDK** — acoplado a un proveedor; contradice el núcleo neutral.
- **Un adaptador «genérico» por monkeypatching** — frágil y sin garantías; una costura oficial es mejor.
- **Depender del SDK de OpenTelemetry** — peso y superficie sin necesidad; OTLP/JSON es un formato de texto simple.
- **Un puntaje compuesto del benchmark** — prohibido por `docs/08` §8.3.
- **Optimizar el costo de captura ahora** — ~2,4 ms por llamada de herramienta en Windows (2 eventos, cada uno abre y
  vuelca el archivo); irrelevante frente a una llamada a un LLM y sin carga medida que lo exija (YAGNI). Se informa.

## Consecuencias

- El adaptador solo es tan reproducible como su modelo: la garantía de replay vale con modelos deterministas.
- Un run importado de OTel sirve como evidencia y para ramas, pero toda llamada cuyas entradas cambien se **deniega**
  hasta que alguien declare sus efectos.
- Los resultados son **provisionales**: sin reproducción independiente, el benchmark no está «validado» (`docs/08` §8.6).
  Las instrucciones de reproducción se probaron desde un clon limpio, pero lo hizo el mismo autor.
- `capture_points` = herramientas declaradas: un run que no llama a alguna aparece con «punto de captura nunca
  observado» (conservador).
