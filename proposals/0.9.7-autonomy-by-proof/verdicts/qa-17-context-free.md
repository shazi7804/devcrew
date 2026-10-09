# QA verdict — final 8 (qa role, Claude, at 67b05bf)

```yaml
verdict: FAIL
commit: 67b05bf
contract: proposals/0.9.7-autonomy-by-proof/requirements.md (Signed sha256:8b6ddde1efc9, matches)
sensors:
  - {cmd: "python3 tools/check_neutral.py --self-test", result: "self-test ok"}
  - {cmd: "python3 tools/check_neutral.py", result: "neutral: ok"}
  - {cmd: "python3 framework/tools/check_live.py --self-test", result: "self-test ok (151 cases)"}
  - {cmd: "python3 framework/tools/check_formal.py --self-test", result: "self-test ok (51 cases)"}
  - {cmd: "python3 framework/tools/check_tasks.py --self-test", result: "self-test ok (56 cases)"}
  - {cmd: "python3 tools/check_repo.py", result: "repo: ok; exits 1 when SKILL.md's interrupts line or Aidlc.tla's Interrupts set is edited (R13 set comparison)"}
  - {cmd: "python3 tools/diagram.py check $(git ls-files '*.md')", result: "ALIGNED"}
  - {cmd: "python3 tools/check_models.py (openjdk 21, tla2tools 1.7.4, sha256 936a2620... matches the pin)", result: "models: ok in 8m34s. Election, ElectionLive, Aidlc, AidlcLive hold. ElectionV096, ElectionLiveBroken, ElectionOnceBroken, ElectionScanBroken, AidlcBroken, AidlcJudgmentBroken, AidlcLiveBroken fail as expected. 5 real boot.py traces accepted, 3 mutants rejected"}
  - {cmd: "check_tasks.py --tasks proposals/0.9.7-autonomy-by-proof/TASKS.md --allow tools/live-allow.txt", result: "tasks: ok"}
  - {cmd: "...same with --rerun", result: "tasks: ok (13m12s)"}
  - {cmd: "check_live.py --requirements proposals/0.9.7-autonomy-by-proof/requirements.md --allow tools/live-allow.txt [--rerun]", result: "live: ok / live: ok (5m12s)"}
  - {cmd: "check_formal.py --requirements proposals/0.9.7-autonomy-by-proof/requirements.md [--rerun]", result: "formal: ok / formal: ok (13m48s; R12, R13, R15 check + vacuity + conformance re-run)"}
  - {cmd: "shasum -a 256 framework/tools/check_live.py", result: "b2397d55...cc15ab, equals what the sensor prints (one copy, the framework's)"}
  - {cmd: "CI (checks.yml, models.yml)", result: "not observed; every step run locally, all green"}
coverage:
  - {req: R1, verify: local, formal: none, evidence: "tasks.template.md has the format. SKILL.md and ARCHITECTURE.md section 6 call TASKS.md the only ledger. Every live 'ledger' mention resolves to it (CHANGELOG history aside)", verdict: PASS}
  - {req: R2, verify: local, formal: none, evidence: "self-test: missing / duplicated / unknown ID fail, Dn and Cn pass", verdict: PASS}
  - {req: R3, verify: local, formal: none, evidence: "own toy-repo repros, plain and --rerun: a [x] with no formal evidence fails, a vacuity run that passes fails, stale evidence fails. Threat model probed on --rerun: an uncommitted change and a case-folded name are refused; an ignored file and an earlier probe's residue (tracked dir, nested repo, TMPDIR) are kept out; out-of-tree symlinks (data, formal source, code) are reported. In every case the re-run was as strict as the plain run or stricter", verdict: PASS}
  - {req: R4, verify: local, formal: none, evidence: "self-test asserts each listed reason, including 6/5 and requirements/standards drift; clean file has no hit", verdict: PASS}
  - {req: R5, verify: local, formal: none, evidence: "all three adapters name TASKS.md the ledger (a mirror may exist, TASKS.md wins). The 'NOT DEFINED' line is gone. Each adapter installs check_tasks.py and runs --self-test at verify", verdict: PASS}
  - {req: R6, verify: local, formal: none, evidence: "phase table names the batch for each gate. The former-gate table maps every 🔴 gate of main's SKILL.md. Batch = one SITREP + end turn", verdict: PASS}
  - {req: R7, verify: local, formal: none, evidence: "five interrupts, each with its sensor. Cn accepted in Todo/Done, refused in progress (self-test). orchestrator.md has the Cn rule", verdict: PASS}
  - {req: R8, verify: local, formal: none, evidence: "template table (action · condition · environment). Phase 5 IN + rule paragraph; release.md consults the list. JudgmentRecorded holds, AidlcJudgmentBroken violates it", verdict: PASS}
  - {req: R9, verify: local, formal: none, evidence: "Property/Formal/Conformance on all 7 example items plus definitions; standards.template.md Formal verification section", verdict: PASS}
  - {req: R10, verify: local, formal: none, evidence: "self-test ok, but a TLA+ AXIOM/ASSUME that shares a line with another unit passes the escape-hatch scan (blocker below)", verdict: FAIL}
  - {req: R11, verify: local, formal: none, evidence: "SKILL.md schema has the vacuity block. check_formal fails a missing vacuity run and one that passed (self-test + own repro)", verdict: PASS}
  - {req: R12, verify: local, formal: checked, evidence: "every listed property holds at its cfg bounds, fairness written in Aidlc.tla / Election.tla. Seeded broken variants yield counterexamples. formal/R12.json re-ran green", verdict: PASS}
  - {req: R13, verify: local, formal: "checked / trace", evidence: "5 sampled boot.py runs accepted, 3 mutants rejected. check_repo fails on a set difference (own edit)", verdict: PASS}
  - {req: R14, verify: local, formal: none, evidence: "AGENTS.md invariant 11; reviewer.md invariants_checked [1..11]", verdict: PASS}
  - {req: R15, verify: local, formal: "checked / trace", evidence: "Election holds for the shipped boot.py; ElectionV096 (previous boot.py) violates AtMostOneActing. session-governance.md names A1-A5", verdict: PASS}
  - {req: N1, verify: local, formal: none, evidence: "R6 table complete; invariants 1-11 intact; the removed judgment stops are covered by the CEO's recorded second ruling", verdict: PASS}
  - {req: N2, verify: local, formal: none, evidence: "invariant 10 byte-identical to 0.9.6 (49d78dd). check_tasks needs both live and formal (own repro)", verdict: PASS}
  - {req: N3, verify: local, formal: none, evidence: "check_tasks/check_formal import only stdlib plus the sibling sensors; check_neutral ok; tla2tools 1.7.4 pinned by sha256", verdict: PASS}
  - {req: N4, verify: local, formal: none, evidence: "auditor verdict PASS-WITH-DEBT, with no blocker/high", verdict: PASS}
blockers:
  - requirement: R10
    clause: "SHALL fail a requirement ... whose spec/proof sources hold an escape hatch -- a proof that is not a proof (`axiom`, `assume`, ... and their kin)"
    problem: >
      The .tla rule matches only at the start of a line: r"^\s*(AXIOM|ASSUME|ASSUMPTION)\b".
      TLA+ lets several units share a line, so `CONSTANT N  ASSUME N = 1` and
      `VARIABLE x  AXIOM Cheat == N = 2` parse in SANY. TLC also reports "No
      error has been found", even though the axiom contradicts the assumption.
      check_formal passes both, plain and --rerun, and check_tasks does too,
      plain and --rerun. So C18's TLA+ fix can be beaten by moving the
      keyword off column 0. The Coq rule (Axiom/Parameter/Hypothesis) uses
      the same anchor, and Coq sentences end in '.', so
      `Lemma l : True. Proof. exact I. Qed. Axiom bad : False.` is a single
      valid line. That case was not run here (no coqc). Loop back to Phase 3:
      match the keyword at any token boundary (keeping TLA+'s
      THEOREM ASSUME ... PROVE form legal), and add self-test cases with the
      keyword mid-line.
    repro: >
      In a toy git repo, commit spec/M.tla containing
      "---- MODULE M ----", "EXTENDS Naturals", "CONSTANT N  ASSUME N = 1",
      "VARIABLE x  AXIOM Cheat == N = 2", "Init == x = 0", "Next == x' = x",
      "Spec == Init /\ [][Next]_x", "====".
      `java -cp tla2tools.jar tla2sany.SANY M.tla` parses it.
      `tlc2.TLC` with "CONSTANT N = 1 / SPECIFICATION Spec" reports no error.
      Add a requirement R2 (Property text, Formal tested, Conformance none)
      whose req/formal/R2.json lists spec/M.tla in `sources`, with a passing
      check and a failing vacuity run, and mark it [x] in TASKS.md.
      check_formal.py --requirements req/requirements.md [--rerun] gives
      "formal: ok". check_tasks.py --tasks req/TASKS.md [--rerun] gives
      "tasks: ok". Put the same ASSUME on its own line and the sensor reports
      "escape hatch in M.tla:4".
debts:
  - "R10 kin not covered: Quint's `assume` declaration in a .qnt source (Quint is one of the candidate tools the contract's non-goals name); Lean `sorryAx`; Verus `#[verifier::external]`; Isabelle `axioms`; Agda `postulate`. Only `assume(false)` is caught for file types the map lacks. Worth handling in the same fix"
  - "check_formal.py --requirements <a directory> dies with an IsADirectoryError traceback, not a message"
notes:
  - "R8: Phase 6's own SKILL.md block does not name the pre-authorized list. Phase 5's rule paragraph covers every high-risk action, release.md consults the list, and Phase 6's irreversible steps are in the ship batch. Met, thinly (as in earlier rounds)"
  - "R3 Threat model, 'never pass what the plain run fails': check_live --rerun accepts a stale local item whose re-run at HEAD is green, while the plain run fails it as stale. check_formal --rerun still reports stale. I read the re-run as stronger proof, not weaker. The asymmetry should still be stated"
  - "N4: the auditor's verdict is at 5757e95; e830d78 (16 files, +130/-20) came later. N1: the reviewer's last round returned five blockers, which e830d78 fixes. Both need one round on the final tree, which is the next step TASKS.md names (C18)"
  - "CI was not observed. Every CI step was run locally at 67b05bf"
```

Retrospective: every sensor is green at 67b05bf, and the threat-model accidents I tried were all kept out of the re-run. The one gap is the escape-hatch regexes: they are anchored to the start of a line, which works for Lean but not for languages that put several statements on one line (TLA+, Coq). A hatch scan needs self-test cases with the keyword mid-line, not only at column 0.
