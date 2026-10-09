# QA verdict — final 4 (qa role, Claude, at 6110064)

Judged: the end state of `feat/0.9.7-autonomy-by-proof` at 6110064 (main..6110064,
141 files; 0.9.6 is an ancestor) against `proposals/0.9.7-autonomy-by-proof/requirements.md`,
R3's *Threat model* included. TASKS.md's `Signed:` hashes match (check_tasks green).
Every sensor ran in a fresh clone with a clean working tree. The threat-model probes ran
in throwaway toy repositories driven by 6110064's sensors, on APFS (case-insensitive).
I read `verdicts/` only after this pass, and only as a regression list (QA final 3's B1
and Security final 3's second blocker are the same class as B1 below).

## Requirement table

| Item | Verify | Formal | Evidence / how judged | Verdict |
|---|---|---|---|---|
| R1 | local | none | `contracts/tasks.template.md` has the three sections, line forms and two-line header. SKILL.md and ARCHITECTURE.md §6 call it the only ledger. Host ledgers are mirrors only | PASS |
| R2 | local | none | the check_tasks self-test fails missing, duplicated and unknown IDs, and passes Dn and Cn | PASS |
| R3 | local | none | Acceptance holds: the self-test covers a `[x]` with failing live or formal evidence and a `[x]` with a status. The *Threat model* does not hold. The C16 clean-tree rule asks `git status`, so an uncommitted change behind an index flag still decides the re-run (B1), and an ignored file still takes part (B2) | FAIL (B1, B2) |
| R4 | local | none | `check_tasks.py --self-test` passes 52 cases, every listed reason included (drifted requirements.md and standards.md, 6/5). It passes a clean file | PASS |
| R5 | local | none | all three adapters use TASKS.md, say "TASKS.md wins", install check_tasks.py and self-test it. The "NOT DEFINED" line is gone | PASS |
| R6 | local | none | SKILL.md has the batch table and an 11-row "Former 🔴 gate -> Now" map with no gate unmapped | PASS |
| R7 | local | none | SKILL.md lists the five interrupts, each with its sensor. check_tasks refuses a Cn in progress. orchestrator.md says a judgment becomes a Cn | PASS |
| R8 | local | none | the template has a Pre-authorized actions table. Phases 5–6 consult it. JudgmentRecorded holds, and AidlcJudgmentBroken violates it | PASS |
| R9 | local | none | every example item in the template carries Property/Formal/Conformance, and the definitions are there. standards.template.md has § Formal verification | PASS |
| R10 | local | none | `check_formal.py --self-test` passes 46 cases, every listed reason and hatch included. `--rerun --only R3,R10` is green. It shares B1: the property text and level are read from the working tree's requirements.md, which `git status` can hide | FAIL (via B1) |
| R11 | local | none | SKILL.md's evidence schema has the vacuity block. The self-test fails a missing vacuity run and one that passed | PASS |
| R12 | local | checked/none | check_models: Election (3573920 states), ElectionLive, Aidlc and AidlcLive hold. ElectionV096, ElectionLiveBroken, ElectionOnceBroken, AidlcBroken, AidlcJudgmentBroken and AidlcLiveBroken each give their expected counterexample. TLC 1.7.4 is pinned by sha256 | PASS |
| R13 | local | checked/trace | the scripted, stampede and three seeded concurrent boot.py traces are accepted, and the three mutants are rejected. check_repo.py compares SKILL.md's sets with the model's: ok | PASS |
| R14 | local | none | AGENTS.md has invariant 11; reviewer.md has `invariants_checked: [1..11]` | PASS |
| R15 | local | checked/trace | the shipped Election holds and ElectionV096 fails AtMostOneActing. session-governance.md states A1–A5 | PASS |
| N1 | local | none | the mapping table is complete, and every removed stop is a sensor or a recorded Cn under the CEO's second ruling | PASS |
| N2 | local | none | invariant 10's text is identical to 0.9.6's. check_tasks requires both check_live and check_formal for Done | PASS |
| N3 | local | none | the sensors import only the stdlib. check_neutral exits 0. CI pins tla2tools 1.7.4 | PASS |
| N4 | local | none | the latest audit (audit-8, at b572f8f) is PASS-WITH-DEBT with no blocker/high finding. The evidence probe re-ran green | PASS |

```yaml
verdict: FAIL
scope: feature (framework)
sensors:
  lint: n/a
  typecheck: n/a
  test: pass   # every CI step of checks.yml, run locally
  build: n/a
  live: pass   # check_live.py --rerun --allow tools/live-allow.txt -> live: ok (TLC env set); local items need no --deployed
  formal: pass # check_formal.py --rerun --only R3,R10 -> formal: ok; R12/R13/R15 re-run inside check_tasks --rerun
  tasks: pass  # check_tasks.py --rerun --allow tools/live-allow.txt -> tasks: ok (rc 0, 10 min)
  commands:
    - "python3 tools/check_neutral.py --self-test -> self-test ok (rc 0)"
    - "python3 tools/check_neutral.py -> neutral: ok (rc 0)"
    - "python3 framework/tools/check_live.py --self-test -> self-test ok (143 cases) (rc 0)"
    - "python3 framework/tools/check_formal.py --self-test -> self-test ok (46 cases) (rc 0)"
    - "python3 framework/tools/check_tasks.py --self-test -> self-test ok (52 cases) (rc 0)"
    - "python3 tools/check_repo.py -> repo: ok (rc 0)"
    - "python3 tools/diagram.py check $(git ls-files '*.md') -> rc 0"
    - "python3 tools/check_models.py -> models: ok (10 models/variants as expected, 5 traces accepted, 3 mutants rejected; 3m38s)"
    - "python3 framework/tools/check_tasks.py --root . --tasks proposals/0.9.7-autonomy-by-proof/TASKS.md --rerun --allow tools/live-allow.txt -> tasks: ok (rc 0)"
    - "python3 framework/tools/check_live.py --root . --requirements proposals/0.9.7-autonomy-by-proof/requirements.md --rerun --allow tools/live-allow.txt -> live: ok (rc 0)"
    - "python3 framework/tools/check_formal.py --root . --requirements proposals/0.9.7-autonomy-by-proof/requirements.md --only R3,R10 --rerun -> formal: ok (rc 0)"
    - "shasum -a 256 framework/tools/check_live.py -> 6ee08537cac59fea4e6db19ba613513b2398064ad90778bb26da7f11038835e2, equal to what it prints"
requirements:
  - {id: R1, verdict: PASS, verify: local, formal: none, evidence: evidence/R1.json + read/grep, traces_to: [main..6110064]}
  - {id: R2, verdict: PASS, verify: local, formal: none, evidence: evidence/R2.json + check_tasks self-test, traces_to: [main..6110064]}
  - {id: R3, verdict: FAIL, verify: local, formal: none, evidence: "evidence/R3.json (self-test); Threat model fails: B1, B2", traces_to: [767ef1e]}
  - {id: R4, verdict: PASS, verify: local, formal: none, evidence: evidence/R4.json + self-test 52 cases, traces_to: [main..6110064]}
  - {id: R5, verdict: PASS, verify: local, formal: none, evidence: evidence/R5.json + read of hosts/*.md, traces_to: [main..6110064]}
  - {id: R6, verdict: PASS, verify: local, formal: none, evidence: evidence/R6.json + SKILL.md gate map, traces_to: [main..6110064]}
  - {id: R7, verdict: PASS, verify: local, formal: none, evidence: evidence/R7.json + SKILL.md / orchestrator.md, traces_to: [main..6110064]}
  - {id: R8, verdict: PASS, verify: local, formal: none, evidence: evidence/R8.json (re-run with TLC: holds), traces_to: [main..6110064]}
  - {id: R9, verdict: PASS, verify: local, formal: none, evidence: evidence/R9.json + templates, traces_to: [main..6110064]}
  - {id: R10, verdict: FAIL, verify: local, formal: none, evidence: "evidence/R10.json (self-test 46 cases); fails via B1", traces_to: [767ef1e]}
  - {id: R11, verdict: PASS, verify: local, formal: none, evidence: evidence/R11.json + self-test, traces_to: [main..6110064]}
  - {id: R12, verdict: PASS, verify: local, formal: checked, evidence: "evidence/R12.json, formal/R12.json, check_models.py run", traces_to: [main..6110064]}
  - {id: R13, verdict: PASS, verify: local, formal: checked, evidence: "evidence/R13.json, formal/R13.json, trace validation run", traces_to: [main..6110064]}
  - {id: R14, verdict: PASS, verify: local, formal: none, evidence: evidence/R14.json + AGENTS.md / reviewer.md, traces_to: [main..6110064]}
  - {id: R15, verdict: PASS, verify: local, formal: checked, evidence: "evidence/R15.json, formal/R15.json, ElectionV096 counterexample", traces_to: [main..6110064]}
  - {id: N1, verdict: PASS, verify: local, formal: none, evidence: evidence/N1.json + gate map, traces_to: [SKILL.md]}
  - {id: N2, verdict: PASS, verify: local, formal: none, evidence: "evidence/N2.json; invariant 10 unchanged vs 0.9.6", traces_to: [AGENTS.md, check_tasks.py]}
  - {id: N3, verdict: PASS, verify: local, formal: none, evidence: "evidence/N3.json; imports read; check_neutral ok", traces_to: [framework/tools, models.yml]}
  - {id: N4, verdict: PASS, verify: local, formal: none, evidence: "verdicts/audit-8-context-free.md PASS-WITH-DEBT", traces_to: [audit-8]}
blockers:
  - requirement: R3 (and R10 through it)
    clause: "Threat model: the sensors SHALL keep accidents out of a re-run: an uncommitted change ..."
    problem: >
      C16's clean-tree rule (check_live.unclean) asks `git status --porcelain`. git status
      skips every path whose index entry carries assume-unchanged or skip-worktree (from
      the user's own `git update-index`, or from sparse-checkout). The re-run then reads
      that path's uncommitted working-tree copy: TASKS.md, the signed files that
      check_tasks hashes, and requirements.md, which check_live, check_formal and
      check_tasks read for the item set, the Verify level and the signed Property. So an
      uncommitted change still decides what HEAD is judged against, which is the class
      C16 says it closed. The probes and scans are not affected, because they read
      HeadTree. The fix: make unclean() also refuse any index entry that `git ls-files -v`
      shows with a lowercase or `S` tag. Or, on a re-run, read the requirements, TASKS.md
      and the signed files from HEAD's blobs.
    repro: |
      (a) check_live, skip-worktree on requirements.md:
        git init; requirements.md = "- **R1** — x / *Verify*: local" + "- **R2** — y / *Verify*: local"; commit (sha S)
        evidence/R1.json = {id R1, verify local, command "echo 'temp: 21'", target "this checkout",
          expect "temp: \\d+", observed "temp: 21", result pass, sha S}; commit   (no R2 evidence)
        check_live.py --root . --requirements requirements.md --rerun
          -> rc 1 "R2: no evidence (evidence/R2.json) at HEAD"
        git update-index --skip-worktree requirements.md; rewrite requirements.md with R1 only
        git status --porcelain -> (empty)
        check_live.py --root . --requirements requirements.md --rerun -> rc 0 "live: ok"
      (b) check_tasks, assume-unchanged on TASKS.md:
        HEAD's TASKS.md has "- [x] R1 x — verifying" (signed, R1 local with fresh evidence)
        check_tasks.py --root . --tasks TASKS.md --rerun -> rc 1 "a Done line carries no status"
        git update-index --assume-unchanged TASKS.md; delete " — verifying" from TASKS.md
        git status --porcelain -> (empty)
        check_tasks.py --root . --tasks TASKS.md --rerun -> rc 0 "tasks: ok"
    loop_back_to: implementation
  - requirement: R3
    clause: "Threat model: the sensors SHALL keep accidents out of a re-run: ... an untracked or ignored file"
    problem: >
      unclean() exempts ignored files by design ("Ignored files are the environment, not
      the tree"), and SKILL.md documents only "an uncommitted or untracked file". But the
      signed clause names ignored files among the accidents to keep out, and the re-run
      reads TASKS.md and the requirements from the working tree. A gitignored ledger that
      HEAD does not contain is therefore judged as if it were HEAD's. HEAD itself has no
      ledger ("no TASKS.md ... the run has no ledger").
    repro: |
      the toy from (b), but with TASKS.md correct, then: git rm --cached TASKS.md;
      echo TASKS.md > .gitignore; git add .gitignore; commit
      git status --porcelain --ignored -> "!! TASKS.md"; git ls-tree HEAD -> no TASKS.md
      check_tasks.py --root . --tasks TASKS.md --rerun -> rc 0 "tasks: ok"
    loop_back_to: implementation
debts:
  - "Carry forward D1-D5, D9, D10, D12-D21 as listed in TASKS.md; nothing new is added to the list."
  - "N4.json probes verdicts/audit.md (the first audit), not the latest; and no audit covers the 432 changed lines from b572f8f to 767ef1e (C16 included). The latest audit has no blocker/high, so N4 passes, but point the evidence at the newest audit."
  - "tools/live-allow.txt exempts every line of framework/tools/check_live.py (regex \\S). It is stated and reasoned (C11), but it blinds the scan to that whole file."
notes:
  - "CI was not observable from here (no PR check log). Every step of checks.yml and models.yml ran locally at 6110064 and was green."
  - "R3 and R10 are In progress in TASKS.md (1/5, stalled 0/3). This round's B1/B2 count as attempt 2 for both."
  - "These held on the re-run in toys: an untracked file and an uncommitted edit (both refused); --deployed now runs in HEAD's checkout (an ignored helper is absent there, so it is refused)."
  - "Independently satisfied: R1, R2, R4-R9, R11-R15, N1-N4."
```

Retrospective: the sensors and models are solid, and every acceptance command is green.
The clean-tree rule trusts `git status` as the definition of "the working tree is HEAD",
and git's index flags make that untrue. Reading the contract from HEAD's blobs would close
the class for good instead of guarding the door. Next time, check index flags and ignored
files first whenever a sensor reads the working tree.
