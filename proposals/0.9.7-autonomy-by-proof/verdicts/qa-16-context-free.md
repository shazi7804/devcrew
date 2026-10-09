# QA verdict — final 7 (qa role, Claude, at fe47490)

```yaml
verdict: FAIL
commit: fe47490
contract: proposals/0.9.7-autonomy-by-proof/requirements.md (Signed sha256:8b6ddde1efc9, matches)
sensors:
  - {cmd: "python3 tools/check_neutral.py --self-test", result: "self-test ok"}
  - {cmd: "python3 tools/check_neutral.py", result: "neutral: ok"}
  - {cmd: "python3 framework/tools/check_live.py --self-test", result: "self-test ok (151 cases)"}
  - {cmd: "python3 framework/tools/check_formal.py --self-test", result: "self-test ok (47 cases)"}
  - {cmd: "python3 framework/tools/check_tasks.py --self-test", result: "self-test ok (54 cases)"}
  - {cmd: "python3 tools/check_repo.py", result: "repo: ok; also exits 1 when SKILL.md's interrupts or batches line is edited away from Aidlc.tla's set"}
  - {cmd: "python3 tools/diagram.py check $(git ls-files '*.md')", result: "ALIGNED"}
  - {cmd: "python3 tools/check_models.py (JAVA=openjdk 21, tla2tools 1.7.4, sha256 pinned)", result: "models: ok in 5m07s -- Election, ElectionLive, Aidlc, AidlcLive hold; ElectionV096, ElectionLiveBroken, ElectionOnceBroken, AidlcBroken, AidlcJudgmentBroken, AidlcLiveBroken fail as expected; 5 real boot.py traces accepted; 3 mutants rejected"}
  - {cmd: "check_tasks.py --tasks proposals/0.9.7-autonomy-by-proof/TASKS.md --allow tools/live-allow.txt", result: "tasks: ok"}
  - {cmd: "...same --rerun", result: "tasks: ok (10m15s)"}
  - {cmd: "check_live.py --requirements proposals/0.9.7-autonomy-by-proof/requirements.md --allow tools/live-allow.txt [--rerun]", result: "live: ok / live: ok -- every Acceptance's recorded command re-ran green in a HEAD checkout"}
  - {cmd: "check_formal.py --requirements proposals/0.9.7-autonomy-by-proof/requirements.md [--rerun]", result: "formal: ok / formal: ok (R12, R13, R15 checks + vacuity + conformance re-run)"}
  - {cmd: "shasum -a 256 framework/tools/check_live.py", result: "b2397d55...cc15ab, equals what the copy prints (one copy: the framework's)"}
  - {cmd: "CI (checks.yml, models.yml)", result: "not observed -- no CI run readable from here; every step run locally, green"}
coverage:
  - {req: R1, verify: local, formal: none, evidence: "tasks.template.md format; SKILL.md 'Keep TASKS.md -- the run's only ledger'; ARCHITECTURE.md section 6 'the only ledger'; every 'the ledger' mention resolves to TASKS.md", verdict: PASS}
  - {req: R2, verify: local, formal: none, evidence: "self-test: missing / duplicated / unknown ID fail; Dn and Cn pass", verdict: PASS}
  - {req: R3, verify: local, formal: none, evidence: "self-test + own repros: a [x] with no formal evidence, a stale sha, a failing probe, a vacuity run that no longer fails each fail plain and --rerun; threat model probed: untracked/ignored/tracked residue of an earlier probe, TMPDIR per probe, a background child, an ignored file in the root, HEAD moving mid-run -- all kept out", verdict: PASS}
  - {req: R4, verify: local, formal: none, evidence: "self-test asserts each listed reason incl. 6/5, requirements/standards drift", verdict: PASS}
  - {req: R5, verify: local, formal: none, evidence: "three adapters name TASKS.md the ledger (mirror, TASKS.md wins); NOT DEFINED gone; each installs check_tasks.py and runs --self-test at verify", verdict: PASS}
  - {req: R6, verify: local, formal: none, evidence: "phase table names each batch; Former-gate table maps every 🔴 gate of main's SKILL.md", verdict: PASS}
  - {req: R7, verify: local, formal: none, evidence: "five interrupts with their sensors; Cn in Todo/Done accepted, in progress refused; orchestrator.md Cn rule", verdict: PASS}
  - {req: R8, verify: local, formal: none, evidence: "template table; Phase 5 IN + rule; JudgmentRecorded holds, AidlcJudgmentBroken fails", verdict: PASS}
  - {req: R9, verify: local, formal: none, evidence: "Property/Formal/Conformance on all 7 example items + definitions; standards.template Formal verification section", verdict: PASS}
  - {req: R10, verify: local, formal: none, evidence: "self-test ok, but a TLA+ AXIOM passes the escape-hatch scan (blocker below)", verdict: FAIL}
  - {req: R11, verify: local, formal: none, evidence: "vacuity block in schema; no vacuity / a passing vacuity re-run fail", verdict: PASS}
  - {req: R12, verify: local, formal: checked, conformance: none, evidence: "check_models.py: every property holds at stated bounds, seeded broken variants yield counterexamples", verdict: PASS}
  - {req: R13, verify: local, formal: checked, conformance: trace, evidence: "real traces accepted, mutant traces rejected; check_repo fails on a set difference", verdict: PASS}
  - {req: R14, verify: local, formal: none, evidence: "AGENTS.md invariant 11; reviewer.md invariants_checked [1..11]", verdict: PASS}
  - {req: R15, verify: local, formal: checked, conformance: trace, evidence: "Election holds; ElectionV096 fails AtMostOneActing; A1-A5 in session-governance.md", verdict: PASS}
  - {req: N1, verify: local, formal: none, evidence: "mapping table complete; reviewer verdicts check invariants 1-11 (read after my pass)", verdict: PASS}
  - {req: N2, verify: local, formal: none, evidence: "invariant 10's whole block byte-identical to 0.9.6 (49d78dd); check_tasks requires check_live and check_formal for Done", verdict: PASS}
  - {req: N3, verify: local, formal: none, evidence: "stdlib-only imports; check_neutral ok; TLA_VERSION 1.7.4 + TLA_SHA256 pinned", verdict: PASS}
  - {req: N4, verify: local, formal: none, evidence: "latest auditor verdict (audit-8, at b572f8f) PASS-WITH-DEBT, no blocker/high", verdict: PASS}
blockers:
  - requirement: R10
    clause: >-
      fails a requirement whose spec/proof sources hold an escape hatch -- a proof
      that is not a proof (`sorry`, `admit`, `Admitted`, `axiom`, `assume`, ...
      and their kin); Acceptance: each escape hatch
    problem: >
      For .tla sources the scan looks only for OMITTED. TLA+'s AXIOM (and its
      synonyms ASSUME / ASSUMPTION) is an unproved fact a TLAPS proof may use
      (`THEOREM T BY Cheat`), i.e. exactly the `axiom` hatch the clause names,
      in the formal language this framework itself picked. check_formal passes
      it, plain and on --rerun. The hatch list covers Lean `axiom` and Coq
      `Axiom`; TLA+ has no case in HATCHES or in the self-test.
    repro: |
      git init a project with requirements.md R2 (*Verify*: local, *Property*:
      GoodProp holds, *Formal*: checked, *Conformance*: none), src/Spec.tla
      ("---- MODULE Spec ----", "GoodProp == TRUE", "AXIOM Cheat == GoodProp",
      "===="), a stand-in checker src/check.py (prints "TLC ok", exits 1 with
      --broken), and formal/R2.json naming sources [src/check.py, src/Spec.tla],
      a vacuity run that fails, sha = the commit holding Spec.tla; commit.
      check_formal.py --requirements req/requirements.md --only R2 [--rerun]
      -> "formal: ok". Replace the AXIOM line with
      "THEOREM T == GoodProp PROOF OMITTED" -> "escape hatch in Spec.tla:3".
      Fix: add r"^\s*AXIOM\b" (and judge ASSUME/ASSUMPTION for a `proved`
      TLAPS source) to HATCHES[".tla"], with a self-test case.
    loop_back: Phase 3 (R10, check_formal.py)
debts:
  - "R10: the self-test has no case for `admit`, a hatch R10 names (the detector works for .lean, .v, .fst, .rs -- checked by hand); add one per language."
  - "N4: the latest audit is at b572f8f; 19 commits since (about +575 lines in check_live.py / check_tasks.py) are unaudited. The Acceptance text is met; re-audit before the ship batch."
  - "R12/R13: CI runs of checks.yml / models.yml were not observable here; record CI's own result (and time, D2) before merge."
  - "Carried: D1-D5, D9, D10, D12-D22 as listed in TASKS.md."
notes:
  - "R3: check_live --rerun clears a stale `local` record by re-running it; check_formal --rerun still reports stale. So a re-run passes a stale live record the plain run fails -- by design (the re-run is the proof), but the two sensors differ; worth one sentence in the docstrings."
  - "R3: a lossy clean filter (e.g. nbstripout) makes the plain scan read disk content the blob lacks; the re-run scans HEAD. More accurate, not weaker; noted only against the literal 'never pass what the plain run fails'."
  - "R8: Phase 6's block does not name the pre-authorized list itself; the rule paragraph sits after Phase 5 and release.md consults it. Met, thinly."
  - "R1: this proposal's TASKS.md signs design.md where the template shows standards.md -- correct for a framework change, which has no standards.md."
  - "Read verdicts/ only after this pass: security-6's HEAD-move blocker re-tested (HEAD moved -> hit, nothing recorded); reviewer-7's R3 (an absolute-path helper) is ruled the environment by R3's signed text; its R12 blocker is closed by ElectedOnceGone."
retrospective:
  - "Worked: re-running every sensor in a clean clone, plus small repo repros of the threat model -- all held."
  - "Missed by 15 rounds: the hatch table was checked per listed word, not per language the framework ships."
  - "Next: for any list labelled 'and their kin', test the framework's own tool first."
```
