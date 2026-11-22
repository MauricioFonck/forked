# Impacto 2026-11-22 (e) — Fase 5: adaptador Pydantic AI, puente OTel y benchmark FCRB

↑ [Índice de impacto](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-22 |
| **Sesión** | [`../sesiones/2026-11-22-e-fase-5-adaptador-y-benchmark.md`](../sesiones/2026-11-22-e-fase-5-adaptador-y-benchmark.md) |
| **Rama / commits** | `main` · commit de la Fase 5 |
| **Estado** | Verificado |

## 1. Qué se va a tocar

| Zona | Archivo / contrato | Otros consumidores |
|---|---|---|
| SDK | `RecordedRun.call_tool` partido en `_begin`/`_Step`; `acall_tool` nuevo; `Recorder.record(source=)` | demo, CLI, adaptador, benchmark, **todos los tests de replay/rama** |
| Composición | `build_application(probe=)`; `export_trace`, `import_trace` | CLI, tests, benchmark |
| Dependencias | extra opcional `pydantic-ai`; `pydantic-ai-slim` en el grupo `dev`; `uv.lock` cambia (+14 paquetes de desarrollo) | CI, contribuyentes |
| Configuración | `known-first-party` y `mypy files` incluyen `examples`, `benchmarks`; `E501` relajado solo en `benchmarks/` | lint y tipos |
| CLI | comandos nuevos `otel-export`, `otel-import` | usuarios, CI |

## 2. Qué funciona hoy y qué le podría pasar

| Id | Comportamiento | Qué le podría pasar | Riesgo | Mitigación |
|---|---|---|---|---|
| CP-022…025, 027, 028 | Replay y rama no ejecutan ni repiten escrituras | El refactor de `call_tool` cambia el orden de captura o deja pasar `ALLOW` | **Alto** | Los 189 tests previos en verde tras el refactor (antes de añadir nada) |
| CP-003…005 | Sin secretos en disco | El importador OTel o el adaptador escriben por un camino sin redacción | **Alto** | Ambos pasan por `session.capture`; S09 y un test cubren argumentos, claves y errores |
| CP-015 | Regla de dependencias | El núcleo importa Pydantic AI | Medio | Los adaptadores viven en `adapters/inbound`; el guardián AST sigue en verde |
| CP-019 | CLI estable | Comandos nuevos rompen los anteriores | Bajo | Tests de CLI previos en verde |
| (nuevo) | Núcleo sin red | Pydantic AI abre red | Medio | Tests con `connect` bloqueado salvo loopback (el bucle de eventos de Windows lo usa) |

## 3. Lo que se descubrió al analizar

- La primera versión del importador guardaba la procedencia en el payload de la **llamada**: un run importado no se
  podía reproducir. Lo detectó un test propio **antes de publicar**; corregido (ver [ADR-013](../forked/decisiones-arquitectura/ADR-013-framework-puente-otel-y-benchmark.md)).
- El control por mutación mostró que S06 era débil (no miraba `is_valid`) y que el runner abortaba en vez de reportar.
- El costo de captura es medible: ≈ 2,4 ms por llamada (2 eventos que abren y vuelcan el archivo). Se informa, no se oculta.
- Pydantic AI imprime un aviso promocional de un producto de pago; se silencia con `PYDANTIC_AI_NO_BANNER=1` en tests, CI
  y benchmark (no se toca el entorno del usuario desde la librería).

## 4. Verificación posterior

| Id | Cómo se verificó | Resultado |
|---|---|---|
| Todos | `uv run pytest` | OK: 219 passed, 1 skipped (symlink en Windows) |
| CP-022…028 | Suite previa tras el refactor del SDK | OK: 189 passed antes de añadir código nuevo |
| CP-040…042 | `test_pydantic_ai_adapter.py` (8) con red bloqueada | OK |
| CP-043, 044 | `test_otel_bridge.py` (15) | OK |
| CP-045, 046 | `test_fcrb.py` (8) + 9 mutaciones del producto | OK: cada defecto hace fallar su escenario |
| Reproducción | clon limpio + `uv sync --locked` + benchmark + ejemplo | ver bitácora |
| Estáticos | ruff · format · mypy strict (92 archivos) | OK |

## 5. Comportamientos nuevos que pasan a protegidos

CP-040 a CP-046 en [`comportamientos-protegidos.md`](comportamientos-protegidos.md).
