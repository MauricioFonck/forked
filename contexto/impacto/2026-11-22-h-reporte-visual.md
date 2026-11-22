# Impacto 2026-11-22 (h) — Reporte visual HTML

↑ [Índice de impacto](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-22 |
| **Sesión** | [`../sesiones/2026-11-22-h-reporte-visual.md`](../sesiones/2026-11-22-h-reporte-visual.md) |
| **Rama / commits** | `main` |
| **Estado** | Verificado |

## 1. Qué se va a tocar

| Zona | Archivo / contrato | Otros consumidores |
|---|---|---|
| CLI | comando nuevo `report` | usuarios; el guardián de documentación (exige documentarlo) |
| Empaquetado | `report.css` como dato dentro de `forked/adapters/inbound/cli/` | la rueda (verificado que viaja) |
| Config | `E501` relajado solo para `html_report.py` (plantillas HTML) | ruff |
| Git | `forked-report.html` en `.gitignore` | contribuyentes |
| CI | el paso de la rueda aislada genera un reporte y busca la CSP | los 6 trabajos |

## 2. Qué funciona hoy y qué le podría pasar

| Id | Comportamiento | Qué le podría pasar | Riesgo | Mitigación |
|---|---|---|---|---|
| CP-003…005 | Sin secretos en disco | El reporte filtra un secreto que se redactó mal | Medio | Solo muestra datos **ya redactados**; se documenta que es una copia de los datos |
| (nuevo) | El reporte es seguro de abrir | Un dato hostil ejecuta código en el navegador | **Alto** | Escape total + CSP estricta + sin JS; 3 mutaciones detectadas |
| CP-015 | Regla de dependencias | La CLI importa un adaptador de salida | Medio | El renderizador vive en `adapters/inbound/cli/` |
| CP-047 | CLI documentada | Comando nuevo sin documentar | Bajo | El guardián falló al añadirlo; se documentó |

## 3. Lo que se descubrió al analizar

- Mi primer test de la CSP fallaba por una suposición errónea: el atributo va con las comillas como entidades HTML
  (`&#x27;none&#x27;`), que el navegador decodifica; el test debe decodificar antes de comparar.
- **Verlo de verdad** destapó tres defectos que ningún test detecta: SVG demasiado grande, números de paso tapados por la
  línea punteada y una tabla que se desbordaba cortando el resultado de la rama. Por eso hay una revisión visual manual y se
  declara que no está automatizada.
- Un digest largo se cortaba por el borde (`overflow-wrap`).

## 4. Verificación posterior

| Id | Cómo se verificó | Resultado |
|---|---|---|
| Todos | `uv run pytest` | OK: 293 passed, 1 skipped (symlink en Windows) |
| CP-057 | 3 mutaciones: escape desactivado · CSP retirada · payload sin escapar | OK: las 3 detectadas |
| CP-058, 059 | 7 tests de integración | OK |
| Visual | capturas con Edge sin interfaz de los runs reales del dueño, antes y después de los arreglos | OK (3 defectos corregidos) |
| Empaquetado | `report.css` dentro de la rueda | OK |
| Estáticos | ruff · format · mypy strict (102 archivos) | OK |

## 5. Comportamientos nuevos que pasan a protegidos

CP-057 a CP-060 en [`comportamientos-protegidos.md`](comportamientos-protegidos.md).
