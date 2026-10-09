# Requirements — <project name>

> Signed intent contract, signed in the 🔴 intent batch. `check_tasks.py`
> re-hashes it at every step (TASKS.md `Signed:`).
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

Each requirement also carries a formal **property** — its acceptance, stated so
a machine can check it — a **formal level** and a **conformance** (see the
aidlc skill § *Formal verification*; `check_formal.py` is the sensor):
- `*Property*:` the formal statement. `none — <reason>` only where nothing can
  be stated formally (copy text, a visual); the CEO signs the reason.
- `*Formal*:` weakest first —
  - `tested` — generated-input or stateful property testing. SAMPLING: not a
    formal method, and named so.
  - `checked` — model checking of a design model, at bounds the evidence states.
  - `proved` — a machine-checked proof, unbounded.
- `*Conformance*:` how the code is tied to the property —
  - `none` — the property is checked against a model or tests only;
  - `trace` — real runs are logged and the checker accepts every trace as a
    behaviour of the model;
  - `refinement` — a proof that the code refines the model.
  A component `standards.md` marks load-bearing is at least `checked` with a
  conformance other than `none`.

- **R1** — WHEN <trigger>, the system SHALL <response>.
  - *Acceptance*: <observable, testable condition that proves R1 is met — on
    the real service, not "a contract test passes">
  - *Verify*: live
  - *Property*: <e.g. for every order, total = Σ line price × qty, never < 0>
  - *Formal*: tested
  - *Conformance*: none
- **R2** — WHILE <state>, the system SHALL <response>.
  - *Acceptance*:
  - *Verify*: live
  - *Property*: <e.g. □(paid ⇒ ◇ shipped ∨ refunded) — a load-bearing flow>
  - *Formal*: checked
  - *Conformance*: trace
- **R3** — WHERE <feature is included>, the system SHALL <response>.
  - *Acceptance*:
  - *Verify*: local — <why it touches no service or remote data>
  - *Property*: none — <why nothing here can be stated formally>
  - *Formal*: — (Property: none)
  - *Conformance*: none

## Non-functional requirements
- **N1** — Performance: <e.g. p95 < 200ms at 50 concurrent users>
  - *Acceptance*:
  - *Property*: none — <a measurement, proven live, not a formal property>
  - *Formal*: — (Property: none)
  - *Conformance*: none
- **N2** — Security / privacy:
  - *Acceptance*:
  - *Property*: <e.g. no request without a session reads another user's row>
  - *Formal*: checked
  - *Conformance*: trace
- **N3** — Accessibility: <e.g. WCAG 2.1 AA>
  - *Acceptance*:
  - *Property*: none — <audited live, not stated formally>
  - *Formal*: — (Property: none)
  - *Conformance*: none
- **N4** — Availability / reliability:
  - *Acceptance*:
  - *Property*: <e.g. a retry never sends a payment twice>
  - *Formal*: checked
  - *Conformance*: none

## Explicit non-goals
What this product deliberately does NOT do (guards against scope creep).

## Platform strategy (app / mobile targets only — signed in the 🔴 intent batch)
Omit this section for a pure web/backend/service target. For an app, fill it in
and get it signed in the intent batch, before Phase 1:
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

## Pre-authorized actions (what the run may do on its own)
Every irreversible or production action the run may take between batches, with
the condition under which it may. Signed in the intent batch. An action that is
not here does not stop the run: the role decides it and records a `Cn`
checkbox in TASKS.md for the CEO to tick at the next batch. List here what
must be confirmed up front.

| Action | Condition | Environment | Blast radius · reversible? |
|---|---|---|---|
| <e.g. deploy to production> | <every sensor green on pre-production, check_live --deployed on HEAD> | <production> | <all users · yes, rollback in 5 min> |

An empty table is a valid answer: then every such action is decided by the
role about to act and recorded as a `Cn` -- never a stop.

## Constraints & dependencies
Budget, timeline, external APIs needing approval, accounts, compliance.

## Open questions blocking design
Numbered. Each must be resolved before Phase 1 can finalize.
