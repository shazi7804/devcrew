Signed: requirements.md sha256:7b665be99e78 · design.md sha256:7b44072f92d2
Gate: 🔴 ship — awaiting CEO

## Done
- [x] R1 TASKS.md defined as the only ledger
- [x] R2 every requirement ID exactly once
- [x] R4 check_tasks.py, the drift halt as code
- [x] R5 every host uses TASKS.md
- [x] R6 three batches, every former gate mapped
- [x] R7 five interrupts, each raised by a machine; a judgment is a Cn
- [x] R8 pre-authorized actions; anything else decided and recorded
- [x] R9 Property · Formal · Conformance
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
- [~] R3 Done only with live + formal evidence — verifying · qa · 2/5 stalled 0/3 · next: QA's two blockers (index flags, an ignored ledger HEAD lacks) fixed test-first; one context-free QA + Security round
- [~] R10 check_formal.py — verifying · qa · 2/5 stalled 0/3 · next: with R3 (C16)

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
- [ ] C12 after QA round 5, the --rerun scans read HEAD's blobs from the object store and each probe's checkout is reset with no index, sparse pattern, worktree config or hook carried over; accepted as a stated limit (HeadTree's docstring) that a probe runs with the user's shell and can still write outside the checkout or into the repo's shared refs and config; after QA rounds 6-7, a symlink at HEAD reads as the file it resolves to in HEAD's tree, component by component, and one that does not resolve (out of the tree, absolute, a loop, another case, two names that differ only in case) is reported, not skipped; the blobs are read once before any command runs and never after, and --src is read by git over HEAD -- undo: revert the commits after b22f5dc
- [ ] C13 the CEO ruled on the loop-bound (2026-10-09, 「依據你建議。該修就修」): threat model A -- a probe is trusted, the sensors keep accidents out and the re-run is never weaker than the plain run (R3, re-signed sha256:040a58119cd0); Loop A for R3/R10 restarts at 1/5; QA round 9's three blockers fixed test-first -- undo: revert R3's Threat model and re-sign
- [ ] C14 the context-free reviewer found ElectedAfterGone covers only a session that is starting; added ElectedOnceGone (a worker whose holder crashed is elected, or none is left alive) to Election.tla, ElectionLive.cfg and R12's Property, with ElectionOnceBroken.cfg (0.9.6's start-only takeover) failing it -- re-signed -- undo: drop the property and its cfg
- [ ] C15 the reviewer's R3 blocker (a probe that runs a tool outside the repository) is ruled the environment, not the tree, under the CEO's threat model; R3 now says so -- re-signed -- undo: revert that sentence
- [ ] C16 the CEO ruled on the second loop-bound (2026-10-09, 「A」): close the whole class -- a re-run refuses a working tree with any uncommitted or untracked file, and --deployed runs in HEAD's checkout -- and restart Loop A for R3/R10 at 1/5 -- undo: revert the commit that adds the clean-tree rule
- [ ] D1 SKILL.md grew 17% and is in every role's prompt: move Formal verification and the hash detail to contracts/ files only orchestrator, qa and implementers load (R6 keeps the gate map)
- [ ] D2 the models job ran 9 m 56 s on a loaded machine: record CI's own time in the R12/R13 evidence once it has run
- [ ] D3 ElectionV096.tla repeats Election.tla's lifecycle layer
- [ ] D4 check_formal.run_cmd beside check_live.probe -- fold into D9
- [ ] D5 the demotion rule is stated in three places
- [ ] D9 check_tasks --rerun runs identical commands repeatedly: memoize per invocation
- [ ] D10 boot.py beat: import subprocess lazily; write the hint files only on change
- [ ] D12 a SIGTERM during a re-run leaves the HEAD checkout registered (finally does not run on a signal): prune stale devcrew worktrees on the next run
- [ ] D13 the per-probe reset drops the index every time, so checkout rewrites the whole tree per probe (2.3-3.1 s on a 124 MB tree): drop it only when ls-files -v shows a flag, once Security rules that is as sound; Security's ruling: sound only with an allow-list of `H` tags, trustctime/checkStat/ignoreStat pinned, sparse and worktree config still dropped, and a same-size mtime-restored self-test
- [ ] D14 HeadTree.files() reads a non-code symlink's target that no check reads: drop `or r in dest` from its read filter
- [ ] D15 check_live and check_formal each load evidence, filter --only and compile `expect`: one helper in check_live (audit, medium)
- [ ] D16 small duplications: the self-test git fixture (4 copies), Aidlc.cfg and AidlcLive.cfg exploring one state space twice, rev-parse HEAD beside tree.head(), a repeated check_tasks case (audit, low)
- [ ] D17 boot.py writes its session hint into the shared temp dir following symlinks: use a per-user 0700 dir and O_NOFOLLOW (security)
- [ ] D18 the evidence secret pattern misses common credential shapes (Stripe, JWT, Google keys, Basic auth, Slack webhooks, cookies): widen it or redact by default (security)
- [ ] D19 role permissions: on KiroCrew every role, reviewer and auditor included, may spawn and write memory; on Claude Code the auditor keeps Bash -- deny those in the adapters (security)
- [ ] D20 CI actions are pinned by tag, not commit sha (security, low)
- [ ] D21 formal evidence is not secret-scanned, and its commands run with the full environment (security, low)
