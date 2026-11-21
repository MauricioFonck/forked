# FORKED Architecture Diagrams

## End-to-end experiment flow

```mermaid
flowchart LR
  A[Baseline workflow] --> B[Capture events]
  B --> C[Immutable run artifacts]
  C --> D[Select checkpoint]
  D --> E[Create branch]
  E --> F[Declare intervention]
  F --> G[Run under effect policy]
  G --> H[Check invariants]
  H --> I[Compare outcomes]
  I --> J[Evidence package]
  J --> K[Offline verification]
```

## Effect policy

```mermaid
flowchart TD
  A[Operation requested] --> B{Effect classified?}
  B -- No --> X[Deny and report unknown]
  B -- Yes --> C{Operation type}
  C -- Recorded read --> D[Replay recorded result]
  C -- Pure local --> E[Run in disposable sandbox]
  C -- External read --> F[Use recording; otherwise deny]
  C -- Local write --> G[Branch-local disposable storage]
  C -- External write --> X2[Deny by default]
```


## Hexagonal architecture and dependency direction

```mermaid
flowchart TB
  CLI[CLI / SDK / Future UI] --> UC[Application use cases]
  UC --> DOM[Domain model and rules]
  UC --> PORTS[Outbound ports]
  JSONL[JSONL adapter] -. implements .-> PORTS
  SQLITE[SQLite adapter] -. implements .-> PORTS
  OTel[OpenTelemetry / framework adapters] -. implements .-> PORTS
  FS[Artifact filesystem adapter] -. implements .-> PORTS
  BOOT[Composition root] --> UC
  BOOT --> JSONL
  BOOT --> SQLITE
  BOOT --> OTel
  BOOT --> FS
```

The arrows from use cases point to abstractions, never to concrete infrastructure. Adapters implement ports. The composition root is the only place that selects and wires concrete implementations.
