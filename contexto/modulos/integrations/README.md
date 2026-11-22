# Contexto `integrations`

↑ [Contextos](../README.md) · [Memoria central](../../README.md)

> Adaptadores a frameworks de agentes (Pydantic AI, LangGraph) y al ecosistema de observabilidad. Decisión:
> [ADR-013](../../forked/decisiones-arquitectura/ADR-013-framework-puente-otel-y-benchmark.md).

## Archivos

| Capa | Archivo | Qué hace |
|---|---|---|
| adaptador | `src/forked/adapters/inbound/frameworks/pydantic_ai_toolset.py` | `ForkedToolset` (`WrapperToolset`), `pydantic_ai_capabilities`; única costura del framework |
| SDK | `src/forked/adapters/inbound/sdk/recorder.py` | `RecordedRun.acall_tool` (gemelo async), `_begin`/`_Step` compartidos, `Recorder.record(source=)` |
| dominio | `src/forked/domain/telemetry/otlp.py` | `to_otlp`, `parse_tool_spans`, `ObservedToolCall`, `InvalidTrace`, `IMPORT_LIMITATIONS` |
| aplicación | `src/forked/application/commands/otel.py` | `ExportTrace`, `ImportTrace` |
| CLI | `src/forked/adapters/inbound/cli/app.py` | `forked otel-export RUN [--include-payloads] [--out]`, `forked otel-import FILE` |
| adaptador | `src/forked/adapters/inbound/frameworks/langgraph_toolnode.py` | `forked_tool_node`, `ForkedToolCalls` (`wrap_tool_call` / `awrap_tool_call`), `langgraph_capabilities` ([ADR-016](../../forked/decisiones-arquitectura/ADR-016-adaptador-langgraph-y-linea-base.md)) |
| ejemplo | `examples/pydantic_ai_expense_agent.py`, `examples/langgraph_expense_agent.py`, `examples/expense_tools.py` | caso de uso de punta a punta (agente de gastos, herramientas compartidas) |
| composición | `src/forked/bootstrap/container.py` | `build_application(probe=)`, `export_trace`, `import_trace` |

Las dependencias `pydantic-ai-slim` y `langgraph` son **extras opcionales** (`forked-runtime[pydantic-ai]`, `forked-runtime[langgraph]`) y están en el grupo `dev`
para los tests; `domain` y `application` no las importan.

## Reglas

| Situación | Resultado |
|---|---|
| Herramienta sin clase de efecto declarada | se graba `unknown`; en una rama, cambiar sus entradas la **deniega** |
| Llamada denegada con `on_denied="raise"` | el agente aborta con `EffectDenied`; `tool.error` registrado |
| Llamada denegada con `on_denied="report"` | el modelo recibe `{"denied": true, "reason": …}`; `tool.error` registrado |
| Argumento o resultado no JSON | `InvalidEvent`; el run queda `failed` |
| Exportar OTel | determinista; sin payloads salvo `--include-payloads`; sin secretos |
| Importar OTel | todo `unknown`; completitud desconocida; ≤ 5 MiB y ≤ 10 000 spans |

## Límites declarados

Solo herramientas (no peticiones al modelo; en LangGraph tampoco los demás nodos ni el estado); replay y ramas
re-ejecutan el agente (un LLM real suele divergir y el replay falla cerrado); en LangGraph el resultado es el texto
que produce y el replay no conserva el `artifact`; los tiempos originales de un trace importado quedan en
`payload.otel`; dos frameworks.

## Comportamientos protegidos

CP-040 a CP-044 y CP-052 a CP-054 en [comportamientos protegidos](../../impacto/comportamientos-protegidos.md).
