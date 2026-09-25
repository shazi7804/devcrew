# Changelog

## 0.7.0 — 2026-09-26
- **Standards layer (single source of truth)**: new `standards.md` contract
  (contracts/standards.template.md) produced WITH the CEO at Phase 1 and locked
  by a "standards hash" like the intent hash. It holds the per-project
  cross-cutting standards the whole team follows: deploy/environment targets, API
  contract style, DB schema source, compliance, naming, observability, security
  baseline. Implementation/QA/Release all read it; a divergence is a gate failure.
- **De-hardcoded deploy target**: removed "Local for test → AWS for production"
  from framework source (devops/reviewer/ARCHITECTURE/README/AGENTS invariant 6).
  The concrete env is the product's, defined in standards.md — the framework
  stores only the rule, not the cloud.

## 0.6.0 — 2026-09-25
Harness enhancements from a survey of recent AI-DLC / multi-agent guidance
(AWS AI-DLC methodology, GitHub multi-agent engineering, spec-drift research):
- **Scope routing**: Phase 0 classifies work (greenfield / feature / bugfix /
  hotfix / refactor / chore) into a `Scope:` field; a scope→phase table decides
  which phases run, so a typo fix no longer walks the full P0–P6 spine. Safety
  floors force a phase back in (ADR change→Architect, auth/data→Security,
  UI→Design) whatever the scope; skipped phases are logged, not dropped.
- **Structured verdict schemas** (`contracts/verdicts.template.md`): QA,
  Security, architecture-change review, self-evolution reviewer, and market
  analyst each end with a machine-checkable YAML verdict block. The orchestrator
  parses it to decide the gate; a missing/malformed block fails the gate.
- **Deterministic sensors**: every gate runs real lint/typecheck/test/build and
  dep/secret scans as commands FIRST (green before any LLM judgment), so
  "CI green" is observed output, not a claim.
- **Traceability**: PR/commit messages carry `Closes Rn`; QA builds a coverage
  table (requirement→PR→test) and the orchestrator keeps the map in the ledger.
  An Rn with no PR, or a PR claiming no Rn, is a gate failure — turning silent
  spec/code drift into a detectable one.

## 0.5.0 — 2026-09-25
- **Mobile AIDLC**: the pipeline now handles native/cross-platform apps, not just
  web/service targets. Added a 🔴 platform-strategy gate at Phase 0 (iOS/Android/
  both, min OS, native vs cross-platform — the concrete stack is per-project,
  never hardcoded in source). Design gains dual HIG + Material 3 guidance; Frontend,
  QA, and Security gain conditional mobile clauses.
- **New role `release` (Release Manager)**: owns each release's version,
  changelog, code signing (Apple certs/profiles, Android keystore), distribution
  channel (TestFlight / Play tracks / store submission), staged rollout, and
  rollback — distinct from DevOps (runtime). Pipeline split: Phase 5 Deploy
  (runtime) + Phase 6 Release (ship artifact). Store review is the true terminal
  state ("submitted" ≠ "released").
- **Architecture-change guard**: a mid-flight change to a signed ADR is
  re-reviewed by architect (llm-council for load-bearing reversals) and
  escalates to a 🔴 CEO/human gate when it crosses a signed boundary (breaks a
  requirement, changes platform strategy, or reverses a CEO-approved ADR).
  architect is now a standing guardian, not only a Phase-1 role.
- New skills: `mobile-build` (simulator/emulator build + screenshot, the mobile
  web-preview), `mobile-verify` (device/OS matrix, permissions, deep links,
  offline, mobile security — the mobile web-verify), `mobile-release` (signing,
  fastlane, tracks, submission, staged rollout — the mobile deploy-web).

## 0.4.0 — 2026-09-20
- Harness hardening: closed 11 AIDLC audit findings — loop bounds (3/5 fix-loop
  cap), budgets, CEO-gate suspension mechanism, intent hash (drift lock),
  contract schema checks, independent gate verification, security left-shift,
  reviewer availability fallback, retrospective capture.
- Added ARCHITECTURE.md (flow, harness layers, the three loops).
- New role analyst (Market Analyst): Phase 0.5 market-validation gate
  with live research, charts, and a GO/PIVOT/NO-GO verdict before build spend.

## 0.3.1 — 2026-09-19
- Reviewer vendor RULE (no hardcoded version in source): dev team = Anthropic, so
  reviewer runs the strongest OpenAI model currently available. The
  installer resolves this to a concrete model version at install time by querying
  the host's model catalog and pins that version into the generated agent
  artifact only. A future clone re-resolves to whatever is strongest then.

## 0.3.0 — 2026-09-19
- Removed the GitHub Action / Bedrock external-review path.
- Self-evolution review now happens INSIDE AIDLC via a new role, reviewer,
  dispatched on a DIFFERENT model family than the change's author and with no team
  memory mounted (unbiased). It never reviews its own change and never merges; the
  CEO makes the final merge.

## 0.2.0 — 2026-09-19
- Self-evolution is now reviewed by an INDEPENDENT external reviewer, not by
  devcrew itself: a GitHub Action (.github/workflows/framework-review.yml) runs
  a Bedrock model from a different family on every PR touching framework/, hosts/,
  or AGENTS.md, checks it against the design invariants, and posts a verdict.
- devcrew NEVER pushes main or self-merges framework changes; the CEO merges.
- Added docs/self-evolution-review.md (flow + one-time GitHub/OIDC/branch-protection setup).

## 0.1.0 — 2026-09-19
- Initial devcrew AIDLC team: orchestrator + 7 role agents (Architect, Design,
  Frontend, Backend, QA, Security, DevOps).
- AIDLC collaboration protocol (phases, gates, contract hand-offs, adversarial
  decision points, gated self-evolution).
- Host-neutral source under framework/ with KiroCrew and Claude Code adapters.
- Shared team memory (lessons, ADRs, retrospectives).
- AI-bootstrap install via AGENTS.md (no human-run installer).
