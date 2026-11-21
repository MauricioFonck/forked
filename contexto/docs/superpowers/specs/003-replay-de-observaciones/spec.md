# Spec 003 · Replay de observaciones grabadas (Fase 2) — BORRADOR

[Bitácora de origen](../../../../sesiones/2026-11-21-arranque-fase-0-y-1.md) · [Contexto `effects`](../../../../modulos/effects/README.md) · [Política de efectos](../../../../diagramas/politica-efectos.md)

**Fecha:** 2026-11-21 · **Estado:** borrador — falta revisión del dueño, `plan.md` y `tasks.md`.

## Qué y por qué

UC-02 de [`docs/04`](../../../../../docs/04-product-requirements.md): elegir un run grabado y re-ejecutar el flujo
alimentando a cada herramienta con su **resultado grabado**, sin repetir escrituras externas. Prueba la hipótesis
[H3](../../../../investigacion/hipotesis.md) y habilita los escenarios FCRB 1 y 4.

## Propuesta

- **Dominio `replay`**: `ReplaySession` con cursor sobre los pares `tool.call`/`tool.result` grabados. Al pedir una
  herramienta, compara nombre y entradas (redactadas) con la siguiente observación; si coincide devuelve la salida
  grabada; si no hay observación o no coincide ⇒ `MissingObservation` / `ReplayDivergence` (**fallo cerrado**).
- **Dominio `effects`**: `EffectPolicy` (Strategy) versionada → `EffectDecision(ALLOW | REPLAY | SIMULATE | DENY, motivo,
  versión, alcance)`. Política por defecto = matriz de [`docs/07`](../../../../../docs/07-security-and-privacy.md) §7.5.
- **SDK**: el mismo `RecordedRun.call_tool(...)` en modo replay **no ejecuta `fn`**: pide decisión a la política y
  devuelve la observación. En replay no existe ningún camino que llame a `fn` para `external_write`/`unknown`.
- **Run de replay**: es un run nuevo, con referencia al run de origen y su propio log (`run.started` registra
  `mode: replay` y `source_run_id`); cada decisión de política es un evento de auditoría.
- **Reporte**: observaciones consumidas / esperadas (fidelidad), divergencias, decisiones de política y límites.

## Condiciones heredadas de la revisión

- `SIMULATE` solo si una política **explícita** lo pide; queda marcado en el evento y en el reporte y nunca se cuenta
  como resultado real ([revisión](../../../../revisiones/2026-11-21-revision-de-preparacion.md)).
- Entradas redactadas: la comparación de entradas en replay usa la forma redactada; un secreto distinto no puede
  distinguirse y así se declara.
- Toda herramienta sin clase grabada se trata como `unknown` ⇒ `DENY`.

## Criterios de aceptación (de `docs/09` Fase 2)

- [ ] El demo reproduce la salida grabada de cada herramienta.
- [ ] Un test prueba que `send_email` (y cualquier `external_write`) **no se invocó** en replay (espía + outbox intacto).
- [ ] Observación faltante ⇒ fallo cerrado, nunca llamada en vivo.
- [ ] Ningún camino de escritura externa alcanzable en modo replay (test + guardián si aplica).
- [ ] Reporte de replay con fidelidad y límites documentados; sin afirmar reproducción exacta.

## Preguntas abiertas para el dueño

1. ¿El replay re-ejecuta el código del flujo (como hoy el demo) o solo valida el log sin código? Propuesta: re-ejecuta.
2. ¿Una divergencia de entradas aborta el replay o se registra y continúa en modo «solo reporte»? Propuesta: aborta.
