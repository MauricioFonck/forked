# ADR-001: Adopt Hexagonal Architecture with a Modular Monolith

- **Status:** Accepted for v0 (revisit only with measured evidence)
- **Date:** 2026-11-21
- **Decision owners:** FORKED maintainers

## Context
FORKED needs to instrument diverse workflows and AI frameworks while keeping its domain rules independent of providers, storage, interfaces and runtime frameworks. Its MVP is local-first and has a small team/contributor footprint. Replay safety, branch immutability and evidence integrity are core product guarantees.

## Decision
Adopt Hexagonal Architecture (Ports and Adapters) inside a modular monolith. Organize code into `domain`, `application`, `application/ports`, `adapters/inbound`, `adapters/outbound` and `bootstrap`.

Use lightweight DDD for domain language, aggregates and invariants. Use dependency injection through explicit composition at startup. Use Strategy/Policy objects for effect decisions, state machines for lifecycle transitions, and pipeline stages for capture. Use Repository/Unit of Work only where persistence boundaries require them. Defer CQRS to read/report complexity and third-party plugin architecture until contracts stabilize.

## Alternatives considered
1. **Layered architecture only:** simple, but often allows framework and persistence details to leak into business logic without explicit ports.
2. **Clean Architecture:** shares the inward-dependency principle; hexagonal terminology better emphasizes replaceable adapters and testable ports for this integration-heavy product. We may borrow compatible practices without running two competing architecture models.
3. **Microservices:** rejected for v0 because deployment, network, observability and consistency costs are unjustified.
4. **Full event sourcing:** rejected because an append-only observation log does not require rebuilding all application state from events.
5. **Framework-centric design:** rejected because it would couple the core to one workflow or AI framework.

## Consequences
### Positive
- Domain and use cases can be tested without external services.
- Framework/provider/storage integrations remain replaceable.
- Safety policy is centralized and testable.
- The system can evolve without premature distributed infrastructure.

### Trade-offs
- More interfaces and explicit wiring than a quick script.
- Contributors must understand dependency direction.
- Poorly designed ports can become generic abstractions; interfaces must remain small and capability-based.

## Guardrails
- No domain imports from adapters or frameworks.
- Application use cases depend on ports, not concrete infrastructure.
- One composition root wires implementations.
- Contract tests validate adapters.
- Dependency direction is checked in CI where practical.
- Any exception or major architecture change requires a new ADR.

## Revisit when
There is measured need for independent deployment, process isolation, distributed execution, or stable third-party plugin support. Do not revisit solely because a pattern is fashionable.
