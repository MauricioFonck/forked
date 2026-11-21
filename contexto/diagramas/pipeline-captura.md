# Pipeline de captura

↑ [Diagramas](README.md) · [Memoria central](../README.md)

```mermaid
flowchart TD
  A["RecordedRun.call_tool(nombre, efecto, fn, **inputs)"] --> B["EventDraft tool.call<br/>payload = {inputs}"]
  B --> C{"¿límite de eventos<br/>alcanzado?"}
  C -- sí --> X1["mark_incomplete + CaptureFailed"]
  C -- no --> D{"¿JSON válido?<br/>(sin NaN, serializable)"}
  D -- no --> X2["InvalidEvent<br/>(el SDK cierra el run como failed)"]
  D -- sí --> E["redact(): claves sensibles<br/>+ valores con forma de credencial"]
  E --> F{"¿tamaño > 64 KiB?"}
  F -- sí --> G["omitted: payload=null<br/>digest sha256 del contenido redactado"]
  F -- no --> H["captured | redacted"]
  G --> I["Run.append(): asigna secuencia,<br/>Event valida invariantes"]
  H --> I
  I --> J{"EventLog.append()"}
  J -- error --> X3["mark_incomplete + CaptureFailed"]
  J -- ok --> K["línea en events.jsonl"]
  K --> L["fn(**inputs) se ejecuta"]
  L --> M["tool.result | tool.error<br/>(mismo pipeline)"]
```

Notas: la herramienta **sí se ejecuta** al grabar (la línea base es una ejecución real). Redactar antes de medir evita
que el digest de un secreto quede en disco ([ADR-007](../forked/decisiones-arquitectura/ADR-007-omitir-no-truncar.md)).
