# Sesión 2026-11-21 — Arranque del proyecto: memoria, revisión de preparación, Fase 0 y Fase 1

↑ [Bitácora de sesiones](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-21 |
| **IA / herramienta** | Claude Code (Opus 5.5) |
| **Rama** | `main` |
| **Commits** | Commit inicial del repositorio (ver `git log`) |
| **Análisis de impacto** | [`../impacto/2026-11-21-arranque-fase-0-y-1.md`](../impacto/2026-11-21-arranque-fase-0-y-1.md) |
| **Fichas de fallo** | [E-001](../errores/errores/E-001-el-guardian-del-grafo-no-veia-mayusculas-en-windows.md) |

## 1. Qué se pidió

Trabajar el proyecto FORKED «tal cual como dice la documentación», mejorándolo donde se pueda para llamar la atención;
crear la carpeta del proyecto en `C:\Users\andre\Music\`; montar una carpeta de contexto **igual de profesional y
detallada** que `NextVent/contexto`; avanzar trabajo; y entregar nombre y descripción (≤ 300 caracteres) para que el
dueño cree el repositorio en GitHub.

Interpretación: el dueño crea el repositorio remoto; esta sesión deja el repositorio local listo para el primer push.

## 2. Qué se encontró (diagnóstico)

- La propuesta (`docs/` + `CLAUDE.md`) es sólida y honesta, pero tiene contradicciones de vocabulario y decisiones
  abiertas que bloquean código: ver la [revisión de preparación](../revisiones/2026-11-21-revision-de-preparacion.md).
- `forked` está tomado en PyPI (respuesta 200 de `pypi.org/pypi/forked/json`) → [ADR-002](../forked/decisiones-arquitectura/ADR-002-nombre-distribucion.md).
- La memoria de NextVent tiene: memoria central con «voy a tocar → leo primero», jerarquía de verdad, `sesiones/` +
  `impacto/` obligatorios por sesión, `comportamientos-protegidos` (`CP-nnn`), catálogo `errores/` (bugs vs. entorno,
  centrado en el concepto), ADR con índice de estado, specs numeradas `spec/plan/tasks`, plantillas, revisiones,
  diagramas, vault de Obsidian y un **guardián** que valida el grafo de enlaces. Todo se replicó y se adaptó (el
  guardián pasó de JS/vitest a Python/pytest).

## 3. Qué se hizo

| Área | Archivo | Cambio | Por qué |
|---|---|---|---|
| raíz | `pyproject.toml`, `uv.lock` | Paquete `forked-runtime`, deps mínimas, ruff/mypy/pytest | [ADR-008](../forked/decisiones-arquitectura/ADR-008-toolchain.md) |
| dominio | `src/forked/domain/shared/{errors,identifiers,canonical,schema}.py` | Errores con `code`, ids validados, JSON canónico, versión de esquema | Fase 1 |
| dominio | `src/forked/domain/runs/{run,event,capabilities,environment,redaction,sequence,completeness}.py` | Agregado, sobre, redacción, orden, completitud | Fase 1 |
| dominio | `src/forked/domain/effects/effect_class.py` | Taxonomía CIP | [ADR-003](../forked/decisiones-arquitectura/ADR-003-vocabulario-cip.md) |
| aplicación | `src/forked/application/{ports/__init__,capture,errors}.py`, `commands/record_run.py`, `queries/inspect_run.py` | Puertos, pipeline, casos de uso | Fase 1 |
| adaptadores | `src/forked/adapters/outbound/persistence/filesystem/{records,store}.py`, `outbound/system/runtime.py` | Formato v0.1, store JSONL + atómico, reloj/ids/entorno | [ADR-004](../forked/decisiones-arquitectura/ADR-004-persistencia-fase-1.md) |
| adaptadores | `src/forked/adapters/inbound/sdk/recorder.py`, `inbound/cli/app.py`, `src/forked/__main__.py` | SDK y CLI | Fase 1 |
| composición | `src/forked/bootstrap/container.py`, `src/forked/demo/toy_agent.py` | Raíz de composición y agente de juguete | Fase 1 |
| tests | `tests/{fakes,unit,contract,security,integration,acceptance,guardians,fixtures}` | 123 tests + 5 del grafo | Definición de terminado |
| protocolo | `spec/cip/v0.1/{event,run}.schema.json`, `scripts/export_schemas.py` | Esquema publicado | [Versionado](../protocolo/versionado.md) |
| OSS | `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `GOVERNANCE.md`, `CITATION.cff`, `CHANGELOG.md`, `.github/**`, `.gitignore`, `.gitattributes` | Políticas, CI, plantillas | `docs/10` §10.3 |
| docs públicas | `README.md` | Reescrito: demo de 60 s, tabla de diferencias, roadmap con estado honesto | Atraer atención sin exagerar |
| agentes | `CLAUDE.md` (numeración, memoria, comandos, guardianes), `AGENTS.md` | Reglas para cualquier agente | Memoria obligatoria |
| docs | `docs/**`, `assets/forked-hero.png` | Copiados sin cambios desde `forked_documentation` | Fuente de la propuesta |
| contexto | `contexto/**` (memoria central, `forked/`, ADR-002…009, `modulos/`, `protocolo/`, `investigacion/`, `diagramas/`, `impacto/`, `sesiones/`, `errores/`, `revisiones/`, `PLANTILLAS/`, `docs/superpowers/` specs 001–003, `.obsidian/`) | Memoria de ingeniería | Pedido del dueño |

## 4. Qué se descartó y por qué

- **SQLite en la Fase 1** — ninguna consulta lo justifica ([ADR-004](../forked/decisiones-arquitectura/ADR-004-persistencia-fase-1.md)).
- **import-linter** — un guardián AST basta ([ADR-005](../forked/decisiones-arquitectura/ADR-005-guardianes-pytest.md)).
- **Truncar payloads grandes** — miente sobre la completitud ([ADR-007](../forked/decisiones-arquitectura/ADR-007-omitir-no-truncar.md)).
- **Copiar el `.docx`/`.pdf` de la propuesta** al repositorio — 5,6 MB duplicando `docs/`; quedaron en la carpeta de origen.
- **Crear el repositorio en GitHub desde la sesión** — el dueño pidió hacerlo él.
- **Adelantar el replay (Fase 2)** — se dejó la spec 003 en borrador con dos preguntas para el dueño; implementarlo sin
  esas respuestas arriesga rehacerlo.

## 5. Qué quedó pendiente / decisiones para el usuario

- Crear el repositorio remoto y hacer el primer push; confirmar que el CI corre en verde en GitHub (no verificado aún).
- Activar el reporte privado de vulnerabilidades en GitHub (lo usan `SECURITY.md` y `CODE_OF_CONDUCT.md`).
- Si el repositorio no se llama `MauricioFonck/forked`, actualizar las URLs de `README.md`, `pyproject.toml`,
  `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CITATION.cff` y `.github/ISSUE_TEMPLATE/config.yml`.
- Responder las dos preguntas abiertas de la [spec 003](../docs/superpowers/specs/003-replay-de-observaciones/spec.md).
- Decidir si se reserva `forked-runtime` en PyPI (no se publicó nada).
- `CITATION.cff` usa «FORKED maintainers» como autor: poner nombres reales si se desea.

## 6. Cómo verificar

Comandos corridos de verdad en esta sesión (Windows 11, Python 3.14.7, uv 0.11.31):

```bash
uv sync                                   # 26 paquetes resueltos
uv run ruff check .                       # All checks passed!
uv run ruff format --check .              # sin cambios pendientes
uv run mypy                               # Success: no issues found in 59 source files
uv run pytest                             # 128 passed (123 + 5 del guardián del grafo)
FORKED_STORE=$(mktemp -d) uv run forked record toy-agent
                                          # 8 eventos, 100 % de puntos declarados, 1 redactado,
                                          # "missing evidence: none detected"; grep de la API key en disco: 0
```

Mutaciones dirigidas (romper la regla, correr la suite, restaurar con copia y volver a verde):

| Mutación | Tests rojos |
|---|---|
| Redacción por nombre de clave desactivada | 14 |
| Redacción por forma de valor desactivada | 8 |
| `_abort` no marca `incomplete` ante fallo de disco | 1 |
| Run sin finalizar reportado `completed` | 2 |
| Línea truncada aceptada | 1 |
| Motivo de fallo sin redactar | 1 |
| `import pydantic` en el dominio | guardián rojo |
| `import typer` en la aplicación | guardián rojo |
| Adaptador de salida importado desde la CLI | guardián rojo |

| Documento huérfano en `contexto/` | guardián del grafo rojo |
| Enlace a archivo inexistente | guardián del grafo rojo |
| Enlace con mayúsculas equivocadas (`Modulos/`) | **no** mordía en Windows → [E-001](../errores/errores/E-001-el-guardian-del-grafo-no-veia-mayusculas-en-windows.md); tras el arreglo, rojo |

Las dos primeras mutaciones de imports fallaron al principio por un `\n` mal escapado en el script de mutación (error
del script, no del código); se repitieron bien y mordieron.
