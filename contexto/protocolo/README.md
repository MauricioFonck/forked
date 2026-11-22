# `protocolo/` — Counterfactual Integrity Protocol (CIP)

↑ [Memoria central](../README.md)

> **Borrador exploratorio v0.1.** No es un estándar publicado. Nombre y esquema son provisionales hasta pasar la
> [puerta de arte previo](../investigacion/arte-previo.md). Propuesta original: [`docs/06`](../../docs/06-cip-protocol-draft.md).

| Documento | Cubre | Implementado |
|---|---|---|
| [Sobre de evento](sobre-de-evento.md) | Cada campo de un evento v0.1.0, reglas y ejemplos | ✅ esquema publicado |
| [Taxonomía de efectos](taxonomia-de-efectos.md) | Las 6 clases y su política por defecto | ✅ `default-deny/1` |
| [Versionado](versionado.md) | SemVer del esquema, compatibilidad y fixtures dorados | ✅ |
| [Puente OpenTelemetry](puente-opentelemetry.md) | Mapeo a OTLP/JSON: exportar spans de herramientas, importar traces como runs | ✅ |
| [Paquete de evidencia](paquete-de-evidencia.md) | Formato `forked-evidence/1`: archivos, manifiesto, verificación | ✅ |

Resuelto para el SDK: checkpoint e intervención ([ADR-011](../forked/decisiones-arquitectura/ADR-011-ramas-checkpoint-y-comparacion.md)),
paquete de evidencia ([ADR-012](../forked/decisiones-arquitectura/ADR-012-paquete-de-evidencia.md)). Abierto: checkpoints
portables entre frameworks e intervenciones adicionales (`docs/12` §12.2).
