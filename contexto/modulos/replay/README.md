# Contexto `replay`

↑ [Contextos](../README.md) · [Memoria central](../../README.md)

> Re-ejecuta el código de un flujo contestando cada llamada a herramienta con la observación grabada. **Nunca ejecuta
> una herramienta.** Decisión: [ADR-010](../../forked/decisiones-arquitectura/ADR-010-replay-estricto-sin-politica.md).

## Archivos

| Capa | Archivo | Qué hace |
|---|---|---|
| dominio | `src/forked/domain/replay/cursor.py` | `ReplayCursor`: pares `tool.call` → resultado, en orden; `MissingObservation`, `ReplayDivergence` |
| aplicación | `src/forked/application/commands/replay_run.py` | `ReplayService.start(source, caps)`: verifica adaptador, carga eventos, abre run nuevo con `replay_of` |
| SDK | `src/forked/adapters/inbound/sdk/recorder.py` | `Recorder.replay(...)`; en replay `call_tool` no llama a `fn`; `RecordedToolError` |
| CLI | `src/forked/adapters/inbound/cli/app.py` | `forked replay RUN_ID` |
| demo | `src/forked/demo/toy_agent.py` | `run_toy_agent(..., replay_of=...)`: mismo código de flujo |

## Reglas (fallo cerrado)

| Situación | Resultado |
|---|---|
| Nombre o clase de efecto distintos a la n-ésima llamada grabada | `ReplayDivergence` |
| Entradas (redactadas) distintas | `ReplayDivergence` «inputs differ» |
| Más llamadas que las grabadas | `MissingObservation` |
| Llamada grabada sin resultado, o resultado `omitted` | `MissingObservation` |
| El flujo termina sin pedir todas las llamadas grabadas | `ReplayDivergence` «N of M» |
| Run de otro adaptador | `ReplayDivergence` antes de empezar |
| La herramienta falló al grabar | se relanza `RecordedToolError(error_type, message)` |

En todos los fallos el run de replay queda `failed` con el motivo (redactado).

## Límites declarados

- Reproduce **observaciones**, no el entorno. Azar o reloj fuera de herramientas ⇒ divergencia.
- Entradas comparadas tras redacción: un secreto distinto no se distingue.
- `RecordedToolError` no recrea el tipo original de la excepción (solo su nombre).
- Sin política de efectos: llega en la Fase 3.

## Comportamientos protegidos

CP-022 a CP-025 en [comportamientos protegidos](../../impacto/comportamientos-protegidos.md#replay).
