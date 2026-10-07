# QA verdict — round 1 (qa role, Claude, at e2baee9)

Ran every sensor and `check_tasks.py --rerun`; checked every acceptance by hand
and adversarially. Fixed since: design.md § 7 (stale evidence, the stripped
checker environment, local re-run freshness, Done-line hyphen, escape-hatch
kin, `none of …`, the table sync, CreateFail, the R12 Property). The
former-gate map was checked row by row against 49d78dd: 11 of 11 mapped.

```yaml
verdict: FAIL
scope: feature (framework)
sensors: {test: pass, live: fail, formal: pass, tasks: fail}
blockers:
  - {requirement: ALL Done, problem: "check_tasks --rerun red: evidence stale (a non-.md verdict committed after it); R12/13/15 probes lost the checker's environment", loop_back_to: implementation}
  - {requirement: R12, problem: "signed Property names LoopBounded; Aidlc.tla defines AtBoundNoProgress / BoundInterrupts instead", loop_back_to: implementation}
  - {requirement: R3, problem: "a Done status after a plain hyphen passes", loop_back_to: implementation}
  - {requirement: R10, problem: "private axiom, Coq Parameter/Hypothesis, Isabelle axiomatization missed; a Property starting 'none of' read as none", loop_back_to: implementation}
passed_by_hand: [R1, R2, R4, R5, R6, R7, R8, R9, R11, R13, R14, R15, N2, N3, N4]
weak_evidence:
  - "most prose items grep one heading; the acceptance rests on the hand check"
  - "a vacuity run is any failing command; nothing ties it to a mutant of the check"
  - "model has no create-failure step while the read is valid"
