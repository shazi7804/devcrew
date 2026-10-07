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
> Status: DRAFT | SIGNED (CEO, design batch) — <date>   ·   its hash goes on
> TASKS.md's `Signed:` line, re-checked by `check_tasks.py`

## Deploy / environments
The deploy topology is a PROJECT decision, never a framework default. Define each
environment and how it is reached:
- **Environments**: e.g. local / dev / staging / prod — list the ones this
  product actually has.
- **Target per env**: cloud/provider/region OR on-prem OR hybrid (e.g.
  prod = a GCP region / on-prem k8s / an AWS account — whatever THIS product is).
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

## Real data & integrations (no fakes)
What `check_live.py` (the live sensor, Phases 3–5) reads. The framework rule is
fixed: no fake data in delivered work, and no `Rn` passes on a fake. This
section only says WHERE, for this product:
- **Production paths** (`--src`) — the source the fake scan covers, e.g. the
  app, the services, the web client. Everything shipped must be listed.
- **Extra test paths** (`--test`) — globs where test doubles may live, beyond
  the defaults (`tests/`, `__tests__/`, `fixtures/`, `*.test.*`, `*.stories.*`,
  …). A test double tests logic in isolation; it is never the evidence that an
  `Rn` is met.
- **Environments** (`--env` + `--live-host`) — the name and host globs of
  pre-production (Phases 3–4) and production (Phase 5), from § *Deploy /
  environments*. Each keeps its own evidence; evidence from any other host is
  red; loopback, private and reserved-test addresses are never live.
- **Version probe per service, per environment** (`--deployed`, once per
  service) — the read-only command that asks the deployed service which
  commit it runs (e.g. `curl -fsS https://<host>/version`); it must name a
  live host of that environment. A service that answers proves the build it runs,
  not HEAD: a re-run counts as fresh proof, and is recorded, only when this
  output contains HEAD's sha.
- **Probes** (the evidence convention, not an option) — per service, the
  read-only command that proves it answers, the `expect` regex its response
  must match, and the environment variable its credential comes from. A
  credential is never written into an evidence file.
- **Allow file** (`--allow`) — the exemption list (`<path-glob> <regex> --
  <reason>`), for a word that is not a fake: a gRPC `…Stub` client class, a
  dev-dependency line such as `pytest-mock` in a manifest, a product feature
  named "demo". It is part of this signed file: changing it is changing the
  standards.

## Formal verification
What `check_formal.py` (Phases 3–4) and each requirement's `Formal:` level are
judged against. The framework fixes the rule — every `Rn` has a `Property:`,
its evidence has a vacuity run, no escape hatch, formal never replaces live.
This section says HOW, for this product:
- **Load-bearing components** — the parts whose requirements must be at least
  `checked` with conformance `trace` or `refinement` (e.g. payment state
  machine, permission checks, sync/replication, scheduling). Everything else
  may be `tested`.
- **Tool per level** — chosen by the architect at Phase 1 after a current web
  search (never from memory): the property-testing library (`tested`), the
  model checker (`checked`), the prover (`proved`), each with a pinned version.
- **Bounds** — the instance sizes each model is checked at (users, items,
  concurrent sessions) and why they are enough; a `checked` result holds at
  these bounds only.
- **Where specs and proofs live** — the paths (e.g. `spec/`, `proofs/`); these
  are the `sources` each evidence file names, and the escape-hatch scan covers.
- **Conformance** — for `trace`: how the code logs the steps the model names
  (an env-gated trace file, one record per atomic step, in real order) and the
  command that checks a trace against the model; for `refinement`: the proof
  and its tool.
- **Vacuity** — the seeded mutant or negated property each check is shown to
  fail on.

## Code quality & efficiency budget
What the `auditor` role (Phase 4) judges against. The framework only requires
that this section exist; the numbers are THIS product's. Fill them in with the
CEO — an unsigned number is one the auditor may not enforce.

- **Audit trigger** — when the efficiency audit runs at all. Framework defaults
  if you leave this alone, **two size triggers, either one fires**:
  **> 1000 changed lines** (added + removed, excluding lockfiles / generated /
  vendored) **OR > 20 changed files**. Both read straight off
  `git diff --shortstat`, so neither can be argued with. Ambiguity runs the audit.
  ⚠️ **A size floor cannot catch a small expensive change** — a one-line
  `<script src>`, a loop turned O(n²), one line added to `package.json`. Those are
  caught upstream (the implementer roles' reuse-first rule) and, for dependencies,
  by the **Security** floor, which has no size condition. **If this project wants
  the auditor on them too, add the trigger here** — e.g. *any new runtime
  dependency*, *touches ≥ 3 modules*, *alters deploy topology*, *scope is
  `greenfield`/`refactor`*. Those were framework defaults until 0.9.1; they are
  now opt-in per project, because a trigger the project did not choose gets
  argued away at the gate instead of respected.
- **Performance budget** — the numbers a change may not regress: p50/p95 latency
  per critical path, query count per request, cold start, frontend LCP/INP,
  bundle size ceiling. These are what a `hot-path` finding is measured against.
- **Running-cost ceiling** — expected $/month envelope and what may not grow
  silently: instance class, always-on vs on-demand, log/metric retention volume,
  egress, storage growth. If the product calls an LLM: tokens per user action and
  the caching expectation.
- **Dependency policy** — when a new runtime dependency is acceptable (size,
  maintenance, licence, does the platform already do it), and who approves one.
- **Duplication tolerance** — where copies are acceptable (e.g. across a
  deliberate service boundary) and where they are not, plus the canonical
  location of shared helpers so reuse has an address.
- **Blocking rule** — the default is: auditor `blocker`/`high` fails the Phase 4
  gate and loops back to implementation; `medium`/`low` are logged as tech debt.
  Change it here if this project wants stricter or advisory-only.

## Other product-specific standards
Anything else the whole team must follow as one source of truth (i18n, a11y
target, feature-flag policy, …).
