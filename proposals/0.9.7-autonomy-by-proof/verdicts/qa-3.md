# QA verdict — round 3 (qa role, Claude, at 1d76120)

I ran every sensor at 1d76120 in a clean clone. The adversarial probes ran in a
second clean clone, so the tree the sensors ran on was never touched. Results:
- all three self-tests pass: check_live 93 cases, check_formal 44, check_tasks 42;
- check_neutral, check_repo and the diagram check pass;
- the full `check_models.py` passes: 9 models, 5 real traces accepted, 3 mutants
  rejected, 2 min 55 s;
- `check_tasks --rerun` on the proposal passes in 5 min 34 s, and no worktree is
  left behind;
- the 32-way election race gives exactly 1 orchestrator, the 20-way takeover race
  gives exactly 1 winner, and empty stdin exits 0.

I probed the two fix commits nobody had QA'd yet:
- **0417190 (the QA-2 blockers) holds.**
  - `requirements.template.md:128-129` now reads "decided by the role about to act
    and recorded as a `Cn` -- never a stop". No sentence in the framework, the
    hosts or the docs still says a judgment or an unlisted action stops the run.
  - The Done-status rule catches `-- verifying`, `· verifying · qa` and
    `· qa · 2/5`. It also catches `- verifying`, `—`/`–` with or without spaces,
    `, verifying`, `: fixing`, `· blocked on CEO`, `· next: deploy` and
    `-- verifying -- qa -- 2/5`.
  - It still passes `Property · Formal · Conformance`, `build - fixing the parser`,
    `tests - building blocks`, `parser: fixing bugs` and every line of this
    proposal's TASKS.md.
  - `AidlcJudgmentBroken.cfg` (`DropRecord = TRUE`) is in `MODELS`. Running TLC on it
    directly prints "Error: Invariant JudgmentRecorded is violated", and
    `--holds Aidlc:AidlcJudgmentBroken` exits 1.
- **7d7aff4 (the reviewer round-4 fixes) holds.**
  - A re-run runs in a `HeadTree` (a detached `git worktree` of HEAD). A probe that
    needs any of these four things now fails:
    - an untracked helper: `re-run exited 127 ... No such file`;
    - a gitignored `*.log` helper: same;
    - a helper listed in `.git/info/exclude`: same;
    - an uncommitted edit: `re-run exited 1` plus `stale`.
  - An uncommitted edit that breaks the working tree does not hide HEAD's proof
    (the re-run on HEAD is clean). Without `--rerun` the same edit is reported
    `stale`.
  - check_formal behaves the same way: an untracked check or vacuity script gives
    "re-run of the check exited 127" and "vacuity run failed for another reason".
  - A committed Markdown change to AGENTS.md, `framework/agents/qa.md`, SKILL.md,
    `docs/x.md` or another proposal's requirements.md makes both live and formal
    evidence stale. A change inside the contract dir or to TASKS.md does not.
  - The worktree is removed after a normal run, a probe timeout, an exception in
    the probe, KeyboardInterrupt, a check_formal exception and a check_formal
    timeout. `git worktree list` shows only the main tree every time.
  - R2/R3 now name the `Cn` exception. That matches check_tasks: `Cn` is allowed in
    Todo or Done, refused In progress, and carries no evidence. R13's Property says
    "sampled", which matches `formal/R13.json` (check_formal checks the two texts
    are equal) and what check_models samples (scripted, stampede, seeds 0-2).
  - R8's evidence now runs TLC (`--holds Aidlc:Aidlc`, observed "Aidlc/Aidlc:
    holds").
  - The stale comments in `Aidlc.tla` are gone.

Everything left is non-blocking and listed under weak_evidence. The Done-status
misses below are all malformed statuses: none is a fragment of the R1 format
`— <status> · <owner> · <n>/5 stalled <k>/3 · next: <step>` (whose `blocked`
must say `blocked on`). Every fragment of a well-formed status is caught.

```yaml
verdict: PASS
scope: feature (framework)
sensors: {test: pass, live: pass, formal: pass, tasks: pass, models: pass, neutral: pass, repo: pass, diagrams: pass, race: pass}
blockers: []
passed_by_hand: [R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, N1, N2, N3, N4]
probes:
  - "check_live/check_formal --rerun, probe needs an untracked / gitignored (*.log) / .git/info/exclude helper -> 're-run exited 127: sh: <helper>: No such file or directory'"
  - "probe needs an uncommitted SKILL.md edit -> 're-run exited 1' + 'stale'; uncommitted edit that breaks the working tree -> --rerun clean (HEAD's proof), no --rerun -> 'stale'"
  - "committed Markdown change to AGENTS.md, framework/agents/qa.md, SKILL.md, docs/x.md, proposals/other-change/requirements.md -> live 'stale -- code changed since b91e2985daec' and formal 'is stale'; change to the contract dir (verdicts/, notes.md, formal/x.tla) or TASKS.md -> not stale"
  - "worktree list after: normal run, probe TimeoutExpired, probe RuntimeError, KeyboardInterrupt, check_formal RuntimeError, check_formal timeout -> only the main tree"
  - "TLC -config AidlcJudgmentBroken.cfg Aidlc -> 'Error: Invariant JudgmentRecorded is violated.'; check_models --holds Aidlc:AidlcJudgmentBroken -> exit 1"
  - "Done-status rule, 41 crafted titles: every round-2 case and every well-formed-status fragment hit; Property · Formal · Conformance, build - fixing the parser, tests - building blocks, parser: fixing bugs pass"
weak_evidence:
  - "check_tasks Done-status misses malformed statuses that the pre-73271d7 rule caught: '- [x] R1 x · blocked', 'x -- blocked', 'x · blocked: CEO' (only 'blocked on' is matched, while the other three status words match bare), 'x · qa 2/5', 'x · attempt 2/5', 'x · stalled 1/3', 'x · verifying.', 'x (verifying)', 'x [verifying]', 'x | verifying | qa', 'x · Verifying · qa'. The 0417190 commit message says 'an attempt count anywhere'; the rule only catches a count straight after a joint"
  - "check_tasks Done-status false positives (fail-closed, fixed by rewording): 'support re-verifying', 'add self-fixing', 'skip pre-building', 'ratio: 16/9 screens', 'cut size, 1/2 the code', 'handle ctx.next: in middleware'"
  - "one HeadTree is shared by every probe in an invocation, so a file one probe writes takes part in the next one: an R1 probe that writes planted.sh into its cwd, then an R2 probe 'sh planted.sh' -> both pass. A fresh tree, or 'git clean -fdx && git checkout -- .' between probes, would close this"
  - "SIGTERM during a re-run (e.g. a CI cancel) leaves the worktree registered and its temp dir on disk: after 'kill -TERM', git worktree list still shows <tmp>/head. finally does not run on a signal, so nothing removes it until 'git worktree remove --force' or prune; results are not affected"
  - "drifted() exempts the whole contract dir, and contract()'s docstring calls it 'signed by hash'. Only requirements.md and design.md are signed, so an unsigned file there (notes.md, or a spec placed under <contract>/formal/) changes with no stale and no drift. A product spec kept there would not make its formal evidence stale without --rerun"
  - "no auditor round covers 0417190 + 7d7aff4 (audit-2 is at 591cf96); N4 rests on audit-2's PASS-WITH-DEBT"
```

Retrospective:
1. Both round-2 blockers and every reviewer-4 finding are fixed, and each fix
   was shown to work by a probe that fails the old code, not by reading the diff.
2. The Done-status rule is a heuristic over free text. It now catches every
   fragment of a well-formed status, but malformed statuses still get through;
   asserting "no status word after any joint" in one place would end this chase.
3. Running each re-run in a HeadTree is the right fix. What remains is the tree
   being shared between probes, and cleanup when a signal kills the process.
