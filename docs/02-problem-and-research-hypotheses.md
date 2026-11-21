# 2. Problem Statement and Research Hypotheses

## 2.1 Problem
A software or agent execution is shaped by more than its visible prompt or code. It may depend on model sampling, tool outputs, database state, time, randomness, filesystem contents, network services, package versions, credentials, and hidden process state.

When a developer changes one decision and compares two runs, the result can be misleading if other conditions changed too. Replaying an execution can also repeat external writes unless the runtime deliberately separates recorded observations from effectful operations.

## 2.2 Precise problem statement
There is no single universally adopted, framework-neutral experiment artifact that, by itself, guarantees causal validity. FORKED will investigate whether a protocol and runtime can improve the discipline and auditability of counterfactual experiments by explicitly recording provenance, interventions, invariants, effect handling, and uncertainty.

This is a research hypothesis, not a claim that no existing product has any of these features.

## 2.3 Core terminology
- **Execution:** one observed run of a workflow or agent.
- **Event:** a timestamped, typed observation about an execution.
- **Checkpoint:** a declared capture point containing the state needed by a supported adapter.
- **Branch:** a new experiment lineage derived from a checkpoint or event prefix.
- **Intervention:** a declared change introduced into a branch.
- **Invariant:** a condition intended to remain constant across compared branches.
- **External effect:** an operation that can affect a system outside the experiment boundary.
- **Recorded observation:** a stored result used during replay rather than repeating the operation.
- **Evidence package:** a portable manifest and associated artifacts documenting an experiment.
- **Replay fidelity:** degree to which a replay reproduces the captured behavior under declared conditions.

## 2.4 Research hypotheses
H1. Explicitly recording provenance and environment fingerprints improves diagnosis of divergent replays compared with unstructured logs.

H2. A typed intervention and invariant model can identify invalid comparisons more reliably than comparing outputs alone.

H3. A default-deny effect policy, combined with recorded observations, can reduce accidental duplicate external writes during replay.

H4. A portable evidence package can allow an independent verifier to validate artifact integrity and inspect the experiment's declared conditions.

H5. A common adapter contract can support multiple frameworks without forcing them to adopt one agent runtime.

## 2.5 Falsification criteria
The project must revise or abandon its core claims if:
- the metadata overhead makes capture unusable for the target workload;
- the runtime cannot reliably distinguish recorded observations from effectful operations;
- invariants cannot be checked or reported honestly;
- adapters require framework-specific semantics that cannot be represented in the protocol;
- the benchmark shows no meaningful improvement over simpler event logging and existing replay tools.

## 2.6 The causal language boundary
FORKED must not label a difference as “caused by” an intervention unless the experiment design supports that conclusion. A report should distinguish:
- **Observed difference:** two recorded outcomes differ.
- **Controlled comparison:** declared variables and invariants were checked to a stated level.
- **Conditional causal estimate:** a causal interpretation is supported under explicit assumptions.
- **Unsupported causal claim:** evidence is insufficient.

A hash proves artifact integrity, not causal truth. A replay proves only what the adapter's guarantees allow.
