# Requirements — devcrew 0.9.5: award-grade design, readable docs, host neutrality

> Signed intent contract for a change to devcrew's own framework. Every gate of
> this change re-reads this file.
> Status: SIGNED (CEO) — 2026-10-01 · R4 amended by the CEO on the same day
> Scope: feature (framework: `framework/` · `hosts/` · `AGENTS.md` · docs)

## Vision
Four goals. The designer reaches award-grade quality on its own. A newcomer can
understand and run devcrew from the README, in English or Traditional Chinese.
The framework carries no host's tool names and no machine's facts. A framework
change goes through the same intent gate as product work.

## Users & context
- Primary user: the CEO, who installs devcrew and runs it.
- Secondary users: every role agent reading `framework/`, and every host adapter.

## Functional requirements (EARS)

- **R1** — WHEN `designer` produces a prototype, it SHALL iterate with the
  `impeccable` skill until the prototype meets the award-grade bar (Awwwards
  rubric, Webby/FWA vetoes, `impeccable detect` exit 0), or SHALL stop on a
  plateau and report the gap.
  - *Acceptance*: `designer.md` and SKILL.md Phase 2 state the rubric, the exit
    condition, the plateau stop and the `design-scorecard.md` output. Both host
    adapters say how to install impeccable.
- **R2** — The README SHALL include, in order: setup steps, "talk to your
  orchestrator naturally", an architecture diagram, the team table, native
  skills (with links where they exist), see it work, docs, and license.
  - *Acceptance*: every section is present, and every relative link resolves.
- **R3** — The README SHALL link each of the 12 agents to its own page under
  `docs/agents/`.
  - *Acceptance*: 12 pages exist, and each one links back to its source prompt.
- **R4** — "See it work" SHALL show how a user uses devcrew. Any output it
  shows SHALL be real output from a command that was actually run.
  - *Acceptance*: the section invents no run, number or result. Each output
    block names the command that produced it.
  - *Amended*: the first draft required a full demo run. The CEO ruled that no
    site should be built or deployed; the section only has to show how to use
    devcrew.
- **R5** — A Traditional Chinese README SHALL exist, and each README SHALL link
  to the other at the top.
  - *Acceptance*: `README.zh-TW.md` exists, and both files carry the language
    switch.
- **R6** — `framework/`, `ARCHITECTURE.md` and `docs/` SHALL name no
  host-specific tool and no specific machine. Host tool names SHALL appear only
  in `hosts/<host>.md`, which maps neutral terms to them.
  - *Acceptance*: `tools/check_neutral.py` exits 0 on the repo, and exits
    non-zero on a fixture that contains `spawn_run` or `128GB EC2`.
- **R7** — The design invariants SHALL include host/deployment neutrality as
  invariant 9, and `reviewer` SHALL check it.
  - *Acceptance*: `AGENTS.md` lists invariant 9, and `reviewer.md` checks it.
- **R8** — WHEN a retro or the CEO proposes a framework change, the orchestrator
  SHALL first write a `proposals/<slug>/requirements.md` and get it
  CEO-signed. `qa` SHALL verify the change against it, `reviewer` SHALL check
  the invariants, and the CEO SHALL merge.
  - *Acceptance*: SKILL.md Phase ∞, `orchestrator.md`, `qa.md`, the Claude Code
    `CLAUDE.md` template and ARCHITECTURE all describe the same path, and no
    file still says "PR + QA gate" without Phase 0.
- **R9** — Every framework PR SHALL run deterministic CI (neutrality check, link
  check, agent frontmatter parse) before review.
  - *Acceptance*: a GitHub Actions workflow runs these checks and fails on a
    violation.
- **R10** — The repo SHALL be MIT licensed.
  - *Acceptance*: a `LICENSE` file exists, and the README links to it.

## Non-functional requirements
- **N1** — No weakened gate: this change removes no approval gate, trigger or
  permission boundary.
  - *Acceptance*: the reviewer checks invariants 1–9 and finds no loosening.

## Explicit non-goals
- No new role.
- No change to the magnitude-floor thresholds.
- No per-agent Chinese pages. The agent pages stay in English.

## Constraints & dependencies
- Claude Code offers only Anthropic models, so a cross-vendor `reviewer` cannot
  run here. Per SKILL.md, the fallback is an `llm-council` across ≥2 distinct
  models (marked degraded); failing that, the change is held until a
  different-vendor review can run, or the CEO decides.
- **CEO decision (2026-10-01), for this change only:** the reviewer runs on a
  stronger model of the same vendor. The author was Opus; the reviewer is
  Fable. Reason given: no other vendor's model is available, and the CEO
  prefers a stronger independent reviewer over holding the change. It is
  recorded here under invariant 8. It is NOT a new default. The rule in
  `SKILL.md` (a different vendor; else a ≥2-model council, degraded; else
  hold) is unchanged, and the reviewer's
  verdict must say that it ran degraded.
- **What actually ran:** Fable was not callable on this account (API 400:
  "data retention mode 'default' is not available for this model"). The
  review therefore fell back to the `SKILL.md` path for ≥2 distinct models: an
  adversarial council of two independent reviewers, on Opus 5.5 and Sonnet 4.5.
  Neither mounts team memory, and neither reads the other's verdict. It is
  degraded twice over: same vendor, and one of the two models (Opus 5.5) is
  the author's own. Opus returned REQUEST-CHANGES (fixed in the same PR);
  Sonnet returned APPROVE.

## Open questions blocking design
None.
