# QA verdict — final 5 (qa role, Claude, at f21b821)

What I judged: the end state of `feat/0.9.7-autonomy-by-proof` at f21b821 (main..f21b821,
143 files; 0.9.6 is an ancestor), against `proposals/0.9.7-autonomy-by-proof/requirements.md`,
including R3's *Threat model*. Every sensor ran in a fresh clone with a clean working tree,
with TLC 1.7.4 on Java 21. I ran the threat-model probes in throwaway toy repositories,
driven by f21b821's own sensors, on APFS (case-insensitive). I read `verdicts/` only after
this pass, and used it only as a regression list. Final 4's B1 (index flags) and B2 (an
ignored ledger) are fixed, and the self-test now covers both. The two blockers below are
new.

## Requirement table

| Item | Verify | Formal | Evidence / how judged | Verdict |
|---|---|---|---|---|
| R1 | local | none | `contracts/tasks.template.md` has the three sections, the line forms and the two-line header. SKILL.md and ARCHITECTURE.md §6 call it the only ledger. Every other "ledger" mention is TASKS.md or a host mirror of it | PASS |
| R2 | local | none | the check_tasks self-test fails a missing, a duplicated and an unknown ID, and passes Dn and Cn | PASS |
| R3 | local | none | The Acceptance holds. A `[x]` fails when its live evidence fails (self-test) or when only its formal evidence fails (toy: `Done but not formal`). A `[x]` that carries a status also fails. The *Threat model* does not hold: an ignored file inside the repository decides a re-run when it reaches the probe through PATH (B1), and a later probe passes on what an earlier probe left in `$TMPDIR` (B2) | FAIL (B1, B2) |
| R4 | local | none | `check_tasks.py --self-test` passes 54 cases. Every reason listed in the Acceptance is covered (drift of requirements.md and standards.md, 6/5), and a clean file has no hit | PASS |
| R5 | local | none | All three adapters use TASKS.md, say "TASKS.md wins", install check_tasks.py and run its self-test. The "NOT DEFINED" line is gone | PASS |
| R6 | local | none | SKILL.md has the batch table and an 11-row "Former 🔴 gate -> Now" map. No old gate is unmapped | PASS |
| R7 | local | none | SKILL.md lists the five interrupts, each with the sensor that raises it. check_tasks refuses a Cn in progress. orchestrator.md says a judgment is recorded as a Cn | PASS |
| R8 | local | none | The template has a *Pre-authorized actions* table, and Phases 5–6 consult it. JudgmentRecorded holds, and AidlcJudgmentBroken violates it | PASS |
| R9 | local | none | The template carries 8/8 Property/Formal/Conformance lines, plus the definitions. standards.template.md has § Formal verification | PASS |
| R10 | local | none | `check_formal.py --self-test` passes 46 cases. `--rerun --only R3,R10` is green. `run_cmd` runs the check in HEAD's checkout but with the caller's whole environment, so it shares B1 and B2 | FAIL (via B1, B2) |
| R11 | local | none | SKILL.md's evidence schema has the vacuity block. The self-test fails evidence with no vacuity run, and evidence whose vacuity run passed | PASS |
| R12 | local | checked/none | In check_models, Election (3573920 states), ElectionLive, Aidlc and AidlcLive hold. Six variants give their expected counterexamples: ElectionV096, ElectionLiveBroken, ElectionOnceBroken, AidlcBroken, AidlcJudgmentBroken and AidlcLiveBroken. TLC is pinned by sha256 | PASS |
| R13 | local | checked/trace | Five boot.py traces are accepted (scripted, stampede, 3 seeded crowds) and three mutants are rejected. check_repo.py passes, and fails when an interrupt is removed from SKILL.md's set (checked in a scratch copy) | PASS |
| R14 | local | none | AGENTS.md has invariant 11. reviewer.md has `invariants_checked: [1..11]` | PASS |
| R15 | local | checked/trace | The shipped Election holds, and ElectionV096 fails AtMostOneActing. session-governance.md states A1–A5 | PASS |
| N1 | local | none | The gate map is complete. Every removed stop is now either a sensor or a recorded Cn | PASS |
| N2 | local | none | Invariant 10's text is byte-identical to 0.9.6's. check_tasks requires both sensors | PASS |
| N3 | local | none | check_live, check_formal and check_tasks import only the stdlib. check_neutral exits 0. CI pins tla2tools 1.7.4 | PASS |
| N4 | local | none | audit-8 is PASS-WITH-DEBT with no blocker/high finding | PASS |

```yaml
verdict: FAIL
scope: feature (framework)
sensors:
  lint: n/a
  typecheck: n/a
  test: pass   # every step of checks.yml, run locally
  build: n/a
  live: pass   # check_live --rerun --only R3,R10 -> live: ok; Done items re-run inside check_tasks --rerun
  formal: pass # check_formal --rerun --only R3,R10 -> formal: ok; R12/R13/R15 re-run inside check_tasks --rerun
  tasks: pass  # check_tasks --rerun -> tasks: ok (rc 0, 13 min 22 s)
  commands:
    - "python3 tools/check_neutral.py --self-test -> self-test ok (rc 0)"
    - "python3 tools/check_neutral.py -> neutral: ok (rc 0)"
    - "python3 framework/tools/check_live.py --self-test -> self-test ok (145 cases) (rc 0)"
    - "python3 framework/tools/check_formal.py --self-test -> self-test ok (46 cases) (rc 0)"
    - "python3 framework/tools/check_tasks.py --self-test -> self-test ok (54 cases) (rc 0)"
    - "python3 tools/check_repo.py -> repo: ok (rc 0)"
    - "python3 tools/diagram.py check $(git ls-files '*.md') -> rc 0"
    - "python3 tools/check_models.py -> models: ok (4 models hold, 6 broken variants fail as expected, 5 traces accepted, 3 mutants rejected)"
    - "python3 framework/tools/check_tasks.py --tasks proposals/0.9.7-autonomy-by-proof/TASKS.md --allow tools/live-allow.txt -> tasks: ok"
    - "python3 framework/tools/check_tasks.py --tasks proposals/0.9.7-autonomy-by-proof/TASKS.md --rerun --allow tools/live-allow.txt -> tasks: ok (rc 0)"
    - "python3 framework/tools/check_live.py --requirements proposals/0.9.7-autonomy-by-proof/requirements.md --evidence proposals/0.9.7-autonomy-by-proof/evidence --allow tools/live-allow.txt -> live: ok"
    - "python3 framework/tools/check_live.py --rerun --requirements proposals/0.9.7-autonomy-by-proof/requirements.md --only R3,R10 --allow tools/live-allow.txt -> live: ok"
    - "python3 framework/tools/check_formal.py --requirements proposals/0.9.7-autonomy-by-proof/requirements.md [--only R3,R10 --rerun] -> formal: ok"
requirements:
  - {id: R1, verdict: PASS, verify: local, formal: none, evidence: evidence/R1.json + read/grep, traces_to: [main..f21b821]}
  - {id: R2, verdict: PASS, verify: local, formal: none, evidence: evidence/R2.json + check_tasks self-test, traces_to: [main..f21b821]}
  - {id: R3, verdict: FAIL, verify: local, formal: none, evidence: "evidence/R3.json (self-test 54 cases); Threat model fails: B1, B2", traces_to: [f50e477]}
  - {id: R4, verdict: PASS, verify: local, formal: none, evidence: evidence/R4.json + self-test, traces_to: [main..f21b821]}
  - {id: R5, verdict: PASS, verify: local, formal: none, evidence: evidence/R5.json + hosts/*.md, traces_to: [main..f21b821]}
  - {id: R6, verdict: PASS, verify: local, formal: none, evidence: evidence/R6.json + SKILL.md gate map, traces_to: [main..f21b821]}
  - {id: R7, verdict: PASS, verify: local, formal: none, evidence: evidence/R7.json + SKILL.md / orchestrator.md, traces_to: [main..f21b821]}
  - {id: R8, verdict: PASS, verify: local, formal: none, evidence: evidence/R8.json + JudgmentRecorded run, traces_to: [main..f21b821]}
  - {id: R9, verdict: PASS, verify: local, formal: none, evidence: evidence/R9.json + templates, traces_to: [main..f21b821]}
  - {id: R10, verdict: FAIL, verify: local, formal: none, evidence: "evidence/R10.json (self-test 46 cases); shares B1, B2 through run_cmd", traces_to: [f50e477]}
  - {id: R11, verdict: PASS, verify: local, formal: none, evidence: evidence/R11.json + self-test, traces_to: [main..f21b821]}
  - {id: R12, verdict: PASS, verify: local, formal: checked, evidence: "formal/R12.json; check_models run", traces_to: [main..f21b821]}
  - {id: R13, verdict: PASS, verify: local, formal: checked, evidence: "formal/R13.json; trace validation; check_repo negative test", traces_to: [main..f21b821]}
  - {id: R14, verdict: PASS, verify: local, formal: none, evidence: evidence/R14.json + AGENTS.md / reviewer.md, traces_to: [main..f21b821]}
  - {id: R15, verdict: PASS, verify: local, formal: checked, evidence: "formal/R15.json; ElectionV096 counterexample", traces_to: [main..f21b821]}
  - {id: N1, verdict: PASS, verify: local, formal: none, evidence: evidence/N1.json + gate map, traces_to: [SKILL.md]}
  - {id: N2, verdict: PASS, verify: local, formal: none, evidence: "invariant 10 identical to 0.9.6's", traces_to: [AGENTS.md, check_tasks.py]}
  - {id: N3, verdict: PASS, verify: local, formal: none, evidence: "AST import scan; check_neutral ok; models.yml pin", traces_to: [framework/tools, models.yml]}
  - {id: N4, verdict: PASS, verify: local, formal: none, evidence: "verdicts/audit-8-context-free.md PASS-WITH-DEBT", traces_to: [audit-8]}
blockers:
  - requirement: R3 (and R10 through it)
    clause: "Threat model: the sensors SHALL keep accidents out of a re-run: ... an untracked or ignored file ... On a re-run they SHALL never pass what the plain run fails."
    problem: >
      A probe runs in HEAD's checkout, but with the caller's PATH. check_formal's run_cmd
      goes further and passes the whole environment. An activated in-repo virtualenv
      (`.venv/`, gitignored) is the most common Python setup, and it puts
      `<repo>/.venv/bin` first on PATH. So a tool that exists only as an ignored file
      inside the repository decides the probe. unclean() lets ignored files through by
      design. The checkout does not contain the file, but the absolute PATH entry still
      reaches it in the working tree. R3's carve-out covers only "a tool outside the
      repository -- on PATH or named by an environment variable". This tool is inside the
      repository. The same path is open to any kept variable whose value points into the
      repository (e.g. a `$TLA2TOOLS_JAR` under an ignored cache dir).
    fix_hint: "on a re-run, map every PATH entry and every passed variable value that lies under the repository root to the same path in HEAD's checkout, or refuse with a message (in both probe() and run_cmd); add a self-test case"
    repro: |
      git init; .gitignore = ".venv/"; .aidlc/requirements.md = "- **R1** — tool prints ok / *Verify*: local";
      app.py; commit (sha S); .aidlc/evidence/R1.json = {id R1, verify local, command "mytool",
        target "mytool in the checkout", expect "tool ok", observed "tool ok", result pass, sha S}; commit;
      edit app.py; commit                                  (R1 is now stale)
      .venv/bin/mytool = '#!/bin/sh\necho tool ok' (chmod +x; ignored; git status --porcelain is empty)
      check_live.py                                  -> rc 1 "R1: stale -- code changed since S"
      PATH=$PWD/.venv/bin:$PATH check_live.py --rerun -> rc 0 "live: ok"
      check_live.py --rerun (venv not on PATH)        -> rc 1 "re-run exited 127: mytool: command not found"
      fresh clone of HEAD, its .venv/bin on PATH      -> rc 1
      Through the ledger too (TASKS.md signed, "- [x] R1"): check_tasks.py -> rc 1 "Done but not live: stale";
      PATH=$PWD/.venv/bin:$PATH check_tasks.py --rerun -> rc 0 "tasks: ok"
    loop_back_to: implementation
  - requirement: R3 (and R10 through it)
    clause: "Threat model: the sensors SHALL keep accidents out of a re-run: ... what an earlier probe left behind ... On a re-run they SHALL never pass what the plain run fails."
    problem: >
      HeadTree resets the checkout between probes. But every probe gets the caller's own
      TMPDIR, and so does every formal check (run_cmd). A file that one probe writes there,
      such as a build cache or tool output, is still present when the next probe runs. The
      next probe can then pass only because of it. The re-run's verdict depends on probe
      order: the same item fails when it runs alone. HeadTree's docstring states writes
      outside the checkout as a limit (from C12, which predates the threat-model ruling).
      The signed out-of-scope is narrower: only a probe that sets out to fool the sensor by
      rewriting git's objects, config or refs. A cache in $TMPDIR is an accident, not an
      attack. HOME cannot be isolated, because live probes need its credentials, so it may
      stay a stated limit. TMPDIR can be isolated cheaply.
    fix_hint: "give each probe and each formal command its own TMPDIR inside HeadTree's temp dir, emptied by get(); state HOME as the remaining limit; add a self-test case"
    repro: |
      git init; .aidlc/requirements.md = R1, R2, both "*Verify*: local"; a.py; commit (sha S)
      R1.json command 'mkdir -p "$TMPDIR/qa5-cache" && echo built > "$TMPDIR/qa5-cache/out" && echo r1 ok', expect "r1 ok", sha S
      R2.json command 'cat "$TMPDIR/qa5-cache/out"', expect "built", sha S; commit; edit a.py; commit (both stale)
      check_live.py                                                -> rc 1 (R1, R2 stale)
      check_live.py --rerun --only R2 --requirements .aidlc/requirements.md -> rc 1 "R2: re-run exited 1: No such file"
      (empty the cache) check_live.py --rerun                      -> rc 0 "live: ok"
    loop_back_to: implementation
debts:
  - "Carry forward D1-D5, D9, D10, D12-D21 as listed in TASKS.md."
  - "check_tasks --self-test has no case that asserts the reason 'Done but not formal'. Its 'Done without evidence' case asserts only the live reason. The behaviour is correct (checked in a toy), but R3's Property names the self-test as its proof."
  - "check_live --rerun accepts stale or orphan evidence when a local re-run passes, while check_formal --rerun still reports it as stale. Read literally, this already lets a re-run pass what the plain run fails. State which is meant (carried from final 2)."
  - "N4.json probes verdicts/audit.md, the first audit, not audit-8. No audit covers the 481 changed lines outside proposals/ since b572f8f (C16, the index-flag and at_head fixes included)."
  - "tools/live-allow.txt exempts every line of check_live.py (regex \\S), as stated in C11."
notes:
  - "CI was not observable from here. Every step of checks.yml and models.yml ran locally at f21b821 and was green."
  - "R3 and R10 are honestly In progress in TASKS.md (2/5, stalled 0/3). This round's B1/B2 are attempt 3 for both. The other 17 items are Done with evidence at f50e477, still fresh at f21b821 (the delta is evidence JSON only)."
  - "These regressions held in toys: probe leftovers inside the checkout (a file, a directory, a commit in the worktree) are gone before the next probe. A skip-worktree edit, an untracked file and a gitignored ledger HEAD lacks are each refused."
  - "Waste is the auditor's lane. Nothing is noted for it beyond the D-items."
```

Retrospective: the sensors, the models and every acceptance command are green. The
checkout boundary holds for what is inside the checkout. Both new gaps come from what a
probe inherits from outside it: PATH entries that reach back into the repository, and a
shared TMPDIR. Next time, list every input a probe inherits (cwd, PATH, the other
variables, the temp dir, HOME) before testing the tree itself.
