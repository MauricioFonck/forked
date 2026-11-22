# Contexto `integrations`

↑ [Contextos](../README.md) · [Memoria central](../../README.md)

> Adaptadores a frameworks de agentes y al ecosistema de observabilidad. Decisión:
> [ADR-013](../../forked/decisiones-arquitectura/ADR-013-framework-puente-otel-y-benchmark.md).

## Archivos

| Capa | Archivo | Qué hace |
|---|---|---|
| adaptador | `src/forked/adapters/inbound/frameworks/pydantic_ai_toolset.py` | `ForkedToolset` (`WrapperToolset`), `pydantic_ai_capabilities`; única costura del framework |
| SDK | `src/forked/adapters/inbound/sdk/recorder.py` | `RecordedRun.acall_tool` (gemelo async), `_begin`/`_Step` compartidos, `Recorder.record(source=)` |
| dominio | `src/forked/domain/telemetry/otlp.py` | `to_otlp`, `parse_tool_spans`, `ObservedToolCall`, `InvalidTrace`, `IMPORT_LIMITATIONS` |
| aplicación | `src/forked/application/commands/otel.py` | `ExportTrace`, `ImportTrace` |
| CLI | `src/forked/adapters/inbound/cli/app.py` | `forked otel-export RUN [--include-payloads] [--out]`, `forked otel-import FILE` |
| ejemplo | `examples/pydantic_ai_expense_agent.py` | caso de uso de punta a punta (agente de gastos) |
| composición | `src/forked/bootstrap/container.py` | `build_application(probe=)`, `export_trace`, `import_trace` |

La dependencia `pydantic-ai-slim` es un **extra opcional** (`forked-runtime[pydantic-ai]`) y está en el grupo `dev`
para los tests; `domain` y `application` no la importan.

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

Solo herramientas (no peticiones al modelo); replay y ramas re-ejecutan el agente (un LLM real suele divergir y el
replay falla cerrado); los tiempos originales de un trace importado quedan en `payload.otel`; un solo framework.

## Comportamientos protegidos

CP-040 a CP-044 en [comportamientos protegidos](../../impacto/comportamientos-protegidos.md).
