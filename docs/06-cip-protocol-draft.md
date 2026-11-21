# 6. Counterfactual Integrity Protocol (CIP) — Draft v0.1

## 6.1 Status
Exploratory protocol draft. Not a published standard. Names and schema are provisional pending prior-art review and implementation feedback.

## 6.2 Protocol objectives
CIP describes an experiment in a machine-readable form:
- baseline execution;
- capture boundary and adapter capabilities;
- intervention(s);
- invariants;
- effect handling policy;
- branch lineage;
- observations and results;
- evidence and limitations.

## 6.3 Minimal conceptual schema

```json
{
  "cip_version": "0.1.0",
  "experiment_id": "exp_...",
  "created_at": "RFC3339 timestamp",
  "baseline": {
    "run_id": "run_...",
    "checkpoint_id": "checkpoint_...",
    "artifact_manifest": "baseline/manifest.json"
  },
  "interventions": [
    {
      "id": "int_001",
      "target": "tool.result",
      "operation": "replace_recorded_observation",
      "value_ref": "artifacts/intervention-value.json"
    }
  ],
  "invariants": [
    {
      "id": "inv_001",
      "description": "same input dataset",
      "verification": "content_hash",
      "status": "verified"
    }
  ],
  "effects_policy": {
    "default": "deny",
    "recorded_observation": "replay",
    "external_write": "deny",
    "unknown": "deny"
  },
  "branches": [],
  "claims": [],
  "limitations": [],
  "artifacts": []
}
```

This is illustrative, not a finalized JSON Schema. Use RFC3339 timestamps and stable identifiers in the implementation.

## 6.4 Event envelope
Required fields:
- `schema_version`
- `event_id`
- `run_id`
- `sequence`
- `event_type`
- `timestamp`
- `source`
- `payload_ref` or redacted payload
- `capture_status`

Optional fields:
- `parent_event_id`
- `trace_id`
- `span_id`
- `tool_name`
- `model_provider`
- `model_name`
- `environment_fingerprint`
- `sensitivity_labels`

## 6.5 Effect taxonomy
- `PURE_LOCAL`: no external state change expected; still subject to sandbox constraints.
- `RECORDED_READ`: result captured and replayed from evidence.
- `EXTERNAL_READ`: external read requiring a recorded response or explicit policy.
- `EXTERNAL_WRITE`: changes external state; deny in replay/branch by default.
- `LOCAL_WRITE`: changes sandbox-local state; allowed only within disposable branch storage.
- `UNKNOWN`: effect cannot be classified; deny by default.

## 6.6 Invariant status
- `VERIFIED`: verification method ran and passed.
- `VIOLATED`: verification method ran and failed.
- `UNKNOWN`: insufficient evidence or no verifier.

Every invariant must include a verification method and evidence reference. A description alone is not verification.

## 6.7 Claim levels
- `OBSERVATIONAL`: reports what was seen.
- `CONTROLLED_COMPARISON`: declares and checks selected invariants.
- `CONDITIONAL_CAUSAL`: causal interpretation with explicit assumptions and design.
- `UNSUPPORTED`: evidence does not support the claim.

## 6.8 Compatibility
CIP should map to OpenTelemetry trace/span identifiers where available. It should not redefine generic trace semantics. The protocol adds experiment-level constructs that tracing conventions do not aim to provide.

## 6.9 Versioning
- Semantic versioning for protocol releases.
- Readers must reject unsupported major versions.
- Minor versions may add optional fields.
- Breaking schema changes require a major version.
- Golden fixtures test forward/backward compatibility.

## 6.10 Open design questions
- How should large payloads be referenced and encrypted?
- How are secrets and personal data represented without leaking them?
- Which checkpoint semantics can be portable across frameworks?
- How should probabilistic model outputs be sampled and reported?
- How should time and randomness be virtualized?
- Which parts belong in protocol vs adapter capability declarations?
