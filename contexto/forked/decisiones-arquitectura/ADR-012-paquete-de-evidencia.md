# ADR-012 — Paquete de evidencia: directorio determinista, integridad y validez separadas, sin firma

↑ [Índice de ADR](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-21 |
| **Estado** | Vigente |
| **Refina** | `docs/09` Fase 4, `docs/04` UC-05, `docs/07` (manifiestos alterados, path traversal), [ADR-011](ADR-011-ramas-checkpoint-y-comparacion.md) |

## Contexto

La Fase 4 pide esquema de manifiesto, SHA-256 por artefacto, exportación determinista, verificador offline y tests de
alteración y faltantes; el verificador debe separar **integridad de hashes** de **validez científica**, y UC-05 exige
reportar «afirmaciones no soportadas» y excluir secretos.

## Decisión

1. **Formato `forked-evidence/1` = directorio**, no archivo comprimido: nada que extraer (sin path traversal al
   importar), diffeable y determinista sin fijar fechas de zip. Contenido en [formato](../../protocolo/paquete-de-evidencia.md).
2. **Determinismo:** el manifiesto no lleva hora de exportación; JSON con claves ordenadas; artefactos copiados byte a
   byte. Mismos runs ⇒ mismos bytes.
3. **Integridad:** cada artefacto listado con `sha256` y `bytes`; falla si algo cambió, falta, sobra (archivo no
   cubierto por el manifiesto) o el manifiesto es ilegible, de otro formato, de un `cip_version` no soportado, o con
   rutas inseguras/duplicadas. Si la integridad falla, la validez **no se evalúa**.
4. **Validez por recálculo:** `runs/` del paquete tiene el layout del store, así que el verificador abre el paquete
   como store de solo lectura, **recalcula** la comparación y **regenera el manifiesto completo** (la exportación es
   determinista): debe ser idéntico al empaquetado, y `comparison.json` idéntico al recalculado. Toda diferencia es
   `unsupported claim` (refinado tras [B-001](../../errores/bugs/B-001-el-verificador-solo-revisaba-el-titular-de-la-afirmacion.md)).
5. **Sin firma.** La gestión de claves está fuera del alcance local-first de v0. Se publica `package_digest` (SHA-256
   del manifiesto) para comparar fuera de banda, y la limitación va dentro del propio manifiesto.
6. **Seguridad de exportación:** rutas validadas con una lista blanca **antes** de resolver; symlinks rechazados al
   leer; nunca se escribe sobre un directorio con contenido; un valor con forma de credencial aborta la exportación
   (defensa en profundidad tras la redacción en captura).

## Alternativas descartadas

- **Zip/tar** — reintroduce path traversal, metadatos de fecha y no aporta nada en local.
- **Firmar con una clave local** — sin infraestructura de confianza solo cambia «quién puede reescribir» por «quién
  tiene el archivo de clave»; se hará con una propuesta concreta (Sigstore/minisign) cuando haya distribución pública.
- **Validez solo leyendo el manifiesto** — el manifiesto es justamente lo que hay que poner a prueba.
- **Un JSON Schema publicado para el manifiesto** — sin consumidores externos aún; el conjunto exacto de campos queda
  fijado por test y documentado. Se publicará con la primera versión estable del formato.

## Consecuencias

- Un atacante que reescriba archivos **y** hashes pasa la integridad, pero no la validez si eso cambia lo que la
  evidencia sostiene, y cambia el `package_digest` (CP-036).
- El paquete se lee entero en memoria (marcado `ponytail:`): suficiente para runs del tamaño actual.
- `inv_parent_unchanged` sigue siendo un digest semántico; el SHA-256 por archivo del paquete cubre los bytes.
