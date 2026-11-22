# Impacto 2026-11-22 (f) — Fase 6: alfa pública (documentación, ejemplos, empaquetado y feedback)

↑ [Índice de impacto](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-22 |
| **Sesión** | [`../sesiones/2026-11-22-f-fase-6-alfa-publica.md`](../sesiones/2026-11-22-f-fase-6-alfa-publica.md) |
| **Rama / commits** | `main` · commit de la Fase 6 |
| **Estado** | Verificado (release pendiente de decisión del dueño) |

## 1. Qué se va a tocar

| Zona | Archivo / contrato | Otros consumidores |
|---|---|---|
| Código | `cli/app.py` (texto de ayuda), `frameworks/pydantic_ai_toolset.py` (mensaje del extra) | usuarios; tests del adaptador |
| Empaquetado | `pyproject.toml` (`sdist.include`) | `uv build`, futuros releases |
| Documentación pública | `README.md` (tabla comparativa, mapa de docs), `CONTRIBUTING.md`, `docs/README.md`, `docs/guide/*`, `docs/release-notes/*` | lectores externos; el guardián |
| Ejemplos | `examples/minimal_sdk.py` | CI, tests |
| GitHub | plantilla `reproduction_report`, etiquetas `reproduction` y `proposal` | quien reporte |
| CI | pasos de rueda y ejemplo mínimo | los 6 trabajos |

## 2. Qué funciona hoy y qué le podría pasar

| Id | Comportamiento | Qué le podría pasar | Riesgo | Mitigación |
|---|---|---|---|---|
| CP-019 | Contrato de la CLI | Cambiar solo el texto de ayuda altera la salida | Bajo | Solo cambia el texto de `--help`; tests de CLI en verde |
| CP-040…042 | Adaptador de Pydantic AI | El `try/except` del import cambia su comportamiento | Medio | `reload` en un test; los 8 tests previos en verde |
| (nuevo) | El sdist ya no incluye `contexto/` ni imágenes | Falta algo necesario para construir desde el sdist | Medio | Se construyó e instaló la rueda desde el sdist en un entorno aislado |
| (nuevo) | README promete honestidad | Alguien reintroduce «único/novedoso» | **Alto** (reputación) | Guardián de sobre-afirmaciones + aviso verificado |

## 3. Lo que se descubrió al analizar

- La ayuda principal de la CLI seguía diciendo «(soon) branch» desde la Fase 1: nadie lo notó en cinco fases.
- El sdist arrastraba todo el repo (2,1 MB, incluido el motor de memoria interno).
- La plantilla de proposals de la Fase 0 referenciaba una etiqueta `proposal` que **no existía**: nada se etiquetaba.
- La tabla comparativa del README hacía afirmaciones absolutas («❌») sobre categorías de otras herramientas sin que el
  arte previo estuviera revisado: ahora lo declara y un test impide quitarlo.
- Un bloqueo de Windows (`os error 4551`, control de aplicaciones) impidió ejecutar el lanzador `forked.exe` recién
  creado en un entorno temporal; es del entorno, no del producto. El CI usa `python -m forked`.

## 4. Verificación posterior

| Id | Cómo se verificó | Resultado |
|---|---|---|
| Todos | `uv run pytest` | OK: 265 passed, 1 skipped (symlink en Windows) |
| CP-047, 048 | 5 mutaciones de la documentación (comando inventado, enlace roto, comando sin documentar, fragmento inválido, enlace roto en README) | OK: cada una hace fallar el test |
| CP-049 | 2 mutaciones (palabras de novedad; aviso del README quitado) | OK |
| CP-050 | rueda instalada en un entorno aislado y sin el repo: `--version`, `record`, `inspect --strict`; extra ausente ⇒ error accionable | OK |
| CP-051 | `test_examples.py` + ejecución del ejemplo | OK |
| Guía | «primer minuto» ejecutado desde un clon limpio | ver bitácora |
| Estáticos | ruff · format · mypy strict (95 archivos) | OK |

## 5. Comportamientos nuevos que pasan a protegidos

CP-047 a CP-051 en [`comportamientos-protegidos.md`](comportamientos-protegidos.md).
