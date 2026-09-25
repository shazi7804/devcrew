# Changelog

## 0.5.0 — 2026-09-25

First release driven by **field use rather than audit**: everything here comes from
running 0.4.0 on a real project for several weeks and recording what actually broke.

- **Host capability contract** (SKILL.md): the protocol needs nine capabilities and
  no host has all nine. The installer now resolves each one against the real host
  *before Phase 0* and ships the result as a host-notes table. Replaces the former
  assumption that `spawn_run` / `ask_question` / `session_ledger_record` exist.
- **Degradation protocol**: generalizes the 0.4.0 reviewer fallback to every gate.
  Substitute, label `DEGRADED:` in the verdict, never claim the pass, never
  simulate the missing capability. Added as design invariants 7 and 8.
- **Mutation testing is now a Phase 4 requirement**: a green suite is a claim, not
  evidence. Every new assertion must be shown to go red when its target is broken.
  The first real mutation run on a live project scored 0/6 — both causes were in
  the tests. Includes the rules that stop a mutation pass from itself being fake
  (anchor must match exactly once; fail, don't crash; check reachability first).
- **Weak-assertion catalogue**: twelve assertion shapes that passed review and
  guarded nothing — count thresholds, substring matches, non-empty checks,
  unasserted round-trips, order-blind completeness checks, and others.
- **Concurrent sessions on one working tree**: git restore commands banned
  (`checkout`/`restore`/`stash`/`reset`), private build artifacts, and shared-baseline
  diffs are not gate evidence while another session is writing.
- **Frozen-zone discipline** (Phase 3): foundational files get extended, never
  edited, to satisfy a feature. Plus derived-values-are-functions and
  converge-duplicate-entry-points.
- **🔴 gate communication register**: prose, no requirement codes, exactly one
  question, then stop. A gate asking three questions gets answered on the easiest.
- **Resume ritual**: ledger → team memory → working tree, before any writing.
- `hosts/claude-code.md` rewritten with field notes from a real install, split into
  `[verified]` and `[unverified]` claims: hooks (use `Stop` not `PostToolUse`; exit
  2 + stderr to block; `stop_hook_active` or infinite loop), slash commands, plan
  mode, headless, and the `role:` frontmatter key being silently ignored.
- 18 lessons promoted into `framework/memory/lessons.md`, plus a **promotion filter**
  in that file's header: a lesson only belongs in the neutral layer if it survives
  being stripped of the stack it was learned on. Added because the first draft of
  this very batch arrived with front-end assumptions in the wording and review sent
  it back.
- **Mutation-testing procedure and the weak-assertion catalogue live in
  `devcrew-qa`, not in the shared skill.** They are one role's reference material;
  every role was paying context for them. SKILL.md keeps only the gate the
  orchestrator enforces ("no new assertion without a recorded red").
- Neutral-layer wording swept for host-specific tool names: the protocol now names
  capabilities (spawn, ask-human, durable ledger, memory write, resource check) and
  leaves tool names to the host adapter. Previously the capability table and the
  body of the same document contradicted each other.

### Review record
Reviewed by `devcrew-reviewer` → **REQUEST-CHANGES** (5 blockers, 3 major, 3 minor),
all addressed above except the invariant-ordering nit, which the reviewer itself
did not press and which would renumber invariants other files cite by number.

`DEGRADED: same-vendor cross-model review (author opus → reviewer sonnet), not
cross-vendor.` No cross-vendor credentials were available at review time. Per the
degradation protocol this gate is **recorded as degraded and does not count as
passed**; the reviewer flagged that the front-end-overreach judgements are exactly
the ones a different vendor's background would have judged better.

## 0.4.0 — 2026-09-20
- Harness hardening: closed 11 AIDLC audit findings — loop bounds (3/5 fix-loop
  cap), budgets, CEO-gate suspension mechanism, intent hash (drift lock),
  contract schema checks, independent gate verification, security left-shift,
  reviewer availability fallback, retrospective capture.
- Added ARCHITECTURE.md (flow, harness layers, the three loops).
- New role devcrew-analyst (Market Analyst): Phase 0.5 market-validation gate
  with live research, charts, and a GO/PIVOT/NO-GO verdict before build spend.

## 0.3.1 — 2026-09-19
- Reviewer vendor RULE (no hardcoded version in source): dev team = Anthropic, so
  devcrew-reviewer runs the strongest OpenAI model currently available. The
  installer resolves this to a concrete model version at install time by querying
  the host's model catalog and pins that version into the generated agent
  artifact only. A future clone re-resolves to whatever is strongest then.

## 0.3.0 — 2026-09-19
- Removed the GitHub Action / Bedrock external-review path.
- Self-evolution review now happens INSIDE AIDLC via a new role, devcrew-reviewer,
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
