# Spec 003 · Plan

[Spec](spec.md) · [Tareas](tasks.md) · [Bitácora](../../../../sesiones/2026-11-21-b-publicacion-y-fase-2.md)

1. **Dominio `replay`**: `ReplayCursor` que empareja la n-ésima llamada viva con la n-ésima `tool.call` grabada
   (nombre, clase, payload redactado + digest) y devuelve su resultado; errores `MissingObservation` y `ReplayDivergence`.
2. **Aplicación**: `RecordingService.start(..., replay_of=)` añade `replay_of` a `run.started`; `ReplayService` valida
   el adaptador, lee el log de origen y devuelve sesión + cursor.
3. **SDK**: `Recorder.replay()`; en replay `call_tool` registra la llamada, resuelve contra el cursor y **no llama a
   `fn`**; al cerrar, observaciones sin consumir ⇒ divergencia. Errores grabados ⇒ `RecordedToolError`.
4. **Demo y CLI**: `run_toy_agent(..., replay_of=)`; `forked replay RUN_ID`; paso de replay en el smoke de CI.
5. **Tests**: aceptación (herramientas parcheadas para explotar, outbox intacto, mismo resultado), cada fallo cerrado,
   CLI; mutaciones sobre «no ejecutar», «comparar» y «todo consumido».
