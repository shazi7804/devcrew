# QA verdict — round 2 (qa role, Claude, at 204ddb1)

Ran every sensor at 204ddb1 in a clean clone (a clean clone). While this
round ran, another session edited the shared working tree (uncommitted changes to
check_formal.py and check_live.py, 12:49–12:52), and that made the first in-place
`--rerun` go red with R13/R15 "stale". That red was a contaminated tree, not this
change. Against clean HEAD the result is: every self-test passes,
`check_tasks --rerun` passes, `check_models.py` passes (8 models plus 5 real
traces and 3 mutants), the 32-way election race gives 1 orchestrator and the
20-way takeover race gives 1 winner.

I probed the three commits nobody had QA'd yet:
- **1506e43** holds. With no Java, a stub Java, a wrong jar or a missing jar,
  every single-check mode exits 2 (no verdict). A Java that passes `-version`
  but has TLC fail also gives exit 2, never "rejected". R13's vacuity shell then
  exits 0, so the vacuity is correctly not satisfied.
- **73271d7** fixes the false positive: a Done title with " · " is no longer
  taken as a status. But it went narrower than it had to and lets through
  status leftovers that the previous rule caught.
- **bf8cb1b** is correct in SKILL.md, orchestrator.md, devops.md and release.md.
  It misses one sentence in requirements.template.md, and that sentence
  contradicts R8. `JudgmentRecorded` does fail TLC when the record is dropped,
  and also when its condition is flipped.

```yaml
verdict: FAIL
scope: feature (framework)
sensors: {test: pass, live: pass, formal: pass, tasks: pass, models: pass, neutral: pass, repo: pass, diagrams: pass, race: pass}
blockers:
  - {requirement: R8, problem: "framework/skills/aidlc/contracts/requirements.template.md:128 still reads 'An empty table is a valid answer: then every such action stops the run.' That is the pre-bf8cb1b rule. R8 says an action not on the list is decided and recorded as a Cn, never a stop, and R7 allows no stop between batches except the five interrupts. Every project's Phase 0 is written from this template.", loop_back_to: implementation}
  - {requirement: R3, problem: "73271d7 narrowed the Done-status rule so that it now needs a single [-—–] dash right before the status word, or 'n/m stalled', or 'next:'. Done lines '- [x] R1 x -- verifying' (the ASCII double hyphen this codebase uses for a dash), '- [x] R1 x · verifying · qa' and '- [x] R1 x · qa · 2/5' now pass. The pre-73271d7 rule flagged all three. This is the round-1 hyphen blocker again, one character away.", loop_back_to: implementation}
passed_by_hand: [R1, R2, R4, R5, R6, R7, R9, R10, R11, R12, R13, R14, R15, N1, N2, N3, N4]
probes:
  - "check_models --holds/--accepts/--models/--trace, run with --java /usr/bin/java (macOS stub) or /nonexistent/java: exit 2 'no Java runtime ... no verdict'"
  - "a fake java that passes -version but has TLC fail: --holds -> 2, --accepts mutant|skip-gen|real -> 2 'no verdict: error: ...'; full mode -> 1 with 16 failures (fail-closed)"
  - "missing jar -> 2; wrong-sha jar -> 2"
  - "R13 vacuity '--accepts mutant; [ $? -ne 1 ]' with no java -> exit 0 (vacuity correctly NOT satisfied)"
  - "Aidlc.tla: review' = review -> 'Invariant JudgmentRecorded is violated'; ~preauth flipped to preauth -> violated again"
  - "check_tasks: 'Property · Formal · Conformance' in Done -> clean; Cn in progress -> hit; Cn duplicated -> hit; [ ] C in Done / [x] C in Todo -> hit"
weak_evidence:
  - "JudgmentRecorded's must-fail run is not a seeded CI variant (AidlcBroken targets NoPhasePastUnsignedBatch only), so CI never shows that this invariant can fail; only this hand probe does"
  - "R12 vacuity 'holds ElectionV096 || holds Aidlc:AidlcBroken' passes if ElectionV096 errors (exit 2) and AidlcBroken is violated; only the --models check covers ElectionV096"
  - "check_models full mode prints 'REJECTED (error: ...)' for a real trace that errored, though its FAIL line says 'no verdict' (cosmetic)"
  - "check_tasks false positive: '- [x] R1 build - fixing the parser' is refused as a status"
  - "check_tasks.py docstring repeats the '- [ ] D1 split the 900-line handler' example line"
  - "the shared working tree has uncommitted edits from a concurrent session; a --rerun there reports stale evidence that is not this change's fault"
```
