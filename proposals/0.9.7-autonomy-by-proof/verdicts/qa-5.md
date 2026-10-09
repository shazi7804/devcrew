# QA verdict — round 5 (qa role, Claude, at 93d1d60)

I ran every sensor at 93d1d60 in a clean clone. The adversarial probes ran in
throwaway repos that import the tools of a second clean clone, so the tree the
sensors ran on was never touched. Results:
- all three self-tests pass: check_live 104 cases, check_formal 45, check_tasks 51;
- check_neutral, check_repo and the diagram check pass (`ALIGNED`);
- the full `check_models.py` passes: 9 models, 5 real traces accepted, 3 mutants
  rejected, 2 min 49 s;
- `check_tasks --allow tools/live-allow.txt --rerun` on the proposal passes
  (`tasks: ok`) in 5 min 10 s. No worktree is left behind and the tree is
  clean afterwards;
- the 32-way election race gives exactly 1 orchestrator, the 20-way takeover race
  gives exactly 1 winner, and empty stdin exits 0.

QA round 4's two blockers, checked against 94ab9e3:
- **Blocker 1 (a probe's commit or branch switch carries into later probes):
  fixed for what round 4 reported.** In a throwaway repo, R1 plants something
  and R2 runs it. Each of these R1 probes now leaves R2 failing with `re-run
  exited 127 ... No such file`:
  - commit on a new branch;
  - commit on the detached HEAD;
  - a file written to `../p.sh`;
  - a file written to `../dd/p.sh`.

  The fix also undoes `--assume-unchanged` on a tracked file (`re-run exited 3`).
  The new self-test cases cover the commit and the `../` file. **But other
  escapes are still open** (blocker 1 below).
- **Blocker 2 (check_tasks skipped the code scan): fixed.** I ran the
  acceptance's exact commands beside the sensor on the real tree:
  - `check_live.py --only <ID>` for each of the 19 IDs, with no `--allow`:
    rc 1, 83 hits each. `check_tasks` with no `--allow`: rc 1, the same 83 hits.
  - the same with `--allow tools/live-allow.txt`: all 19 give `live: ok`, and
    `check_tasks` gives `tasks: ok`.
  - with `--rerun` and `--allow`: all 19 give `live: ok`, and `check_tasks
    --rerun` gives `tasks: ok`.
  - with `--rerun` and no `--allow`: `check_live --only R3` gives rc 1 with
    83 hits; `check_tasks --rerun` gives rc 1 with 83 code-scan hits and no
    other hit.
  - `check_formal.py --only <ID>`: all 19 give `formal: ok`. With `--rerun`,
    R12, R13 and R15 also give `formal: ok`.

  In 13 throwaway-repo cases, each run with and without `--rerun`, check_tasks
  and `check_live --only R1` agreed every time:
  - the mock alone;
  - an allow file committed, and an allow file uncommitted (on a re-run HEAD's
    allow file is read, so both say "No such file");
  - the mock only in the working tree, and the mock committed but hidden by an
    uncommitted edit;
  - a mock inside and outside `--src`, and one covered by `--test`;
  - an allow entry for the wrong path, a too-broad entry, a whole-file `\S`
    entry and a missing allow file;
  - `MOCK_DATA`.

**tools/live-allow.txt, judged entry by entry:**
- `check_formal.py make a lazy fake fail`: narrow, one prose line. Justified.
- `check_tasks.py fake-requirements\.md|mockTemp|a mock`: narrow. It matches the
  6 self-test decoy lines and would also exempt a real `mockTemp` or "a mock" in
  that file. Justified.
- `check_live.py \S`: **a whole-file exemption.** Without it there are 76 hits,
  spread over the regex tables, docstrings, messages and the self-test, so a
  per-line pattern would be long. As written, though, any fake added to
  check_live.py (for example `return mock_reading()`) passes the scan, and
  check_live.py is installed into every project. `allowed()`'s "cannot exempt
  everything" guard does not catch it: `\S` does not match `""`, and BROAD is
  only tested for wildcard globs. The entry is disclosed as C11 for the CEO to
  tick, so it is not hidden. It is weak evidence, not a blocker.

Blockers:

1. **A probe can still change what the `--rerun` code scan reads, so a committed
   mock passes both `check_live --only <ID> --rerun` and `check_tasks --rerun`.**
   It can also plant state for a later probe whose own command looks harmless.
   This falsifies the HeadTree docstring and C9: "a scan there read it -- no
   uncommitted change ... nothing an earlier probe wrote". It is the same class
   as round 4's blocker 1. The reset pins the commit, but it keeps three kinds of
   state:
   - the checkout's index flags;
   - its sparse-checkout state;
   - hooks, config and attributes from the repo's shared git dir. These run
     during the reset itself.

   Repro, a throwaway repo with `src/app.js` = `export const t = mockTemp();`
   committed, R1 `local`, its evidence at that sha, and TASKS `- [x] R1 a`:
   ```
   R1 command: git update-index --skip-worktree src/app.js && echo 'export const t = 3;' > src/app.js; echo temp: 21
     check_live.py --root <d> --requirements proposals/x/requirements.md --only R1 --rerun  -> rc 0  live: ok
     check_tasks.py --root <d> --tasks proposals/x/TASKS.md --rerun                          -> rc 0  tasks: ok
   R1 command: git sparse-checkout set --no-cone /proposals/ >/dev/null 2>&1; echo temp: 21
     check_live ... --only R1 --rerun -> rc 0 live: ok;  check_tasks --rerun -> rc 0 tasks: ok
   R1 command: (writes $(git rev-parse --git-common-dir)/hooks/post-checkout that runs
               `git update-index --skip-worktree src/app.js; echo "export const t = 3;" > src/app.js`); echo temp: 21
     check_live ... --only R1 --rerun -> rc 0 live: ok   (and the hook stays installed in the repo)
   R1 command: git config filter.qq.smudge 'sed s/mockTemp/realTemp/'; git config filter.qq.clean cat;
               echo '*.js filter=qq' > $(git rev-parse --git-common-dir)/info/attributes; echo x >> src/app.js; echo temp: 21
     check_live ... --only R1 --rerun -> rc 0 live: ok
   Without the R1 trick (command `echo temp: 21`): both rc 1, `src/app.js:1: `mock``.
   ```
   The same tricks also carry from probe to probe. R1 sets `--skip-worktree` on a
   committed `fail.sh` (`exit 3`) and overwrites it, and then R2 `sh fail.sh`
   passes. R1 runs `sparse-checkout`, or sets worktree-config sparse, and then R2
   `test ! -e fail.sh && echo temp: 21` passes. check_formal's escape-hatch scan
   reads the same `tree.get()` on `--rerun`. I found that by reading the code
   (line 247) and did not probe it.

   Fix:
   - (a) The scans should read HEAD's blobs from the object store at the pinned
     sha, not files in a checkout. For example, `git --no-replace-objects
     ls-tree -r -z <sha>` and then `cat-file --batch`, which applies no filter
     or attribute. This closes all four cases above for the scan.
   - (b) For probes, before each reset:
     - delete the worktree's `index`, `info/sparse-checkout` and
       `config.worktree`;
     - run the checkout, reset and clean with
       `-c core.sparseCheckout=false -c core.hooksPath=/dev/null`.

     I tested (b) on a copy: it closes skip-worktree, sparse, worktree-config
     and the hook, for probes and for the scan, and the check_live self-test
     still passes (104). On its own, though, it re-opens the smudge-filter case,
     because a fresh index rewrites every file through the filter. So (a) is
     still needed for the scan.
   - (c) Record as a stated limit, the way C4 is recorded, what no checkout
     reset can undo: a probe runs with the user's shell, so it can write
     outside the per-invocation temp dir (`../../x`, an absolute path such as `$HOME/x`) and into the
     repo's shared refs, stash, config and hooks.

   Add the skip-worktree and sparse cases to the self-test.

```yaml
verdict: FAIL
scope: feature (framework)
sensors: {test: pass, live: pass, formal: pass, tasks: pass, models: pass, neutral: pass, repo: pass, diagrams: pass, race: pass}
blockers:
  - "--rerun code scan reads a checkout a probe can still alter: R1 'git update-index --skip-worktree src/app.js && echo \"export const t = 3;\" > src/app.js; echo temp: 21' over a committed 'export const t = mockTemp();' -> check_live --only R1 --rerun rc 0 'live: ok' and check_tasks --rerun rc 0 'tasks: ok' (without the trick both rc 1 'src/app.js:1: `mock`'). Same with 'git sparse-checkout set --no-cone /proposals/', a post-checkout hook in the shared hooks dir, or a smudge filter in shared config + info/attributes. Probe-to-probe: skip-worktree or sparse in R1 makes an innocuous R2 pass. Fix: scan HEAD's blobs from the object store at the pinned sha; per probe drop index/sparse-checkout/config.worktree and reset with -c core.sparseCheckout=false -c core.hooksPath=/dev/null; state the shared-git-dir / outside-temp-dir limit"
passed_by_hand: [R1, R2, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, N1, N2, N3]
probes:
  - "round-4 blocker 1: R1 commits on a new branch / on detached HEAD / writes ../p.sh / writes ../dd/p.sh, R2 runs it -> 're-run exited 127'; --assume-unchanged on a tracked failing script -> 're-run exited 3'"
  - "escapes still open: --skip-worktree, sparse-checkout, worktree-config sparse, post-checkout hook in the shared hooks dir, smudge filter via shared config + info/attributes (blocker 1); also git stash / git tag in R1 then 'git stash pop' / 'git checkout t' in R2, a shared-config alias, '../../x' and an absolute path -> R2 passes (outside a checkout reset; record as a limit)"
  - "round-4 blocker 2: on the real tree, check_live --only <ID> (19 IDs) vs check_tasks, with/without --rerun, with/without --allow tools/live-allow.txt -> agree every time (83 hits without --allow, ok with it); check_formal --only <ID> 19/19 ok, --rerun R12/R13/R15 ok"
  - "check_tasks vs check_live --only R1 in throwaway repos, 13 cases x {plain, --rerun}: mock, allow committed / uncommitted, mock only uncommitted, committed mock hidden by an uncommitted edit, --src inside/outside, --test glob, wrong-path allow, broad allow, whole-file \\S allow, missing allow file, MOCK_DATA -> 26/26 agree"
  - "live-allow.txt: without it 83 hits (check_live.py 76, check_tasks.py 6, check_formal.py 1); with it 0"
  - "races: 32 elections -> 1 'only orchestrator'; 20 takeovers of an expired claim -> 1 'Took over'; empty stdin exit=0"
  - "cleanup: after every sensor run and every acceptance command, git worktree list shows only the main tree and git status is clean; SIGINT cleans up; SIGTERM leaves the worktree registered (D12)"
weak_evidence:
  - "tools/live-allow.txt 'framework/tools/check_live.py \\S' exempts the whole delivered file: a real fake added to check_live.py passes the scan. allowed() rejects a regex that matches '' and BROAD only for wildcard globs, so `\\S` or `.` with a literal path exempts everything in that file; disclosed as C11. The other two entries are narrow and justified"
  - "QA-3/QA-4 Done-status misses unchanged: 'x · qa 2/5', 'x · verifying (qa)', 'x · verifying by qa', 'x · building…', 'x • verifying', 'x / verifying', 'x; verifying', 'x ~ fixing', 'x > building', 'x · stalled', 'x · 2 / 5', 'x · in progress', 'x · wip', 'x verifying' (all malformed); 'x — blocked waiting CEO' now hits"
  - "QA-4 false positives unchanged (fail-closed): 'ratio: 16/9 screens', 'cut size, 1/2 the code', 'handle ctx.next: in middleware', 'fix (building) docs', 'list: verifying, fixing, building'"
  - "QA-4 shared HeadTree: commit/branch and '../' closed; a probe still leaves branches (e.g. 'evil') in the main repo's shared refs, and can still write state that survives a reset (blocker 1 and the stated-limit list)"
  - "QA-4 evidence JSON read from the working tree on --rerun: unchanged. Committed 'exit 3' -> rc 1; an uncommitted swap to 'echo temp: 21' -> check_live and check_tasks --rerun both pass. Moot in CI, where the working tree is HEAD"
  - "QA-4 SIGTERM: unchanged, a worktree is left registered (D12)"
  - "QA-4 auditor coverage: still no audit round after audit-3 (1d76120); bbc708d and 94ab9e3 (+33 check_live, +53 check_tasks, new tools/live-allow.txt) are unaudited, and N4 is not re-judged here"
  - "QA-4 verdicts/** exempt from staleness for any file type, and the root-level requirements.md layout: stated rules, not re-probed"
  - "CI (.github/workflows/checks.yml) runs only the self-tests; nothing in CI runs check_tasks or check_live with --allow tools/live-allow.txt, and no standards.md names it, so that pass-through is exercised only by hand at the ship batch"
```

Retrospective:
1. Both round-4 blockers are fixed as reported. I checked each one with its
   round-4 repro and with the acceptance's exact command run beside the sensor,
   not by reading the diff. Running the 19 `--only` commands with and without
   `--allow` is what showed that the sensors agree.
2. "Reset to the pinned sha" only resets the commit. A git checkout also keeps
   index flags and sparse patterns, and it reads hooks, config and attributes
   from the shared git dir. A probe can change any of these. A scan that has to
   read HEAD should read HEAD's objects, not a working copy, because a working
   copy is exactly what a probe can change.
3. Next round, after the scan reads blobs, re-run this round's escape
   probes and the 26-case agreement battery. Also try `refs/replace` and
   `core.fsmonitor` against the probe checkout.
