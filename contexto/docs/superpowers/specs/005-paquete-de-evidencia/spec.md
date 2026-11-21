# Spec 005 · Paquete de evidencia y verificador offline (Fase 4)

[Plan](plan.md) · [Tareas](tasks.md) · [Bitácora](../../../../sesiones/2026-11-21-d-fase-4-evidencia.md) · [Impacto](../../../../impacto/2026-11-21-d-fase-4-evidencia.md) · [Contexto `evidence`](../../../../modulos/evidence/README.md)

**Fecha:** 2026-11-21 · **Estado:** hecha

## Qué y por qué

UC-05 de [`docs/04`](../../../../../docs/04-product-requirements.md): exportar un experimento como paquete cuyo
manifiesto lista artefactos, hashes, versión de esquema, entorno y políticas; un verificador comprueba hashes y
esquema y reporta alteraciones, faltantes y afirmaciones no soportadas. Es lo que vuelve **portable** la evidencia de
las Fases 1–3 y prueba la hipótesis [H5](../../../../investigacion/hipotesis.md) en el demo.

## Decisiones

[ADR-012](../../../../forked/decisiones-arquitectura/ADR-012-paquete-de-evidencia.md): directorio determinista,
integridad y validez separadas, validez por recálculo, sin firma, exportación con rutas en lista blanca y escaneo de
credenciales.

## Criterios de aceptación

| Criterio (`docs/09` Fase 4 · `docs/04` UC-05) | Cómo se cumple |
|---|---|
| Esquema de manifiesto | [Formato](../../../../protocolo/paquete-de-evidencia.md), campos fijados por test |
| SHA-256 por artefacto | `artifacts[].sha256` + `bytes` |
| Exportación determinista | CP-033 |
| Verificable offline, solo con el paquete | CP-034 (store borrado) |
| Detecta artefactos cambiados y faltantes | CP-035 (+ extras) |
| Separa integridad de validez | CP-036 |
| Reporta afirmaciones no soportadas | CP-036 |
| Excluye secretos | Redacción en captura + CP-039 |

## Fuera de alcance

Firma, formatos comprimidos, varios experimentos por paquete, importar paquetes a un store.
