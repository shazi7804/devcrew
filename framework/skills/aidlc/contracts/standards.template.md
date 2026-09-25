# Standards — <project name>

> The project's **single source of truth for cross-cutting standards**. Defined
> WITH the human (CEO) at Phase 1, alongside `design.md`. Every downstream phase
> — implementation, QA, release — reads THIS file and must follow it; a
> divergence is a gate failure, exactly like intent drift.
>
> NONE of these values live in the devcrew framework/skills. The framework only
> requires that this file be produced and signed; the concrete values are the
> product's, filled in here per project. Leave a section `N/A` (with a one-line
> why) rather than deleting it, so a reviewer sees it was considered.
>
> Status: DRAFT | SIGNED (CEO) — <date>   ·   Standards hash: <recorded at sign-off>

## Deploy / environments
The deploy topology is a PROJECT decision, never a framework default. Define each
environment and how it is reached:
- **Environments**: e.g. local / dev / staging / prod — list the ones this
  product actually has.
- **Target per env**: cloud/provider/region OR on-prem OR hybrid (e.g.
  prod = GCP asia-east1 / on-prem k8s / AWS us-east-1 — whatever THIS product is).
- **Promotion path**: how a build moves local → … → prod, and who approves each.
- **Rollback**: how each env rolls back.
- *This replaces any hardcoded "Local → AWS prod" assumption.* DevOps (Phase 5)
  and Release (Phase 6) deploy to exactly what is written here.

## API contract standard
- Style (REST / gRPC / GraphQL), versioning scheme, error-response shape,
  auth mechanism, and where the canonical API spec lives (OpenAPI file, proto, …).
- The API spec file (if any) is the source of truth FE and BE both build against.

## Data / DB schema
- Datastore(s) and where the canonical schema / migrations live.
- Migration policy (who owns it, forward-only?, review required?).
- Data classification (PII / sensitive) tie-in to compliance below.

## Compliance & privacy
- Regimes that apply (GDPR / HIPAA / PCI / SOC2 / app-store privacy / none) and
  the concrete obligations each imposes on this product.
- Data residency / retention requirements.

## Naming & code conventions
- Repo/branch/commit conventions (e.g. the `Closes Rn` traceability marker),
  language style guides, lint/format config location.

## Observability standard
- Required logs / metrics / traces, log format, alerting destinations, the SLOs
  a release is measured against.

## Security baseline
- Secret management (vault/manager), TLS/cert policy, dependency-pinning policy,
  authn/authz model. Ties into the Phase-1 threat model and Phase-4 Security gate.

## Other product-specific standards
Anything else the whole team must follow as one source of truth (i18n, a11y
target, performance budget, feature-flag policy, …).
