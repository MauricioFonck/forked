# Taxonomía de efectos

↑ [Protocolo](README.md) · [Memoria central](../README.md)

Fuente: CIP §6.5 y la matriz de replay seguro de [`docs/07`](../../docs/07-security-and-privacy.md) §7.5. Vocabulario
único por [ADR-003](../forked/decisiones-arquitectura/ADR-003-vocabulario-cip.md).

| Clase (`effect_class`) | Significa | Política por defecto en replay / rama (Fase 2) |
|---|---|---|
| `pure_local` | Sin cambio de estado externo esperado | Permitir solo dentro de un sandbox declarado |
| `recorded_read` | Resultado capturado que se reproduce desde la evidencia | Reproducir el resultado grabado |
| `external_read` | Lee estado externo | Usar la respuesta grabada; si no hay, **denegar** (fallo cerrado) |
| `external_write` | Cambia estado externo | **Denegar** |
| `local_write` | Cambia estado local del sandbox | Solo en almacenamiento desechable de la rama |
| `unknown` | No se puede clasificar | **Denegar** |

Reglas transversales: una respuesta grabada faltante ⇒ fallo cerrado; replay y ramas nunca caen en silencio a una
llamada en vivo; toda decisión `allow` lleva versión de política, motivo, alcance y evento de auditoría.

## Quién declara la clase

Hoy, el adaptador al llamar `RecordedRun.call_tool(nombre, EffectClass.X, fn, …)`. Una clasificación errónea del
adaptador es el mayor riesgo de esta capa: la Fase 2 debe tratar como `unknown` toda herramienta que aparezca en replay
sin clase grabada.
