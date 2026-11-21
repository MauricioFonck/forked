# Sesión 2026-11-21 (b) — Publicación en GitHub y Fase 2 (replay)

↑ [Bitácora de sesiones](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-21 |
| **IA / herramienta** | Claude Code (Opus 5.5) |
| **Rama** | `main` |
| **Commits** | merge de Dependabot #1 (`9a492f1`), commit de la Fase 2 (ver `git log`) |
| **Análisis de impacto** | [`../impacto/2026-11-21-b-publicacion-y-fase-2.md`](../impacto/2026-11-21-b-publicacion-y-fase-2.md) |
| **Fichas de fallo** | ninguna |

## 1. Qué se pidió

El dueño creó `MauricioFonck/forked`, pasó los comandos de `git remote`/`push` y pidió «continuar con todo lo que haga
falta de la mejor manera», de forma profesional.

## 2. Qué se encontró (diagnóstico)

- Primer push: CI en verde en los 6 trabajos. Aviso: `astral-sh/setup-uv@v6` usa Node 20 (obsoleto).
- Dependabot abrió #1 (`setup-uv` 6→7) y #2 (`actions/checkout` 4→7). #1 se fusionó y quitó el aviso; #2 quedó en
  conflicto con #1 y se le pidió `@dependabot rebase`.
- Al diseñar el replay: una política de efectos no tiene caso de uso en la Fase 2 → [ADR-010](../forked/decisiones-arquitectura/ADR-010-replay-estricto-sin-politica.md).

## 3. Qué se hizo

| Área | Archivo | Cambio | Por qué |
|---|---|---|---|
| GitHub | repo | Descripción, 8 topics, reporte privado de vulnerabilidades activado (API) | `SECURITY.md` lo usa |
| GitHub | PR #1 | Fusionado (squash) | Quita el aviso de Node 20 |
| dominio | `src/forked/domain/replay/{__init__,cursor}.py` | `ReplayCursor` y errores | Fase 2 |
| aplicación | `src/forked/application/commands/replay_run.py`, `record_run.py` | `ReplayService`; `replay_of` en `start` | Fase 2 |
| SDK | `src/forked/adapters/inbound/sdk/recorder.py` | `Recorder.replay`, `RecordedToolError`, context manager compartido | Fase 2 |
| CLI / demo | `adapters/inbound/cli/app.py`, `demo/toy_agent.py`, `bootstrap/container.py` | `forked replay`; demo reproducible | Fase 2 |
| tests | `tests/acceptance/test_replay.py`, `tests/integration/test_cli.py` | 8 + 2 tests | Definición de terminado |
| CI | `.github/workflows/ci.yml` | Smoke: `replay` y outbox con 1 solo mensaje | CP-022 en cada plataforma |
| docs | `README.md`, `CHANGELOG.md` | Estado, demo de replay, roadmap (política → Fase 3) | Honestidad pública |
| contexto | ADR-010, `modulos/replay/`, CP-022…025, spec 003 (plan/tasks), estado, roadmap, memoria central, esta bitácora, impacto | Memoria | Método |

## 4. Qué se descartó y por qué

- `EffectPolicy` en la Fase 2 — una sola respuesta posible (ADR-010).
- Emparejar llamadas sin orden y modo «solo reporte» — ver ADR-010.
- Recrear el tipo original de la excepción grabada — requiere importar código arbitrario por nombre; se relanza
  `RecordedToolError` con el nombre.

## 5. Qué quedó pendiente / decisiones para el usuario

- PR #2 de Dependabot: fusionar cuando termine su rebase y el CI esté verde.
- Fase 3: escribir la spec 004 (ramas + una intervención + política de efectos + invariantes). Decisión del dueño: qué
  es un checkpoint (propuesta: índice de secuencia del log).
- Las dos preguntas de la spec 003 se resolvieron con las propuestas por defecto; el dueño puede revertirlas.

## 6. Cómo verificar

```bash
uv run ruff check .                 # All checks passed!
uv run ruff format --check .        # sin cambios
uv run mypy                         # Success: no issues found in 63 source files
uv run pytest                       # 138 passed
FORKED_STORE=$(mktemp -d) sh -c 'uv run forked record toy-agent; uv run forked replay $(uv run forked runs | cut -d" " -f1)'
                                    # replayed … (0 tools executed); outbox: 1 mensaje; grep sk-toy: 0
gh run list --workflow ci.yml       # push de main: success (6 trabajos)
```

Mutaciones: replay ejecuta `fn` → 7 rojos; sin comparar nombre/clase → 1 rojo; sin exigir consumo total → 1 rojo.
