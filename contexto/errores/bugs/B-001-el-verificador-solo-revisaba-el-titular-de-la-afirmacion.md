# B-001 — El verificador solo revisaba el titular de la afirmación

↑ [Catálogo de fallos](../README.md)

| | |
|---|---|
| **Tipo** | Bug de producto (seguridad: evasión de verificación) |
| **Contexto** | `evidence` — `src/forked/domain/evidence/package.py`, `src/forked/application/commands/evidence.py` |
| **Detectado por** | revisión de seguridad automática sobre el commit `ba69084` (2026-11-21) |
| **Arreglado en** | commit siguiente a `ba69084` |
| **Estado** | Cerrado |

## 1. Síntoma

`forked verify` daba `ok` a un paquete en el que alguien había reescrito el `statement` («Proven: the rate causes it»),
la intervención, la evidencia faltante, el entorno, la política, las limitaciones, añadido una invariante inventada
`verified` o reescrito `comparison.json`, siempre que corrigiera los hashes. Fallo **silencioso**: el verificador
existía justamente para atrapar eso.

## 2. A qué se debía

`check_claims` comparaba contra la evidencia recalculada solo `claim.level` y el estado de las invariantes que el
recálculo conoce. Todo lo demás que el manifiesto **atestigua** se aceptaba tal cual.

## 3. Conceptos técnicos en juego

### Lo que no se tuvo en cuenta

**Verificar una lista blanca de campos deja pasar todos los que olvidaste.** Si un documento atestigua N cosas,
revisar k < N es aceptar N − k afirmaciones sin pruebas.

### Lo que se aplicó al arreglarlo

**Regenerar y comparar el todo.** Como la exportación es determinista, el verificador vuelve a construir el manifiesto
desde los runs empaquetados y exige igualdad exacta; `comparison.json` se compara byte a byte con el recalculado. Los
chequeos campo a campo se mantienen solo para dar mensajes claros.

## 4. Cómo se solucionó

- `check_claims(manifest, recomputed, comparison_json)`: compara `comparison.json`, `claim.statement`,
  `experiment.{baseline,branch,intervention}`, `missing_evidence`; marca invariantes extra y repetidas.
- `verify_evidence(files, compare, regenerate)`: regenera el manifiesto con `ExportEvidence` sobre el paquete y reporta
  cada campo de primer nivel que difiere.

## 5. Cómo evitar que se repita

- **Regla accionable:** un verificador compara **todo** lo atestiguado contra un recálculo; si existe una función
  determinista que produce el artefacto, se reusa para regenerarlo.
- **Red de seguridad:** CP-036 ampliado; `test_every_attested_manifest_field_is_recomputed` (6),
  `test_fields_outside_the_comparison_are_regenerated` (4), `test_rewritten_comparison_json_with_fixed_hash_is_unsupported`;
  mutaciones (4, 1, 1 rojos).
- **Dónde más aplica:** futuros adaptadores que importen evidencia de otras herramientas, y la firma de manifiestos.
