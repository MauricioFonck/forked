# Contexto `benchmarks` — FCRB

↑ [Contextos](../README.md) · [Memoria central](../../README.md)

> Benchmark **provisional y no validado**: 10 escenarios de `docs/08` §8.2, una línea base ejecutada y un runner
> reproducible. Decisión: [ADR-013](../../forked/decisiones-arquitectura/ADR-013-framework-puente-otel-y-benchmark.md).
> Guía pública (inglés): [`benchmarks/README.md`](../../../benchmarks/README.md).

## Archivos

| Archivo | Qué hace |
|---|---|
| `benchmarks/fcrb/scenarios.py` | S01…S10; cada uno devuelve `ScenarioResult` (métricas medidas, línea base, notas) |
| `benchmarks/fcrb/baseline.py` | línea base «logs simples» **ejecutada** + la lista de líneas base no ejecutadas con su motivo |
| `benchmarks/fcrb/baseline_langgraph.py` | línea base del viaje en el tiempo de LangGraph **ejecutada** (solo S04) |
| `benchmarks/fcrb/runner.py` | `run_all`, `measure_overhead`, `deterministic_view`, `render_report`, `main` |
| `benchmarks/fcrb/common.py` | `normalized_tool_events` (equivalencia entre adaptadores) |
| `tests/benchmarks/test_fcrb.py` | corre los escenarios, exige reproducibilidad y que **pueda fallar** |

`python -m benchmarks.fcrb --out DIR [--no-overhead] [--warmup N] [--runs N]` ⇒ `results.json` + `REPORT.md`.

## Reglas

- Métricas separadas, **sin puntaje único** (`docs/08` §8.3). Un escenario que revienta es `fail`, no aborta.
- Solo `overhead` y `environment` varían entre corridas; lo demás es determinista (test).
- Cada línea base no ejecutada se lista con el motivo; nada se «compara» sin haberse ejecutado. Hoy se ejecutan dos:
  logs simples (S04, S06, S08, S09) y viaje en el tiempo de LangGraph (S04), y esta última se presenta como *otra
  herramienta con otro propósito*, no como un defecto.
- El benchmark **debe poder fallar**: 9 mutaciones del producto, cada una detectada por su escenario
  ([bitácora](../../sesiones/2026-11-22-e-fase-5-adaptador-y-benchmark.md#6-cómo-verificar)).

## Resultados de la primera corrida (Windows 11, Python 3.13)

10/10 `pass`. Costo de captura ≈ 2,4 ms por llamada de herramienta (mediana; p95 ≈ 4,9 ms; 2 eventos, cada uno
abre y vuelca el archivo), ≈ 380 bytes por evento. Línea base de logs simples: re-ejecutar «replay» envió el email
dos veces (prevención 0), una línea eliminada y un valor alterado **no se detectan**, y el secreto aparece en claro.
CPU y memoria no se miden.

## Límites declarados

Flujos de juguete con modelo guionado; dos líneas base ejecutadas (LangGraph solo en S04); verificación en un directorio limpio, no en otra
máquina; **sin reproducción independiente** ⇒ no se puede llamar «validado» (`docs/08` §8.6).

## Comportamientos protegidos

CP-045, CP-046 y CP-056 en [comportamientos protegidos](../../impacto/comportamientos-protegidos.md).
