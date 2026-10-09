# QA verdict — round 6 (qa role, Claude, at a5774be)

I ran every sensor at a5774be in a clean clone. The adversarial probes ran in
throwaway repos that import the tools of a second clean clone, so the tree the
sensors ran on was never touched. Results:
- all three self-tests pass: check_live 110 cases, check_formal 45, check_tasks 51;
- check_neutral (and its self-test), check_repo and the diagram check pass (`ALIGNED`);
- the full `check_models.py` passes: 9 models, 5 real traces accepted, 3 mutants
  rejected, 2 min 44 s;
- `check_tasks --allow tools/live-allow.txt --rerun` on the proposal passes
  (`tasks: ok`) in 5 min 14 s. No worktree is left behind and the tree is
  clean afterwards;
- the 32-way election race gives exactly 1 orchestrator, the 20-way takeover race
  gives exactly 1 winner, and empty stdin exits 0.

QA round 5's blocker, checked against 816e237:
- **The --rerun scan escapes: fixed.** A throwaway repo has
  `src/app.js` = `export const t = mockTemp();` committed, R1 `local`, its
  evidence at that sha, and TASKS `- [x] R1 a`. R1's command does the trick and
  then `echo temp: 21`. With each of these tricks, `check_live --only R1 --rerun`
  and `check_tasks --rerun` both give rc 1 `src/app.js:1: `mock``:
  - skip-worktree;
  - `sparse-checkout set --no-cone /proposals/`;
  - worktree-config sparse (`extensions.worktreeConfig` + `config --worktree
    core.sparseCheckout` + `read-tree -mu`);
  - a post-checkout hook in the shared hooks dir;
  - a smudge filter in shared config + `info/attributes`;
  - `git replace` of the blob, and of the commit;
  - `core.fsmonitor`;
  - `info/grafts`;
  - `shallow`.

  In each case one worktree is left at the end (the main one).
- **Probe-to-probe: fixed for checkout state.** R1 plants something and R2
  runs `sh fail.sh` (committed `exit 3`), or `test ! -e fail.sh`. Each of these
  R1 probes leaves R2 failing (`re-run exited 3` or `1`) in both check_live and
  check_tasks:
  - skip-worktree;
  - sparse;
  - worktree-config sparse;
  - a post-checkout hook;
  - assume-unchanged;
  - `git replace` of the blob;
  - fsmonitor;
  - `core.untrackedCache`;
  - a file ignored through the worktree's `info/exclude`.
- **What still gets through is shared repo state.** Each of these makes R2 pass:
  - a smudge filter in shared config + `info/attributes`;
  - the same filter through `core.attributesFile`;
  - `git stash` in R1 and then `git stash pop` in R2;
  - rewriting the loose object of a committed blob in the shared object store.

  The loose-object rewrite also gets the --rerun **scan** past a committed
  mock (rc 0 `live: ok` / `tasks: ok`). These are all writes to the repo's
  shared config, refs or object store, outside the checkout. HeadTree's
  docstring and C12 state that as the limit, so they are weak evidence, not
  blockers. One gap in the wording: it does not name the object store, and
  the scan could leave it out of the limit entirely (see weak_evidence).
- **But the move from the checkout to blobs opened a new hole** (blocker 1).

Round 5's 26-case agreement battery, re-run: each of the 13 cases ran plain and
with `--rerun`, and check_tasks and `check_live --only R1` agreed on the return
code and the hit list in **26/26**. The cases were:
- the mock alone;
- an allow file committed, and an allow file uncommitted (`--rerun` gives
  `--allow allow.txt: not in HEAD` in both);
- the mock only in the working tree;
- a committed mock hidden by an uncommitted edit;
- a mock inside `--src` and one outside it;
- a mock covered by `--test`;
- an allow entry for the wrong path;
- a too-broad entry (both refuse it: "cannot exempt everything");
- a whole-file `\S` entry;
- a missing allow file;
- `MOCK_DATA`.

The acceptance's exact commands, run on the real tree beside check_tasks:
- `check_live.py --only <ID>` for each of the 19 IDs, with no `--allow`:
  rc 1, 85 hits each (check_live.py 78, check_tasks.py 6, check_formal.py 1).
  `check_tasks` gives rc 1 with the same 85 code-scan hits and no other hit.
- the same with `--allow tools/live-allow.txt`: all 19 give `live: ok`, and
  `check_tasks` gives `tasks: ok`.
- with `--rerun --allow`: all 19 give `live: ok`, and `check_tasks` gives
  `tasks: ok`.
- with `--rerun` and no `--allow`: `check_live --only R3` gives rc 1 with
  85 hits; `check_tasks --rerun` gives rc 1 with 85 code-scan hits and no
  other hit.
- `check_formal.py --only <ID>`: all 19 give `formal: ok`. With `--rerun`,
  R12, R13 and R15 also give `formal: ok`.
- afterwards `git worktree list` shows only the main tree, and `git status`
  is clean.

Blockers:

1. **The --rerun code scan no longer reads a committed symlink, so a production
   file that is a symlink to a mock passes both `check_live --only <ID> --rerun`
   and `check_tasks --rerun`. The plain scan catches it, and 93d1d60's --rerun
   caught it too.** `HeadTree.files()` keeps only modes `100644`/`100755`, so a
   `120000` entry is dropped. If its target is a test fixture (exempt by
   TEST_DIR) or a non-code file (`.txt`, exempt by NOT_CODE), the fake is never
   scanned under the name that ships. The runtime still follows the link: Node
   imports `src/app.js` and runs the fixture's `mockTemp()`.

   So the gate mode is now weaker than the plain mode, and this round made it
   so. The scan() docstring says "on a re-run, over HEAD's blobs", and C12
   says the --rerun scans "read HEAD's blobs", but at HEAD this file is a blob
   (a symlink) and the scan skips it without saying so. R3 says Done = live
   evidence fresh at HEAD, where live evidence includes the no-fake scan of
   invariant 10. Here a `[x]` goes Done over a shipped fake.

   Repro, a throwaway repo:
   ```
   mkdir -p tests && mv src/app.js tests/fixture.js && ln -s ../tests/fixture.js src/app.js   # before the commit
   git ls-tree -r HEAD src  ->  120000 blob bc972b9d...  src/app.js
   R1 local, command `echo temp: 21`, evidence at that sha; TASKS `- [x] R1 a`
     check_live.py --root <d> --requirements proposals/x/requirements.md --only R1           -> rc 1  src/app.js:1: `mock`: export const t = mockTemp();
     check_tasks.py --root <d> --tasks proposals/x/TASKS.md                                  -> rc 1  Done but not live: src/app.js:1: `mock`
     check_live.py ... --only R1 --rerun                                                     -> rc 0  live: ok
     check_tasks.py ... --rerun                                                              -> rc 0  tasks: ok
     (the same two --rerun commands with the tools at 93d1d60                                -> rc 1, 1 hit each)
   The same holds for `src/app.js -> data.txt` (data.txt holds the mock): plain rc 1, --rerun rc 0.
   ```
   check_formal's --rerun source read has the same cause, but it fails closed.
   `blobs[str(src)]` raises KeyError on a symlinked spec, so the result is
   "source ... does not exist". I found that by reading the code and did not
   probe it.

   Fix:
   - in `files()`, resolve `120000` entries inside the tree: read the link blob
     as the target, normalise it against the link's directory, and follow up
     to a bound;
   - scan the target's bytes under the **link's** path, so the link's suffix
     and its non-test location decide whether it is code;
   - a link that leaves the tree or dangles has no content at HEAD: skip it,
     or report it;
   - add a self-test case, a symlink into `tests/`.

```yaml
verdict: FAIL
scope: feature (framework)
sensors: {test: pass, live: pass, formal: pass, tasks: pass, models: pass, neutral: pass, repo: pass, diagrams: pass, race: pass}
blockers:
  - "--rerun code scan drops committed symlinks (HeadTree.files() keeps only 100644/100755): src/app.js -> ../tests/fixture.js holding 'export const t = mockTemp();' -> check_live --only R1 --rerun rc 0 'live: ok' and check_tasks --rerun rc 0 'tasks: ok', while plain check_live/check_tasks rc 1 'src/app.js:1: `mock`' and the --rerun of 93d1d60 rc 1. Node runs the fixture through the link. Same with a link to data.txt. A regression of 816e237; the gate mode is now weaker than the plain one. Fix: resolve 120000 entries inside the tree and scan the target's bytes under the link's path; self-test case"
passed_by_hand: [R1, R2, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, N1, N2, N3]
probes:
  - "round-5 scan escapes (--rerun, check_live --only R1 and check_tasks): skip-worktree, sparse --no-cone, worktree-config sparse + read-tree, post-checkout hook, smudge filter + info/attributes -> all rc 1 'src/app.js:1: `mock`'; new: git replace (blob and commit), core.fsmonitor, info/grafts, shallow -> all rc 1"
  - "round-5 probe-to-probe (R1 plants, R2 'sh fail.sh' / 'test ! -e fail.sh'): skip-worktree, sparse, worktree-config sparse, post-checkout hook, assume-unchanged, git replace, fsmonitor, untrackedCache, worktree info/exclude -> R2 're-run exited 3' (or 1) in both sensors"
  - "shared-state residue (covered by the C12 limit): smudge filter via shared config + info/attributes or core.attributesFile, git stash -> stash pop, a rewritten loose object -> R2 passes; the rewritten loose object also gets the --rerun scan past a committed mock (rc 0); a probe's 'git branch evil' stays in the main repo"
  - "scan reads: a 25 MB file with the mock on line 5000001 -> caught in both modes; a filename with a newline -> caught in both; working-tree-encoding=UTF-16LE in a committed .gitattributes -> plain misses (it reads the UTF-16 checkout, NUL => binary), --rerun catches (it reads the UTF-8 blob)"
  - "agreement battery, 13 cases x {plain, --rerun} -> 26/26 agree on rc and hits"
  - "real tree: check_live --only <ID> (19) vs check_tasks: no --allow 85/85 hits, --allow ok/ok, --rerun --allow ok/ok, --rerun alone R3 85 vs 85 code hits and no other; check_formal --only 19/19 ok; --rerun R12/R13/R15 ok"
  - "races: 32 elections -> 1 'only orchestrator'; 20 takeovers of an expired claim -> 1 'Took over'; empty stdin exit=0"
  - "cleanup: after every sensor and acceptance run, git worktree list shows only the main tree and git status is clean; SIGTERM during a --rerun probe leaves 2 worktrees registered (D12)"
weak_evidence:
  - "files() reads blobs after the probes ran, so a probe that rewrites a loose object (chmod u+w + a zlib 'blob N\\0...' under the same oid) changes what the --rerun scan and check_formal's escape-hatch scan see: committed mock -> rc 0. This is outside the checkout, so the C12 limit covers it, but the limit names only 'shared refs, config and hooks', not the object store. A cheap fix removes the case: call tree.files() before the first probe, so nothing a probe does can reach the scan"
  - "files() keys by path decoded with errors='replace': two non-UTF-8 paths that decode alike collide. src/a\\376.js (mock) + src/a\\377.js (clean) -> files() has 1 entry ('export const t = 3;'), scan []. That contradicts the docstring 'every regular file'. The plain scan skips every non-UTF-8 path (root/rel with U+FFFD is not a file). Key by bytes or use surrogateescape. On macOS the --rerun checkout fails closed ('cannot check out HEAD')"
  - "a deleted loose object gives an IndexError traceback in files() ('data[at:nl].split()[2]' on '<oid> missing'), not a message. It fails closed"
  - "scan heuristics carried over from 0.9.6, the same in both modes: a NUL in the first 8 KiB ('// \\0' in a leading comment), a UTF-16 blob with a BOM, an upper-case suffix (App.JS), a directory symlink into a TEST_DIR name (src -> vendor/mocks), and gitlinks/submodules are not scanned. Obfuscation-class or out of the commit; not 0.9.7 claims"
  - "tools/live-allow.txt still has 'framework/tools/check_live.py \\S' (whole-file exemption, C11); allowed() still accepts \\S with a literal path"
  - "QA-3/QA-4 Done-status misses unchanged: 'x · qa 2/5', 'x · verifying (qa)', 'x · verifying by qa', 'x · building…', 'x • verifying', 'x / verifying', 'x; verifying', 'x ~ fixing', 'x > building', 'x · stalled', 'x · 2 / 5', 'x · in progress', 'x · wip', 'x verifying' all 'tasks: ok'; 'x — blocked waiting CEO' hits"
  - "QA-4 false positives unchanged (fail-closed): 'ratio: 16/9 screens', 'cut size, 1/2 the code', 'handle ctx.next: in middleware', 'fix (building) docs', 'list: verifying, fixing, building'"
  - "evidence JSON is still read from the working tree on --rerun: committed 'exit 3' -> rc 1; an uncommitted swap to 'echo temp: 21' -> check_live and check_tasks --rerun both pass. Moot in CI"
  - "SIGTERM: a worktree is still left registered (D12)"
  - "auditor coverage: audit-4 is at 93d1d60; 816e237 (check_live +126/-25, check_formal +9/-10, check_tasks +1/-4) is unaudited, and N4 is not re-judged here"
  - "CI (.github/workflows/checks.yml) still runs only the self-tests; check_tasks/check_live with --allow tools/live-allow.txt run only by hand at the ship batch"
```

Retrospective:
1. Round 5's blocker is fixed as reported. Every escape round 5 listed, and
   the new ones it suggested (`refs/replace`, fsmonitor), now fail in both
   sensors. What is left is shared repo state, which C12 states as the limit.
2. Changing what the scan reads changed what it can see. A checkout follows a
   symlink, so the old scan read the link's target. A blob listing filtered to
   regular files drops the link. Each such change should be tested against
   the cases the old reader handled by accident: symlinks, non-UTF-8 names and
   attributes-driven encodings. Run them in both modes and diff the results.
3. Next round, after the symlink fix, re-run this round's probe scripts.
   Check that `files()` runs before the first probe, or that the limit names
   the object store.
