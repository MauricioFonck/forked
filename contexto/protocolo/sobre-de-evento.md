# Sobre de evento — esquema v0.1.0

↑ [Protocolo](README.md) · [Memoria central](../README.md)

Esquema publicado: [`spec/cip/v0.1/event.schema.json`](../../spec/cip/v0.1/event.schema.json) (generado desde
`EventRecord` en `adapters/outbound/persistence/filesystem/records.py`). Una línea de `events.jsonl` = un evento.

## Campos

| Campo | Obligatorio | Tipo | Regla |
|---|---|---|---|
| `schema_version` | sí | `"MAJOR.MINOR.PATCH"` | Hoy `0.1.0`. Mayor no soportada ⇒ se rechaza antes de validar |
| `event_id` | sí | `evt_[0-9a-z]{8,64}` | Único por evento |
| `run_id` | sí | `run_[0-9a-z]{8,64}` | El run dueño; debe coincidir con la carpeta |
| `sequence` | sí | entero ≥ 0 | Contiguo desde 0 en orden de archivo ([ADR-009](../forked/decisiones-arquitectura/ADR-009-secuencia-ids-tiempo.md)) |
| `event_type` | sí | enum | `run.started` · `tool.call` · `tool.result` · `tool.error` · `run.completed` · `run.failed` |
| `timestamp` | sí | RFC 3339 con zona | Sin zona ⇒ inválido |
| `source` | sí | string no vacío | `forked.recorder`, `forked.sdk`, … |
| `capture_status` | sí | enum | `captured` · `redacted` · `omitted` |
| `payload` | no | JSON | Ya redactado. Ausente/`null` si `omitted` |
| `payload_digest` | si `omitted` | `sha256:<hex>` | Del contenido **redactado** ([ADR-007](../forked/decisiones-arquitectura/ADR-007-omitir-no-truncar.md)) |
| `redacted_paths` | si `redacted` | lista de rutas | Estilo JSONPath (`$.inputs.api_key`); vacía si `captured` |
| `tool_name` | en `tool.*` | string | — |
| `effect_class` | en `tool.*` | enum | [Taxonomía](taxonomia-de-efectos.md) |
| `parent_event_id` | no | `evt_…` | `tool.result`/`tool.error` apuntan a su `tool.call` |
| `trace_id`, `span_id` | no | string | Puente futuro con OpenTelemetry |

Campos del borrador CIP §6.4 **aún no usados**: `payload_ref` (payloads externos), `model_provider`, `model_name`,
`environment_fingerprint` por evento (hoy vive en `run.json`), `sensitivity_labels`.

## Ejemplo (fixture dorado `02-tool-call-redacted.json`)

```json
{"schema_version":"0.1.0","event_id":"evt_00000000000000000000000000000002",
 "run_id":"run_00000000000000000000000000000001","sequence":1,"event_type":"tool.call",
 "timestamp":"2026-11-21T12:00:00.001000Z","source":"forked.sdk","capture_status":"redacted",
 "payload":{"inputs":{"base":"USD","quote":"EUR","api_key":"[REDACTED]"}},
 "redacted_paths":["$.inputs.api_key"],"tool_name":"get_exchange_rate","effect_class":"external_read"}
```

Los cinco fixtures están en `tests/fixtures/events/v0.1/`. `run.json` tiene su propio esquema:
[`spec/cip/v0.1/run.schema.json`](../../spec/cip/v0.1/run.schema.json).
