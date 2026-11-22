# Spec 006 · Plan

[Spec](spec.md) · [Tareas](tasks.md) · [Bitácora](../../../../sesiones/2026-11-22-e-fase-5-adaptador-y-benchmark.md)

1. **Decidir el framework con datos**: instalar cada candidato en un entorno aislado, contar paquetes y probar un
   agente guionado con la red bloqueada y un punto único de intercepción.
2. **SDK**: partir `call_tool` en `_begin`/`_Step` y añadir `acall_tool`; `Recorder.record(source=)`;
   `build_application(probe=)`.
3. **Adaptador** `ForkedToolset` + extra opcional + ejemplo de punta a punta.
4. **Puente OTel** en el dominio (OTLP/JSON puro), casos de uso y comandos de CLI.
5. **Benchmark**: línea base ejecutada, 10 escenarios, overhead, runner y tests.
6. **Controles**: romper FORKED a propósito y exigir que el escenario correcto falle.
7. **Docs, CI y reproducción desde un clon limpio.**
