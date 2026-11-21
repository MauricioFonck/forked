# Arquitectura

↑ [Memoria central](../README.md)

> Cómo está construido FORKED **hoy**. La decisión fundacional está en
> [ADR-001](../../docs/14-adr-001-hexagonal-architecture.md) y el diseño completo, en
> [`docs/05-architecture.md`](../../docs/05-architecture.md). Diagrama: [hexagonal](../diagramas/hexagonal.md).

## 1. Estilo

**Hexagonal (puertos y adaptadores) dentro de un monolito modular.** Un solo paquete Python, dividido por contextos
acotados. Las dependencias apuntan hacia adentro y un [guardián](../../tests/guardians/test_dependency_rule.py) lo hace
cumplir en cada `pytest`.

| Capa | Ruta | Puede importar | No puede importar |
|---|---|---|---|
| Dominio | `src/forked/domain/` | biblioteca estándar, `forked.domain` | Pydantic, Typer, adaptadores, aplicación |
| Aplicación | `src/forked/application/` (+ `ports/`) | estándar, dominio, aplicación | Pydantic, Typer, adaptadores, bootstrap |
| Adaptadores de entrada | `src/forked/adapters/inbound/` (CLI, SDK) | aplicación, dominio, bootstrap | adaptadores de salida concretos |
| Adaptadores de salida | `src/forked/adapters/outbound/` | todo lo anterior + librerías | — |
| Raíz de composición | `src/forked/bootstrap/container.py` | todo | — |
| Demo | `src/forked/demo/` | SDK y dominio | adaptadores de salida |

## 2. Árbol actual

```text
src/forked/
  domain/
    shared/      errors · identifiers (RunId, EventId) · canonical (JSON canónico, sha256) · schema (versión)
    runs/        run (agregado + máquina de estados) · event (sobre, tipos, estado de captura)
                 capabilities · environment · redaction · sequence · completeness
    effects/     effect_class (taxonomía CIP)
  application/
    ports/       EventLog · RunRepository · Clock · IdGenerator · EnvironmentProbe
    capture.py   CapturePipeline + CaptureLimits
    errors.py    RunNotFound · CorruptRecording · StorageFailure · CaptureFailed
    commands/    record_run (RecordingService, RecordingSession)
    queries/     inspect_run (InspectRun, ListRuns, RunReport)
  adapters/
    inbound/cli/ app.py (Typer)          inbound/sdk/ recorder.py (Recorder, RecordedRun)
    outbound/persistence/filesystem/     records.py (Pydantic, formato v0.1) · store.py
    outbound/system/runtime.py           SystemClock · RandomIdGenerator · PlatformProbe
  bootstrap/container.py                 build_application()
  demo/toy_agent.py                      agente de juguete
```

## 3. Flujo de una grabación

1. `Recorder.record(capabilities)` → `RecordingService.start`: crea `RunId`, toma la huella de entorno, guarda
   `run.json` en `recording` y escribe `run.started`.
2. `RecordedRun.call_tool(nombre, efecto, fn, **inputs)` → `tool.call` → ejecuta `fn` → `tool.result` (con
   `parent_event_id`) o `tool.error` y relanza.
3. Cada payload pasa por el [pipeline de captura](../diagramas/pipeline-captura.md); el agregado `Run` asigna la
   secuencia y crea el `Event` (que valida sus invariantes); `EventLog.append` lo persiste.
4. Al salir del bloque: `run.completed` (con el `outcome`) o, ante excepción, `run.failed` con el motivo **redactado**.
   `run.json` se reemplaza atómicamente con el estado final.
5. Si el proceso muere, `run.json` queda en `recording` y toda inspección posterior lo reporta `incomplete`.

## 4. Errores

Todo fallo esperado es un `ForkedError` con `code` estable (`invalid_identifier`, `invalid_event`, `illegal_transition`,
`unsupported_schema_version`, `run_not_found`, `corrupt_recording`, `storage_failure`, `capture_failed`). Los adaptadores
traducen `OSError`, `ValidationError` y `JSONDecodeError` a estos tipos; ninguna excepción de terceros cruza al dominio.
La CLI imprime `error[<code>]: mensaje` y sale con 2.

## 5. Patrones usados — y dónde

| Patrón | Dónde | Por qué |
|---|---|---|
| Agregado + máquina de estados | `domain/runs/run.py` | Solo `Run` cambia estado y asigna secuencias |
| Objeto valor | `RunId`, `EventId`, `Event`, `AdapterCapabilities`, `EnvironmentFingerprint` | Inmutables y validados al construirse |
| Pipeline | `application/capture.py` | Etapas ordenadas: validar → redactar → limitar |
| Puertos `Protocol` + DI explícita | `application/ports/`, `bootstrap/` | Sin framework de DI |
| Repositorio | `RunRepository` | Solo donde hay frontera de persistencia real |
| Strategy/Policy | ⏳ Fase 2 (política de efectos) | — |

**No usados a propósito:** CQRS con bases separadas, event sourcing global, `BaseRepository[T]` genérico, plugins de
terceros, microservicios. Razones en [ADR-001](../../docs/14-adr-001-hexagonal-architecture.md).
