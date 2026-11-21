# Spec 001 · Plan

[Spec](spec.md) · [Tareas](tasks.md) · [Bitácora](../../../../sesiones/2026-11-21-arranque-fase-0-y-1.md)

1. **Leer** toda la propuesta y la memoria de referencia (NextVent) y escribir la revisión de preparación.
2. **Decidir** lo que la propuesta deja abierto (nombre, vocabulario, persistencia, toolchain, idioma) como ADR.
3. **Andamiar** `pyproject.toml` (uv + hatchling), `src/forked/` por capas, `tests/` por tipo.
4. **Guardianes**: regla de dependencias (AST), esquema publicado, grafo de `contexto/`.
5. **CI**: lint, formato, mypy, pytest, smoke test del demo; Linux 3.11–3.14, Windows y macOS 3.12.
6. **Políticas**: LICENSE (Apache-2.0), SECURITY, CONTRIBUTING, CODE_OF_CONDUCT, GOVERNANCE, CITATION, CHANGELOG,
   plantillas de issue/PR, Dependabot, `.gitattributes` con LF.
7. **Memoria `contexto/`** completa: memoria central, áreas, plantillas, índices y bitácora.
