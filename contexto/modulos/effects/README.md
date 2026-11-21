# Contexto `effects` — Effects & Safety

↑ [Contextos](../README.md) · [Memoria central](../../README.md)

## Responsabilidad

Clasificar cada operación según lo que puede hacerle al mundo fuera del experimento y decidir —con una **política
explícita, versionada y denegar-por-defecto**— si en replay o en una rama se reproduce, se permite en sandbox, se
simula de forma **declarada** o se deniega.

## Estado

| Pieza | Estado | Dónde |
|---|---|---|
| Taxonomía `EffectClass` (6 clases del CIP) | ✅ | `domain/effects/effect_class.py` |
| Declarar la clase en cada evento de herramienta | ✅ | `RecordedRun.call_tool(nombre, efecto, …)` |
| Política (`ALLOW` · `REPLAY` · `SIMULATE` · `DENY`) con versión, motivo y evento de auditoría | ⏳ Fase 2 | [spec 003](../../docs/superpowers/specs/003-replay-de-observaciones/spec.md) |
| Aprobaciones explícitas del usuario | ⏳ | — |

## Reglas (vigentes desde ya para todo diseño)

- `unknown` y `external_write` ⇒ **denegar** en replay y en ramas.
- Lecturas grabadas ⇒ se resuelven desde la observación capturada; si falta, **fallo cerrado**, jamás llamada en vivo.
- `local_write` ⇒ solo en almacenamiento desechable de la rama.
- `SIMULATE` debe quedar marcado en la evidencia como simulación; nunca se reporta como resultado real.
- La política es un objeto de dominio (Strategy/Policy), no `if` dispersos en adaptadores.

Detalle de cada clase: [taxonomía de efectos](../../protocolo/taxonomia-de-efectos.md) ·
[diagrama de la política](../../diagramas/politica-efectos.md).
