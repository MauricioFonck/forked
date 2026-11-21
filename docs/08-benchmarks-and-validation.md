# 8. Benchmarks and Validation Plan

## 8.1 Purpose
The benchmark must test whether FORKED adds value beyond event logging, existing replay features, and experiment comparison tools. It must be independently reproducible.

## 8.2 Benchmark suite
Working name: FORKED Counterfactual Reliability Benchmark (FCRB). Name is provisional and subject to trademark/prior-art review.

Initial scenarios:
1. Deterministic toy workflow with recorded tool calls.
2. Workflow with time/randomness dependency.
3. Agent tool call with recorded external read.
4. Attempted external write during replay.
5. Branch intervention changing one tool observation.
6. Missing event in the recording.
7. Environment version mismatch.
8. Tampered evidence artifact.
9. Sensitive field redaction.
10. Two adapters producing equivalent protocol artifacts.

## 8.3 Metrics
- **Replay fidelity:** proportion of expected recorded observations consumed correctly.
- **Capture completeness:** proportion of declared capture points recorded.
- **Invariant verification rate:** proportion of declared invariants with a valid verification result.
- **Unsafe effect prevention:** number/rate of prohibited effects successfully blocked.
- **Evidence completeness:** required manifest/artifact fields present and verifiable.
- **Branch isolation:** parent artifacts remain unchanged after branch execution.
- **Overhead:** capture latency, storage growth, and CPU/memory overhead.
- **Portability:** ability to verify package on a separate machine/environment.

Do not combine these into one opaque score in v0.

## 8.4 Baselines
Compare against:
- plain application logs;
- OpenTelemetry trace capture;
- framework-native replay/checkpoint features where applicable;
- Temporal workflow replay for suitable deterministic workflows;
- Phoenix trace/experiment workflows for suitable LLM application cases.

The benchmark must document where a baseline is not applicable rather than force an unfair comparison.

## 8.5 Experimental method
- Publish exact code and configuration.
- Pin dependency versions.
- Separate warm-up from measured runs.
- Repeat probabilistic model scenarios and report distributions.
- Record model/provider/version and sampling settings where available.
- Use synthetic test data.
- Publish raw results and analysis scripts.
- Report failures and limitations, not only successful cases.

## 8.6 Release gate
Do not call the benchmark “validated” until:
- at least one independent person can reproduce it from a clean environment;
- fixtures and expected outputs are versioned;
- safety cases are included;
- benchmark methodology is reviewed;
- results are reproducible within stated tolerances.
