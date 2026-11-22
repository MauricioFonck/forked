# Impacto 2026-11-22 (g) — Arte previo, adaptador de LangGraph y release de la alfa

↑ [Índice de impacto](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-22 |
| **Sesión** | [`../sesiones/2026-11-22-g-arte-previo-langgraph-y-release.md`](../sesiones/2026-11-22-g-arte-previo-langgraph-y-release.md) |
| **Rama / commits** | `main` |
| **Estado** | Verificado (el release se describe en la bitácora) |

## 1. Qué se va a tocar

| Zona | Archivo / contrato | Otros consumidores |
|---|---|---|
| README | tabla comparativa reescrita desde la matriz | lectores externos; guardián |
| Dependencias | extra `langgraph` + grupo `dev` (+38 paquetes de desarrollo); `uv.lock` | CI (6 trabajos), contribuyentes |
| SDK | `RecordedToolError.message` (atributo nuevo) | adaptadores |
| Benchmark | S04 (línea base LangGraph), S10 (3 adaptadores), `common.normalized_tool_events(parse_json_outputs=)`, versiones en `results.json` | tests del benchmark, guía 06 |
| Ejemplos | herramientas compartidas en `examples/expense_tools.py`; el ejemplo de Pydantic AI las importa | tests, benchmark |

## 2. Qué funciona hoy y qué le podría pasar

| Id | Comportamiento | Qué le podría pasar | Riesgo | Mitigación |
|---|---|---|---|---|
| CP-040…042 | Adaptador de Pydantic AI | El refactor de herramientas compartidas cambia sus tests | Medio | 8 tests previos en verde tras el cambio |
| CP-045, 046 | Benchmark reproducible, línea base medida | Añadir LangGraph vuelve no determinista la parte «determinista» | Medio | Test de reproducibilidad en verde (las versiones van en `environment`, excluido) |
| CP-049 | Sin sobre-afirmaciones | La matriz cita palabras prohibidas | Bajo | La matriz entra en el guardián (`PAGES`); redactada sin superlativos |
| (nuevo) | README admite lo que ya existe | Alguien lo borra para «sonar mejor» | **Alto** (reputación) | Test que exige el enlace a `docs/15`, «already done» y «not found in what we read» |

## 3. Lo que se descubrió al analizar

- El arte previo es **más denso de lo esperado**: lo básico ya existe. Eso cambió el README y el posicionamiento
  ([ADR-015](../forked/decisiones-arquitectura/ADR-015-posicionamiento-tras-el-arte-previo.md)).
- Un proyecto declara como límite que las escrituras no se aíslan en replay: señal de que el hueco de efectos es real.
- El registro de atributos GenAI de OpenTelemetry dice que los atributos «se movieron» a otro repositorio: los nombres
  que usa el puente podrían cambiar (no se verificó la estabilidad de la especificación).
- **Mutación sobreviviente**: ningún test exigía que, grabando, el agente recibiera el `ToolMessage` original. Test nuevo.
- Mis dos tests iniciales de LangGraph eran erróneos (un `Command` inválido lo rechaza LangGraph antes del envoltorio; el
  test del extra ausente debía bloquear también los submódulos cacheados): corregidos antes de commitear.
- Mi tabla inicial de la matriz afirmaba cosas generales (Phoenix «basado en OTel», «local-first» de otras plataformas)
  que **no verifiqué**: se marcaron «not read».

## 4. Verificación posterior

| Id | Cómo se verificó | Resultado |
|---|---|---|
| Todos | `uv run pytest` | OK: 281 passed, 1 skipped (symlink en Windows) |
| CP-052…054 | 12 tests de LangGraph con la red bloqueada + 5 mutaciones del adaptador | OK: 4 detectadas de inicio, 1 tras añadir el test de fidelidad |
| CP-055 | 3 mutaciones de la documentación (quitar «already done», quitar límites de la matriz, afirmar unicidad) | OK |
| CP-056 | `python -m benchmarks.fcrb`: 10/10 `pass`; S04 con LangGraph = 1 escritura repetida frente a 0 de FORKED; S10 equivalente en 3 adaptadores | OK |
| Estáticos | ruff · format · mypy strict (100 archivos) | OK |

## 5. Comportamientos nuevos que pasan a protegidos

CP-052 a CP-056 en [`comportamientos-protegidos.md`](comportamientos-protegidos.md).
