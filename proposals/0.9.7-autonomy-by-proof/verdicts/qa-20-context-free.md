# QA verdict — final 11 (qa role, Claude, at 22565c0)

Scope: framework change, judged against proposals/0.9.7-autonomy-by-proof/requirements.md
(Signed sha256:f2328d0084d0, matches TASKS.md). Judged on the end state of the tree in
a fresh clone checked out at 22565c0 (detached, clean). Every sensor and self-test the
contract names was run, and so was each Acceptance's command. I wrote my own fixture
repositories for R3's Threat model and the R3/R4 acceptance behaviour. I did not read
verdicts/ until this pass was finished; after it I used verdicts/ only as a regression
list (QA round 3's `.gitattributes` leftover and the security round's shared-stash
blocker were both re-run and are fixed).

Sensors run, with results:
- `tools/check_neutral.py --self-test`: self-test ok. `tools/check_neutral.py`: neutral: ok.
- `framework/tools/check_live.py --self-test`: self-test ok (155 cases).
- `framework/tools/check_formal.py --self-test`: self-test ok (66 cases).
- `framework/tools/check_tasks.py --self-test`: self-test ok (59 cases).
- `tools/check_repo.py`: repo: ok. Mutating SKILL.md's `interrupts:` line, or adding a
  row to its interrupt table, makes it fail with the difference named (R13).
- `tools/diagram.py check $(git ls-files '*.md')`: ALIGNED.
- `tools/check_models.py` (TLC from tla2tools 1.7.4, Java 21): models: ok. Election
  (4,456,387 states) and ElectionLive hold. Aidlc and AidlcLive hold. ElectionV096,
  ElectionLiveBroken, ElectionOnceBroken, ElectionScanBroken, AidlcBroken,
  AidlcJudgmentBroken and AidlcLiveBroken each fail on the expected property. The
  scripted, stampede and three seeded concurrent boot.py traces are accepted, and the
  three seeded boot.py mutants are rejected. 7 m 48 s on this machine.
- `check_tasks.py --tasks proposals/0.9.7-autonomy-by-proof/TASKS.md --allow tools/live-allow.txt`: tasks: ok.
- `... --rerun` (same args): tasks: ok (12 m 23 s; re-runs every Done item's probes and formal checks).
- `check_live.py --requirements <proposal>/requirements.md --allow tools/live-allow.txt`, plain and `--rerun`: live: ok. Both cover all 19 items, R3 and R10 included.
- `check_formal.py --requirements <proposal>/requirements.md`, plain and `--rerun`: formal: ok
  (the R12, R13 and R15 checks and vacuity runs were all re-executed).
- The clone was still clean after every run.

Checked by hand, with my own fixtures (each one built as a small git repo, with the sensors run from outside it):
- R3 Acceptance: (a) the live record is fresh and the formal record's vacuity run passed.
  check_tasks fails ("Done but not formal ... no vacuity run that failed"), plain and on
  re-run. (b) a `[x]` line carries a status: it fails "a Done line carries no status".
  (c) a probe that exits 1 at HEAD fails on the re-run.
- R3 Threat model:
  - Uncommitted edit: the re-run refuses it ("commit or stash").
  - Untracked file: the re-run refuses it.
  - Ignored file: the re-run runs, and a probe asserting the file is absent passes, so the file takes no part.
  - Leftovers from an earlier probe: the next probe saw no file, no nested `.git` dir and an empty TMPDIR. A background job that redirects its output was killed when its probe ended.
  - A case-colliding pair (src/app.js, src/App.js): reported on the re-run.
  - A user's stash: the probe's checkout cannot see it.
  - A stale local record re-proved at HEAD passes. That is the signed exception.
  - A stale formal record stays a hit on the re-run.
- R1, R5, R6, R7, R9, R11 and R14: read and grepped as their Acceptance says. N2: invariant
  10 is byte-identical to 0.9.6's (feat/0.9.6-live-verification). N3: check_tasks.py and
  check_formal.py import only the standard library plus the sibling sensors, and models.yml
  pins tla2tools 1.7.4 (check_models.py checks its sha256).

```yaml
verdict: PASS
scope: feature (framework)
sensors:
  lint: n/a
  typecheck: n/a
  test: pass        # check_neutral, check_live (155), check_formal (66), check_tasks (59) self-tests
  build: n/a
  repo: pass        # tools/check_repo.py; tools/diagram.py check: ALIGNED
  neutral: pass     # tools/check_neutral.py
  models: pass      # tools/check_models.py: 11 configs as expected, 5 traces accepted, 3 mutants rejected
  live: pass        # check_live.py --rerun over all 19 items (Verify: local; no --deployed applies)
  formal: pass      # check_formal.py --rerun over all 19 items
  tasks: pass       # check_tasks.py plain and --rerun, --allow tools/live-allow.txt
requirements:
  - {id: R1,  verdict: PASS, verify: local, formal: none,    evidence: evidence/R1.json + tasks.template.md, SKILL.md, ARCHITECTURE.md §6}
  - {id: R2,  verdict: PASS, verify: local, formal: none,    evidence: evidence/R2.json + check_tasks self-test (missing/duplicated/unknown, Dn, Cn)}
  - {id: R3,  verdict: PASS, verify: local, formal: none,    evidence: evidence/R3.json + own repros (formal-only failure, Done with a status, Threat model cases)}
  - {id: R4,  verdict: PASS, verify: local, formal: none,    evidence: check_tasks --self-test, every listed case asserting its reason}
  - {id: R5,  verdict: PASS, verify: local, formal: none,    evidence: hosts/*.md install check_tasks.py, run its self-test at verify, "TASKS.md wins"; no "NOT DEFINED"}
  - {id: R6,  verdict: PASS, verify: local, formal: none,    evidence: SKILL.md phase table + former-gate -> batch table, none unmapped}
  - {id: R7,  verdict: PASS, verify: local, formal: none,    evidence: SKILL.md five interrupts with sensors; Cn rule in check_tasks and orchestrator.md}
  - {id: R8,  verdict: PASS, verify: local, formal: none,    evidence: template table; Phase 5 consults it; JudgmentRecorded holds, AidlcJudgmentBroken fails}
  - {id: R9,  verdict: PASS, verify: local, formal: none,    evidence: requirements.template.md Property/Formal/Conformance; standards.template.md Formal verification}
  - {id: R10, verdict: PASS, verify: local, formal: none,    evidence: check_formal --self-test (66) incl. every escape hatch; --rerun re-executes}
  - {id: R11, verdict: PASS, verify: local, formal: none,    evidence: SKILL.md schema vacuity block; check_formal refuses missing or passing vacuity}
  - {id: R12, verdict: PASS, verify: local, formal: checked, evidence: formal/R12.json re-run; models.yml; broken variants fail}
  - {id: R13, verdict: PASS, verify: local, formal: checked, evidence: formal/R13.json re-run; traces accepted, mutants rejected; check_repo set compare}
  - {id: R14, verdict: PASS, verify: local, formal: none,    evidence: AGENTS.md invariant 11; reviewer.md invariants_checked [1..11]}
  - {id: R15, verdict: PASS, verify: local, formal: checked, evidence: formal/R15.json re-run; ElectionV096 counterexample; session-governance.md A1-A5}
  - {id: N1,  verdict: PASS, verify: local, formal: none,    evidence: R6 mapping table; no loosening found; reviewer's own check is its verdict}
  - {id: N2,  verdict: PASS, verify: local, formal: none,    evidence: invariant 10 unchanged vs 0.9.6; check_tasks requires both sensors (own repro)}
  - {id: N3,  verdict: PASS, verify: local, formal: none,    evidence: stdlib imports; check_neutral ok; tla2tools 1.7.4 pinned + sha256}
  - {id: N4,  verdict: PASS, verify: local, formal: none,    evidence: auditor verdict PASS-WITH-DEBT (TASKS.md), no blocker/high}
blockers: []
debts:
  - "R3 (inside the stated scope limit, not a blocker): HeadTree.get() drops the clone's index, info/sparse-checkout and config.worktree but not info/attributes. A probe that writes .git/info/attributes (`* text eol=crlf`) changes the bytes every later probe checks out. Repro: R1 writes it and prints ok1; R2 is `od -c data.txt | grep -q '\\r' && echo CRLF`, expecting CRLF. `--only R2` fails, but the full `--rerun` passes. The Threat model rules out a probe that rewrites git's objects, config or refs, and this is git-dir state of the same kind. Dropping info/attributes alongside sparse-checkout is a one-line fix."
notes:
  - "R8: SKILL.md's own Phase 6 block does not name the pre-authorized list. Phase 5's paragraph covers every high-risk action, and release.md consults the list. But Phase 6's GATE says submission is ship-batch only, while release.md also allows a pre-authorized submission. This is the same as earlier rounds' note, and it overlaps the CEO's open C21. Aligning the two texts would remove the ambiguity."
  - "R3: a record whose sha is orphaned (not in HEAD's history) and that a local re-run proves at HEAD is passed, like a stale one. I read that as within C20's re-proved-record exception."
  - "R3: a re-run is stricter than the plain run where the tree has a symlinked evidence directory, an ignored allow file, or a working-tree-encoding attribute on a scanned file. It fails closed, which the contract permits."
  - "R4: the self-test's '[x] without fresh evidence' case uses missing evidence. Stale evidence is covered by check_live's self-test, and a formal-only failure was shown by my repro."
  - "R11: SKILL.md describes the vacuity block in prose (a run that must fail and did, printing its expect). The exact keys (command, expect, observed, result: fail) are in check_formal.py's docstring, which SKILL.md names as the full spec."
  - "R3 and R10 are still `In progress` in TASKS.md (4/5, stalled 0/3). Every sensor passes on their evidence at HEAD. Moving them to Done is the orchestrator's step before the ship batch."
  - "N2's 'invariant 10 unchanged' is judged against 0.9.6, which this branch carries (the contract depends on it; main does not yet have invariant 10)."
```

Retrospective: (1) Running the sensors on my own fixture repos was faster and sharper than
reading the 1,900-line sensor. (2) I looked at the reset ordering because of an earlier
blocker and found a neighbouring state file (info/attributes) still carried between
probes. (3) Next time, start the 12-minute check_tasks re-run in the background before
any reading.
