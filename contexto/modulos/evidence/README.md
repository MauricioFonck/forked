# Contexto `evidence`

↑ [Contextos](../README.md) · [Memoria central](../../README.md)

> Exportar un experimento (base + rama) como paquete verificable y verificarlo offline sin nada más que el paquete.
> Formato: [`forked-evidence/1`](../../protocolo/paquete-de-evidencia.md). Decisión:
> [ADR-012](../../forked/decisiones-arquitectura/ADR-012-paquete-de-evidencia.md).

## Archivos

| Capa | Archivo | Qué hace |
|---|---|---|
| dominio | `src/forked/domain/evidence/package.py` | `build_package`, `check_integrity`, `check_claims`, `is_safe_path`, `sha256` |
| dominio | `src/forked/domain/comparison/compare.py` | `Comparison.as_dict()` (también lo usa la CLI) |
| aplicación | `src/forked/application/commands/evidence.py` | `ExportEvidence`, `verify_evidence`, `VerificationReport`, `Validity` |
| puerto | `src/forked/application/ports/__init__.py` | `ArtifactReader.raw_files(run_id)` |
| adaptador | `src/forked/adapters/outbound/persistence/filesystem/store.py` | `raw_files` (bytes de `events.jsonl` y `run.json`) |
| adaptador | `src/forked/adapters/outbound/evidence/directory.py` | `write_package` (no sobrescribe), `read_package` (rechaza symlinks) |
| composición | `src/forked/bootstrap/container.py` | `Application.export_evidence`, `verify_package` (abre el paquete como store) |
| CLI | `src/forked/adapters/inbound/cli/app.py` | `forked export`, `forked verify [--json]` |

## Límites declarados

- Manifiesto **sin firma**: la integridad es consistencia interna; comparar `package_digest` fuera de banda.
- Paquete leído entero en memoria.
- Un experimento por paquete (base + una rama).
- La validez comprueba que las afirmaciones se siguen de la evidencia **según las reglas de FORKED**; no juzga si el
  experimento estaba bien diseñado.

## Comportamientos protegidos

CP-033 a CP-039 en [comportamientos protegidos](../../impacto/comportamientos-protegidos.md).
