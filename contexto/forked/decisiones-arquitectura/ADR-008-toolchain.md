# ADR-008 — Toolchain: uv + hatchling, Python ≥ 3.11, Pydantic solo en el borde (2026-11-21)

↑ [Índice de ADR](README.md)

- **Contexto.** [`docs/05`](../../../docs/05-architecture.md) §5.13 propone Python 3.11+ «a confirmar», Pydantic en los
  bordes, Typer, pytest, Hypothesis, Ruff y un verificador de tipos.
- **Decisión.**
  - **Python ≥ 3.11** confirmado; CI en 3.11, 3.12, 3.13 y 3.14 (Linux) y 3.12 en Windows y macOS.
  - **uv** para entornos y lock (`uv.lock` versionado; CI usa `uv sync --locked`). **hatchling** como backend de build.
  - **Pydantic 2** solo en `adapters/outbound/persistence/filesystem/records.py`; el dominio usa dataclasses de la
    biblioteca estándar. **Typer** solo en la CLI.
  - **mypy `--strict`** sobre `src` y `tests` (los tests pueden omitir anotaciones de funciones, pero se chequean).
  - **ruff** con reglas `E F W I B UP SIM RUF PT S N ANN TID`; se ignoran `ANN401` y `N818` (los errores del dominio
    se nombran por su significado, `RunNotFound`, no `RunNotFoundError`).
- **Alternativas.** Poetry/PDM (uv es más rápido y también instala Python) · pyright (mypy tiene plugin de Pydantic) ·
  attrs/Pydantic en el dominio (rompe la regla de dependencias).
- **Consecuencias.** Una sola herramienta para instalar y correr; dependencias de ejecución mínimas (2).
