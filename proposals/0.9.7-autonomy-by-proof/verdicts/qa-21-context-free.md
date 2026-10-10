# QA verdict — final 12 (qa role, Claude, at 2c1049f)

Scope: a framework change, judged against proposals/0.9.7-autonomy-by-proof/requirements.md
(signed sha256:f2328d0084d0, which matches TASKS.md). I judged the end state of the tree in
a fresh clone, detached at 2c1049f and clean. The diff is main (1be4a57)..2c1049f. 2c1049f
only records evidence at 79d1994. I ran every sensor and self-test the contract names, and
each Acceptance's own command. I built my own fixture repositories to test R3's Threat
model and the R3/R4 acceptance behaviour. I did not read verdicts/ until my pass was done;
after that I used it only as a regression list.

Sensors run, with results:
- `python3 tools/check_neutral.py --self-test`: self-test ok. `python3 tools/check_neutral.py`: neutral: ok.
- `python3 framework/tools/check_live.py --self-test`: self-test ok (159 cases).
- `python3 framework/tools/check_formal.py --self-test`: self-test ok (66 cases).
- `python3 framework/tools/check_tasks.py --self-test`: self-test ok (59 cases).
- `python3 tools/check_repo.py`: repo: ok. I changed SKILL.md's `interrupts:` line in one
  run and its `batches:` line in another, and each time it failed with the difference
  named (R13).
- `python3 tools/diagram.py check $(git ls-files '*.md')`: ALIGNED.
- `python3 tools/check_models.py` (TLC from tla2tools 1.7.4, Java 21): models: ok, in 8 m 04 s.
  - Election (4,456,387 states), ElectionLive, Aidlc and AidlcLive hold.
  - ElectionV096, ElectionLiveBroken, ElectionOnceBroken, ElectionScanBroken, AidlcBroken,
    AidlcJudgmentBroken and AidlcLiveBroken each fail on the property they should.
  - The scripted, stampede and three seeded concurrent boot.py traces are accepted. The three
    boot.py mutants are rejected.
- `check_tasks.py --tasks proposals/0.9.7-autonomy-by-proof/TASKS.md --allow tools/live-allow.txt`:
  tasks: ok. With `--rerun` (same arguments): tasks: ok, in 13 m 19 s.
- `check_live.py --requirements <proposal>/requirements.md --allow tools/live-allow.txt`:
  live: ok, both plain and with `--rerun` (4 m 37 s).
- `check_formal.py --requirements <proposal>/requirements.md`: formal: ok, both plain and with
  `--rerun` (11 m 01 s). The R12, R13 and R15 checks and their vacuity runs were run again.
- `shasum -a 256` on the sensors: check_live.py a016109343dd05cc1af839483dda19ddfaaf80b9cf758ecbfeb0957398ccc16b
  (it matches the hash the sensor prints), check_formal.py 218898c7…daad, check_tasks.py
  3e4a1e91…b396. The project copy and the framework copy are the same file here.
- Every Acceptance command recorded in evidence/*.json was run at this tree. Each exits 0 with
  its expected output.

My own checks, each in a small fixture git repo with the sensors run from outside it:
- **R3 Acceptance.**
  - A `[x]` with good live evidence but no formal evidence fails check_tasks with "Done but
    not formal", both plain and with `--rerun`.
  - A `[x]` that still carries an R1-form status fails with "a Done line carries no status".
- **R3 Threat model**, on `check_live --rerun`:
  - An untracked file: the re-run refuses it.
  - An ignored file: the re-run runs, and a probe in the re-run cannot see the file.
  - A `.git/info/attributes`, in the repository or in a linked worktree: the re-run refuses it.
  - An earlier probe rewrote the tracked `.gitattributes` to `eol=crlf`: the next probe still
    read the file as LF.
  - A `nohup` background job left by an earlier probe was killed before it could write into
    the next probe's checkout.
  - A case-colliding pair (`data.txt` / `Data.txt`): on this filesystem the user's tree is
    dirty, so the re-run refuses it.
  - A tracked symlink out of the tree: the re-run reports it. The plain scan does not, so
    the re-run is the stricter of the two.
- **R1, R5, R6, R7, R9, R11, R14.** I read and grepped each one as its Acceptance says.
  - R6: all eleven old 🔴 gates of main's SKILL.md appear in the old gate → batch table.
  - R7: orchestrator.md says a judgment becomes a `Cn` and other questions wait for the
    next batch.
  - R15: session-governance.md's A1–A5 match Election.tla's stated assumptions.
- **N2.** Invariant 10's text is byte-identical to 0.9.6's (49d78dd).
- **N3.** check_tasks.py and check_formal.py import only the standard library plus their
  sibling sensors. models.yml pins tla2tools 1.7.4, and check_models.py checks its sha256.

Regression list (prior verdicts, read after my pass): round 12's reviewer R3 blocker
(`.git/info/attributes` not refused) is fixed — `unclean()` now refuses it, including in a
linked worktree. The `.gitattributes` leftover regression stays fixed.

```yaml
verdict: PASS
scope: feature (framework)
sensors:
  lint: n/a
  typecheck: n/a
  test: pass        # check_neutral self-test; check_live (159), check_formal (66), check_tasks (59) self-tests
  build: n/a
  repo: pass        # tools/check_repo.py (set comparison proven to fail on a mutated SKILL.md); diagram.py: ALIGNED
  models: pass      # tools/check_models.py: every model holds, 7 broken variants fail, 5 real traces accepted, 3 mutants rejected
  neutral: pass     # tools/check_neutral.py
  live: pass        # check_live.py --rerun --allow tools/live-allow.txt (every item Verify: local; no --deployed needed)
  formal: pass      # check_formal.py --rerun (R12, R13, R15 checks and vacuity runs re-executed)
  tasks: pass       # check_tasks.py --rerun --allow tools/live-allow.txt
requirements:
  - {id: R1, verdict: PASS, verify: local, formal: none, evidence: "evidence/R1.json; tasks.template.md; SKILL.md and ARCHITECTURE.md §6 name TASKS.md the only ledger; every other 'ledger' mention is a host mirror that defers to it", traces_to: [main..2c1049f]}
  - {id: R2, verdict: PASS, verify: local, formal: none, evidence: "evidence/R2.json; self-test cases for missing/duplicated/unknown ID, Dn and Cn", traces_to: [main..2c1049f]}
  - {id: R3, verdict: PASS, verify: local, formal: none, evidence: "evidence/R3.json; my fixtures: a [x] failing only formal -> 'Done but not formal' (plain and --rerun); a [x] with a status fails; Threat model clauses exercised as listed above", traces_to: [main..2c1049f]}
  - {id: R4, verdict: PASS, verify: local, formal: none, evidence: "evidence/R4.json; self-test has each named case (sections, status, blocked reason, IDs, [x] without evidence, [x] with status, requirements/standards drift, 6/5)", traces_to: [main..2c1049f]}
  - {id: R5, verdict: PASS, verify: local, formal: none, evidence: "evidence/R5.json; the three adapters say TASKS.md wins, install check_tasks.py and run its self-test; no 'NOT DEFINED'", traces_to: [main..2c1049f]}
  - {id: R6, verdict: PASS, verify: local, formal: none, evidence: "evidence/R6.json; SKILL.md phase table + old gate -> batch table, all 11 old 🔴 gates mapped", traces_to: [main..2c1049f]}
  - {id: R7, verdict: PASS, verify: local, formal: none, evidence: "evidence/R7.json; the five interrupts with their sensors; Cn accepted in Todo or Done and refused in progress (self-test); orchestrator.md", traces_to: [main..2c1049f]}
  - {id: R8, verdict: PASS, verify: local, formal: none, evidence: "evidence/R8.json; Pre-authorized actions table; Phase 5 consults it; JudgmentRecorded holds, and AidlcJudgmentBroken fails it", traces_to: [main..2c1049f]}
  - {id: R9, verdict: PASS, verify: local, formal: none, evidence: "evidence/R9.json; Property/Formal/Conformance on all 7 example items + definitions; standards.template Formal verification section", traces_to: [main..2c1049f]}
  - {id: R10, verdict: PASS, verify: local, formal: none, evidence: "evidence/R10.json; check_formal --self-test (66 cases) and --rerun", traces_to: [main..2c1049f]}
  - {id: R11, verdict: PASS, verify: local, formal: none, evidence: "evidence/R11.json; vacuity block in SKILL.md's schema; self-test: no vacuity run / one that passed", traces_to: [main..2c1049f]}
  - {id: R12, verdict: PASS, verify: local, formal: checked, evidence: "evidence/R12.json, formal/R12.json re-run; check_models.py models: ok; broken variants fail", traces_to: [main..2c1049f]}
  - {id: R13, verdict: PASS, verify: local, formal: checked, evidence: "evidence/R13.json, formal/R13.json re-run; 5 real traces accepted, 3 mutants rejected; check_repo set check fails on mutation", traces_to: [main..2c1049f]}
  - {id: R14, verdict: PASS, verify: local, formal: none, evidence: "evidence/R14.json; AGENTS.md invariant 11; reviewer.md invariants_checked [1..11]", traces_to: [main..2c1049f]}
  - {id: R15, verdict: PASS, verify: local, formal: checked, evidence: "evidence/R15.json, formal/R15.json re-run; Election holds; ElectionV096 yields an AtMostOneActing counterexample; A1-A5 stated", traces_to: [main..2c1049f]}
  - {id: N1, verdict: PASS, verify: local, formal: none, evidence: "evidence/N1.json; the R6 table maps every former gate; invariants 1-11 present. The acceptance names the reviewer: this round's reviewers own it", traces_to: [evidence/N1.json]}
  - {id: N2, verdict: PASS, verify: local, formal: none, evidence: "evidence/N2.json; invariant 10 byte-identical to 0.9.6; check_tasks requires both sensors (my fixture: formal-only failure is a hit)", traces_to: [evidence/N2.json]}
  - {id: N3, verdict: PASS, verify: local, formal: none, evidence: "evidence/N3.json; stdlib only; check_neutral ok; TLA_VERSION 1.7.4 pinned with sha256", traces_to: [evidence/N3.json]}
  - {id: N4, verdict: PASS, verify: local, formal: none, evidence: "evidence/N4.json; no new role, TASKS.md one file. The acceptance is the auditor's verdict: this round's auditor owns it", traces_to: [evidence/N4.json]}
blockers: []
debts:
  - "R3/N2 test coverage: no case in check_tasks --self-test asserts the reason 'Done but not formal'. A mutant with the check_formal arm of check() deleted still prints 'self-test ok (59 cases)'. The shipped behaviour is correct (my fixture gets the exact hit, plain and --rerun). But the recorded evidence of R3 and N2 does not prove the formal half, and a regression there would pass CI. Fix: one case, a Done item whose live record is good and whose formal record is missing."
  - "N4's evidence command greps verdicts/audit.md (the round-1 audit) rather than the newest auditor verdict. Point it at the audit of the final implementation once this round's auditor reports."
  - "Done-status heuristic: an R1-form status line (em/en dash, `--`, `·`, `:`, `,`, brackets, `n/5`, `next:`) is always caught. A bare status word after `;`, `/`, `→`, `=`, `~` or backticks is not, e.g. `- [x] R1 login; verifying`. That is outside R1's form, but cheap to close."
notes:
  - "R8: SKILL.md's own Phase 6 block and its phase-table row do not name the pre-authorized list. Grepping the Phase 6 section for 'pre-authori' finds 0 matches; Phase 5 has 2. Phase 6's irreversible steps are ship-batch items, and release.md and mobile-release consult the list. Read as met, as in earlier rounds. SKILL.md (submission is ship-batch only) is stricter than release.md (pre-authorized or ship batch), so no gate is weakened. One line would align them."
  - "Code scan, outside 0.9.7's contract (0.9.6's no-fake rule), the same in plain and re-run: a directory symlink into a test path is not scanned under its production name. Example: `lib -> tests`, with `app.py` running `import lib.x` and tests/x.py defining `mock_user`, passes both scans. A file symlink to the same file is scanned as production. For the auditor or a later proposal."
  - "R3's re-proved exception also clears an `orphan` record (sha not in HEAD's history), not only a stale one. The docstring says so ('a stale or rewritten-history sha'). I read that as within 'a stale record the re-run itself proves again at HEAD'."
  - "N1 and N4 are judged by other roles in this round (reviewer and auditor). My PASS on them covers only what QA can check. Their gates stand on their own verdicts."
  - "R3 and R10 stay In progress in TASKS.md at 1/5, as their next step names. C21 is still a pending CEO ruling, and D1-D29 are logged debts. None of these is a new finding."
  - "CI was not observed at 2c1049f. I ran every step of checks.yml and models.yml locally (Python 3.14, Java 21), and all were green."
```

Retrospective:
- Worked: mutation-testing the self-test caught a coverage gap that reading the cases alone did not.
- Failed: the re-run sensors take ~30 min in sequence, most of it model checking repeated across R8, R12, R13 and R15 (D9).
- Change: add the 'Done but not formal' self-test case before the ship batch, so R3's own evidence proves both halves.
