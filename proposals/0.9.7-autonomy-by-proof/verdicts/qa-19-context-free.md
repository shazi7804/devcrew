# QA verdict — final 10 (qa role, Claude, at 2bf32b9)

SITUATION: QA judged the end state of branch feat/0.9.7-autonomy-by-proof at
2bf32b9 (diff main..2bf32b9) against its signed contract,
proposals/0.9.7-autonomy-by-proof/requirements.md (`Signed:` hash 3139d052b472,
matched by `check_tasks.py`). I worked in a throwaway clone of the repo and
built my own toy repositories for the repros.
ACTION: I ran every CI step in checks.yml and models.yml locally, then the
three gate sensors, plain and with `--rerun`, on the proposal. I ran each
Acceptance's command, mutation-tested `check_repo.py`'s set comparison, and
probed R3's *Threat model* with toy repositories.
STATUS: FAIL. Every sensor is green, but one clause of R3's *Threat model*
fails. When one probe leaves an untracked `.gitattributes` in the shared HEAD
checkout, the per-probe reset applies it before it removes it. The next probe
then runs on files that are not HEAD's bytes. A `[x]` whose own
`check_live --only <ID> --rerun` is red passes `check_tasks --rerun`.
NEXT: loop back to implementation (Phase 3) for R3. The fix is to run
`clean -ffdx` before `checkout -f` in `HeadTree.get()`, or to remove every
untracked `.gitattributes` first, with a self-test case. Then rerun
`check_tasks --rerun`. CEO: nothing to decide. This is a fix inside the signed
contract, not a judgment.

Commands I ran at 2bf32b9, and their results:
- `python3 tools/check_neutral.py --self-test` gave "self-test ok". `python3 tools/check_neutral.py` gave "neutral: ok".
- `python3 framework/tools/check_live.py --self-test` gave "self-test ok (153 cases)".
- `python3 framework/tools/check_formal.py --self-test` gave "self-test ok (66 cases)".
- `python3 framework/tools/check_tasks.py --self-test` gave "self-test ok (59 cases)".
- `python3 tools/check_repo.py` gave "repo: ok". `python3 tools/diagram.py check $(git ls-files '*.md')` gave "ALIGNED".
- `python3 tools/check_models.py` (TLC from tla2tools 1.7.4, sha256 936a2620… matching the pin) gave "models: ok" in 6 m 55 s:
  - all 4 holding configs hold, and all 7 broken variants fail on the expected property;
  - all 5 trace sets (scripted, stampede, seeds 0–2) are accepted, and all 3 boot.py mutants are rejected.
- `check_tasks.py --tasks proposals/0.9.7-autonomy-by-proof/TASKS.md --allow tools/live-allow.txt`, plain, gave "tasks: ok". With `--rerun` it also gave "tasks: ok" (10 m 08 s).
- `check_live.py --requirements <proposal>/requirements.md --allow tools/live-allow.txt` gave "live: ok", both plain and with `--rerun`.
- `check_formal.py --requirements <proposal>/requirements.md` gave "formal: ok", both plain and with `--rerun` (8 m).
- After all of this, `git status --porcelain --ignored` in the clone was empty and `git worktree list` showed only the main tree.

```yaml
verdict: FAIL
scope: "feature (framework: framework/ · hosts/ · AGENTS.md · docs · CI)"
sensors:
  lint: n/a
  typecheck: n/a
  test: pass        # check_neutral / check_live / check_formal / check_tasks self-tests; check_repo; diagram check
  build: n/a
  models: pass      # tools/check_models.py: 11 model runs as expected, 5 trace sets accepted, 3 mutants rejected
  live: pass        # check_live.py --rerun --allow tools/live-allow.txt: live: ok (every item Verify: local)
  formal: pass      # check_formal.py --rerun: formal: ok
  tasks: pass       # check_tasks.py plain and --rerun: tasks: ok
requirements:
  - {id: R1, verdict: PASS, verify: local, formal: none, evidence: "contracts/tasks.template.md has the three sections and the header. SKILL.md and ARCHITECTURE.md §6 call TASKS.md the only ledger, and every other 'ledger' mention is a host mirror of it"}
  - {id: R2, verdict: PASS, verify: local, formal: none, evidence: "self-test cases for a missing, duplicated and unknown ID, plus Dn and Cn"}
  - {id: R3, verdict: FAIL, verify: local, formal: none, evidence: "The Acceptance's self-test cases pass, and so does my toy repo (a [x] that fails only formal fails plain and --rerun). The Threat model fails on an earlier probe's untracked .gitattributes (blocker B1)"}
  - {id: R4, verdict: PASS, verify: local, formal: none, evidence: "check_tasks --self-test: 59 cases, each asserting its reason, covering every case the Acceptance lists, plus a clean file"}
  - {id: R5, verdict: PASS, verify: local, formal: none, evidence: "All three adapters name TASKS.md the ledger and say a mirror loses to it. The 'NOT DEFINED' line is gone. Each adapter installs check_tasks.py and runs its self-test at verify"}
  - {id: R6, verdict: PASS, verify: local, formal: none, evidence: "SKILL.md's phase table names each batch. Its former-gate → batch table has one row per former gate, none unmapped"}
  - {id: R7, verdict: PASS, verify: local, formal: none, evidence: "SKILL.md lists five interrupts, each with its sensor. Cn is allowed in Todo/Done and refused in progress (self-test). orchestrator.md:66-72 states the Cn rule"}
  - {id: R8, verdict: PASS, verify: local, formal: none, evidence: "requirements.template.md has the Pre-authorized actions table. Phase 5 consults it, and its rule paragraph covers every high-risk action. JudgmentRecorded holds, and AidlcJudgmentBroken violates it"}
  - {id: R9, verdict: PASS, verify: local, formal: none, evidence: "Every example item in requirements.template.md has Property/Formal/Conformance lines plus the definitions. standards.template.md has a Formal verification section (load-bearing components, tool per level, bounds)"}
  - {id: R10, verdict: PASS, verify: local, formal: none, evidence: "check_formal --self-test: 66 cases, covering every listed reason and every escape hatch named. --rerun re-executes the check and the vacuity run"}
  - {id: R11, verdict: PASS, verify: local, formal: none, evidence: "SKILL.md's schema has a vacuity block. Self-test cases cover a missing vacuity run and one that passed"}
  - {id: R12, verdict: PASS, verify: local, formal: checked, evidence: "check_models.py: every property in R12's Property holds at the stated bounds. The seeded broken variants fail (ElectionV096, AidlcBroken, AidlcJudgmentBroken, the Live/Once/Scan breaks). The formal --rerun is green"}
  - {id: R13, verdict: PASS, verify: local, formal: checked, evidence: "trace validation accepts the scripted, stampede and three seeded concurrent runs, and rejects the three mutants. check_repo.py fails when an interrupt is dropped, a batch is added or the set line is deleted (mutation-tested)"}
  - {id: R14, verdict: PASS, verify: local, formal: none, evidence: "AGENTS.md invariant 11; reviewer.md invariants_checked: [1..11]"}
  - {id: R15, verdict: PASS, verify: local, formal: checked, evidence: "Election holds and the ElectionV096 model yields AtMostOneActing violated. session-governance.md has an assumptions table A1-A5"}
  - {id: N1, verdict: PASS, verify: local, formal: none, evidence: "R6 mapping table complete. The reviewer's check is recorded in the proposal's reviewer verdicts"}
  - {id: N2, verdict: PASS, verify: local, formal: none, evidence: "invariant 10 is byte-identical to 0.9.6's (feat/0.9.6-live-verification, an ancestor). check_tasks needs both the live and formal sensors (toy repo: formal alone fails a [x])"}
  - {id: N3, verdict: PASS, verify: local, formal: none, evidence: "check_tasks.py/check_formal.py import only the stdlib plus the sibling sensors. check_neutral exits 0. models.yml pins tla2tools 1.7.4, and check_models.py checks the jar's sha256"}
  - {id: N4, verdict: PASS, verify: local, formal: none, evidence: "TASKS.md records the auditor's PASS-WITH-DEBT. Its medium/low findings are logged as Dn"}
blockers:
  - requirement: R3
    clause: "Threat model: 'The sensors SHALL keep accidents out of a re-run: ... what an earlier probe left behind'. The Acceptance (a [x] whose check_live.py --only <ID> fails) also fails under --rerun"
    problem: >
      HeadTree.get() resets the shared checkout in this order: drop the index,
      `checkout -f`, `reset --hard`, `clean -ffdx`. Git applies an untracked
      `.gitattributes` from the working tree during that checkout, and the
      clean only removes it afterwards. So when an earlier probe writes one
      (for example `git lfs track`, a generator, a fixture), it rewrites the
      files the next probe sees, and that probe runs on bytes that are not
      HEAD's. The leftover can be at the root or in any directory where HEAD
      has no `.gitattributes`, and can carry eol=crlf, ident or a filter.
      check_formal --rerun's check and vacuity runs share the same reset. A
      probe that edits a tracked `.gitattributes` is correctly undone, because
      git then uses HEAD's copy from the index.
    repro: >
      In an empty git repo: req/requirements.md holds R1 and R2, both
      `Verify: local` with `Property: none — text`. data.txt holds "hello\n"
      (LF). Commit. Then write local evidence at that sha:
      R1 command `printf '* text eol=crlf\n' > .gitattributes; echo ok1`, expect ok1;
      R2 command `od -c data.txt | grep -q '\\r' && echo CRLF || echo LFONLY`,
      expect CRLF (false at HEAD). Commit, then add TASKS.md with
      `Signed: requirements.md sha256:<12>`, Done `- [x] R1 a` and `- [x] R2 b`,
      and commit. Results:
      `check_live.py --requirements req/requirements.md --rerun --only R2` gives
      rc 1, "R2 ... does not match expect".
      `check_live.py --requirements req/requirements.md --rerun` gives rc 0, live: ok.
      `check_tasks.py --tasks req/TASKS.md --rerun` gives rc 0, tasks: ok.
      A subdirectory variant shows the same flip: R1 writes `f.txt ident` to
      sub/.gitattributes, and R2 expects `$Id: <40 hex> $` in sub/f.txt. R2
      fails alone and passes after R1.
    loop_back_to: implementation
debts: []   # nothing new beyond TASKS.md's D1-D26. D26 (no --live-host in check_tasks) and D12 (SIGTERM leaves a worktree) were seen again and are already logged
notes:
  - "R3, carried from QA rounds 15-18: check_live --rerun clears a stale or orphan `local` record by re-running it green at HEAD, so plain check_tasks fails 'stale' where --rerun passes (toy repo: plain rc 1, --rerun rc 0). check_formal --rerun still reports stale. I read the re-run as the stronger proof (C8), not as one of the accidents the Threat model lists. Still, 'never pass what the plain run fails' says otherwise literally, and one sentence beside it would settle which reading is meant"
  - "R8: SKILL.md's own Phase 6 block does not name the pre-authorized list. Phase 5's rule paragraph covers every high-risk action, and release.md and mobile-release (Phase 6's procedure) consult it. Phase 6's GATE lists submission as ship-batch only, while release.md also allows a pre-authorized submission. Met, thinly, as in earlier rounds; aligning the two texts would remove the ambiguity"
  - "R10 'and their kin': every named hatch is caught. Kin not yet in the list include F* `--admit_smt_queries true` / `--lax`, Coq `Unset Guard Checking`, Agda `{-# TERMINATING #-}` / `--type-in-type`, Dafny `{:only}` and Verus `#[verifier::external]`. The list is open-ended, so this is not a blocker"
  - "R3: an ignored, unsigned design.md beside the requirements fails both plain and --rerun ('exists but is not signed'). An ignored file can still decide a re-run, though only toward failing. Not a pass of what plain fails"
  - "CI: origin's feat/0.9.7-autonomy-by-proof is at 49d78dd, so no CI run exists at 2bf32b9. I ran every checks.yml and models.yml step locally, and all are green"
```

Retrospective:
- What worked: building a toy repo per Threat-model clause, and comparing `--only` against the full run, found a probe-to-probe leak that the per-probe checks had missed.
- What failed: the reset's order of operations had never been tested against what git itself reads from the working tree during checkout. Attributes are such a read.
- Change next time: for every "reset" a sensor performs, list which files git reads from the working tree during that step, and add one self-test case per file.
