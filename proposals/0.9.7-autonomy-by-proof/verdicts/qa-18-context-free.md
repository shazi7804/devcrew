# QA verdict — final 9 (qa role, Claude, at ca1433f)

Contract: `proposals/0.9.7-autonomy-by-proof/requirements.md`, sha256:8b6ddde1efc9,
matching TASKS.md's `Signed:` line. I judged the end state of the tree
(`main..ca1433f`) in a fresh clone of the repo. Every sensor and model check
was run in a clone of its own. I read `verdicts/` only after my own pass was
done, and used it only as a regression list.

```yaml
verdict: FAIL
commit: ca1433f
scope: feature (framework)
contract: proposals/0.9.7-autonomy-by-proof/requirements.md (Signed sha256:8b6ddde1efc9, matches)
sensors:
  lint: n/a
  typecheck: n/a
  test: pass        # the four self-tests below
  build: n/a
  live: pass        # check_live --rerun over all 19 items, --allow tools/live-allow.txt
  formal: pass      # check_formal --rerun
  tasks: pass       # check_tasks plain and --rerun
  commands:
    - {cmd: "python3 tools/check_neutral.py --self-test", result: "self-test ok"}
    - {cmd: "python3 tools/check_neutral.py", result: "neutral: ok"}
    - {cmd: "python3 framework/tools/check_live.py --self-test", result: "self-test ok (152 cases)"}
    - {cmd: "python3 framework/tools/check_formal.py --self-test", result: "self-test ok (55 cases)"}
    - {cmd: "python3 framework/tools/check_tasks.py --self-test", result: "self-test ok (56 cases)"}
    - {cmd: "python3 tools/check_repo.py", result: "repo: ok. It exits 1 when the interrupts line or the batches line in SKILL.md is edited away from Aidlc.tla's set"}
    - {cmd: "python3 tools/diagram.py check $(git ls-files '*.md')", result: "ALIGNED"}
    - {cmd: "python3 tools/check_models.py (openjdk 21, tla2tools 1.7.4, sha256 pinned)", result: "models: ok in 11m05s. Election, ElectionLive, Aidlc and AidlcLive hold. ElectionV096, ElectionLiveBroken, ElectionOnceBroken, ElectionScanBroken, AidlcBroken, AidlcJudgmentBroken and AidlcLiveBroken fail as expected. 5 real boot.py traces are accepted and 3 mutants rejected"}
    - {cmd: "python3 framework/tools/check_tasks.py --tasks proposals/0.9.7-autonomy-by-proof/TASKS.md --allow tools/live-allow.txt", result: "tasks: ok"}
    - {cmd: "... check_tasks.py ... --rerun", result: "tasks: ok (the clone stays clean, and no worktree is left behind)"}
    - {cmd: "python3 framework/tools/check_formal.py --requirements proposals/0.9.7-autonomy-by-proof/requirements.md [--rerun]", result: "formal: ok / formal: ok"}
    - {cmd: "python3 framework/tools/check_live.py --requirements proposals/0.9.7-autonomy-by-proof/requirements.md --allow tools/live-allow.txt --rerun", result: "live: ok. Every R/N Acceptance command was re-executed at HEAD"}
    - {cmd: "shasum -a 256 framework/tools/check_{live,formal,tasks}.py", result: "a6d7e97c..., 389d65a5..., 32c75b66... On this repo the framework copy is the copy that runs, and check_live's self-printed hash equals my own"}
requirements:
  - {id: R1, verdict: PASS, verify: local, formal: none, evidence: "tasks.template.md has the three sections, the header and the status forms. SKILL.md and ARCHITECTURE.md section 6 call TASKS.md the only ledger. Every remaining 'ledger' mention is TASKS.md or a host mirror of it"}
  - {id: R2, verify: local, formal: none, verdict: PASS, evidence: "self-test cases for a missing, a duplicated and an unknown ID. Dn passes in Todo. Cn passes in Todo and Done and is refused In progress"}
  - {id: R3, verify: local, formal: none, verdict: PASS, evidence: "My own toy repos (plain vs --rerun): a [x] without formal evidence fails, matching check_formal --only. A [x] with a status fails. Threat model, 19 accident scenarios: untracked helper, uncommitted edit, ignored file read by a probe, residue from an earlier probe (cwd file, ignored dir, nested repo, $TMPDIR file, background writer, chmod, tracked file turned into a symlink or a dir, same-size same-mtime edit, info/exclude), an out-of-tree symlink, and a case-folded name pair. Each one is refused or kept out. Each probe gets a fresh TMPDIR. An unwritable leftover fails loudly and leaves no worktree. In no scenario did the re-run pass what the plain run failed. HeadTree's docstring states the out-of-scope limit"}
  - {id: R4, verify: local, formal: none, verdict: PASS, evidence: "self-test asserts each listed reason (sections missing/out of order, bad status, bare blocked, IDs, [x] without evidence, [x] with status, requirements/standards drift, 6/5) and that a clean file has no hit"}
  - {id: R5, verify: local, formal: none, verdict: PASS, evidence: "All three adapters make TASKS.md the ledger. A mirror is allowed, and TASKS.md wins. The 'NOT DEFINED' line is gone. Each adapter installs check_tasks.py and runs its --self-test at verify"}
  - {id: R6, verify: local, formal: none, verdict: PASS, evidence: "The phase table names a batch for each gate. The 'Former 🔴 gate' table maps every 🔴 gate in main's SKILL.md (P0, platform, P0.5, P1 standards, P2, P6 signing, P6 submission, the ∞ proposal, ∞ merge, architecture escalation, high-risk action). Each batch is one SITREP that ends the turn"}
  - {id: R7, verify: local, formal: none, verdict: PASS, evidence: "SKILL.md lists exactly five interrupts, each with the sensor that raises it. check_tasks handles Cn as R2 says. orchestrator.md says a judgment becomes a Cn and is never a stop. The old budget stops and gate stops are gone from ARCHITECTURE.md section 4, the MC skill, analyst.md and mobile-release"}
  - {id: R8, verify: local, formal: none, verdict: PASS, evidence: "requirements.template.md has a Pre-authorized actions table (action, condition, environment, blast radius). SKILL.md Phase 5 consults it. JudgmentRecorded holds in Aidlc.cfg, and AidlcJudgmentBroken violates it"}
  - {id: R9, verify: local, formal: none, verdict: PASS, evidence: "Every example item in requirements.template.md has Property, Formal and Conformance lines, and the template defines them. standards.template.md has a Formal verification section (load-bearing components, tool per level, bounds)"}
  - {id: R10, verify: local, formal: none, verdict: FAIL, evidence: "The sensor catches every hatch R10 names, `admit` included (checked by hand). --rerun re-executes the check and the vacuity run. But the self-test has no case for `admit`; see blockers"}
  - {id: R11, verify: local, formal: none, verdict: PASS, evidence: "check_formal fails evidence with no vacuity run, or with one that passed (self-test). SKILL.md's schema has a vacuity entry; see notes"}
  - {id: R12, verify: local, formal: checked, verdict: PASS, evidence: "models.yml runs check_models.py with the pinned TLC. Every property in R12's Property holds at the stated bounds (3 sessions for safety, 2 for liveness, 2 items, 5/3). The fairness is written down (WF Agent; Election's WF/SF Fairness). Seeded broken variants yield counterexamples. formal/R12.json re-ran green"}
  - {id: R13, verify: local, formal: checked, verdict: PASS, evidence: "Scripted, stampede and 3 seeded concurrent boot.py traces are accepted by ElectionTrace. 3 mutants are rejected. check_repo fails on a mismatch between the SKILL.md sets and the Aidlc.tla sets (mutated both ways)"}
  - {id: R14, verify: local, formal: none, verdict: PASS, evidence: "AGENTS.md has invariant 11. reviewer.md has invariants_checked [1..11]"}
  - {id: R15, verify: local, formal: checked, verdict: PASS, evidence: "Election holds for the shipped boot.py. ElectionV096 (the previous boot.py) violates AtMostOneActing. session-governance.md states A1-A5 (timing, beat, stop-on-demotion, local FS, no permanent file-op failure)"}
  - {id: N1, verify: local, formal: none, verdict: PASS, evidence: "The R6 table is complete. Every removed stop is either a sensor-raised interrupt or a Cn under the CEO's recorded second ruling. I found no loosened gate, bound or trigger. Loop A is still 5/3 and is enforced"}
  - {id: N2, verify: local, formal: none, verdict: PASS, evidence: "Invariant 10's text is byte-identical to 0.9.6's. check_tasks runs both check_live and check_formal for every Done item"}
  - {id: N3, verify: local, formal: none, verdict: PASS, evidence: "AST import scan: check_tasks and check_formal import only the stdlib plus their sibling sensors. check_neutral passes. The TLC 1.7.4 jar is pinned by sha256 and runs headless"}
  - {id: N4, verify: local, formal: none, verdict: PASS, evidence: "The newest auditor verdict is PASS-WITH-DEBT with no blocker or high finding, so the Acceptance text is met; see debts"}
blockers:
  - requirement: R10
    clause: "Acceptance: `check_formal.py --self-test` exits 0, each case asserting the REASON: ... each escape hatch."
    problem: >
      R10 names `admit` as an escape hatch, but the self-test has no case for it.
      Its hatch cases cover sorry, axiom, Admitted, assume, {:axiom},
      external_body, OMITTED, AXIOM/ASSUME/ASSUMPTION and assume(False), and
      none of them is an `admit`. So the self-test cannot fail if `admit`
      detection breaks. The shipped detector does catch it today, so this is a
      missing proof, not a missing check. The fix is one self-test case per
      `admit` rule (.lean, .v, .rs `admit(`, .fst/.fsti). Loop back to Phase 3.
    repro: >
      Copy framework/tools/check_live.py and check_formal.py to a scratch dir.
      In the copy of check_formal.py, delete every `admit` pattern from HATCHES
      (the .lean, .v, .rs and .fst/.fsti entries). Run
      `python3 check_formal.py --self-test`: it prints "self-test ok (55 cases)"
      and exits 0. The unmodified hatches() still reports
      "theorem t : p := by admit" in a .lean file.
    loop_back_to: implementation
debts:
  - "N4: the newest audit is at 67b05bf. 01d1c3a (round 1 after C18; 29 files, +224/-57 outside proposals/) has not been audited. Re-audit before the ship batch."
  - "Constraints: this change edits reviewer.md, so the reviewer may not review it alone. No final-tree review by a second model family or by a council is recorded yet (TASKS R3 'next' and C3 say so)."
  - "R12/R13: CI's own runs of checks.yml and models.yml cannot be seen from here. Record CI's result and time (D2) before merge."
  - "Carried, not new: D1-D5, D9, D10 and D12-D26 as listed in TASKS.md."
notes:
  - "R3: check_live --rerun clears a stale `local` record by re-running it at HEAD, while check_formal --rerun still reports stale. So a re-run can pass a stale live record that the plain run fails. This is by design (the re-run is the proof, C8) and is not one of the accidents the Threat model lists. It is still worth a sentence beside 'never pass what the plain run fails'."
  - "R8: SKILL.md's Phase 6 section does not name the pre-authorized list itself. release.md and the mobile-release skill (Phase 6's procedure) do, and Phase 6's own irreversible actions are ship-batch items."
  - "R11: the vacuity entry in SKILL.md's schema describes the run in prose ('one run that MUST fail ... and did, printing its own expect'). The field names (command, expect, observed, result: fail) appear only in check_formal's docstring, which SKILL.md calls the full spec."
  - "R7: hosts/aidlc-mission-control.skill.md's architecture guard still says 'Escalate to a 🔴 CEO decision when the change crosses a signed boundary'. SKILL.md routes the same case through the superseding ADR and the `cross-design` interrupt. Align the wording."
  - "R1: orchestrator.md asks to 'record the measured diff size and which trigger fired in TASKS.md'. TASKS.md has no place for a record. Point it at the SITREP or the audit verdict instead."
  - "Regression list (verdicts/, read after my pass): the earlier blockers are fixed at ca1433f. These are: mid-line TLA+ and Coq hatches (now in the self-test), old gates in analyst.md, mobile-release and the adapters, and the budget stops in ARCHITECTURE.md section 4 and the MC skill. qa-16 recorded the missing `admit` case only as a debt, and TASKS.md never logged it."
```

Retrospective:
1. The re-run harness held against 19 accident scenarios. The weak spot was a gap in the self-test's coverage, not in the sensor's behaviour.
2. A mutation run (delete a rule, run the self-test) is what showed the gap. Reading the code alone would not have.
3. A debt that one QA round records but TASKS.md never logs gets lost. Every debt should become a Dn.
