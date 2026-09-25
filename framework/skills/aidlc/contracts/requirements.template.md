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
Use EARS phrasing. Each requirement has an ID and an explicit acceptance condition.

- **R1** — WHEN <trigger>, the system SHALL <response>.
  - *Acceptance*: <observable, testable condition that proves R1 is met>
- **R2** — WHILE <state>, the system SHALL <response>.
  - *Acceptance*:
- **R3** — WHERE <feature is included>, the system SHALL <response>.
  - *Acceptance*:

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

## Constraints & dependencies
Budget, timeline, external APIs needing approval, accounts, compliance.

## Open questions blocking design
Numbered. Each must be resolved before Phase 1 can finalize.
