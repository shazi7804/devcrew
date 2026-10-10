# QA verdict — final 13 (qa role, Claude, at 13c8936)

Scope: a framework change, judged against proposals/0.9.7-autonomy-by-proof/requirements.md
(signed sha256:f2328d0084d0, which matches TASKS.md). The diff is main..13c8936. 13c8936 only
records evidence at 1ae32b9. I judged the end state of the tree in a fresh clone, detached at
13c8936 and clean. I ran every sensor and self-test the contract names, and each Acceptance's
own command. I built fixture repositories to test R3's Threat model. I did not read verdicts/
until my own pass was done. After that I used it only as a regression list.

Sensors run, with results (Python 3.14, Java 21, tla2tools 1.7.4):
- `tools/check_neutral.py --self-test`: self-test ok. `tools/check_neutral.py`: neutral: ok.
- `framework/tools/check_live.py --self-test`: self-test ok (162 cases).
- `framework/tools/check_formal.py --self-test`: self-test ok (66 cases).
- `framework/tools/check_tasks.py --self-test`: self-test ok (64 cases).
- `tools/check_repo.py`: repo: ok. With SKILL.md's `interrupts:` line edited in a copy, it
  fails and names the difference (R13).
- `tools/diagram.py check $(git ls-files '*.md')`: ALIGNED.
- `tools/check_models.py`: models: ok, in 7 m 13 s. Election, ElectionLive, Aidlc and
  AidlcLive hold. ElectionV096, ElectionLiveBroken, ElectionOnceBroken, ElectionScanBroken,
  AidlcBroken, AidlcJudgmentBroken and AidlcLiveBroken each fail on the property they should.
  The scripted, stampede and three seeded concurrent boot.py traces are accepted, and the
  three boot.py mutants are rejected.
- `check_tasks.py --tasks proposals/0.9.7-autonomy-by-proof/TASKS.md --allow tools/live-allow.txt`:
  tasks: ok. With `--rerun`: tasks: ok, in 20 m 02 s.
- `check_live.py --requirements <proposal>/requirements.md --allow tools/live-allow.txt`:
  live: ok. With `--rerun`, the first run had one hit: R11's probe (`check_formal.py
  --self-test`) timed out at 300 s. Other jobs were loading the machine at the time, and the
  same self-test took 5 m 42 s at 10% CPU. A second run, `--rerun --only R11,R3,R10`, gave
  live: ok in 2 m 54 s.
- `check_formal.py --requirements <proposal>/requirements.md`: formal: ok, both plain and with
  `--rerun` (16 m 58 s).
- `shasum -a 256 framework/tools/check_live.py`: aa863712…56f2. This matches what the sensor
  prints, and the framework copy is the copy that ran.
- The evidence/*.json Acceptance commands were re-run by check_tasks/check_live `--rerun`.
  Each one passed at this tree.

Requirement table (all items `Verify: local`):
- R1 PASS. tasks.template.md has the format. SKILL.md and ARCHITECTURE.md §6 call TASKS.md the
  only ledger.
- R2 PASS. The self-test fails a missing, duplicated or unknown ID, and passes Dn and Cn.
- R3 FAIL. The Acceptance cases pass. The Threat model clause "On a re-run they SHALL never
  pass what the plain run fails" does not hold for a filtered file: see blocker 1.
- R4 PASS. Every case the Acceptance lists is in the self-test, and each one asserts its reason.
- R5 PASS. All three adapters say so, the "NOT DEFINED" line is gone, and each adapter installs
  check_tasks.py and runs its self-test.
- R6 PASS. The phase table names each batch. The 11-row former-gate map leaves nothing unmapped.
- R7 PASS. SKILL.md lists the five interrupts, each with its sensor. check_tasks accepts Cn in
  Todo or Done and refuses it in progress. orchestrator.md states the Cn rule.
- R8 PASS. The template has the table. Phases 5–6 consult it. JudgmentRecorded holds, and its
  broken variant fails.
- R9 PASS. Both templates have what the Acceptance asks for.
- R10 FAIL. The self-test passes, and so does `--rerun` on the proposal. But on a re-run the
  escape-hatch scan reads only HEAD's raw blob of a filtered source: see blocker 1.
- R11 PASS. SKILL.md's schema has the vacuity block, and the sensor fails a vacuity run that is
  missing or that passed.
- R12 PASS. The models hold at their stated bounds, and the seeded broken variants yield
  counterexamples.
- R13 PASS. Real boot.py traces are accepted and the mutants are rejected. check_repo fails on a
  set difference.
- R14 PASS. AGENTS.md has invariant 11. reviewer.md checks [1..11].
- R15 PASS. ElectionV096 fails AtMostOneActing. session-governance.md names A1–A5.
- N1 PASS. The R6 map covers every former gate, and every stop removed is recorded under
  invariant 8.
- N2 PASS. Invariant 10's text is unchanged since 0.9.6 (49d78dd). check_tasks requires both
  sensors.
- N3 PASS. The sensors use only the stdlib (plus each other). check_neutral passes. TLA 1.7.4 is
  pinned with its sha256.
- N4 PASS. The audit-14 verdict is PASS-WITH-DEBT, with no blocker or high finding.

```yaml
verdict: FAIL
sensors:
  - {name: check_neutral --self-test / run, result: pass}
  - {name: check_live --self-test, result: "pass (162 cases)"}
  - {name: check_formal --self-test, result: "pass (66 cases)"}
  - {name: check_tasks --self-test, result: "pass (64 cases)"}
  - {name: check_repo, result: pass}
  - {name: diagram check, result: pass}
  - {name: check_models (TLC 1.7.4), result: "pass, 7m13s"}
  - {name: check_tasks --rerun --allow tools/live-allow.txt, result: "pass, 20m02s"}
  - {name: check_live --rerun --allow tools/live-allow.txt, result: "pass (R11 timed out at 300s once under machine load; it passed when re-run)"}
  - {name: check_formal --rerun, result: "pass, 16m58s"}
coverage:
  - {id: R1, verify: local, formal: none, verdict: PASS}
  - {id: R2, verify: local, formal: none, verdict: PASS}
  - {id: R3, verify: local, formal: none, verdict: FAIL}
  - {id: R4, verify: local, formal: none, verdict: PASS}
  - {id: R5, verify: local, formal: none, verdict: PASS}
  - {id: R6, verify: local, formal: none, verdict: PASS}
  - {id: R7, verify: local, formal: none, verdict: PASS}
  - {id: R8, verify: local, formal: none, verdict: PASS}
  - {id: R9, verify: local, formal: none, verdict: PASS}
  - {id: R10, verify: local, formal: none, verdict: FAIL}
  - {id: R11, verify: local, formal: none, verdict: PASS}
  - {id: R12, verify: local, formal: "checked / none", verdict: PASS}
  - {id: R13, verify: local, formal: "checked / trace", verdict: PASS}
  - {id: R14, verify: local, formal: none, verdict: PASS}
  - {id: R15, verify: local, formal: "checked / trace", verdict: PASS}
  - {id: N1, verify: local, formal: none, verdict: PASS}
  - {id: N2, verify: local, formal: none, verdict: PASS}
  - {id: N3, verify: local, formal: none, verdict: PASS}
  - {id: N4, verify: local, formal: none, verdict: PASS}
blockers:
  - requirement: R3 (and R10)
    clause: "R3 Threat model: 'On a re-run they SHALL never pass what the plain run fails'; R10: fails a requirement whose spec/proof sources hold an escape hatch"
    problem: >
      Round 5 (1ae32b9) fixed this for check_live's code scan only: a filtered file is now
      scanned both as its raw blob and as its filtered read. check_formal's re-run does not do
      the same. It reads formal sources, and the evidence and formal records too, through
      HeadTree.blob(), and blob() returns only got[0], the raw blob. The plain run reads the
      working tree, which holds the smudged bytes. Take a repository with an ordinary filter:
      a committed `*.tla filter=x` and a filter driver in the repo config, with the file
      checked out through it (an LFS-style setup; no probe runs, nothing is rewritten). git
      status is clean, so unclean() lets the re-run start. Plain check_formal and check_tasks
      fail on the OMITTED that is on disk. With --rerun, both pass. Security-12 named exactly
      this path ("check_formal's escape-hatch scan ... inherit the gap"), and the fix did not
      reach it. The same root cause lets a re-run pass an evidence record whose working-tree
      form says result "fail".
    phase: 3
    repro: |
      SENS=<repo>/framework/tools; T=$(mktemp -d); cd $T; git init -q
      git config user.name t; git config user.email t@t
      git config filter.hide.clean "sed s/OMITTED/ELIDED/"
      git config filter.hide.smudge "sed s/ELIDED/OMITTED/"
      echo '*.tla filter=hide' > .gitattributes; mkdir -p req/formal req/evidence spec
      printf '# r\n- **R1** — x\n  - *Verify*: local\n  - *Property*: Safe holds\n  - *Formal*: checked\n  - *Conformance*: none\n' > req/requirements.md
      printf -- '---- MODULE M ----\nSafe == TRUE\nTHEOREM Safe PROOF OMITTED\n====\n' > spec/M.tla
      printf 'import sys\nTOOL = "TLC"\nif "--broken" in sys.argv: print("is violated"); sys.exit(1)\nprint("No error has been found")\n' > spec/check.py
      git add -A; git commit -qm code; rm spec/M.tla; git checkout -- spec/M.tla; SHA=$(git rev-parse HEAD)
      # formal record: command "python3 spec/check.py spec/M.tla", sources [spec/M.tla, spec/check.py],
      #   tool TLC, bounds "1 state", expect/observed "No error has been found", result pass, sha $SHA,
      #   vacuity {command: "python3 spec/check.py spec/M.tla --broken", expect/observed "is violated", result fail}
      # live record req/evidence/R1.json: local, command "python3 spec/check.py", expect "No error", sha $SHA
      # TASKS.md: `check_tasks.py --sign requirements.md` + "## Done / - [x] R1 x / ## In progress / ## Todo"
      git add -A; git commit -qm ledger
      python3 $SENS/check_formal.py --requirements req/requirements.md          # exit 1: escape hatch in M.tla:3
      python3 $SENS/check_formal.py --requirements req/requirements.md --rerun  # exit 0: formal: ok
      python3 $SENS/check_tasks.py --tasks req/TASKS.md                         # exit 1: Done but not formal
      python3 $SENS/check_tasks.py --tasks req/TASKS.md --rerun                 # exit 0: tasks: ok
      # same for an evidence record: a filter on req/evidence/*.json whose smudge writes
      # "result":"fail" -> plain check_live exit 1 ("probe result is 'fail'"), --rerun exit 0
debts:
  - "The Done-status heuristic misses a status joined by a dash the regex does not list: '- [x] R1 a ― verifying' (U+2015), '‒' (U+2012), '−' (U+2212), and '/ blocked on x'. The defined form (` — ` plus the full status line) is caught. (note; outside R1's defined form)"
  - "The 300 s probe timeout fails a slow but sound local probe on a loaded machine: R11's check_formal --self-test took 5m42s at 10% CPU while other jobs ran. (environment; note)"
notes:
  - "The logged debts D1–D29 and the pending rulings C1–C22 were not re-raised."
  - "Other R3 accident classes I tried, all handled: untracked/ignored files, symlinks, case clashes, an earlier probe's leftovers, and the evidence-dir symlink. In each, the re-run is at least as strict as the plain run."
```

Retrospective:
- Every machine sensor is green, and all 19 items meet their Acceptance except one clause.
- The remaining gap is one helper (HeadTree.blob returns only the raw blob). It sits beside a fix that was applied to only one of its three callers.
- Fix: return or scan both reads in blob()'s callers (or refuse a re-run when the filtered and on-disk reads differ), and add a self-test for check_formal on a filtered source.
