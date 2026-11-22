# Sesión 2026-11-22 (g) — Arte previo, adaptador de LangGraph y release de la alfa

↑ [Bitácora de sesiones](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-22 |
| **IA / herramienta** | Claude Code (Sonnet 5.5) |
| **Rama** | `main` |
| **Commits** | ver `git log` (arte previo, LangGraph, release) |
| **Análisis de impacto** | [`../impacto/2026-11-22-g-arte-previo-langgraph-y-release.md`](../impacto/2026-11-22-g-arte-previo-langgraph-y-release.md) |
| **Fichas de fallo** | ninguna (defectos detectados antes de commitear; ver §2) |

## 1. Qué se pidió

El dueño aceptó la lista de decisiones y pendientes de la Fase 6 («haz todo esto, de la manera más profesional
posible»): publicar la alfa, habilitar Discussions, hacer la matriz de arte previo, buscar una reproducción
independiente y construir el segundo adaptador (LangGraph).

**Lo que no puede hacer una IA, dicho desde el principio:** publicar en PyPI (requiere el token del dueño) y ser la
persona independiente que reproduzca el benchmark.

## 2. Qué se encontró (diagnóstico)

- Arte previo: ver [ADR-015](../forked/decisiones-arquitectura/ADR-015-posicionamiento-tras-el-arte-previo.md) y [`docs/15`](../../docs/15-prior-art-matrix.md).
  Lo básico ya existe; el README se reescribió para reconocerlo.
- LangGraph: ver [ADR-016](../forked/decisiones-arquitectura/ADR-016-adaptador-langgraph-y-linea-base.md). Su viaje en el tiempo repitió el email (1 → 2).
- Una mutación sobrevivió y generó un test; dos tests míos estaban mal (corregidos); la tabla inicial de la matriz tenía
  celdas no verificadas (marcadas «not read»); un comando de shell con heredocs anidados falló al analizarse y no aplicó
  nada (rehecho con herramientas de archivo).

## 3. Qué se hizo

| Área | Archivo | Cambio | Por qué |
|---|---|---|---|
| arte previo | `docs/15-prior-art-matrix.md`, `docs/12`, `docs/README.md`, `README.md`, `contexto/investigacion/arte-previo.md` | Matriz, estado de la puerta, README reescrito | `docs/12` §12.3 |
| guardián | `tests/guardians/test_public_docs.py` | La matriz entra; el README debe admitir lo existente | CP-055 |
| adaptador | `src/forked/adapters/inbound/frameworks/langgraph_toolnode.py` | `forked_tool_node`, `ForkedToolCalls` | ADR-016 |
| SDK | `adapters/inbound/sdk/recorder.py` | `RecordedToolError.message` | Adaptadores |
| ejemplos | `examples/{expense_tools,langgraph_expense_agent}.py` | Herramientas compartidas; ejemplo LangGraph | Equivalencia entre adaptadores |
| benchmark | `benchmarks/fcrb/{baseline_langgraph,scenarios,runner,common}.py` | Línea base LangGraph, S10 ×3, versiones | ADR-016 |
| tests | `tests/acceptance/test_langgraph_adapter.py` (12), `tests/benchmarks/test_fcrb.py`, `tests/guardians/test_public_docs.py` | Nuevos | CP-052…056 |
| dependencias | `pyproject.toml`, `uv.lock` | extra `langgraph` | ADR-016 |
| docs | `README.md`, `CHANGELOG.md`, `docs/guide/04,05,06`, `examples/README.md`, `benchmarks/README.md` | LangGraph y línea base | Honestidad pública |
| contexto | ADR-015/016, spec 008, CP-052…056, estado, roadmap, memoria central, índices | Memoria | Método |
| GitHub | repositorio | Discussions habilitado | Decisión del dueño |

## 4. Qué se descartó y por qué

Ver las alternativas de los ADR-015 y ADR-016: seguir diciendo «primer/único», ocultar lo existente, esperar a cerrar
toda la puerta, envolver herramientas una a una, parchear `ToolNode`, registrar el estado del grafo.

## 5. Qué quedó pendiente / decisiones para el usuario

- **PyPI**: no se publicó (requiere tu token y el nombre queda tomado para siempre).
- **Reproducción independiente** del benchmark por una persona ajena (ver el issue de convocatoria).
- **Cerrar la puerta de arte previo**: OpenInference, W3C Trace Context, OCI/in-toto, patentes, modelos de datos.
- Valorar registrar las llamadas al modelo y el estado del grafo.

## 6. Cómo verificar

```bash
uv sync --locked
uv run ruff check .                 # All checks passed!
uv run ruff format --check .        # sin cambios
uv run mypy                         # Success: no issues found in 100 source files
uv run pytest                       # 281 passed, 1 skipped (symlink en Windows)
uv run python -m examples.langgraph_expense_agent
uv run python -m benchmarks.fcrb --out results/   # 10 pass; S04 incluye la línea base de LangGraph
```

Mutaciones del adaptador de LangGraph (aplicadas y revertidas): clase de efecto por defecto `pure_local` (detectada) ·
`on_denied` ignorado (detectada) · mensaje original descartado (**sobrevivió** → test de fidelidad → detectada) ·
candado retirado (detectada). Mutaciones de la documentación: ver el impacto.
