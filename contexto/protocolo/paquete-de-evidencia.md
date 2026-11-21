# Paquete de evidencia `forked-evidence/1`

↑ [Protocolo](README.md)

Decisión: [ADR-012](../forked/decisiones-arquitectura/ADR-012-paquete-de-evidencia.md). Código: `src/forked/domain/evidence/package.py`.

## Archivos

```
<paquete>/
  manifest.json
  comparison.json
  runs/<baseline_id>/events.jsonl
  runs/<baseline_id>/run.json
  runs/<branch_id>/events.jsonl
  runs/<branch_id>/run.json
```

## `manifest.json` (campos exactos, fijados por test)

| Campo | Tipo | Contenido |
|---|---|---|
| `package_format` | string | `"forked-evidence/1"` |
| `cip_version` | string | versión del esquema de evento (`0.1.0`) |
| `experiment` | objeto | `baseline`, `branch`, `intervention` (id, target, operation, checkpoint, value), `effects_policy` |
| `environment` | objeto | `baseline` y `branch`: hechos de entorno capturados (`null` si faltan) |
| `invariants` | lista | `{id, verification, status}` por invariante |
| `claim` | objeto | `level` (`observational` / `controlled_comparison`) y `statement` |
| `limitations` | lista | del adaptador + de FORKED (incluye «no firmado») |
| `missing_evidence` | lista | evidencia faltante de ambos runs |
| `artifacts` | lista | `{path, sha256: "sha256:<hex>", bytes}` de cada archivo salvo el manifiesto |

Claves ordenadas, indentación 2, UTF-8, salto de línea final. Sin hora de exportación (determinismo).

## Verificación (`forked verify DIR`)

| Pregunta | Qué se comprueba | Falla si |
|---|---|---|
| Integridad | Manifiesto legible, formato y versión soportados; cada artefacto con su SHA-256 y tamaño | cambiado, faltante, extra, ruta insegura/duplicada, manifiesto inválido |
| Validez (solo si la integridad pasa) | Se recalcula la comparación desde `runs/` y se **regenera el manifiesto**; `comparison.json` y el manifiesto deben coincidir exactamente | cualquier campo atestiguado distinto (nivel, statement, invariantes extra, entorno, política, limitaciones…) ⇒ `unsupported claim` |

Salida: `package_digest` (SHA-256 del manifiesto) para comparar con una copia obtenida por otra vía; códigos de salida
0 (todo bien), 1 (integridad o validez fallan), 2 (no es un directorio de paquete, symlink, error).
