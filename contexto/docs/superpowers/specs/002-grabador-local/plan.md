# Spec 002 · Plan

[Spec](spec.md) · [Tareas](tasks.md) · [Bitácora](../../../../sesiones/2026-11-21-arranque-fase-0-y-1.md)

1. **Dominio compartido**: errores tipados con `code`, `RunId`/`EventId` con patrón estricto, JSON canónico + sha256,
   versión de esquema y regla de compatibilidad.
2. **Dominio `runs`**: `Event` que valida sus invariantes; agregado `Run` con máquina de estados; redacción pura;
   chequeo de secuencia; evaluación de completitud y evidencia faltante. `EffectClass` en `effects`.
3. **Aplicación**: puertos `Protocol`; `CapturePipeline`; `RecordingService`/`RecordingSession` (abortar ⇒
   `incomplete`); `InspectRun`/`ListRuns`.
4. **Adaptadores**: formato v0.1 con Pydantic; `FileSystemRunStore` (JSONL + `run.json` atómico); reloj, ids y sonda de
   entorno reales; SDK `Recorder`; CLI Typer.
5. **Composición**: `build_application()`; demo `toy_agent` con limitaciones declaradas.
6. **Tests**: dobles en memoria; unidad, contrato (doble = real), seguridad, integración CLI, aceptación offline,
   propiedades con Hypothesis; esquema publicado y 5 fixtures dorados.
7. **Verificación**: ruff, mypy strict, pytest y mutaciones dirigidas sobre cada regla de seguridad.
