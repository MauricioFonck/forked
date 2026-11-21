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
| CP-036 | Integridad y validez son preguntas separadas: un manifiesto que afirma más que la evidencia (causal, o invariante `verified` que recalcula distinto) es `unsupported claim` aunque los hashes cuadren | `test_inflated_claim_with_intact_hashes_is_unsupported` · `test_rehashed_tampering_is_caught_by_recomputation` · mutaciones (2 y 2) | `docs/04` UC-05 |
| CP-037 | Manifiesto ilegible, faltante, de otro formato/versión, con rutas inseguras o duplicadas ⇒ integridad `FAILED` | `test_bad_manifest_fails_integrity` (5) · `test_unparseable_or_missing_manifest` · mutación (1) | `docs/07` manifiestos alterados |
| CP-038 | Rutas inseguras y symlinks se rechazan **antes** de resolver nada; nunca se escribe sobre un directorio con contenido | `test_unsafe_artifact_paths_are_refused` (7) · `test_symlink_in_package_is_rejected` (Linux/macOS) · `test_export_refuses_non_empty_target` · mutaciones (7 y 1) | `docs/07` path traversal · [E-001](../errores/errores/E-001-el-guardian-del-grafo-no-veia-mayusculas-en-windows.md) |
| CP-039 | Un valor con forma de credencial bloquea la exportación | `test_credential_shaped_value_blocks_export` · mutación (1) | `docs/04` UC-05 «excluye secretos» |
