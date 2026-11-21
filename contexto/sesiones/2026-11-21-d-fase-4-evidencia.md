# Sesión 2026-11-21 (d) — Fase 4: paquete de evidencia y verificador offline

↑ [Bitácora de sesiones](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-21 |
| **IA / herramienta** | Claude Code (Opus 5.5) |
| **Rama** | `main` |
| **Commits** | commit de la Fase 4 (ver `git log`) |
| **Análisis de impacto** | [`../impacto/2026-11-21-d-fase-4-evidencia.md`](../impacto/2026-11-21-d-fase-4-evidencia.md) |
| **Fichas de fallo** | ninguna |

## 1. Qué se pidió

«Dale, continúa con la fase 4».

## 2. Qué se encontró (diagnóstico)

- `docs/09` Fase 4: esquema de manifiesto, SHA-256, exportación determinista, verificador offline, tests de
  alteración y faltantes; salida que separe integridad de validez. `docs/04` UC-05 añade «afirmaciones no soportadas»
  y «excluye secretos»; `docs/07`, manifiestos alterados y path traversal.
- El layout `runs/<id>/` del store sirve tal cual dentro del paquete: el verificador recalcula con el código existente.

## 3. Qué se hizo

| Área | Archivo | Cambio | Por qué |
|---|---|---|---|
| dominio | `src/forked/domain/evidence/{__init__,package}.py` | Formato, integridad, afirmaciones, rutas, credenciales | UC-05 |
| dominio | `src/forked/domain/comparison/compare.py` | `Comparison.as_dict()` | Reuso CLI + exportador |
| aplicación | `src/forked/application/commands/evidence.py`, `application/ports/__init__.py` | `ExportEvidence`, `verify_evidence`, `ArtifactReader` | UC-05 |
| adaptadores | `adapters/outbound/evidence/{__init__,directory}.py`, `adapters/outbound/persistence/filesystem/store.py` | Escribir/leer paquetes; `raw_files` | Fase 4 |
| composición / CLI | `bootstrap/container.py`, `adapters/inbound/cli/app.py` | `export_evidence`, `verify_package`; `forked export`, `forked verify` | Fase 4 |
| tests | `tests/acceptance/test_evidence.py`, `tests/integration/test_cli.py` | 23 + 1 | Definición de terminado |
| CI | `.github/workflows/ci.yml` | export + verify, y verify tras borrar el store | CP-034 en cada plataforma |
| docs | `README.md`, `CHANGELOG.md` | Estado, demo, roadmap | Honestidad pública |
| contexto | ADR-012, `protocolo/paquete-de-evidencia.md`, `modulos/evidence/`, CP-033…039, spec 005, estado, roadmap, memoria central, índices | Memoria | Método |

## 4. Qué se descartó y por qué

Ver «Alternativas descartadas» del [ADR-012](../forked/decisiones-arquitectura/ADR-012-paquete-de-evidencia.md): zip/tar,
firma con clave local, validez leyendo solo el manifiesto, JSON Schema publicado del manifiesto (por ahora).

## 5. Qué quedó pendiente / decisiones para el usuario

- Fase 5 (adaptador y benchmark): **elegir el primer framework** a integrar (LangGraph, OpenAI Agents SDK, CrewAI…)
  tras la revisión de [arte previo](../investigacion/arte-previo.md). Es decisión del dueño.
- Firma de manifiestos cuando haya distribución pública.

## 6. Cómo verificar

```bash
uv run ruff check .                 # All checks passed!
uv run ruff format --check .        # sin cambios
uv run mypy                         # Success: no issues found in 75 source files
uv run pytest                       # 178 passed, 1 skipped (symlink en Windows)
S=$(mktemp -d); export FORKED_STORE=$S
uv run forked record toy-agent; R=$(uv run forked runs | cut -d' ' -f1)
B=$(uv run forked branch $R --at 3 --value 0.5 | head -1 | awk '{print $NF}')
uv run forked export $R $B --out $S/pkg   # 6 archivos
uv run forked verify $S/pkg               # integrity ok · validity controlled_comparison · exit 0
```

Mutaciones (aplicadas y revertidas una a una): hash no comparado 2 · extras ignorados 1 · afirmaciones sin revisar 2
· sin escaneo de credenciales 1 · toda ruta segura 7 · `ok` ignora validez 2 · sobrescribir directorio 1 · formato
sin revisar 1. Todas detectadas.
