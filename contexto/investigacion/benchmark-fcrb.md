# Benchmark FCRB (nombre provisional)

↑ [Investigación](README.md) · [Memoria central](../README.md)

FORKED Counterfactual Reliability Benchmark. Diseño en [`docs/08`](../../docs/08-benchmarks-and-validation.md). No se
llama «validado» hasta que una persona independiente lo reproduzca desde un entorno limpio.

| # | Escenario | Soporte al 2026-11-21 |
|---|---|---|
| 1 | Flujo de juguete determinista con herramientas grabadas | 🟡 grabación sí (`forked record toy-agent`); replay no |
| 2 | Dependencia de tiempo/aleatoriedad | ⏳ (tiempo y aleatoriedad aún no se virtualizan) |
| 3 | Lectura externa grabada | 🟡 se graba `get_exchange_rate` (`external_read`, stub declarado) |
| 4 | Intento de escritura externa durante replay | ⏳ Fase 2 — `send_email` ya está clasificado `external_write` |
| 5 | Intervención de rama que cambia una observación | ⏳ Fase 3 |
| 6 | Evento faltante en la grabación | 🟡 detectado: huecos, `next_sequence` ≠ líneas, puntos no observados (CP-007, CP-012) |
| 7 | Versiones de entorno distintas | 🟡 la huella se graba; la comparación es Fase 3 |
| 8 | Artefacto de evidencia manipulado | 🟡 `run.json` ajeno o líneas inválidas se rechazan; manifiesto con hash es Fase 4 |
| 9 | Redacción de campos sensibles | ✅ cubierto por tests (CP-003, CP-004, CP-005) |
| 10 | Dos adaptadores que producen artefactos equivalentes | ⏳ Fase 5 |

## Métricas (sin puntaje único opaco)

Fidelidad de replay · completitud de captura (ya calculada por `inspect`) · tasa de verificación de invariantes ·
prevención de efectos inseguros · completitud de evidencia · aislamiento de ramas · sobrecosto · portabilidad.
