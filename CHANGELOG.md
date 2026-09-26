# Changelog

## 0.8.1 — 2026-09-26
- **Closed a 0.7.0 gap: the standards layer was only half-installed.** That entry
  claimed "Implementation/QA/Release all read `standards.md`", but only
  `architect`, `devops`, and `reviewer` mentioned the contract — `frontend`,
  `backend`, `qa`, and `release` never did, so on a fresh install three of the
  four consumers would never open the file the CEO signed. Each now reads it with
  a role-specific clause naming the sections that bind it: frontend (naming, API
  call style, client observability, what may not be logged), backend (API contract
  style, schema source + migration tool, security/observability baselines), qa
  (re-checks the **standards hash** for drift and traces the `Nn` conditions that
  live in `standards.md` rather than `requirements.md`), release (environments +
  promotion path decide the channel, agreed rollback, compliance regimes drive the
  store declarations, observability gates a staged rollout). In all four, a
  divergence is a gate failure — the fix is to get the standard re-signed, not to
  deviate quietly.

## 0.8.0 — 2026-09-26
- **Third host: Mission Control** (`hosts/mission-control.md` +
  `hosts/aidlc-mission-control.skill.md`). On mc the JSON files are the bus, so
  the harness is realized as data: neutral `spawn` → tasks with `assignedTo` +
  `blockedBy`; 🔴 CEO gate → a **pending row in `decisions.json`** (nothing
  dispatches a task that has one, so the gate physically suspends the run);
  ledger → `missions.json` `taskHistory` + `loopDetection`; budgets →
  `daemon-config.json`; outward P5/P6 actions → Field Ops tasks with
  `approvalRequired`. The AIDLC protocol installs as a skill-library entry that
  is injected into every role prompt.
- **Three-layer wiring diagram** in the adapter: mc as the runtime (JSON bus, the
  `scheduler → dispatcher → prompt-builder → security → runner` chain), devcrew as
  the AIDLC flow on top, and the adapter in between shown as what it really is —
  half a one-time install transform (which source file becomes which host file),
  half a data convention that mc's own functions enforce. Every box is labelled with
  the real file/function, plus a second diagram for how board mode cuts the daemon
  out. Recorded there: the role prompt is assembled from `agents.json` +
  `skills-library.json` by `buildTaskPrompt()` — `.claude/commands/<id>/user.md` is
  a mirror read only by `buildScheduledPrompt()`, never the dispatch path; skill
  links resolve from both `agent.skillIds` and `skill.agentIds`; `task.notes` IS
  injected into the prompt, which is why the contract path and intent hash go there.
- **Two install modes, because mc has no per-project cwd.** The daemon pins
  `cwd` to the mc repo root and spawns a non-interactive `claude -p`, so when the
  live data dir belongs to another product repo the adapter installs **board
  mode**: mc is the CEO's board and the interactive session dispatches. Only when
  the mc repo itself is the workspace does the daemon run the roles.
- **Data-dir trap documented as Step 0**: the live directory is
  `MC_DATA_DIR` / `.mc-data-dir` / `<app root>/data`; the repo's
  `mission-control/data/` is seed data, and installing there silently changes
  nothing the running app sees.
- **Honest degradation recorded**: mc can only spawn the `claude` binary
  (`ALLOWED_BINARIES`) and has no per-agent model field, so the self-evolution
  reviewer's cross-vendor rule (invariant 4) cannot be met on that host. Per
  ARCHITECTURE §7 the change is reviewed on KiroCrew or HELD unmerged with a
  pending decision — never silently self-approved.
- `AGENTS.md` host detection gains a Mission Control row plus a precedence rule
  (a mc workspace also has `.claude/`; install the mc way — the Claude Code
  artifacts are a subset).

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
