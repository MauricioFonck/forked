# Spec 009 · Reporte visual local

[Plan](plan.md) · [Tareas](tasks.md) · [Bitácora](../../../../sesiones/2026-11-22-h-reporte-visual.md) · [Impacto](../../../../impacto/2026-11-22-h-reporte-visual.md)

**Fecha:** 2026-11-22 · **Estado:** hecha

## Qué y por qué

El dueño pidió poder **ver visualmente** lo que hoy sale por consola: grabación, replay, rama, invariantes y evidencia.
Decisión: [ADR-017](../../../../forked/decisiones-arquitectura/ADR-017-reporte-html-autocontenido.md).

## Criterios de aceptación

| Criterio | Cómo se cumple |
|---|---|
| Un archivo que se abre con doble clic, sin servidor ni red | `forked report … --open`; CSP estricta (CP-058) |
| Muestra línea de tiempo, efectos, estado de captura y payloads | `test_report_for_one_run` (CP-059) |
| Muestra el fork, las invariantes, el nivel de afirmación y la evidencia verificada | `test_report_for_a_branch_…` (CP-059) |
| Datos hostiles no ejecutan código | `test_hostile_recorded_data_is_escaped` + 3 mutaciones (CP-057) |
| Reproducible byte a byte | `test_report_is_deterministic` (CP-058) |
| Errores claros | run desconocido / no es rama ⇒ salida 2 (CP-059) |
| Documentado y verificable en la rueda | referencia de la CLI (guardián), paso de CI con la rueda aislada |

## Fuera de alcance

Servidor local o Studio interactivo, varios pares por informe, edición, revisión visual automatizada.
