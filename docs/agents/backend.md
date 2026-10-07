# backend — Backend R&D

> Implements the services, APIs and data layer from `design.md`, correctly,
> securely and without waste.

[← The team](../../README.md#the-team) · Source prompt:
[`framework/agents/backend.md`](../../framework/agents/backend.md)

## At a glance

| | |
|---|---|
| **Phase** | 3, in parallel with `frontend` |
| **Reads** | `design.md` (data model, interfaces, ADRs) · `standards.md` 🔒 |
| **Produces** | Service code, unit and integration tests, and a PR with `Closes Rn` |
| **Gate** | Tests are green, the PR is open, and the APIs match the design's interface contract, and every requirement has live evidence from the deployed service and formal evidence |
| **Tools** | read · write · edit · shell · search · web |
| **Skills** | aidlc |
| **Memory** | Shared team memory |

## What it does

1. **Implements to the ADRs and `standards.md`**: API style, versioning, error
   shape, schema source, migration tool, and the observability baseline.
2. **Secure by default**: parameterized queries, input validation, least
   privilege, secrets from a vault, and explicit error handling.
3. **Tests the acceptance conditions** of the requirements its code serves.
4. **Reuses before it writes.** It searches the repo for an existing helper
   first and adds no speculative layers. It batches queries instead of making
   one per row, indexes the columns it filters on, and paginates unbounded
   reads.
5. **Proves each requirement it closes formally**: the check at its signed
   level, a vacuity run that failed as it should, and the evidence file in
   `formal/`, alongside the live evidence. It never edits a signed property and
   ships no escape hatch (`sorry`, `admit`, `assume`).

## What it will not do

- Diverge from an ADR or a standard without saying so. It flags the problem to
  the architect, or gets the standard re-signed.
- Hardcode a secret.
- Build on fake data. No mock, stub, seed or illustrative data in production
  code. If a service or credential is missing, it reports BLOCKED and names it.
- Report done on a red build.

## Where it sits

```
architect (design.md) ──▶ frontend ∥ backend ──▶ PRs ──▶ qa · security · auditor
```
