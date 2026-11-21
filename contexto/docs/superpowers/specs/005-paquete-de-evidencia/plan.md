# Spec 005 · Plan

[Spec](spec.md) · [Tareas](tasks.md) · [Bitácora](../../../../sesiones/2026-11-21-d-fase-4-evidencia.md)

1. **Dominio** `evidence/package.py`: rutas seguras, `build_package` determinista con escaneo de credenciales,
   `check_integrity`, `check_claims`. Mover la serialización de la comparación a `Comparison.as_dict()`.
2. **Puerto** `ArtifactReader` + `FileSystemRunStore.raw_files`.
3. **Aplicación** `ExportEvidence` y `verify_evidence` (validez solo si la integridad pasa).
4. **Adaptador** de directorio (`write_package`, `read_package`); composición con `verify_package` que abre el
   paquete como store.
5. **CLI** `export` / `verify` con códigos 0/1/2; smoke de CI que verifica tras borrar el store.
6. **Tests y mutaciones** de alteración, faltantes, extras, manifiesto, rutas, symlinks, secretos, determinismo.
