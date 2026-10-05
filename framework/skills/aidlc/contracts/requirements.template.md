# Requirements — <project name>

> Signed intent contract. Every downstream gate re-reads this file.
> Status: DRAFT | SIGNED (CEO) — <date>
> Scope: greenfield | feature | bugfix | hotfix | refactor | chore | docs
>   (decides which phases run — see the aidlc skill's scope-routing table;
>    Phase 5/6 are target-aware, and safety floors force Architecture/Security/
>    Design back in regardless of scope)

## Vision (one paragraph)
What this product is, for whom, and the single core outcome it must deliver.

## Users & context
- Primary user:
- Secondary users:
- Where/how it is used:

## Functional requirements (EARS)
Use EARS phrasing. Each requirement has an ID, an explicit acceptance condition,
and a verification level. There is no level that accepts a fake (see the aidlc
skill § *No fake data*):
- `live` — the DEFAULT, and what a missing line means. Proven against the real,
  deployed service and real data it depends on.
- `local` — only for a requirement that touches NO external service and NO
  remote data (layout, an on-device computation). Proven on the real runtime
  with real input. Say why in one clause; the CEO signs the level with the rest.

- **R1** — WHEN <trigger>, the system SHALL <response>.
  - *Acceptance*: <observable, testable condition that proves R1 is met — on
    the real service, not "a contract test passes">
  - *Verify*: live
- **R2** — WHILE <state>, the system SHALL <response>.
  - *Acceptance*:
  - *Verify*: live
- **R3** — WHERE <feature is included>, the system SHALL <response>.
  - *Acceptance*:
  - *Verify*: local — <why it touches no service or remote data>

## Non-functional requirements
- **N1** — Performance: <e.g. p95 < 200ms at 50 concurrent users>
  - *Acceptance*:
- **N2** — Security / privacy:
  - *Acceptance*:
- **N3** — Accessibility: <e.g. WCAG 2.1 AA>
  - *Acceptance*:
- **N4** — Availability / reliability:
  - *Acceptance*:

## Explicit non-goals
What this product deliberately does NOT do (guards against scope creep).

## Platform strategy (app / mobile targets only — a 🔴 CEO-signed Phase-0 decision)
Omit this section for a pure web/backend/service target. For an app, fill it in
and get it signed before Phase 1:
- **Platforms**: iOS only / Android only / both / + web?
- **Minimum supported OS**: iOS __ / Android API __
- **Build strategy**: native (Swift + Kotlin) / Flutter / React Native / KMP —
  and the one-line reason (the Architect proposes via llm-council; CEO signs).
- **Store presence**: App Store / Play / both; distribution = public store /
  enterprise / internal test only.
- **Monetization affecting the build**: IAP / subscriptions / paid up-front /
  none.
  - *Acceptance*: the platform matrix above is decided and CEO-signed; every
    later phase builds only for these platforms/OS versions.

## Real services & data (every one this product talks to)
One row per external service, API, datastore or data feed, so nobody discovers
at Phase 4 that it was never connected:

| Service / data | Used by | Account + credential owner | Exists today? |
|---|---|---|---|
| <e.g. weather API> | R2 | <who provides the key> | yes / no — <what is missing> |

A credential or service that does not exist yet is an **open question blocking
design** (below), answered by the CEO — never a reason to build on a fake.

## Constraints & dependencies
Budget, timeline, external APIs needing approval, accounts, compliance.

## Open questions blocking design
Numbered. Each must be resolved before Phase 1 can finalize.
