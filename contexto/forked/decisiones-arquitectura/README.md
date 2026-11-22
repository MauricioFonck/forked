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
| [017](ADR-017-reporte-html-autocontenido.md) | Reporte visual: un HTML autocontenido, sin JavaScript, con CSP estricta y salida determinista | Vigente | `adapters/inbound/cli/html_report.py`, `tests/integration/test_html_report.py` |
| [016](ADR-016-adaptador-langgraph-y-linea-base.md) | Adaptador de LangGraph por `wrap_tool_call`; su viaje en el tiempo como línea base medida | Vigente | `adapters/inbound/frameworks/langgraph_toolnode.py`, `benchmarks/fcrb/baseline_langgraph.py` |
| [015](ADR-015-posicionamiento-tras-el-arte-previo.md) | Posicionamiento tras el arte previo: capa de seguridad y evidencia, no «el grabador»; diferencia solo como combinación acotada | Vigente | `docs/15-prior-art-matrix.md`, `tests/guardians/test_public_docs.py` |
| [014](ADR-014-documentacion-publica-y-puerta-de-release.md) | Documentación pública verificada por tests; sin release sin decisión del dueño | Vigente | `tests/guardians/test_public_docs.py`, `docs/guide/` |
| [013](ADR-013-framework-puente-otel-y-benchmark.md) | Pydantic AI primero (por factibilidad, sin datos de demanda); puente OTLP/JSON sin SDK de OTel; benchmark que debe poder fallar | Vigente | `adapters/inbound/frameworks/`, `domain/telemetry/`, `benchmarks/` |
| [012](ADR-012-paquete-de-evidencia.md) | Paquete = directorio determinista; integridad y validez separadas; validez por recálculo; sin firma | Vigente | `domain/evidence/package.py`, `tests/acceptance/test_evidence.py` |
| [011](ADR-011-ramas-checkpoint-y-comparacion.md) | Checkpoint = secuencia de un `tool.call`; una intervención; política default-deny; invariantes y nivel de afirmación | Vigente | `domain/branches/`, `domain/comparison/`, `tests/acceptance/test_branch.py` |
| [010](ADR-010-replay-estricto-sin-politica.md) | Replay estricto que nunca ejecuta herramientas; política de efectos a la Fase 3 | Vigente | `domain/replay/cursor.py`, `tests/acceptance/test_replay.py` |
