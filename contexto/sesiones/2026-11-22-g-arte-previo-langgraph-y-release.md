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
- **`SECURITY.md` seguía diciendo «replay, ramas y exportación de evidencia no están implementados»** desde la Fase 0:
  falso hacía cinco fases y justo en la política de seguridad. Reescrito (garantías con enlace a la guía, alcance de
  «bypass», telemetría de frameworks).
- **CI en Python 3.14**: `langsmith` (dependencia transitiva de LangChain) trae un plugin de pytest y un
  `DeprecationWarning` que, con `filterwarnings = error`, tumbaba pytest solo en 3.14. Reproducido en un venv 3.14
  local; arreglado con el plugin desactivado y un filtro acotado por mensaje y por módulo de origen.
- **Telemetría de terceros**: LangChain puede enviar trazas a LangSmith si el usuario activa sus variables; FORKED no
  envía nada, pero eso no cubre al framework envuelto. Ahora lo dicen la guía y `SECURITY.md`.
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
| GitHub | repositorio | Discussions habilitado; etiquetas; **pre-release `v0.1.0a1`**; issues de convocatoria | Decisión del dueño |
| release | `pyproject.toml`, `src/forked/__init__.py`, `CITATION.cff`, `CHANGELOG.md`, `uv.lock`, `docs/release-notes/v0.1.0a1.md`, `SECURITY.md`, `README.md` | Versión `0.1.0a1`; notas finalizadas; `SECURITY.md` corregido | Release |
| CI | `pyproject.toml` | Plugin `langsmith_plugin` desactivado + filtro de advertencia acotado | Python 3.14 |

### Reproducción en frío del benchmark (no independiente)

Tras publicar `v0.1.0a1` se lanzó **un agente de IA sin ningún contexto del proyecto** (instrucciones: solo `README.md`,
`docs/guide/*` y `benchmarks/README.md`; no leer `contexto/`; trabajar en un directorio temporal; no tocar nada
público). Resultado: **10/10 `pass`**, `results.json` idéntico en dos corridas (sin `overhead` ni `environment`), y una
mutación elegida por él (apagar `RedactionPolicy.looks_like_secret`) hizo fallar **exactamente S09**. No encontró
sobre-afirmaciones; señaló la línea base de logs simples como débil por construcción.

**No cuenta como reproducción independiente** (misma máquina, mismo modelo de IA, sin humano): es una prueba de que la
documentación se sostiene sola. Fricciones que destapó y se corrigieron: no había forma cómoda de copiar el id de run
(se añadió una variable de shell), faltaba decir qué Python elige `uv` (`--python`), el costo de captura medido
(5,4 ms) contradecía el «2–3 ms» publicado (ahora «2–5 ms, varía con la carga»), y la salida de consola tenía una raya
larga que se corrompía en Windows (`�`; ahora ASCII, con test para la ayuda de la CLI y el ejemplo). Quedó registrado en
`benchmarks/README.md` («Reproduction log») sin llamarlo independiente.

## 4. Qué se descartó y por qué

Ver las alternativas de los ADR-015 y ADR-016: seguir diciendo «primer/único», ocultar lo existente, esperar a cerrar
toda la puerta, envolver herramientas una a una, parchear `ToolNode`, registrar el estado del grafo.

## 5. Qué quedó pendiente / decisiones para el usuario

- **PyPI**: no se publicó (requiere tu token y el nombre queda tomado para siempre). Los artefactos están listos y
  validados: `twine check` pasa y la rueda se instala y corre en un entorno limpio, con y sin extras. Comandos exactos en
  el informe de cierre.
- **Reproducción independiente** del benchmark por una persona ajena: issue [#3](https://github.com/MauricioFonck/forked/issues/3)
  (fijado). La corrida en frío de un agente de IA **no** la sustituye.
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

Release (verificado antes de etiquetar): `uv build` → rueda 77 KB y sdist 130 KB; `uvx twine check dist/*` PASSED;
rueda instalada con `[langgraph]` ⇒ el adaptador de Pydantic AI da el error accionable (los extras están aislados);
CI en verde en 6 trabajos (Linux 3.11–3.14, Windows, macOS).

Mutaciones del adaptador de LangGraph (aplicadas y revertidas): clase de efecto por defecto `pure_local` (detectada) ·
`on_denied` ignorado (detectada) · mensaje original descartado (**sobrevivió** → test de fidelidad → detectada) ·
candado retirado (detectada). Mutaciones de la documentación: ver el impacto.
