# Sesión 2026-11-22 (h) — Reporte visual HTML

↑ [Bitácora de sesiones](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-22 |
| **IA / herramienta** | Claude Code (Sonnet 5.5) |
| **Rama** | `main` |
| **Commits** | ver `git log` |
| **Análisis de impacto** | [`../impacto/2026-11-22-h-reporte-visual.md`](../impacto/2026-11-22-h-reporte-visual.md) |
| **Fichas de fallo** | ninguna |

## 1. Qué se pidió

«¿Cómo puedo ver todo eso visualmente?» (tras probar la CLI con sus propios runs).

## 2. Qué se encontró (diagnóstico)

Solo había consola. Se decidió un único HTML autocontenido ([ADR-017](../forked/decisiones-arquitectura/ADR-017-reporte-html-autocontenido.md)). Al probar
con los runs reales del dueño se vio que su comando `forked runs | primero` tomaba un run **anterior** al recién grabado
(el almacén ya tenía runs); la guía se corrigió en la sesión anterior.

## 3. Qué se hizo

| Área | Archivo | Cambio | Por qué |
|---|---|---|---|
| CLI | `src/forked/adapters/inbound/cli/{html_report.py,report.css,app.py}` | Renderizador y comando `report` | Pedido del dueño |
| tests | `tests/integration/test_html_report.py` (7) | Seguridad, contenido, determinismo, errores | CP-057…059 |
| docs | `docs/guide/{01,03,05}`, `README.md`, `CHANGELOG.md`, `.github/workflows/ci.yml`, `pyproject.toml`, `.gitignore` | Documentar y probar en la rueda | Guardián |
| contexto | ADR-017, spec 009, CP-057…060, estado, índices | Memoria | Método |

## 4. Qué se descartó y por qué

Servidor local, gráficos en JavaScript, Graphviz, Markdown, PNG: ver el ADR-017.

## 5. Qué quedó pendiente / decisiones para el usuario

- Probar FORKED con un **flujo propio** del dueño (aceptó; falta que describa cuál).
- Revisión visual automatizada y un Studio interactivo: solo con necesidad medida.

## 6. Cómo verificar

```bash
uv run forked record toy-agent
uv run forked branch <run> --at 3 --value 0.5
uv run forked report <run> <branch> --open     # una página: línea de tiempo, fork, invariantes, evidencia
uv run pytest tests/integration/test_html_report.py
```

Mutaciones del reporte (aplicadas y revertidas): escape desactivado · CSP retirada · payload sin escapar en la línea de
tiempo: las 3 hacen fallar un test.
