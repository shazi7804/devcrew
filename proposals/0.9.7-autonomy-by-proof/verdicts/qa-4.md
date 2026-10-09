# QA verdict — round 4 (qa role, Claude, at c7f33ed)

I ran every sensor at c7f33ed in a clean clone. The adversarial probes ran in
throwaway repos that import the tools of a second clean clone, so the tree the
sensors ran on was never touched. Results:
- all three self-tests pass: check_live 102 cases, check_formal 45, check_tasks 48;
- check_neutral, check_repo and the diagram check pass (`ALIGNED`);
- the full `check_models.py` passes: 9 models, 5 real traces accepted, 3 mutants
  rejected, 2 min 54 s;
- `check_tasks --rerun` on the proposal passes (`tasks: ok`) in 4 min 57 s. No
  worktree is left behind and the tree is clean afterwards;
- the 32-way election race gives exactly 1 orchestrator, the 20-way takeover race
  gives exactly 1 winner, and empty stdin exits 0.

Reviewer round 5's four findings, checked against bbc708d:
- **(a) A re-run scans HEAD: holds.**
  - The fake is committed at HEAD and an uncommitted edit hides it. Then
    `check_live --rerun` reports ``src/app.js:1: `mock` ``. Without `--rerun` it
    reports nothing, which is expected: that run reads the working tree.
  - With `--rerun`, an uncommitted allow-file entry for that fake has no effect,
    and neither does deleting the allow file: HEAD's allow file is the one read.
  - check_formal: the escape hatch is committed and an uncommitted edit removes
    it. `--rerun` still reports `escape hatch` (that is the new self-test case).
- **(b) The checkout is reset between probes: partly holds.** A file one probe
  plants is gone before the next probe runs, whether it is plain, gitignored or
  inside a nested `git init` repo (`re-run exited 127 ... No such file`).
  `check_tasks` gives check_live and check_formal one HeadTree: the formal
  commands ran in the same path the live probes used. **But the reset does not
  pin HEAD's commit** (blocker 1).
- **(c) Only the record is exempt from staleness: holds.** I committed one change
  per file beside a nested requirements.md and looked for `stale`:
  - not stale: design.md, standards.md, TASKS.md, verdicts/qa.md,
    evidence/R9.json, formal/R1.json, and requirements.md (a change there is
    drift instead);
  - stale: model.tla, notes.md, formal/M.tla, evidence/helper.sh,
    evidence/x.txt, evidence/sub/h.py, sub/x.py.
- **(d) Done-status rule: holds.** These all hit: `· blocked`, `-- blocked`,
  `· blocked: CEO`, `(verifying)`, `[verifying]`, `· Verifying · qa`,
  `· BLOCKED`, `(Blocked)`, `· Next: ship`, `· stalled 1/3`, `· attempt 2/5`,
  `· attempts 2/5`, `· verifying.` and `| verifying | qa`. So does every
  round-3 case. These pass: `support re-verifying`, `add self-fixing`,
  `skip pre-building`, `co-building the API`,
  `Property · Formal · Conformance`, `build - fixing the parser` and
  `tests - building blocks`.

Worktree cleanup works on these exit paths, with `git worktree list` showing
only the main tree after each one:
- check_live.run and a check_evidence call that shares one tree: normal end,
  probe TimeoutExpired, probe RuntimeError, KeyboardInterrupt;
- check_tasks with the shared tree: a check_formal RuntimeError,
  KeyboardInterrupt, or a timeout;
- the CLI on SIGINT.

SIGTERM still leaves the worktree registered (D12, recorded).

Blockers:

1. **A probe that commits, or switches branch, inside the HEAD checkout carries
   what it wrote into every later probe.** This falsifies C9 and the HeadTree
   docstring ("nothing an earlier probe wrote"), and breaks R3's "fresh at
   HEAD": R2 passes only because of R1. `HeadTree.get()` runs
   `git reset -q --hard` with no target. That resets to the checkout's *own*
   HEAD, and the probe has moved it. This is the same class of hole as the
   nested repo that reviewer round 5 rated high. Repro, with a throwaway repo
   that has evidence R1 and R2, both `local`, sha = the first commit:
   ```
   R1 command: git checkout -q -b evil && echo 'echo temp: 21' > p.sh && git add p.sh && git -c user.email=a@b -c user.name=a commit -qm p; echo temp: 21
   R2 command: sh p.sh
   check_live.run(d, [d/"requirements.md"], rerun=True)  ->  []      (both pass)
   git branch -a (main repo, after)                       ->  evil * main
   HeadTree: probe commits q; get() again -> q exists: True, checkout HEAD == main HEAD: False
   ```
   The same sequence with `git commit` on the detached HEAD, and no branch
   switch, also passes. The fix:
   - record HEAD's sha when the tree is created;
   - reset with `checkout -q --detach -f <sha>`, then `reset -q --hard <sha>`,
     then `clean -qffdx`.

   With that patched in, the same run gives `R2: re-run exited 127: sh: p.sh: No
   such file or directory`. Add this case to the self-test.

2. **`check_tasks` never runs check_live's no-fake code scan, so a `[x]` passes
   while `check_live.py --only <ID>` fails.** R3's acceptance is "the TASKS
   sensor fails a `[x]` whose `check_live.py --only <ID>` ... fails".
   check_tasks calls `check_live.check_evidence` only, never `check_code`.
   It already did this at 1d76120, and no earlier round caught it.
   Repro: a throwaway repo with `src/app.js` = `export const t = mockTemp();`,
   `proposals/x/requirements.md` R1 `local`, its evidence at that sha, and a
   TASKS.md with `## Done` / `- [x] R1 x`:
   ```
   check_tasks.py --root <d> --tasks proposals/x/TASKS.md            -> rc 0  tasks: ok
   check_tasks.py --root <d> --tasks proposals/x/TASKS.md --rerun    -> rc 0  tasks: ok
   check_live.py --root <d> --requirements proposals/x/requirements.md --only R1 --rerun
       -> rc 1  src/app.js:1: `mock`: export const t = mockTemp();
   ```
   There are two ways to close it:
   - in check_tasks, add `check_live.check_code(tree.get() if rerun else root, None, (), [])`
     as a `Done but not live` hit;
   - or amend R3's acceptance, which needs a CEO re-sign.

   SKILL.md's gate ④ runs check_live separately, so a gate that follows SKILL
   still catches the fake. check_tasks alone does not.

```yaml
verdict: FAIL
scope: feature (framework)
sensors: {test: pass, live: pass, formal: pass, tasks: pass, models: pass, neutral: pass, repo: pass, diagrams: pass, race: pass}
blockers:
  - "HeadTree.get() resets with `reset --hard` (no target), so a probe that commits or checks out a branch in the HEAD checkout survives into later probes: R1 'git checkout -q -b evil && ... git commit -qm p', R2 'sh p.sh' -> check_live.run(rerun=True) == [] and branch 'evil' left in the main repo. Pin the sha: checkout --detach -f <sha> && reset --hard <sha> && clean -ffdx (verified to give 'R2: re-run exited 127')"
  - "R3 acceptance unmet: check_tasks calls check_evidence only, never check_code; a committed `mockTemp()` in src/app.js -> check_tasks (with and without --rerun) 'tasks: ok' rc 0, while check_live --only R1 --rerun rc 1 'src/app.js:1: `mock`'"
passed_by_hand: [R1, R2, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, N1, N2, N3]
probes:
  - "--rerun: HEAD has mockTemp(), working tree hides it -> 'src/app.js:1: `mock`'; uncommitted allow entry / deleted allow file -> still hit (HEAD's allow file read); without --rerun -> no hit (working tree)"
  - "probe-to-probe planting via plain file / gitignored file / nested `git init` repo -> 're-run exited 127'; via `git commit` in the checkout or `git checkout -b` -> R2 PASSES; via '../p.sh' (outside the checkout) -> R2 PASSES"
  - "check_tasks shares one HeadTree: the formal run_cmd cwd equals the tree the live check used; worktree removed after formal RuntimeError / KeyboardInterrupt / timeout"
  - "staleness beside proposals/x/requirements.md, one committed change each: design.md, standards.md, TASKS.md, verdicts/qa.md, verdicts/helper.sh, evidence/R9.json, formal/R1.json, requirements.md -> not stale; model.tla, notes.md, formal/M.tla, evidence/helper.sh, evidence/x.txt, evidence/sub/h.py, sub/x.py -> stale"
  - "Done-status battery, 40 malformed + 16 prose titles: all reviewer-5 (d) forms hit, re-verifying / self-fixing / pre-building / co-building pass"
  - "cleanup: check_live.run and shared-tree check_evidence on normal / TimeoutExpired / RuntimeError / KeyboardInterrupt, CLI SIGINT -> worktree list shows only the main tree; CLI SIGTERM -> worktree left registered (D12)"
  - "races: 32 elections -> 1 'only orchestrator'; 20 takeovers of an expired claim -> 1 'Took over'; empty stdin exit=0"
weak_evidence:
  - "QA-3 Done-status misses: fixed except 'x · qa 2/5' (a count after an owner, not after a joint). Still missed, all malformed: 'x · verifying (qa)', 'x · verifying by qa', 'x · building…', 'x — blocked waiting CEO', 'x • verifying', 'x / verifying', 'x; verifying', 'x ~ fixing', 'x > building', 'x · stalled', 'x · 2 / 5', 'x · in progress', 'x · wip', 'x verifying'"
  - "QA-3 false positives: 're-verifying', 'self-fixing', 'pre-building' fixed; 'ratio: 16/9 screens', 'cut size, 1/2 the code', 'handle ctx.next: in middleware' still flagged; newly flagged: 'fix (building) docs', 'list: verifying, fixing, building' (fail-closed, fixed by rewording)"
  - "QA-3 shared HeadTree: closed for plain, ignored and nested-repo files; open for a probe that commits or switches branch (blocker 1) and for a file a probe writes outside the checkout (the per-invocation temp dir, '../p.sh'). A probe can also leave a branch in the main repo's shared refs"
  - "QA-3 SIGTERM: unchanged, now recorded as D12 (prune on the next run); results not affected"
  - "QA-3 whole-contract-dir exemption: closed (only the record is exempt). verdicts/** is exempt for any file type, so a helper placed in verdicts/ makes nothing stale. That is the stated rule, noted only because a non-JSON file in evidence/ does make evidence stale"
  - "QA-3 auditor coverage: audit-3 (at 1d76120) now covers 0417190 and 7d7aff4; bbc708d (+99 lines check_live, +34 check_tasks, +26 check_formal) has no audit round, and N4 is not re-judged here"
  - "on --rerun the evidence JSON is read from the working tree: an uncommitted edit that swaps a failing committed command ('exit 3') for 'echo temp: 21' makes the re-run pass with no hit. The evidence dir is exempt from staleness, so nothing flags it. Moot in CI, where the working tree is HEAD"
  - "a requirements.md at the repo root exempts only itself, design.md, standards.md and TASKS.md, so a root-level formal/R1.json or verdicts/ change makes live evidence stale (fail-closed; the default STATE layout is nested and unaffected)"
```

Retrospective:
1. Three of reviewer round 5's four findings are fully fixed: the HEAD scans,
   the narrowed staleness exemption and the Done-status forms. Each was shown
   by a probe against c7f33ed, not by reading the diff (the old code was not
   re-run here).
2. "Reset before every probe" means two things: delete what the probe added, and
   return to the commit being proven. bbc708d did the first. A probe can move the
   checkout's HEAD, so a reset with no target does not do the second. Pinning the
   sha at creation fixes it in one line.
3. The R3 composition gap was already there at 1d76120, and three QA rounds and
   five review rounds missed it. They checked check_tasks against check_live's
   *evidence* half and never against the whole `check_live --only` command that
   the acceptance names. Next round, run the acceptance's exact command beside
   the sensor that claims to check it.
