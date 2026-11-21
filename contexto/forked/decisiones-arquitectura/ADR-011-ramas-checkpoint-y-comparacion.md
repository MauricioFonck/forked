# ADR-011 — Ramas: checkpoint, una intervención, política default-deny, invariantes y nivel de afirmación

↑ [Índice de ADR](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-21 |
| **Estado** | Vigente |
| **Refina** | `docs/12` §12.2.2 (checkpoint portable, abierta), `docs/06` §6.3 y §6.6–6.7, `docs/07` §7.5, [ADR-003](ADR-003-vocabulario-cip.md), [ADR-010](ADR-010-replay-estricto-sin-politica.md) |

## Contexto

La Fase 3 pide linaje inmutable, referencia a checkpoint, **un** tipo de intervención, stream propio por rama,
comparación e invariantes, con tres criterios: padre intacto, intervención en la evidencia y lo desconocido nunca
marcado como verificado. `docs/12` deja abierto qué es un checkpoint portable.

## Decisión

1. **Checkpoint = `sequence` de un evento `tool.call` del padre.** Es estable, visible en `inspect --events` y no
   depende de ningún framework. Cualquier otro valor ⇒ `InvalidCheckpoint` antes de crear la rama.
2. **Una intervención:** `replace_recorded_observation` sobre `tool.result` (la del ejemplo del CIP §6.3). La
   llamada del checkpoint debe coincidir con la del padre; su resultado se reemplaza por el valor declarado.
3. **Resolución por posición:** antes del checkpoint, replay estricto (falla cerrado). Después, replay mientras la
   llamada coincida con la siguiente grabada; a la primera diferencia se pierde la alineación (sin re-sincronizar) y
   todo lo demás va a la política.
4. **Política `default-deny/1`:** `ALLOW` solo para `pure_local` declarado; `DENY` para `recorded_read`,
   `external_read`, `external_write`, `local_write` y `unknown`. `DENY` no ejecuta: registra `tool.error`
   `EffectDenied` con motivo y lanza `EffectDenied` al flujo, que decide qué hacer (el demo lo anota en su resultado).
   **No existe `SIMULATE`**: no hay caso de uso y su riesgo es justamente el que prohíbe `CLAUDE.md`.
5. **Linaje en el `run.started` de la rama** (`branch_of`, `parent_log_digest`, `intervention`, `effect_policy`):
   append-only y redactado por el pipeline, sin tabla ni repositorio nuevo. El padre solo se lee.
6. **Cinco invariantes fijas**, declaración (id, descripción, método) separada del resultado
   (`verified/violated/unknown` + evidencia):
   `inv_parent_unchanged` (digest de contenido), `inv_prefix_replayed`, `inv_no_live_side_effects`,
   `inv_same_environment`, `inv_same_adapter`. Rama no finalizada o secuencia inválida ⇒ `unknown`.
7. **Nivel de afirmación:** `controlled_comparison` solo si todas están `verified` y la rama terminó `completed`;
   si no, `observational`. Nunca `conditional_causal`: un par de runs no sostiene una causa. Sin puntaje de confianza.

## Alternativas descartadas

- **Checkpoint por índice de llamada (1, 2, 3…)** — más corto, pero ambiguo frente a lo que muestra `inspect`.
- **Snapshot de estado del proceso** — es «OS snapshotting», prohibido por la primera milestone y no portable.
- **`SIMULATE` para escrituras** — sería un resultado inventado; si llega, será explícito y marcado (`docs/07`).
- **Invariantes declaradas por el usuario** — sin verificadores no pasan de descripción («una descripción no es
  verificación», CIP §6.6). Se añadirán con verificadores concretos.
- **Re-sincronizar por contenido tras divergir** — necesita un algoritmo de alineación y una razón para confiar en él.

## Consecuencias

- `inv_parent_unchanged` compara un digest **del log parseado**: un cambio solo de formato en el archivo no se
  detecta. La Fase 4 lo complementa con SHA-256 por archivo; CP-026 ya lo comprueba byte a byte en tests.
- `inv_no_live_side_effects` solo ve lo que pasa por `call_tool`: código del flujo fuera del SDK puede hacer
  cualquier cosa. Limitación declarada; un sandbox real es trabajo futuro.
- `inv_same_environment` compara los hechos capturados, no la máquina entera.
- Hacer replay de una rama cuyo email fue denegado relanza `RecordedToolError`, no `EffectDenied`: el demo no lo
  captura. Aceptado: no es un caso pedido.
