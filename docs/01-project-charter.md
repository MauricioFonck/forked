# 1. Project Charter

## 1.1 Executive summary
FORKED is proposed as open-source infrastructure for trustworthy counterfactual experimentation. It helps developers and researchers examine alternative outcomes of instrumented software workflows and AI agents while recording the conditions, interventions, external observations, and limitations that shape each result.

The project begins with a constrained local runtime and a versioned experiment format. It does not begin as a universal virtual machine, a new agent framework, or a promise to replay every application exactly.

## 1.2 Vision
Make software and AI-system experiments inspectable, branchable, reproducible within declared boundaries, and independently verifiable.

## 1.3 Mission
Provide open tooling and a common protocol for:
- capturing execution evidence;
- replaying recorded observations safely;
- creating isolated experiment branches;
- declaring interventions and invariants;
- classifying external effects;
- comparing outcomes;
- packaging evidence and limitations.

## 1.4 Why now
AI applications increasingly combine probabilistic model outputs, tools, retrieval, mutable data, APIs, and long-running workflows. Existing observability and evaluation systems help inspect runs and compare versions, while workflow engines address replay and durable execution within defined programming constraints. There is room to investigate a cross-tool experiment layer that makes the validity conditions of alternative-run comparisons explicit.

## 1.5 Target users
1. AI application engineers debugging tool-using agents.
2. Platform engineers testing workflow changes.
3. AI evaluation researchers comparing interventions.
4. Open-source framework maintainers seeking interoperable experiment artifacts.
5. Security and reliability teams validating that experiments do not repeat production side effects.

## 1.6 Value proposition
FORKED should answer:
- What was captured?
- What was changed?
- What was held constant?
- Which operations were replayed from recorded observations?
- Which operations were simulated, blocked, or re-executed?
- Which invariants were verified, violated, or unknown?
- What conclusions are supported, and what remains uncertain?

## 1.7 Business and sustainability logic
The core protocol and runtime are open source. Potential future sustainability options (not MVP commitments):
- hosted collaboration and artifact storage;
- enterprise policy and audit features;
- managed benchmark execution;
- support and integration services;
- sponsored research and grants.

The open-source core must remain useful without a paid service. No monetization decision may compromise protocol neutrality or user control of data.

## 1.8 Success definition
Initial success is a working, documented vertical slice with tests and a public benchmark. Adoption metrics matter later. Stars, downloads, and social reach are not evidence of technical validity.

## 1.9 Non-goals for v0
- Arbitrary full-machine snapshots.
- Transparent capture of every OS call.
- Automatic causal proof.
- Autonomous production experimentation.
- Automatic re-execution of write operations.
- A hosted SaaS product.
- Model quality ranking.
