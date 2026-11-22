# Sesión 2026-11-22 (e) — Fase 5: adaptador Pydantic AI, puente OpenTelemetry y benchmark FCRB

↑ [Bitácora de sesiones](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-22 |
| **IA / herramienta** | Claude Code (Sonnet 5.5) |
| **Rama** | `main` |
| **Commits** | commit de la Fase 5 (ver `git log`) |
| **Análisis de impacto** | [`../impacto/2026-11-22-e-fase-5-adaptador-y-benchmark.md`](../impacto/2026-11-22-e-fase-5-adaptador-y-benchmark.md) |
| **Fichas de fallo** | ninguna (los defectos se detectaron antes de publicar; ver §2) |

## 1. Qué se pidió

«Continúa con la Fase 5; para el framework dame recomendaciones en base a la lógica de negocio y escoge el mejor de todos».

## 2. Qué se encontró (diagnóstico)

- `docs/09` pide elegir el framework «por demanda de usuarios y factibilidad»: **no hay datos de demanda**, así que
  se evaluó por factibilidad con datos medidos (ver [ADR-013](../forked/decisiones-arquitectura/ADR-013-framework-puente-otel-y-benchmark.md)):
  17 / 38 / 39 paquetes instalados, prueba offline con la red bloqueada, y un único punto de intercepción.
- Defectos propios detectados **antes** de publicar: (1) el importador de OTel hacía irreproducibles los runs
  importados (la procedencia iba en el payload de la llamada) y el export anidaba `inputs` dos veces; (2) el control
  por mutación mostró que S06 solo miraba la lista de huecos y que el runner abortaba con una excepción en vez de
  reportar `fail`. Todos corregidos; ninguno llegó a `main`.
- Una prueba de red bloqueada falló por mi propio guardián: el bucle de eventos de Windows usa un `connect` a localhost.
  Los guardianes de red bloquean ahora solo direcciones no locales.

## 3. Qué se hizo

| Área | Archivo | Cambio | Por qué |
|---|---|---|---|
| SDK | `src/forked/adapters/inbound/sdk/recorder.py` | `_begin`/`_Step`, `acall_tool`, `record(source=)` | Compartir lógica sync/async |
| adaptador | `src/forked/adapters/inbound/frameworks/{__init__,pydantic_ai_toolset}.py` | `ForkedToolset`, `pydantic_ai_capabilities` | Primer framework |
| dominio | `src/forked/domain/telemetry/{__init__,otlp}.py` | OTLP/JSON: exportar e importar | Puente OTel |
| aplicación | `src/forked/application/commands/otel.py` | `ExportTrace`, `ImportTrace` | Puente OTel |
| CLI / composición | `adapters/inbound/cli/app.py`, `bootstrap/container.py` | `otel-export`, `otel-import`, `probe=` | Puente OTel; escenario S07 |
| ejemplo | `examples/{__init__,pydantic_ai_expense_agent}.py`, `examples/README.md` | Caso de uso de punta a punta | Criterio de salida |
| benchmark | `benchmarks/{__init__,README}.py/md`, `benchmarks/fcrb/{__init__,__main__,common,baseline,scenarios,runner}.py` | FCRB | Criterio de salida |
| tests | `tests/acceptance/{test_pydantic_ai_adapter,test_otel_bridge}.py`, `tests/benchmarks/test_fcrb.py`, `tests/conftest.py` | 8 + 15 + 8 nuevos | Definición de terminado |
| dependencias | `pyproject.toml`, `uv.lock` | extra opcional, grupo dev, config de ruff/mypy | ADR-013 |
| CI | `.github/workflows/ci.yml` | export/import OTel, ejemplo y benchmark | Reproducibilidad en cada plataforma |
| docs | `README.md`, `CHANGELOG.md` | Estado, comandos, roadmap | Honestidad pública |
| contexto | ADR-013, `modulos/{integrations,benchmarks}/`, `protocolo/puente-opentelemetry.md`, CP-040…046, spec 006, estado, roadmap, memoria central, índices | Memoria | Método |

## 4. Qué se descartó y por qué

Ver «Alternativas descartadas» del ADR-013: LangGraph primero, OpenAI Agents SDK, adaptador por monkeypatching,
depender del SDK de OpenTelemetry, puntaje compuesto, optimizar el costo de captura sin carga medida.

## 5. Qué quedó pendiente / decisiones para el usuario

- **Reproducción independiente** del benchmark por alguien que no sea el autor: sin ella no puede llamarse «validado».
- Segundo adaptador (LangGraph) y su línea base de viaje en el tiempo nativo, cuando haya demanda o para la Fase 6.
- Fase 6 (alfa pública): sitio de docs, repositorio de ejemplos, notas de versión; revisar el **arte previo** antes de
  usar la palabra «novedoso» ([arte previo](../investigacion/arte-previo.md)).
- Decidir si se publica `forked-runtime` en PyPI (nada publicado).

## 6. Cómo verificar

```bash
uv sync --locked
uv run ruff check .                 # All checks passed!
uv run ruff format --check .        # sin cambios
uv run mypy                         # Success: no issues found in 92 source files
uv run pytest                       # 219 passed, 1 skipped (symlink en Windows)
uv run python -m examples.pydantic_ai_expense_agent   # 4 pasos, claim controlled_comparison
uv run python -m benchmarks.fcrb --out results/       # 10 pass; exit 0
```

Mutaciones del producto contra el benchmark (aplicadas y revertidas una a una; entre paréntesis, los escenarios que
fallaron): redacción apagada (S08, S09) · replay que ejecuta (S01–S04, S06) · afirmación siempre «controlada» (S07) ·
`is_valid` siempre verdadero (S06) · huecos no calculados (S06) · `verify` ignora la validez (S08) · hashes sin comparar
(S08) · rama que muta al padre (S05, S07, S08, S09) · entorno sin comparar (S07). Tras corregir S06 y el runner, todas
detectadas.

Reproducción desde un clon limpio: ver la nota al final de esta sesión.
