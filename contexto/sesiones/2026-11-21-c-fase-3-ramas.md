# Sesión 2026-11-21 (c) — Fase 3: ramas, intervención, política y comparación

↑ [Bitácora de sesiones](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-21 |
| **IA / herramienta** | Claude Code (Opus 5.5) |
| **Rama** | `main` |
| **Commits** | commit de la Fase 3 (ver `git log`) |
| **Análisis de impacto** | [`../impacto/2026-11-21-c-fase-3-ramas.md`](../impacto/2026-11-21-c-fase-3-ramas.md) |
| **Fichas de fallo** | ninguna |

## 1. Qué se pidió

«Perfecto, sigue con la siguiente fase». El dueño aceptó la propuesta de checkpoint (posición en lo grabado).

## 2. Qué se encontró (diagnóstico)

- `docs/09` Fase 3 y `docs/04` UC-03/04 piden linaje, checkpoint, una intervención, stream por rama, comparación e
  invariantes; el CIP §6.3 ya sugiere la intervención `replace_recorded_observation`.
- El cursor del replay servía casi entero para la rama: solo faltaba separar «coincide» de «tiene resultado».
- Una mutación sobrevivió (checkpoint sin comparar) → test nuevo.

## 3. Qué se hizo

| Área | Archivo | Cambio | Por qué |
|---|---|---|---|
| dominio | `src/forked/domain/replay/cursor.py` | `match`, `try_resolve` | Reuso en ramas |
| dominio | `src/forked/domain/effects/policy.py` | Política `default-deny/1` | `docs/07` §7.5 |
| dominio | `src/forked/domain/branches/{__init__,branch}.py` | Intervención, resolutor, digest del log | UC-03 |
| dominio | `src/forked/domain/comparison/{__init__,compare}.py` | Comparación, invariantes, nivel de afirmación | UC-04 |
| aplicación | `application/commands/{record_run,replay_run}.py`, `application/queries/inspect_run.py` | `lineage`, `branch()`, `CompareRuns` | Fase 3 |
| SDK / demo / CLI | `adapters/inbound/sdk/recorder.py`, `demo/toy_agent.py`, `adapters/inbound/cli/app.py`, `bootstrap/container.py` | `Recorder.branch`, `forked branch`, `forked compare` | Fase 3 |
| tests | `tests/acceptance/test_branch.py`, `tests/acceptance/test_replay.py`, `tests/integration/test_cli.py` | 15 + 2 nuevos; firma del demo | Definición de terminado |
| CI | `.github/workflows/ci.yml` | Smoke con `branch` y outbox intacto | CP-026/027 en cada plataforma |
| docs | `README.md`, `CHANGELOG.md` | Demo de rama/comparación, estado, roadmap | Honestidad pública |
| contexto | ADR-011, `modulos/branches/`, `modulos/effects/`, `modulos/replay/`, CP-026…032, spec 004, estado, roadmap, memoria central, índices | Memoria | Método |

## 4. Qué se descartó y por qué

Ver «Alternativas descartadas» del [ADR-011](../forked/decisiones-arquitectura/ADR-011-ramas-checkpoint-y-comparacion.md):
checkpoint por índice de llamada, snapshot de proceso, `SIMULATE`, invariantes del usuario sin verificador,
re-sincronización por contenido.

## 5. Qué quedó pendiente / decisiones para el usuario

- Fase 4: paquete de evidencia + verificador offline (siguiente).
- Invariantes declaradas por el usuario, más intervenciones y políticas aprobadas por el usuario: después de la
  Fase 4, si hay caso de uso.

## 6. Cómo verificar

```bash
uv run ruff check .                 # All checks passed!
uv run ruff format --check .        # sin cambios
uv run mypy                         # Success: no issues found in 69 source files
uv run pytest                       # 155 passed
S=$(mktemp -d); export FORKED_STORE=$S
uv run forked record toy-agent
uv run forked branch "$(uv run forked runs | cut -d' ' -f1)" --at 3 --value 0.5
                                    # #2 intervene, #3 deny; 5 invariantes verified; controlled_comparison
ls "$S/toy-outbox"                  # message-0001.json (nada enviado por la rama)
```

Mutaciones (script en el directorio temporal de la sesión, aplicadas y revertidas una a una):

| Mutación | Tests rojos |
|---|---|
| La política permite todo | 7 |
| Digest del padre siempre «verificado» | 1 |
| Rama siempre «finalizada» | 1 |
| Nivel siempre `controlled_comparison` | 2 |
| Sin replay antes del checkpoint | 6 |
| Llamada del checkpoint sin comparar | 0 → se añadió un test → 1 |
