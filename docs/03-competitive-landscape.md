# 3. Competitive and Adjacent Landscape

## 3.1 Research method and caution
This is a scoped public-source review, not an exhaustive patent search or legal freedom-to-operate opinion. Product features evolve. Re-check official documentation, repositories, licenses, and release notes before public claims or integration commitments.

FORKED must describe competitors accurately and avoid saying “nothing like this exists.” Several adjacent products already support important pieces of the proposed workflow.

## 3.2 Direct and adjacent projects

### LangGraph — time travel and checkpoint branching
Public documentation describes replaying from checkpoints and resuming execution from a previous state, including modifying state to explore alternatives. This is a direct overlap with the branching concept.
- Strength: native state/checkpoint model for graph-based agent workflows.
- Boundary/opportunity for FORKED: investigate a cross-framework experiment artifact and explicit integrity/effect accounting rather than recreating LangGraph's graph runtime.
- Source: https://docs.langchain.com/oss/python/langgraph/use-time-travel/

### Temporal — durable execution and deterministic replay
Temporal records event histories and replays workflow code to rebuild state. Its documentation explains deterministic constraints and the need to put external interactions such as API calls, database queries, LLM invocations, and file I/O into Activities. Side-effect APIs record non-deterministic values for replay.
- Strength: mature durable execution model, event history, replay constraints, side-effect handling.
- Boundary/opportunity: FORKED should not compete as a workflow orchestrator. It can explore experiment packaging and cross-system comparison for instrumented workloads, potentially integrating with Temporal.
- Sources: https://docs.temporal.io/workflows ; https://docs.temporal.io/workflow-definition

### Arize Phoenix — AI observability, evaluation, and experiments
Phoenix is open source and offers tracing, evaluations, datasets, experiments, prompt/model comparisons, and span replay. It uses OpenTelemetry-based instrumentation and supports many frameworks/providers.
- Strength: broad AI observability and evaluation workflow; strong overlap in trace inspection and experiment comparison.
- Boundary/opportunity: FORKED must go beyond trace visualization. Its differentiator must be branch semantics, side-effect policy, declared invariants, and evidence packages. Phoenix should be considered an integration/benchmark peer, not dismissed.
- Sources: https://github.com/Arize-ai/phoenix ; https://arize.com/docs/phoenix/

### OpenTelemetry GenAI semantic conventions
OpenTelemetry's GenAI conventions describe spans and attributes for model calls, agent operations, planning, tool execution, and related events. Some conventions are marked Development.
- Strength: emerging interoperability layer for telemetry.
- Boundary/opportunity: FORKED should consume/export OpenTelemetry rather than inventing a competing tracing vocabulary. CIP should define experiment semantics not already covered by spans.
- Sources: https://github.com/open-telemetry/semantic-conventions-genai ; https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md

### LangSmith — tracing and evaluation ecosystem
LangSmith provides tracing, evaluation, datasets, and iteration workflows for LLM applications. Confirm current feature boundaries and licensing from its official docs before making detailed comparison claims.
- Strength: integrated developer workflow for tracing and evaluation.
- Boundary/opportunity: position FORKED around portable experiment evidence and controlled branch semantics; offer export/import integrations where possible.
- Source: https://docs.smith.langchain.com/

### Agent observability and evaluation platforms
A broader group of tools provides traces, sessions, evaluations, cost/latency metrics, prompt iteration, and debugging. This category is adjacent rather than a single competitor. Perform a product-by-product review before naming additional vendors in external material.

## 3.3 Feature comparison (high-level, not a scorecard)

| Capability | LangGraph | Temporal | Phoenix | OpenTelemetry GenAI | FORKED target |
|---|---|---|---|---|---|
| Execution tracing | Framework-dependent | Event history | Yes | Instrumentation schema | Ingest/export |
| Checkpoint/replay | Yes, graph state | Yes, deterministic workflow replay | Span replay/experiment reruns | No runtime | Adapter-dependent |
| Branch alternative | Yes | Not primary product positioning | Experiments and replay workflows | No | Core concept |
| Side-effect policy | Framework/app design | Activities and recorded side effects | Not core runtime guarantee | Not runtime policy | Default-deny policy layer |
| Cross-framework protocol | No universal branch protocol | Workflow platform APIs | Broad integrations | Telemetry standard | Proposed CIP |
| Evidence package | Framework-specific state/history | Workflow history | Trace/dataset/experiment artifacts | Telemetry data | Proposed portable package |
| Causal validity guarantee | No universal guarantee | Replay determinism constraints | Evaluation comparison | No causal guarantee | Must report assumptions; no universal guarantee |

## 3.4 Positioning statement
FORKED complements rather than replaces existing runtimes and observability platforms. It aims to add a portable experiment layer that records what was changed, what was held constant, how external effects were handled, and what can legitimately be concluded.

## 3.5 Competitive moat hypothesis
Potential defensibility may come from:
1. a well-designed, adopted protocol;
2. reliable adapters across ecosystems;
3. a benchmark suite that becomes a reference;
4. independent evidence verification;
5. trusted safety defaults and transparent limitations.

A visual dashboard alone is not a moat.
