# QA verdict — round 9 (qa role, Claude, at bda2550)

I ran every sensor at bda2550 in clean clones. The adversarial probes ran in
throwaway repos that import the tools of a separate clean clone, so the trees
the sensors ran on were never touched. Each probe used a fresh repo per
sensor and mode wherever a probe has side effects. Results:
- all three self-tests pass: check_live 124 cases, check_formal 45, check_tasks 51;
- check_neutral (and its self-test), check_repo and the diagram check pass (`ALIGNED`);
- the full `check_models.py` passes: 9 models, 5 real traces accepted, 3 mutants
  rejected, 2 min 51 s;
- `check_tasks --allow tools/live-allow.txt --rerun` on the proposal passes
  (`tasks: ok`) in 5 min 13 s. No worktree is left behind and the tree is
  clean afterwards;
- the 32-way election race gives exactly 1 orchestrator and the 20-way takeover
  race gives exactly 1 winner, twice each. Empty stdin exits 0.

QA round 8's blockers, checked against 666999f:
- **Blocker 1 (case collision) is fixed for whole names.** HEAD has
  `src/app.sh -> ../tests/X.sh`, `tests/X.sh` clean and `tests/x.sh` a mock.
  Plain gives rc 1 with the mock in both sensors. `--rerun` gives rc 1 with
  `src/app.sh: tests/X.sh collides with another name of HEAD's tree on a
  case-insensitive filesystem`. An NFC/NFD pair of file names (`café.sh`
  twice) is reported the same way. But a collision one directory up is not
  checked (blocker 3).
- **Blocker 2 (`--deployed` before `files()`) is fixed.** A `--deployed`
  probe that rewrites the loose blob of `HEAD:src/app.js` gives rc 1
  `src/app.js:1: `mock`` under `--rerun`. The object was rewritten (`git
  cat-file -p HEAD:src/app.js` now shows the clean text).
- **Blocker 3 (`./spec/M.tla`) is fixed.** check_tasks gives rc 1 `escape
  hatch in M.tla:2` in both modes, and the probe did rewrite the blob.
- **Blocker 4 (`--src`) is fixed.** In the sweep below, each of 38 `--src`
  forms gives the same rc in all four runs.

The differential sweep proposed in round 8: each plain input, run plain and
with `--rerun`, in `check_live --only R1` and check_tasks:
- **`--src`, 38 forms, 0 where `--rerun` is weaker.**
  - Same rc in all four runs (rc 1): `.`, `src`, `./src`, `src/`,
    `src/*.js`, `*.js`, `src/**`, `**/app.js`, `/src`, an absolute path, a
    file path, `:!lib`, `:^lib`, `:(exclude)lib`, `:(exclude)*.md`,
    `:(glob)src/**/*.js`, `:(icase)SRC`, `:(icase,glob)**/APP.js`,
    `:(top)src`, `:/src`, `:(literal)src/a/app.js`, `src/a/../a`,
    `docs/../src`, `lnk/../src`, `src/./a`, `src//a`, `lib src`, `../x`.
  - rc 0 in all four: `SRC`, `Src/a`, `:(attr:x)src`, `:(glob)**/APP.js`,
    `nope`, `s?c`, `[s]rc`, `src/a/app.js/`, and `lnk` and `lnk/a` (a
    directory link to src).
- **`--test`, 8 globs:** each gives the same rc in all four runs.
- **`--allow`, 14 spellings:**
  - Same rc in all four runs: `allow.txt`, `./allow.txt`,
    `sub/../allow.txt`, a resolved absolute path, `.//allow.txt`,
    `allow.txt/`, a committed link `al -> allow.txt`, an uncommitted file,
    and a working-tree edit that adds an exemption.
  - Stricter on `--rerun` (`not in HEAD`): an absolute path under a
    symlinked prefix, and `ALLOW.TXT`.
  - A working-tree edit that drops a committed exemption gives plain rc 1
    and `--rerun` rc 0. That is by design: the re-run judges HEAD's code
    with HEAD's allow file, and plain also reports the evidence stale.
  - **Weaker:** `d/../allow.txt` and `nodir/../allow.txt` (blocker 2).
- **The evidence dir and `--env`:** `--env prod` with evidence under
  `prod/`, `--env prod` with evidence only at the top, and `--env ..`, each
  with and without a mock: the same rc in all four runs.
- **Formal sources (check_formal `--only R1` and check_tasks):** the plain
  name, and `./` given with a hatch, agree. **Weaker:** `d/../M.tla` and
  `nodir/../spec/M.tla` (blocker 2).

The choke point "read once, before any command, never after":
- **Commands before `files()`: none found.** `_run` calls `files()` first
  under `--rerun`, before the `--deployed` loop. check_tasks and
  check_formal reach `files()` through `get()` or `blob()` before their
  first command. Plain mode runs no command.
- **Reads after a command:**
  - `HeadTree.ls()` runs `git read-tree <sha>` after every probe, and reads
    HEAD's tree objects from the object store (blocker 1);
  - `drifted()` reads the working tree and HEAD's history once per
    requirement, after the probes of earlier requirements;
  - the evidence and formal JSON are read from the working tree after the
    earlier probes (weak evidence below);
  - `_check_evidence`'s `head`, which `--record` stamps, is read after the
    `--deployed` probes.

The collision rule on ordinary repos:
- **0 false positives.** `files()` ran over 32 local repositories, about
  45 000 tree entries in all: this repo, 20 other project repos, Homebrew
  and its taps, nvm, oh-my-zsh and three Go source trees. None had a fold
  group, and none had a name flagged.
- **The fold agrees with APFS on all 19 pairs I tried**, made as real files
  on this disk. The pairs: ß/ss, the Kelvin sign, the ﬁ/ﬀ/ﬆ ligatures, σ/ς/Σ,
  NFC/NFD é, the Å/Ångström sign, İ, ǰ, ŉ, ᾳ/αι, combining ypogegrammeni,
  and the Ω/Ohm sign. Each pair the fold puts together, APFS also treats as
  one name, and each pair it keeps apart (İx/ix, ǅ/dž) APFS also keeps
  apart. A zero-width joiner stays distinct in both.
- On a case-sensitive filesystem every pair it reports is a false positive,
  but the rule fails closed there.
- **The rule folds whole entry names only, not the directories on the path**
  (blocker 3).

Regression:
- **The symlink battery (round 8's 37 forms; 38 entries in the script): 0
  forms where `--rerun` is weaker.** The four-way results match round 8
  form for form: same rc 1 in all four; plain rc 1 and reported on
  `--rerun`; stricter on `--rerun` (loops, self-loop, `x -> x/..`, dangling,
  `.git/config`, a code-named link to a directory, `file/../file`, trailing
  `/`); and rc 0 in all four for the non-code link to a directory, the link
  inside `tests/` and the `.txt` link.
- **Round 5-7 scan escapes:** all 11 tricks, in both sensors under
  `--rerun`, give rc 1 with only `src/app.js:1: `mock``, and 1 worktree.
  The tricks: skip-worktree, sparse, worktree-config sparse, post-checkout,
  smudge + attributes, replace blob, replace commit, fsmonitor, grafts,
  shallow and the loose-object rewrite.
- **Probe-to-probe:** all 9 plants, in both sensors, give rc 1 with only R2
  failing (`exited 3`, or `127` for ok.sh).
- **The agreement battery agrees in 26/26 cases.**
- **The acceptance's exact commands, on the real tree:**
  - `check_live.py --only <ID>` for each of the 19 IDs, with no `--allow`:
    rc 1 and 91 hits each (check_live.py 84, check_tasks.py 6,
    check_formal.py 1). The list is byte-identical for all 19 IDs.
    `check_tasks` gives rc 1 with the same 91 lines (diff empty);
  - with `--allow tools/live-allow.txt`: 19/19 give `live: ok`, and
    `check_tasks` gives `tasks: ok`;
  - with `--rerun --allow`: 19/19 give `live: ok`;
  - with `--rerun` and no `--allow`: `check_live --only R3` gives the same
    91 lines as plain (diff empty). `check_tasks --rerun` gives rc 1 with 91
    code hits and no other hit;
  - `check_formal.py --only <ID>`: 19/19 give `formal: ok`. With `--rerun`,
    R12, R13 and R15 also give `formal: ok`;
  - afterwards there is 1 worktree, and `git status` is clean.

Blockers:

1. **`--rerun` reads HEAD's tree objects after the probes have run.**
   `HeadTree.ls()` runs `git read-tree <sha>` into a temporary index from
   `check_code`, which is the last step of the sensor. A probe, or a
   `--deployed` command, that rewrites the loose tree object of `HEAD:src`
   to leave out `app.js` therefore removes the mock from what the scan
   lists. git does not check the hash on that read. This falsifies three
   statements:
   - the HeadTree docstring: "read once before any command runs ... and
     never after";
   - C12: "the blobs are read once before any command runs and never
     after";
   - the CHANGELOG: "nothing a probe does to a checkout or the object store
     changes what they see".
   ```
   src/app.js = 'export const t = mockTemp();' (committed), src/ok.js clean; R1 local; TASKS `- [x] R1 a`
   rewrite_tree.py: oid = rev-parse HEAD:src; new = mktree(ls-tree oid minus app.js);
                    copy the loose file of `new` over the loose file of `oid` (chmod 644 first)
   R1 command: python3 rewrite_tree.py src app.js && echo temp: 21
   check_live.py --root . --requirements proposals/x/requirements.md --only R1          -> rc 1  src/app.js:1: `mock`
   check_live.py ... --only R1 --rerun                                                   -> rc 0  live: ok
   check_tasks.py --root . --tasks proposals/x/TASKS.md                                  -> rc 1  Done but not live: src/app.js:1: `mock`
   check_tasks.py ... --rerun                                                            -> rc 0  tasks: ok
   R1 `echo 'temp: 21'` + --deployed "curl -fsS -o /dev/null https://github.com/ && python3 rewrite_tree.py src app.js && echo <HEAD sha>"
   check_live.py ... --only R1 --rerun --deployed ...                                    -> rc 0  live: ok
   afterwards: git ls-tree HEAD:src -> error: hash mismatch; GIT_INDEX_FILE=<tmp> git read-tree HEAD -> rc 0, ls-files lists src/ok.js only
   ```
   Fix (fail-closed): build the temporary index (`read-tree <sha>`) inside
   `files()`, before any command, and keep it for the invocation. `ls()`
   then runs only `ls-files` against that index. Or make `ls()` raise once a
   command has run if the index was not built up front. Add a self-test
   case: a probe that rewrites HEAD's tree object.

2. **A name with a `..` component is resolved lexically on `--rerun`.** The
   kernel resolves it through symlinks and existing directories, so a
   re-run reads a different file from the one the plain scan and the probe
   read.
   - For formal sources, 666999f's `canon()` introduced this (`posixpath.normpath`).
     At f9aa58d the same inputs gave `source ... does not exist` on a re-run.
   - For `--allow`, the same thing comes from `os.path.relpath`. It predates
     this round, but the bar covers it.
   - The `blob()` docstring says "however spelled", and the CHANGELOG says
     "A symlink resolves as the kernel does".
   ```
   formal: spec/M.tla line 2 `Inv == OMITTED`, M.tla clean, d -> spec/deep (dir link); R1 Property "Spec holds", Formal checked, Conformance none
     formal/R1.json sources ["d/../M.tla", "spec/check.py"], command "python3 spec/check.py d/../M.tla" (the kernel opens spec/M.tla)
     check_formal.py --root . --requirements proposals/x/requirements.md --only R1       -> rc 1  escape hatch in M.tla:2 `Inv == OMITTED`
     check_formal.py ... --only R1 --rerun                                                -> rc 0  formal: ok
     check_tasks.py --root . --tasks proposals/x/TASKS.md                                 -> rc 1  Done but not formal: ... escape hatch in M.tla:2
     check_tasks.py ... --rerun                                                           -> rc 0  tasks: ok
     sources ["nodir/../spec/M.tla", ...] (no nodir/): plain rc 1 `source nodir/../spec/M.tla does not exist`, --rerun rc 0 (both sensors)
     (at f9aa58d both give --rerun rc 1 `source d/../M.tla does not exist`)
   allow: allow.txt exempts src/app.js mockTemp; sub/allow.txt exempts nothing; d -> sub/deep
     check_live.py ... --only R1 --allow d/../allow.txt                                   -> rc 1  src/app.js:1: `mock` (the kernel reads sub/allow.txt)
     check_live.py ... --only R1 --allow d/../allow.txt --rerun                           -> rc 0  live: ok
     check_tasks.py ... --allow d/../allow.txt  / --rerun                                 -> rc 1 / rc 0 tasks: ok
     --allow nodir/../allow.txt: plain rc 1 `[Errno 2] No such file or directory`, --rerun rc 0 (both sensors)
   ```
   Fix (fail-closed): do not collapse `..` lexically, in `canon()` or in
   `--allow`'s relpath. Either resolve a name component by component through
   HEAD's tree with `resolve()` (each step must be a directory, or a link
   that resolves to one), or refuse any name that has a `..` component:
   `blob()` returns None, which becomes `does not exist` or `not in HEAD`.
   Add a self-test case.

3. **The collision rule folds whole entry names only, not the directories
   on the path.** If a symlink and a directory fold together (`TESTS` and
   `tests/`, or NFC and NFD `café`), the checkout keeps only one of them.
   `resolve()` follows the link, but the kernel opens the directory. No
   name is reported, because `TESTS` and `tests/x.sh` fold to different
   keys. The fix commit says "two names of HEAD's tree that fold together
   ... are reported, not guessed", and that is false for directory
   prefixes.
   ```
   git ls-tree -r HEAD:  120000 TESTS -> e
                         100644 e/x.sh      = 'echo "temp: 22"'
                         100644 tests/x.sh  = mock_temp() / echo "temp: $(mock_temp)"
                         120000 src/app.sh -> ../TESTS/x.sh
   R1 local `sh src/app.sh`; TASKS `- [x] R1 a`
   a fresh `git worktree add` of HEAD (macOS, case-insensitive APFS): only tests/ exists; sh src/app.sh -> temp: 21
   check_live.py --root . --requirements proposals/x/requirements.md --only R1          -> rc 1  src/app.sh:1: `mock`
   check_live.py ... --only R1 --rerun                                                   -> rc 0  live: ok
   check_tasks.py --root . --tasks proposals/x/TASKS.md                                  -> rc 1  Done but not live: src/app.sh:1: `mock`
   check_tasks.py ... --rerun                                                            -> rc 0  tasks: ok
   the same with tests/café -> ../e (NFD link) and tests/café/x.sh (NFC dir, mock),
     src/app.sh -> ../tests/café/x.sh: checkout runs temp: 21; plain rc 1 `mock`, --rerun rc 0 (both sensors)
   ```
   Fix (fail-closed): fold every path prefix as well as every entry: each
   leading directory of each entry, and each symlink entry as a possible
   directory. Report any read whose resolution passes through a component
   whose folded prefix has more than one spelling in HEAD's tree. Add a
   self-test case.

```yaml
verdict: FAIL
scope: feature (framework)
sensors: {test: pass, live: pass, formal: pass, tasks: pass, models: pass, neutral: pass, repo: pass, diagrams: pass, race: pass}
blockers:
  - "HeadTree.ls() runs `git read-tree <sha>` after the probes: a probe (or --deployed command) that rewrites the loose tree object of HEAD:src to drop app.js gives check_live --only R1 --rerun rc 0 'live: ok' and check_tasks --rerun rc 0 'tasks: ok' while plain gives rc 1 'src/app.js:1: `mock`'. The docstring / C12 / CHANGELOG 'read once before any command, never after' is false. Fix: read-tree into the temporary index inside files(), before any command; ls() only runs ls-files on it"
  - "a `..` in a formal source or --allow is collapsed lexically on --rerun (canon(): posixpath.normpath; --allow: os.path.relpath), not as the kernel resolves it: source 'd/../M.tla' with d -> spec/deep reads M.tla (clean) on --rerun while the kernel and plain read spec/M.tla (`Inv == OMITTED`): check_formal/check_tasks plain rc 1, --rerun rc 0; 'nodir/../spec/M.tla' plain 'does not exist', --rerun rc 0 (a regression from f9aa58d); --allow d/../allow.txt (d -> sub/deep) and nodir/../allow.txt: plain rc 1, --rerun rc 0 in both sensors. Fix: resolve through HEAD's tree or refuse a `..` component"
  - "the collision rule folds whole names, not directory prefixes: TESTS -> e (clean) beside tests/x.sh (mock), src/app.sh -> ../TESTS/x.sh: the checkout holds tests/ and runs the mock ('temp: 21'); plain rc 1 'src/app.sh:1: `mock`', --rerun rc 0 in both sensors; the same with an NFD link dir beside an NFC real dir. Fix: fold every path prefix; report any read through a component with two spellings"
passed_by_hand: [R1, R2, R4, R5, R6, R7, R8, R9, R11, R12, R13, R14, R15, N1, N2, N3]
probes:
  - "round-8 blockers re-run: whole-name case collision and NFC/NFD file pair -> reported on --rerun; --deployed blob rewrite -> rc 1; './spec/M.tla' + blob rewrite -> rc 1; the 5 failing --src forms -> same rc in all four"
  - "differential sweep x {check_live --only R1, check_tasks} x {plain, --rerun}: --src 38 forms, 0 weaker; --test 8 globs, 0 weaker; --allow 14 spellings: 9 same, 2 stricter (unresolved absolute, ALLOW.TXT), 1 by design (a working-tree edit that drops a committed exemption: the re-run judges HEAD), 2 weaker (`..`, blocker 2); --env / evidence dir 4 cases, same; formal sources: './', plain name same, `..` weaker (blocker 2)"
  - "choke point: no command runs before files() in check_live, check_tasks or check_formal; after a command, ls() reads the object store (blocker 1); drifted(), the evidence/formal JSON and --record's head read the working tree / refs after earlier probes (weak evidence)"
  - "tree-object rewrite via a probe and via --deployed -> --rerun rc 0 (blocker 1)"
  - "collision rule: 32 local repos (~45 000 entries, incl. three Go trees and Homebrew) -> 0 fold groups, 0 flagged; 19 Unicode pairs made on APFS -> the fold agrees on every one; prefix collisions (link vs dir, case and NFC/NFD) -> --rerun weaker (blocker 3)"
  - "symlink battery, 38 entries (round 8's 37 forms) x 4 runs: 0 weaker, results identical to round 8"
  - "round 5-7 scan escapes (11) x both sensors --rerun -> rc 1, only 'src/app.js:1: `mock`', 1 worktree; probe-to-probe (9) x both -> only R2 fails"
  - "agreement battery 13 cases x {plain, --rerun} -> 26/26"
  - "real tree: check_live --only <ID> (19) no --allow: 91 hits each, byte-identical, = check_tasks 91 (diff empty); --allow 19/19 ok + tasks ok; --rerun --allow 19/19 ok; --rerun R3 = plain (diff empty); check_tasks --rerun no --allow 91 code hits, no other; check_formal --only 19/19 ok, --rerun R12/R13/R15 ok"
  - "races (twice): 32 elections -> 1 'only orchestrator'; 20 takeovers -> 1 'Took over'; empty stdin exit=0"
  - "cleanup: every probe repo, the models clone and the real-tree runs end with 1 worktree and a clean git status"
weak_evidence:
  - "evidence JSON read after earlier probes (C12: a probe can write outside the checkout): R1's probe writes evidence/R2.json (sha HEAD, `echo temp: 21`) into the main tree; R2 had no evidence: check_live --only R1,R2 / check_tasks plain rc 1 'R2: no evidence', --rerun rc 0. Fail-closed fix: read every evidence and formal JSON, and compute every drifted() verdict, before the first command"
  - "drifted() per requirement compares to the working tree and HEAD's ref after earlier probes, and _check_evidence's head (stamped by --record) is read after --deployed's probes: same C12 class, not separately reproduced"
  - "the files() docstring says an unresolvable symlink 'maps to None'; it now maps to a message string (and a colliding name too)"
  - "plain mode with a root spelled through a symlink (a symlinked prefix) reports evidence stale (contract() compares resolved paths): plain is stricter, a usability note"
  - "carried over unchanged: tools/live-allow.txt keeps 'framework/tools/check_live.py \\S' (C11); a non-code link to a directory, and --src through a directory link, are scanned in neither mode; SIGTERM leaves a worktree registered (D12); CI runs only the self-tests; 666999f (check_live +127/-32) is not covered by an audit round"
```

Retrospective:
1. The round-8 fix made one choke point for blobs, but `ls()` was added in
   the same commit as a second reader of the object store. It runs at the
   end of the sensor, outside the choke point. An "up front" claim holds
   only if every git call that reads objects is listed and placed before
   the first command. The next round should grep for every `git` call on
   the `--rerun` path and check where each one runs relative to the first
   `probe` or `run_cmd`.
2. `canon()` fixed one spelling (`./`) by bringing in a lexical rule (`..`)
   that the kernel does not follow. A name normaliser for a gate has to
   resolve as the filesystem does or refuse. "Make two spellings equal" is
   not fail-closed.
3. The collision fix checked the exact repro (two files) rather than the
   class (two paths the filesystem merges). The OS-level differential that
   round 8 proposed should vary every path component: file, directory and
   link, each in case and normalization forms.
