Signed: requirements.md sha256:e3a031f9da07 · design.md sha256:7b44072f92d2
Gate: 🔴 ship — awaiting CEO

## Done
- [x] R1 TASKS.md defined as the only ledger
- [x] R2 every requirement ID exactly once
- [x] R3 Done only with live + formal evidence
- [x] R4 check_tasks.py, the drift halt as code
- [x] R5 every host uses TASKS.md
- [x] R6 three batches, every former gate mapped
- [x] R7 five interrupts, each raised by a machine; a judgment is a Cn
- [x] R8 pre-authorized actions; anything else decided and recorded
- [x] R9 Property · Formal · Conformance
- [x] R10 check_formal.py
- [x] R11 vacuity runs
- [x] R12 the protocol models, checked in CI
- [x] R13 boot.py trace-validated; sets in sync
- [x] R14 invariant 11
- [x] R15 the model's finding fixed, assumptions stated
- [x] N1 no gate weakened without the CEO's recorded decision
- [x] N2 formal never replaces live
- [x] N3 stdlib sensors, neutral, pinned checker
- [x] N4 small on purpose (auditor: PASS-WITH-DEBT)

- [x] C6 git stopped mid-session (Xcode licence); ran on the Command Line Tools binary until the CEO accepted the licence — resolved, the workaround is removed

## In progress

## Todo
- [ ] C1 added assumption A5 (a file operation does not fail forever) so election liveness holds — undo: drop the SF terms in Election.tla's Fairness; ElectionLive then fails, as TLC shows
- [ ] C2 kept the untracked docs/timeline.html out of git status via .git/info/exclude (local only) — undo: delete that line
- [ ] C3 the last fixes (1506e43, 73271d7 and the Cn rule) were checked by check_tasks --rerun and the models, not by another reviewer or QA round — undo: run one before merge
- [ ] C4 accepted check_formal's stated limit: it binds a check to a named tool and source, but cannot prove the program is a faithful checker; a reviewer reads that in the diff
- [ ] C5 dropped D6-D8 (mechanising the judgment stops): under the CEO's second ruling a judgment is a Cn, not a stop
- [ ] C7 after review round 4, amended the signed requirements and re-signed them (sha256:e3a031f9da07): R2/R3 now state the Cn exception the sensor already made, R13's Property says sampled runs, not every run -- undo: revert those hunks of 7d7aff4 and re-sign
- [ ] C8 a local re-run is now HEAD's proof by running in a throwaway checkout of HEAD, instead of refusing a tree with untracked or ignored files beside it -- undo: restore clean_head (7d7aff4)
- [ ] C9 after QA round 3, the HEAD checkout is reset before every probe (clean -ffdx, so a nested repo goes too) and shared by one invocation (D11 closed), and on --rerun the no-fake and escape-hatch scans read it -- QA round 4 and reviewer round 6 check it -- undo: revert the HeadTree commits after 1d76120
- [ ] C10 narrowed what is exempt from staleness beside a feature's requirements to the run's record (signed contracts, TASKS.md, verdicts/, evidence and formal JSON); a model or helper kept there now makes evidence stale -- undo: contract() returns the whole dir
- [ ] C11 after QA round 4, check_tasks runs check_live's code scan for Done items (R3: Done = `check_live --only <ID>` green), so devcrew's own tree needs tools/live-allow.txt: three exemptions, one per sensor file that names fakes to hunt them -- undo: drop the scan from check_tasks and amend R3 (a CEO re-sign)
- [ ] C12 after QA round 5, the --rerun scans read HEAD's blobs from the object store and each probe's checkout is reset with no index, sparse pattern, worktree config or hook carried over; accepted as a stated limit (HeadTree's docstring) that a probe runs with the user's shell and can still write outside the checkout or into the repo's shared refs and config -- undo: revert the commit after b22f5dc
- [ ] D1 SKILL.md grew 17% and is in every role's prompt: move Formal verification and the hash detail to contracts/ files only orchestrator, qa and implementers load (R6 keeps the gate map)
- [ ] D2 the models job ran 9 m 56 s on a loaded machine: record CI's own time in the R12/R13 evidence once it has run
- [ ] D3 ElectionV096.tla repeats Election.tla's lifecycle layer
- [ ] D4 check_formal.run_cmd beside check_live.probe -- fold into D9
- [ ] D5 the demotion rule is stated in three places
- [ ] D9 check_tasks --rerun runs identical commands repeatedly: memoize per invocation
- [ ] D10 boot.py beat: import subprocess lazily; write the hint files only on change
- [ ] D12 a SIGTERM during a re-run leaves the HEAD checkout registered (finally does not run on a signal): prune stale devcrew worktrees on the next run
