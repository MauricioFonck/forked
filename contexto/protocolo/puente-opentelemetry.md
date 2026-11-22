# Puente OpenTelemetry (OTLP/JSON)

↑ [Protocolo](README.md)

Decisión: [ADR-013](../forked/decisiones-arquitectura/ADR-013-framework-puente-otel-y-benchmark.md). Código:
`src/forked/domain/telemetry/otlp.py`. CIP **no redefine** el tracing (`docs/06` §6.8): solo mapea.

## Exportar (`forked otel-export RUN`)

Un `resourceSpans` con un span raíz `forked.run <adaptador>` y un span hijo por llamada de herramienta.

| Campo / atributo | Valor |
|---|---|
| `traceId` | `trace_id` del evento si existe; si no, `sha256(run_id)[:32]` |
| `spanId` | `span_id` del evento; si no, `sha256(event_id)[:16]` |
| `name` | `execute_tool <herramienta>` |
| `gen_ai.operation.name` / `gen_ai.tool.name` | `execute_tool` / nombre |
| `gen_ai.tool.call.arguments` / `.result` | **solo con `--include-payloads`** (ya redactados) |
| `forked.effect_class` · `forked.call_capture_status` · `forked.outcome_capture_status` | clase y estados de captura |
| `forked.decision` | `replay` / `intervene` / `deny` en replay y ramas |
| `forked.inputs_digest` · `forked.outputs_digest` | SHA-256 canónico (sin exponer datos) |
| `status.code` | 1 = resultado, 2 = error (`error.type` + `message`), 0 = sin resultado |

Determinista: mismos eventos, mismo JSON.

## Importar (`forked otel-import FILE`)

Se toman los spans con `gen_ai.operation.name = execute_tool` o nombre `execute_tool <x>`, ordenados por hora de inicio.

| Resultado en FORKED | Por qué |
|---|---|
| `effect_class = unknown` en cada llamada | un trace no dice nada de efectos ⇒ denegada en ramas si cambian sus entradas |
| `capture_points` vacío ⇒ completitud «desconocida» | un trace no declara puntos de captura |
| payload de la llamada = `{"inputs": …}` | misma forma que el SDK ⇒ el run importado se puede reproducir y bifurcar |
| procedencia (`start/end_unix_nano`, `inputs_present`, `result_present`) en el payload del **resultado** | no contamina la comparación de entradas |
| `trace_id` / `span_id` válidos (32 / 16 hex) se conservan; los inválidos se descartan | |

Rechazos (`invalid_trace` / `storage_failure`): JSON malformado, sin spans de herramienta, span sin nombre de
herramienta, más de 10 000 spans, archivo de más de 5 MiB o inexistente. Los secretos de los argumentos se redactan
al capturar, como en cualquier run.
