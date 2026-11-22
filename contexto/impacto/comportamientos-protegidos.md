# Comportamientos protegidos

↑ [Índice de impacto](README.md) · [Memoria central](../README.md)

> Lo que **ya funciona** y ninguna edición puede romper, con la forma de comprobarlo. Registro **vivo**: crece con
> cada sesión. No es una lista de features; es la lista de garantías que un usuario ya da por hechas.

- **Id** estable (`CP-nnn`): no se reutiliza. El siguiente libre, al 2026-11-21, es **CP-022**.
- **Red de seguridad**: el test que lo cubre, o «manual» si solo se comprueba a mano (un hueco declarado vale más que
  uno oculto). «Mutación» indica que se demostró que el test muerde.
- **Origen**: la sesión, el ADR o la ficha de fallo que lo consolidó.

---

## Captura y orden (`runs`)

| Id | Comportamiento | Red de seguridad | Origen |
|---|---|---|---|
| CP-001 | La secuencia es contigua desde 0 por run y la asigna **solo** el agregado `Run`; los estados terminales rechazan eventos y transiciones | `test_run_lifecycle.py` · `test_record_run.py::test_recording_produces_ordered_typed_events` · propiedades en `test_sequence_and_completeness.py` | [ADR-009](../forked/decisiones-arquitectura/ADR-009-secuencia-ids-tiempo.md) |
| CP-002 | Un borrador inválido no consume número de secuencia | `test_run_lifecycle.py::test_invalid_draft_does_not_consume_a_sequence_number` | sesión 2026-11-21 |
| CP-006 | Un payload > límite se **omite** con digest sha256 del contenido redactado; nunca se trunca | `test_record_run.py::test_oversized_payload_is_omitted_with_digest_not_truncated` | [ADR-007](../forked/decisiones-arquitectura/ADR-007-omitir-no-truncar.md) |
| CP-007 | Un run nunca finalizado se reporta `incomplete` con cada punto de captura no observado y la diferencia entre `next_sequence` y el log | `test_sequence_and_completeness.py::test_unfinished_run_is_reported_incomplete` · `test_toy_agent_end_to_end.py::test_interrupted_run_is_reported_incomplete` · mutación | [ADR-004](../forked/decisiones-arquitectura/ADR-004-persistencia-fase-1.md) |
| CP-008 | Un fallo al persistir un evento lanza `CaptureFailed` y marca el run `incomplete`; nunca se descarta en silencio | `test_record_run.py::test_storage_failure_marks_run_incomplete_and_raises` · mutación | sesión 2026-11-21 |
| CP-009 | Superar el límite de eventos falla cerrado y deja el run `incomplete` | `test_record_run.py::test_event_limit_fails_closed` | `docs/07` §7.3.8 |
| CP-010 | Sin puntos de captura declarados la completitud es **desconocida** (`None`), nunca 100 % | `test_sequence_and_completeness.py::test_no_declared_points_means_unknown_not_complete` | sesión 2026-11-21 |
| CP-011 | Un hecho de entorno no capturado queda `None` y aparece como evidencia faltante; nunca se inventa | `test_sequence_and_completeness.py::test_missing_environment_fact_is_reported` · `test_cli.py::test_strict_exits_1_when_evidence_is_missing` | sesión 2026-11-21 |
| CP-018 | En el demo, la escritura externa ocurre exactamente una vez durante la grabación y las limitaciones del adaptador aparecen en todo reporte | `test_toy_agent_end_to_end.py::test_record_and_inspect_toy_agent` | sesión 2026-11-21 |

## Secretos y seguridad

| Id | Comportamiento | Red de seguridad | Origen |
|---|---|---|---|
| CP-003 | Los valores bajo claves sensibles se redactan **antes** de persistir; la API key del demo nunca llega a disco | `test_redaction.py` · `test_record_run.py::test_redaction_happens_before_persistence` · `test_persistence_security.py::test_demo_secret_never_reaches_disk` · mutación | [ADR-007](../forked/decisiones-arquitectura/ADR-007-omitir-no-truncar.md) |
| CP-004 | Strings con forma de credencial (`sk-…`, `ghp_…`, `AKIA…`, `Bearer …`, PEM…) se redactan en cualquier posición | `test_redaction.py::test_secret_shaped_values_are_redacted_anywhere` · mutación | ADR-007 |
| CP-005 | El motivo de fallo (mensaje de excepción) se redacta en `run.json` y en `run.failed` | `test_record_run.py::test_secret_in_failure_reason_is_redacted_everywhere` · mutación | sesión 2026-11-21 |
| CP-012 | Una línea JSONL malformada, truncada, enorme, con versión mayor no soportada o inválida falla cerrada con `CorruptRecording` y su número de línea | `test_persistence_security.py::test_malformed_lines_fail_closed_with_line_number` · `test_oversized_line_is_rejected` · mutación | [ADR-004](../forked/decisiones-arquitectura/ADR-004-persistencia-fase-1.md) |
| CP-013 | El patrón de `RunId` hace imposible el path traversal | `test_identifiers_and_schema.py::test_invalid_run_ids_are_rejected` · `test_persistence_security.py::test_path_traversal_through_run_id_is_impossible` · `test_cli.py::test_errors_are_explicit_with_code` | ADR-009 |
| CP-014 | `run.json` se reemplaza atómicamente y se rechaza si pertenece a otro run | contrato `test_snapshot_round_trips_and_save_replaces` · `test_persistence_security.py::test_tampered_run_metadata_is_rejected` | ADR-004 |
| CP-017 | Grabar e inspeccionar funciona con la red bloqueada | `test_toy_agent_end_to_end.py` (fixture `no_network`) | `docs/04` RNF |

## Estructura, contratos y CLI

| Id | Comportamiento | Red de seguridad | Origen |
|---|---|---|---|
| CP-015 | El dominio solo importa stdlib; la aplicación no importa frameworks ni adaptadores; los adaptadores de salida solo se importan desde `bootstrap` | `tests/guardians/test_dependency_rule.py` · mutación (3) | [ADR-001](../../docs/14-adr-001-hexagonal-architecture.md) · [ADR-005](../forked/decisiones-arquitectura/ADR-005-guardianes-pytest.md) |
| CP-016 | `spec/cip/v0.1/` coincide con el código y los 5 fixtures dorados hacen ida y vuelta sin cambios | `tests/guardians/test_published_schema.py` | [versionado](../protocolo/versionado.md) |
| CP-019 | La CLI sale con 0 / 1 (`--strict` con evidencia faltante) / 2 (error) e imprime `error[<code>]` | `tests/integration/test_cli.py` | sesión 2026-11-21 |
| CP-020 | El doble `InMemoryRunStore` y `FileSystemRunStore` pasan **el mismo** contrato | `tests/contract/test_run_store_contract.py` | lección heredada de NextVent (B-053) |
| CP-021 | `contexto/` no tiene enlaces rotos ni documentos huérfanos y toda spec está indexada | `tests/guardians/test_context_graph.py` | ADR-005 |

## Replay

| Id | Comportamiento | Red de seguridad | Origen |
|---|---|---|---|
| CP-022 | En replay **ninguna herramienta se ejecuta**, de ninguna clase de efecto; el outbox no cambia | `test_replay.py::test_replay_reproduces_outcome_without_executing_any_tool` · `test_cli.py::test_replay_does_not_touch_the_outbox` · smoke de CI · mutación (7 rojos) | [ADR-010](../forked/decisiones-arquitectura/ADR-010-replay-estricto-sin-politica.md) |
| CP-023 | Cualquier diferencia de nombre, clase o entradas redactadas aborta el replay (`ReplayDivergence`) y el run queda `failed` | `test_changed_input_diverges_and_fails_the_replay` · `test_effect_class_change_diverges` · mutación (1) | ADR-010 |
| CP-024 | Sin observación utilizable (llamada extra, sin resultado, resultado omitido) ⇒ `MissingObservation`, nunca llamada en vivo | `test_extra_call_has_no_observation` · `test_omitted_result_cannot_be_replayed` | `docs/04` UC-02 |
| CP-025 | Llamadas grabadas no pedidas o run de otro adaptador ⇒ el replay falla | `test_unrequested_recorded_calls_fail_the_replay` · `test_other_adapters_run_cannot_be_replayed` · mutación (1) | ADR-010 |

## Ramas, política y comparación

| Id | Comportamiento | Red de seguridad | Origen |
|---|---|---|---|
| CP-026 | Crear una rama y compararla **no modifica ni un byte** de los artefactos del padre | `test_branch.py::test_branch_changes_outcome_denies_write_and_keeps_parent_intact` | `docs/09` Fase 3 · [ADR-011](../forked/decisiones-arquitectura/ADR-011-ramas-checkpoint-y-comparacion.md) |
| CP-027 | En una rama, una llamada nueva que no sea `pure_local` **no se ejecuta**: `EffectDenied` + `tool.error` con motivo | `test_changed_non_pure_call_after_checkpoint_is_denied` (5 clases) · smoke de CI · mutación (7 rojos) | `docs/07` §7.5 |
| CP-028 | Antes del checkpoint, y en el checkpoint mismo, la rama exige coincidir con el padre; si no, falla cerrado | `test_prefix_divergence_fails_closed` · `test_checkpoint_call_must_match_parent_inputs` · mutaciones (6 y 1 rojos) | ADR-011 |
| CP-029 | La intervención y el linaje quedan en `run.started` de la rama, redactados | `test_secret_in_intervention_value_is_redacted` · aserción de `intervention` en el test principal | `docs/09` «la intervención aparece en la evidencia» |
| CP-030 | Evidencia faltante o rama no finalizada ⇒ invariante `unknown`, nunca `verified`; padre alterado ⇒ `violated` | `test_incomplete_branch_leaves_invariants_unknown_never_verified` · `test_tampered_parent_violates_invariant_and_downgrades_claim` · mutaciones (1 y 1) | CIP §6.6 |
| CP-031 | `controlled_comparison` solo con todas las invariantes verificadas y rama completa; nunca se emite una afirmación causal | mismos tests · mutación (2 rojos) | CIP §6.7 · `CLAUDE.md` |
| CP-032 | Checkpoint que no es un `tool.call` ⇒ `InvalidCheckpoint` **antes** de crear el run de la rama | `test_checkpoint_must_be_a_tool_call` · `test_cli.py::test_branch_rejects_bad_value_and_bad_checkpoint` | ADR-011 |

## Paquete de evidencia

| Id | Comportamiento | Red de seguridad | Origen |
|---|---|---|---|
| CP-033 | Exportar dos veces los mismos runs produce **los mismos bytes** | `test_evidence.py::test_export_is_deterministic` | `docs/09` Fase 4 |
| CP-034 | El verificador solo necesita el paquete (store borrado) | `test_exported_package_verifies_without_the_store` · smoke de CI | `docs/08` portabilidad · [ADR-012](../forked/decisiones-arquitectura/ADR-012-paquete-de-evidencia.md) |
| CP-035 | Archivo alterado, faltante o extra ⇒ integridad `FAILED` y la validez **no se evalúa** | `test_changed_artifact_fails_integrity_and_skips_validity` · `test_missing_and_unexpected_files_are_reported` · mutaciones (2 y 1) | `docs/09` Fase 4 |
| CP-036 | Integridad y validez son preguntas separadas: **todo** campo atestiguado se regenera desde la evidencia; cualquier diferencia (nivel, statement, intervención, invariantes extra, entorno, política, limitaciones, `comparison.json`) es `unsupported claim` aunque los hashes cuadren | `test_inflated_claim_with_intact_hashes_is_unsupported` · `test_rehashed_tampering_is_caught_by_recomputation` · `test_every_attested_manifest_field_is_recomputed` (6) · `test_fields_outside_the_comparison_are_regenerated` (4) · `test_rewritten_comparison_json_with_fixed_hash_is_unsupported` · mutaciones (2, 2, 4, 1, 1) | `docs/04` UC-05 |
| CP-037 | Manifiesto ilegible, faltante, de otro formato/versión, con rutas inseguras o duplicadas ⇒ integridad `FAILED` | `test_bad_manifest_fails_integrity` (5) · `test_unparseable_or_missing_manifest` · mutación (1) | `docs/07` manifiestos alterados |
| CP-038 | Rutas inseguras y symlinks se rechazan **antes** de resolver nada; nunca se escribe sobre un directorio con contenido | `test_unsafe_artifact_paths_are_refused` (7) · `test_symlink_in_package_is_rejected` (Linux/macOS) · `test_export_refuses_non_empty_target` · mutaciones (7 y 1) | `docs/07` path traversal · [E-001](../errores/errores/E-001-el-guardian-del-grafo-no-veia-mayusculas-en-windows.md) |
| CP-039 | Un valor con forma de credencial bloquea la exportación | `test_credential_shaped_value_blocks_export` · mutación (1) | `docs/04` UC-05 «excluye secretos» |

## Adaptador, puente OpenTelemetry y benchmark

| Id | Comportamiento | Red de seguridad | Origen |
|---|---|---|---|
| CP-040 | Con el adaptador de Pydantic AI, replay y rama **no ejecutan ninguna herramienta** y una llamada denegada no se ejecuta; todo con la red bloqueada | `test_pydantic_ai_adapter.py::test_replay_executes_no_tool` · `test_branch_denies_the_changed_email_and_reports_it_to_the_model` · fixture `offline` · escenario S03 | [ADR-013](../forked/decisiones-arquitectura/ADR-013-framework-puente-otel-y-benchmark.md) |
| CP-041 | Cada herramienta lleva su clase de efecto; sin declarar ⇒ `unknown`; una denegación aborta el agente (`raise`) o se **reporta explícitamente** al modelo (`report`), nunca se finge un éxito | `test_denial_can_abort_the_run_instead` · `test_undeclared_tool_is_unknown_and_denied_when_its_inputs_change` | ADR-013 |
| CP-042 | Argumento o resultado no JSON ⇒ `InvalidEvent` y el run queda `failed`; parámetros llamados `name`/`fn` no chocan con el SDK | `test_non_json_tool_result_fails_loudly` · `_mystery_agent` (parámetros `name`, `fn`) | ADR-013 |
| CP-043 | El export OTel es determinista, no incluye payloads sin `--include-payloads` y nunca incluye secretos | `test_otel_bridge.py::test_export_is_deterministic` · `test_payloads_and_secrets_stay_out_unless_requested` · S09 | `docs/06` §6.8 |
| CP-044 | Un trace importado marca todo `unknown`, completitud desconocida, misma forma de payload que el SDK (reproducible y bifurcable); trazas malformadas, vacías o enormes se rechazan; secretos redactados | `test_round_trip_import_marks_every_effect_unknown` · `test_imported_run_can_be_branched_and_denies_unknown_effects` · `test_malformed_traces_are_rejected` · `test_too_many_spans_are_refused` · `test_secret_in_imported_arguments_is_redacted` | ADR-013 |
| CP-045 | El runner reporta un escenario que revienta como `fail` (no aborta), no combina métricas en un puntaje, su parte determinista es reproducible y **el benchmark puede fallar** | `test_fcrb.py::test_a_crashing_scenario_is_reported_as_failed_not_raised` · `test_deterministic_part_is_reproducible` · `test_no_combined_score_and_limitations_are_stated` · `test_benchmark_can_fail_when_an_unsafe_effect_is_allowed` · 9 mutaciones | `docs/08` §8.3, §8.5 |
| CP-046 | Las líneas base se **miden** (no se afirman) y las no ejecutadas se listan con su motivo | `test_baseline_is_measured_not_assumed` · `NOT_EXECUTED` | `docs/08` §8.4 |

## Documentación pública, ejemplos y empaquetado

| Id | Comportamiento | Red de seguridad | Origen |
|---|---|---|---|
| CP-047 | La referencia de la CLI documenta **exactamente** los comandos que existen: ni falta uno ni hay uno inventado | `test_public_docs.py::test_every_command_is_documented_and_nothing_is_invented` · mutación (2 rojos) | [ADR-014](../forked/decisiones-arquitectura/ADR-014-documentacion-publica-y-puerta-de-release.md) |
| CP-048 | Los enlaces relativos del README y de las páginas de usuario resuelven; todo `forked <comando>` mencionado existe; los fragmentos de Python de la guía parsean | `test_relative_links_resolve` · `test_documented_commands_exist` · `test_python_snippets_parse` · mutaciones (1, 1, 1, 1) | ADR-014 |
| CP-049 | La documentación pública no afirma novedad ni superlativos mientras el arte previo esté abierto, y el README conserva el aviso de que su comparación no es una revisión de arte previo | `test_no_novelty_or_superlative_claims_while_prior_art_is_unreviewed` · `test_readme_discloses_that_its_comparison_is_not_a_prior_art_review` · mutaciones (1 y 1) | [arte previo](../investigacion/arte-previo.md) |
| CP-050 | La rueda construida se instala y ejecuta **fuera del repositorio**; el adaptador de Pydantic AI sin su extra da un error accionable | paso de CI «Package smoke test» · `test_missing_extra_gives_an_actionable_error` | ADR-014 |
| CP-051 | Los ejemplos documentados siguen funcionando | `tests/acceptance/test_examples.py` · pasos de CI | ADR-014 |

## Segundo adaptador, arte previo y línea base de LangGraph

| Id | Comportamiento | Red de seguridad | Origen |
|---|---|---|---|
| CP-052 | Con el adaptador de LangGraph, replay y rama **no ejecutan ninguna herramienta**, una llamada denegada no se ejecuta y todo corre con la red bloqueada | `test_langgraph_adapter.py::test_replay_executes_no_tool` · `test_branch_denies_the_changed_email_and_tells_the_model` · `test_denial_can_abort_the_graph_instead` · fixture `offline` | [ADR-016](../forked/decisiones-arquitectura/ADR-016-adaptador-langgraph-y-linea-base.md) |
| CP-053 | Grabando, el agente recibe el `ToolMessage` **original** sin tocar; en replay el resultado se reconstruye desde el contenido (el `artifact` no está disponible: límite declarado) | `test_recording_hands_the_agent_the_original_message_and_replay_content_only` · mutación (sobrevivió → detectada) | ADR-016 |
| CP-054 | Un `Command` se rechaza; una herramienta sin declarar es `unknown`; un error de herramienta se propaga y se reproduce como `RecordedToolError`; las llamadas paralelas de un paso mantienen una secuencia válida | `test_command_result_is_rejected_loudly` · `test_undeclared_tool_is_unknown_and_answered_by_the_intervention` · `test_tool_error_propagates_and_is_replayed_as_recorded_error` · `test_parallel_tool_calls_in_one_step_keep_a_valid_sequence` · mutaciones (1, 1) | ADR-016 |
| CP-055 | La matriz de arte previo declara sus límites y lo no revisado; el README reconoce lo que ya existe, enlaza la matriz y no convierte «no encontrado» en «no existe» | `test_public_docs.py::test_prior_art_matrix_states_its_limits` · `test_readme_comparison_points_to_the_evidence_and_admits_what_already_exists` · 3 mutaciones | [ADR-015](../forked/decisiones-arquitectura/ADR-015-posicionamiento-tras-el-arte-previo.md) |
| CP-056 | La línea base de LangGraph se **mide** (S04), S10 compara tres adaptadores y el informe registra las versiones de los frameworks | `test_fcrb.py::test_baseline_is_measured_not_assumed` · `_framework_versions` | ADR-016 · `docs/08` §8.5 |

## Reporte visual y salida de consola

| Id | Comportamiento | Red de seguridad | Origen |
|---|---|---|---|
| CP-057 | Los datos grabados (nombres de herramienta, argumentos, resultados, errores) **se escapan** en el reporte HTML; un dato hostil no ejecuta código | `test_html_report.py::test_hostile_recorded_data_is_escaped` · 3 mutaciones (sin escape, sin CSP, payload sin escapar) | [ADR-017](../forked/decisiones-arquitectura/ADR-017-reporte-html-autocontenido.md) |
| CP-058 | El reporte no tiene JavaScript ni recursos externos, lleva una CSP estricta y es **determinista** | `test_report_loads_nothing_and_runs_no_script` · `test_report_is_deterministic` | ADR-017 |
| CP-059 | El reporte muestra línea de tiempo, efectos, estados de captura, el fork, las invariantes, el nivel de afirmación y la evidencia verificada; un run desconocido o una rama que no lo es salen con código 2 | `test_report_for_one_run` · `test_report_for_a_branch_shows_…` · `test_unknown_run_and_non_branch_exit_2` · `test_open_flag_opens_the_file_in_the_browser` | ADR-017 |
| CP-060 | La salida de consola y la ayuda de la CLI son ASCII (una raya larga se corrompía en Windows); solo se tolera el marco de Rich | `test_cli.py::test_help_text_of_every_command_is_ascii` · `test_examples.py::test_example_output_is_ascii_…` | reproducción en frío ([sesión g](../sesiones/2026-11-22-g-arte-previo-langgraph-y-release.md)) |
