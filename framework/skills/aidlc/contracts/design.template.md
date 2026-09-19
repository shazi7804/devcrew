# Design — <project name>

> Derived from requirements.md. Every requirement Rn/Nn must map to something here.
> Status: DRAFT | REVIEWED

## Architecture overview
ASCII/diagram of the system: components and how they talk.

## Requirement → design map
| Requirement | Satisfied by |
|---|---|
| R1 | <component / mechanism> |
| R2 | |
| N1 | |

An unmapped requirement is a hole — do not leave the table incomplete.

## Technology decisions (ADRs)
For each load-bearing choice, one ADR. Selection for the big ones (language,
framework, data store, compute, hosting) should be backed by an `llm-council`
comparison against the requirements' constraints.

### ADR-1: <decision title, e.g. "Backend runtime">
- **Context**: what forces this decision (which requirements/constraints)
- **Options considered**: A / B / C — with the trade-off that matters
- **Decision**: <chosen option>
- **Why (vs alternatives)**: tied back to the requirements
- **Consequences**: what this commits us to, what it costs

### ADR-2: ...

## Data model
Entities, key fields, relationships, storage.

## Key interfaces / APIs
Endpoints or contracts between components.

## Cross-cutting concerns
AuthN/Z, observability, error handling, config/secrets, scaling.

## Risks & mitigations
Top technical risks and how the design addresses them.

## Phase breakdown (hand-off to implementation)
Ordered, each with a demo/acceptance criterion QA can check.
