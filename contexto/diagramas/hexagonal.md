# Hexagonal: capas y dependencias

↑ [Diagramas](README.md) · [Memoria central](../README.md)

```mermaid
flowchart TB
  subgraph IN[Adaptadores de entrada]
    CLI["cli/app.py<br/>Typer"]
    SDK["sdk/recorder.py<br/>Recorder · RecordedRun"]
  end
  subgraph APP[Aplicación]
    REC["commands/record_run.py<br/>RecordingService · RecordingSession"]
    INS["queries/inspect_run.py<br/>InspectRun · ListRuns"]
    PIPE["capture.py<br/>CapturePipeline"]
    PORTS["ports/<br/>EventLog · RunRepository · Clock<br/>IdGenerator · EnvironmentProbe"]
  end
  subgraph DOM[Dominio — solo stdlib]
    RUN["runs/<br/>Run · Event · redaction<br/>sequence · completeness"]
    EFF["effects/<br/>EffectClass"]
    SH["shared/<br/>errors · ids · canonical · schema"]
  end
  subgraph OUT[Adaptadores de salida]
    FS["persistence/filesystem<br/>records.py (Pydantic) · store.py"]
    SYS["system/runtime.py<br/>SystemClock · RandomIdGenerator · PlatformProbe"]
  end
  BOOT["bootstrap/container.py"]
  CLI --> BOOT
  CLI --> INS
  SDK --> REC
  REC --> PIPE
  REC --> PORTS
  INS --> PORTS
  APP --> DOM
  FS -. implementa .-> PORTS
  SYS -. implementa .-> PORTS
  BOOT --> APP
  BOOT --> FS
  BOOT --> SYS
```

La flecha de la aplicación a los adaptadores **no existe**: la aplicación solo ve puertos. Lo vigila
[`test_dependency_rule.py`](../../tests/guardians/test_dependency_rule.py).
