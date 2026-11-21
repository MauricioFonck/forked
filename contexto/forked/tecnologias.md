# Tecnologías

↑ [Memoria central](../README.md)

> Versiones resueltas el 2026-11-21 en `uv.lock`. Decisión: [ADR-008](decisiones-arquitectura/ADR-008-toolchain.md).

## Ejecución

| Pieza | Versión | Dónde se usa | Por qué |
|---|---|---|---|
| Python | ≥ 3.11 (CI: 3.11–3.14) | Todo | `StrEnum`, `datetime.UTC`, `add_note` |
| Pydantic | 2.x | Solo `adapters/outbound/persistence/filesystem/records.py` | Validación del formato en disco y generación del JSON Schema |
| Typer | 0.x | Solo `adapters/inbound/cli/` | CLI tipada |

El dominio y la aplicación **no tienen dependencias de terceros**.

## Desarrollo

| Pieza | Uso |
|---|---|
| uv | Entornos, lock reproducible (`uv.lock`), instalación de Python |
| hatchling | Backend de build |
| pytest | Runner de tests (`pythonpath = ["."]`, warnings como error) |
| Hypothesis | Tests de propiedades: orden de eventos, idempotencia de la redacción |
| ruff | Lint (incluye reglas de seguridad `S`) y formato |
| mypy | `--strict` con plugin de Pydantic |
| GitHub Actions | CI en Linux (3.11–3.14), Windows y macOS (3.12) + smoke test del demo |
| Dependabot | Actualizaciones semanales de `uv` y Actions |

## Descartadas (por ahora)

| Pieza | Motivo |
|---|---|
| SQLite | Ninguna consulta lo justifica aún ([ADR-004](decisiones-arquitectura/ADR-004-persistencia-fase-1.md)) |
| import-linter | Un guardián AST de 90 líneas hace lo mismo sin dependencia ([ADR-005](decisiones-arquitectura/ADR-005-guardianes-pytest.md)) |
| Contenedor DI | Raíz de composición escrita a mano ([ADR-001](../../docs/14-adr-001-hexagonal-architecture.md)) |
| Docker | Solo para un futuro sandbox de demostración; los tests no lo requieren |
| OpenTelemetry SDK | Llega como adaptador en la Fase 5 |
