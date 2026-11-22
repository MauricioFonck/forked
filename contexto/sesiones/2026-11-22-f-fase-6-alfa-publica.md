# Sesión 2026-11-22 (f) — Fase 6: alfa pública (documentación, ejemplos, empaquetado y feedback)

↑ [Bitácora de sesiones](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-22 |
| **IA / herramienta** | Claude Code (Sonnet 5.5) |
| **Rama** | `main` |
| **Commits** | commit de la Fase 6 (ver `git log`) |
| **Análisis de impacto** | [`../impacto/2026-11-22-f-fase-6-alfa-publica.md`](../impacto/2026-11-22-f-fase-6-alfa-publica.md) |
| **Fichas de fallo** | ninguna (hallazgos menores corregidos; ver §2) |

## 1. Qué se pidió

«Continúa con la fase 6».

## 2. Qué se encontró (diagnóstico)

- Ya existían CONTRIBUTING, SECURITY, plantillas y gobierno (Fase 0). Faltaban documentación de usuario, un ejemplo
  mínimo, notas de versión, un canal de feedback con objetivo y verificar que el **paquete** funciona instalado.
- Hallazgos al probar el paquete: ayuda de la CLI desactualizada («(soon) branch»), sdist de 2,1 MB con todo el repo,
  error poco amable sin el extra, y una etiqueta `proposal` inexistente referenciada por una plantilla.
- La tabla comparativa del README afirmaba negativos sobre categorías de otras herramientas sin arte previo: se
  declaró como ilustrativa y se protegió con un test.
- **El release no se hizo**: etiquetar, publicar en PyPI y crear el GitHub Release son acciones públicas y difíciles de
  retirar (ver [ADR-014](../forked/decisiones-arquitectura/ADR-014-documentacion-publica-y-puerta-de-release.md)).

## 3. Qué se hizo

| Área | Archivo | Cambio | Por qué |
|---|---|---|---|
| código | `adapters/inbound/cli/app.py`, `adapters/inbound/frameworks/pydantic_ai_toolset.py` | Ayuda al día; error accionable del extra | Hallazgos |
| empaquetado | `pyproject.toml` | `sdist.include` | Sdist de 116 KB |
| ejemplos | `examples/minimal_sdk.py`, `tests/acceptance/test_examples.py` | Ejemplo mínimo sin framework | Primer contacto |
| docs de usuario | `docs/README.md`, `docs/guide/01…06` | Guía completa | Fase 6 |
| notas de versión | `docs/release-notes/v0.1.0-alpha.1.md` | **Borrador** | Fase 6 |
| comunidad | `CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/reproduction_report.yml`, etiquetas | Dónde ayudar; reportes de reproducción | Feedback externo |
| README | `README.md` | Mapa de docs, aviso en la tabla comparativa | Honestidad |
| tests | `tests/guardians/test_public_docs.py` (44), `tests/acceptance/test_pydantic_ai_adapter.py` (+1) | Guardián de documentación | CP-047…051 |
| CI | `.github/workflows/ci.yml` | Paso de rueda aislada; ejemplo mínimo | CP-050, CP-051 |
| contexto | ADR-014, spec 007, CP-047…051, estado, roadmap, memoria central, índices | Memoria | Método |

## 4. Qué se descartó y por qué

Sitio con generador, referencia de CLI autogenerada, publicar ya, habilitar Discussions: ver «Alternativas
descartadas» del ADR-014.

## 5. Qué quedó pendiente / decisiones para el usuario

- **Decidir el release**: etiquetar `v0.1.0-alpha.1`, crear el GitHub Release con las notas, y si se publica
  `forked-runtime` en PyPI (el nombre queda tomado para siempre). Antes habría que subir la versión (`0.1.0a1`) en
  `pyproject.toml`, `__init__.py`, `CITATION.cff` y `CHANGELOG`, y poner URLs absolutas en el README para PyPI.
- Habilitar **GitHub Discussions** (ajuste del repositorio).
- **Arte previo** (puerta abierta) y **reproducción independiente** (otra persona).
- Elegir el siguiente trabajo: segundo adaptador (LangGraph) o más escenarios/baselines.

## 6. Cómo verificar

```bash
uv sync --locked
uv run ruff check .                 # All checks passed!
uv run ruff format --check .        # sin cambios
uv run mypy                         # Success: no issues found in 95 source files
uv run pytest                       # 265 passed, 1 skipped (symlink en Windows)
uv build --out-dir dist/            # rueda 73 KB, sdist 116 KB
uv run --isolated --no-project --with dist/*.whl python -m forked record toy-agent   # fuera del repo
```

Mutaciones sobre la **documentación** (aplicadas y revertidas; cada una hace fallar el guardián): comando inventado ·
enlace roto en la guía · comando sin documentar en la referencia · fragmento de Python inválido · enlace roto en el
README · palabras de novedad · aviso de arte previo quitado.
