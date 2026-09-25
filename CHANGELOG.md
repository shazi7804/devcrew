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

- **The cross-vendor reviewer gate now has no fallback: it HOLDs.** 0.4.0 said
  "degrade to same-vendor-different-model". That sentence was read as permission by
  every later session on a host with no second vendor, and produced eleven ledger
  entries labelled `DEGRADED:` that were not reviews. A same-vendor model is not a
  weaker cross-vendor reviewer — the gate's whole power is the vendor difference, so
  two models from one vendor share exactly the blind spot being looked for.
  Same-vendor may run as *pre-review*; it does not close the gate. Generalized into
  degradation rule 1 and invariant 8: before accepting a substitute, name the
  property the gate's power comes from and check the substitute has it.

### Review record
**Cross-vendor, actually executed** (`us.deepseek.r1-v1:0` via Bedrock, no team
memory mounted, author was Claude Opus 5) → **REQUEST-CHANGES**, 1 major: the
degradation protocol still permitted same-vendor review for the self-evolution gate,
failing invariant 3. That finding is addressed by the entry above — the reviewer
caught the draft shipping upstream the exact rule the downstream project had just
removed. A second cross-vendor reviewer (`us.amazon.nova-pro-v1:0`) returned
REQUEST-CHANGES with five findings, all of the form "the wording could be
strengthened" and none naming a concrete defect; recorded for completeness, not
acted on.

Before that: same-vendor pre-review (Opus 5 → Sonnet) → REQUEST-CHANGES, 11
findings, 10 addressed. The declined one was an invariant-ordering nit that would
renumber invariants other files cite by number. **That pass is recorded as
pre-review, not as the gate** — which is the rule this release adds.

Merge decision belongs to the CEO. `main` is untouched.

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
