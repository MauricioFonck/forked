# Decisiones de arquitectura (ADRs)

↑ [Memoria central](../../README.md)

Registro de **por qué** el sistema es como es. Cada decisión incluye contexto, decisión, alternativas y consecuencias.
Añade una entrada cuando tomes una decisión arquitectónica relevante, con la [plantilla](../../PLANTILLAS/plantilla-adr.md).

- **ADR-001** es público y fundacional: vive en [`docs/14-adr-001-hexagonal-architecture.md`](../../../docs/14-adr-001-hexagonal-architecture.md)
  (inglés). Los siguientes viven aquí.
- Las decisiones provisionales `D-001…D-014` de [`docs/12`](../../../docs/12-decisions-and-open-questions.md) siguen
  vigentes salvo donde un ADR de aquí las **refina** (lo dice en su sección «Refina»).
- Numeración continua; un número nunca se reutiliza. Un ADR reemplazado se marca «Reemplazado por ADR-NNN».

### Estado de cada ADR (revisado contra el código el 2026-11-21)

| ADR | Título | Estado | Evidencia |
|-----|--------|--------|-----------|
| [001](../../../docs/14-adr-001-hexagonal-architecture.md) | Hexagonal dentro de un monolito modular | Vigente | `tests/guardians/test_dependency_rule.py` |
| [002](ADR-002-nombre-distribucion.md) | Distribución `forked-runtime`, import `forked` | Vigente | `pyproject.toml` |
| [003](ADR-003-vocabulario-cip.md) | Vocabulario único: taxonomía CIP, niveles de afirmación, estados en minúscula | Vigente (parcial: efectos y estados de captura implementados) | `domain/effects/effect_class.py` |
| [004](ADR-004-persistencia-fase-1.md) | JSONL + `run.json` atómico; SQLite diferido | Vigente | `adapters/outbound/persistence/filesystem/store.py` |
| [005](ADR-005-guardianes-pytest.md) | Guardianes como tests de pytest | Vigente | `tests/guardians/` |
| [006](ADR-006-idioma.md) | Público en inglés, memoria en español | Vigente | este directorio |
| [007](ADR-007-omitir-no-truncar.md) | Payload grande: omitir con digest, nunca truncar; sobre-redacción aceptada | Vigente | `application/capture.py` |
| [008](ADR-008-toolchain.md) | uv + hatchling, Python ≥ 3.11, Pydantic solo en el borde | Vigente | `pyproject.toml`, `uv.lock` |
| [009](ADR-009-secuencia-ids-tiempo.md) | Secuencia contigua desde 0, ids aleatorios, tiempo UTC con zona | Vigente | `domain/runs/run.py`, `domain/runs/sequence.py` |
| [010](ADR-010-replay-estricto-sin-politica.md) | Replay estricto que nunca ejecuta herramientas; política de efectos a la Fase 3 | Vigente | `domain/replay/cursor.py`, `tests/acceptance/test_replay.py` |
