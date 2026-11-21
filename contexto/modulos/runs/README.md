# Contexto `runs` — Runs & Capture

↑ [Contextos](../README.md) · [Memoria central](../../README.md)

## Responsabilidad

Grabar una ejecución como una secuencia **ordenada, tipada y redactada** de eventos, y decir con honestidad **qué tan
completa** quedó esa grabación. Cubre UC-01 de [`docs/04`](../../../docs/04-product-requirements.md) y FR-001…FR-004 y
FR-015 (parcial: SDK y CLI).

## Qué problema resuelve

Sin una grabación fiable no hay replay ni comparación. Y una grabación incompleta que parece completa es peor que
ninguna: lleva a conclusiones falsas. Por eso este contexto produce, junto con los eventos, una **lista explícita de
evidencia faltante**.

## Archivos

| Archivo | Capa | Responsabilidad |
|---|---|---|
| `domain/runs/run.py` | Dominio | Agregado `Run`, `RunStatus`, `RunSnapshot`, `PreparedPayload`; máquina de estados |
| `domain/runs/event.py` | Dominio | `Event` (sobre, valida invariantes), `EventDraft`, `EventType`, `CaptureStatus` |
| `domain/runs/capabilities.py` | Dominio | `AdapterCapabilities` (nombre, versión, puntos de captura, limitaciones) |
| `domain/runs/environment.py` | Dominio | `EnvironmentFingerprint`; hechos faltantes = `None`, nunca inventados |
| `domain/runs/redaction.py` | Dominio | `RedactionPolicy`, `redact()` por nombre de clave y forma de valor |
| `domain/runs/sequence.py` | Dominio | `check_sequence()`: huecos, duplicados, desorden, eventos ajenos |
| `domain/runs/completeness.py` | Dominio | `assess()`: estado efectivo, completitud y evidencia faltante |
| `domain/shared/*` | Dominio | Errores, identificadores, JSON canónico + sha256, versión de esquema |
| `application/capture.py` | Aplicación | `CapturePipeline`: validar → redactar → limitar tamaño |
| `application/commands/record_run.py` | Aplicación | `RecordingService`, `RecordingSession` |
| `application/queries/inspect_run.py` | Aplicación | `InspectRun`, `ListRuns`, `RunReport` |
| `application/ports/__init__.py` | Puertos | `EventLog`, `RunRepository`, `Clock`, `IdGenerator`, `EnvironmentProbe` |
| `adapters/outbound/persistence/filesystem/records.py` | Adaptador | Formato v0.1 en Pydantic ↔ dominio |
| `adapters/outbound/persistence/filesystem/store.py` | Adaptador | `FileSystemRunStore` (implementa `EventLog` + `RunRepository`) |
| `adapters/outbound/system/runtime.py` | Adaptador | `SystemClock`, `RandomIdGenerator`, `PlatformProbe` |
| `adapters/inbound/sdk/recorder.py` | Entrada | `Recorder.record()`, `RecordedRun.call_tool()` |
| `adapters/inbound/cli/app.py` | Entrada | Comandos `record`, `inspect`, `runs` |
| `bootstrap/container.py` | Composición | `build_application()` |
| `demo/toy_agent.py` | Demo | Agente de juguete y sus limitaciones declaradas |

## Reglas de negocio clave

- Estados: `recording` → `completed` | `failed` | `incomplete`. Los terminales no aceptan nada más
  ([diagrama](../../diagramas/ciclo-de-vida-run.md)). `completed` **no** significa captura completa.
- El primer evento es `run.started`; el último, `run.completed` o `run.failed`. Los eventos de herramienta exigen
  `tool_name` y `effect_class`; `tool.result`/`tool.error` llevan `parent_event_id` del `tool.call`.
- Todo payload pasa por el pipeline **antes** de existir como `Event` ([diagrama](../../diagramas/pipeline-captura.md)).
- Completitud = puntos declarados observados / declarados. Sin puntos declarados ⇒ **desconocida** (`None`).
- Evidencia faltante incluye: run sin finalizar, primer/último evento incorrecto, `next_sequence` ≠ líneas del log,
  huecos/duplicados/desorden, puntos declarados no vistos o vistos sin declarar, hechos de entorno faltantes, payloads
  omitidos.
- Límite de eventos por run (100 000) y de bytes por payload (64 KiB): al superarlos, se **falla cerrado** o se omite
  con digest ([ADR-007](../../forked/decisiones-arquitectura/ADR-007-omitir-no-truncar.md)).

## Persistencia

`<store>/runs/<run_id>/events.jsonl` (append-only) y `run.json` (atómico). Detalle y recuperación ante caídas en
[ADR-004](../../forked/decisiones-arquitectura/ADR-004-persistencia-fase-1.md); formato de línea en
[sobre de evento](../../protocolo/sobre-de-evento.md). Al leer: línea > 1 MiB, sin `\n`, JSON inválido, versión mayor no
soportada o registro inválido ⇒ `CorruptRecording` con número de línea. `run.json` de otro run ⇒ `CorruptRecording`.

## CLI

| Comando | Qué hace | Salida |
|---|---|---|
| `forked record toy-agent [--store DIR]` | Ejecuta y graba el agente de juguete | Id del run + reporte |
| `forked inspect RUN_ID [--events] [--json] [--strict]` | Reporte de un run | 0 ok · 1 con `--strict` si falta evidencia · 2 error |
| `forked runs [--store DIR]` | Lista runs | Una línea por run |
| `forked --version` | Versión | — |

`--store` también se toma de `FORKED_STORE`; por defecto `.forked/`. Los errores se imprimen como
`error[<code>]: <mensaje>` en stderr.

## Consumido por

- Usuarios vía CLI y SDK. Mañana: el contexto **replay** leerá `EventLog` para resolver observaciones grabadas.

## Tests que lo cuidan

`tests/unit/domain/*`, `tests/unit/application/test_record_run.py`, `tests/contract/test_run_store_contract.py`,
`tests/security/test_persistence_security.py`, `tests/integration/test_cli.py`,
`tests/acceptance/test_toy_agent_end_to_end.py`. Comportamientos: CP-001…CP-020 en
[comportamientos protegidos](../../impacto/comportamientos-protegidos.md).

## 📌 Pendiente de pasada profunda

- [ ] Ficha por archivo de `domain/runs/run.py` y `application/commands/record_run.py` con la
  [plantilla de archivo](../../PLANTILLAS/plantilla-archivo.md).
- [ ] Lista blanca de claves para reducir sobre-redacción (cuando un adaptador real lo necesite).
