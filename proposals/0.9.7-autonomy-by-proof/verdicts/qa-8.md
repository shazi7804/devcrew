# QA verdict — round 8 (qa role, Claude, at f9aa58d)

I ran every sensor at f9aa58d in clean clones. The adversarial probes ran in
throwaway repos that import the tools of a separate clean clone, so the trees
the sensors ran on were never touched. Results:
- all three self-tests pass: check_live 118 cases, check_formal 45, check_tasks 51;
- check_neutral (and its self-test), check_repo and the diagram check pass (`ALIGNED`);
- the full `check_models.py` passes: 9 models, 5 real traces accepted, 3 mutants
  rejected, 2 min 53 s;
- `check_tasks --allow tools/live-allow.txt --rerun` on the proposal passes
  (`tasks: ok`) in 5 min 18 s. No worktree is left behind and the tree is
  clean afterwards;
- the 32-way election race gives exactly 1 orchestrator and the 20-way takeover
  race gives exactly 1 winner, twice each. Empty stdin exits 0.

QA round 7's blockers, checked against 912fe89 and 6eda50b:
- **Differential symlink battery: 37 forms, none where `--rerun` is weaker.**
  Each form ran in its own repo: check_live `--only R1` and check_tasks, plain
  and `--rerun`. The repo has a committed mock under `tests/`, R1 is `local`,
  and TASKS has `- [x] R1 a`. A form counts as a failure when plain gives rc 1
  and `--rerun` gives rc 0.
  - **Same rc and hits in all four runs (rc 1):** the round-6 `../tests/` form;
    through a directory link; `d/..` after a directory link; `./` and `//` in
    the target; chains of 2 and 5; a chain that stays inside `tests/`; nested
    directory links (`a -> b -> tests`); a directory link inside a real
    directory; a directory link to `tests/sub` holding a link with `..`; a
    directory link followed by an `up -> ..` link; `lnk -> sub/..` (a link to
    the root); `../d/../../tests/` after a directory link; a link through
    `src2 -> src`; a link to a `.txt` file and to a `docs/*.md` file; `.env`
    and `cfg/.env.local` links.
  - **Plain rc 1, `--rerun` rc 1 with `src/app.sh: a symlink that does not
    resolve to a file of HEAD's tree`:** an absolute link into the repo; an
    absolute link outside it; a `../../` escape; an escape and return; a link
    in the wrong case (`../TESTS/`); a wrong-case directory link name
    (`../PROD/`); a directory link up and back through the repo's own name.
    Round 7's blocker 2 is fixed.
  - **Plain rc 0, `--rerun` rc 1 (stricter):** a 2-link loop; a self-loop;
    `x -> x/..` (a directory link whose target is itself, through `..`); a
    dangling link; a link into `.git/config`; a code-named link to a
    directory; `../tests/fixture.sh/../clean.sh`; a trailing `/`.
  - **Chains:** a 39-link chain gives rc 1 in all four runs. Plain stops at
    macOS's 32 hops and hits the intermediate links. A 41-link chain gives
    rc 1 in all four runs, and `--rerun` reports the head link.
  - **rc 0 in all four runs:** a non-code-named link to a directory; a link
    inside `tests/`; `src/app.txt -> ../tests/fixture.sh`.
- **But one more symlink form makes `--rerun` weaker: a case collision**
  (blocker 1).
- **6eda50b's subset read.** For the 59 names `files()` loads on the real tree,
  each one is byte-identical to `git show HEAD:<path>`, and every `want` name
  is loaded. The HEAD tree has no symlinks. The allow file under `--rerun`, as
  `allow.txt`, `./allow.txt`, `sub/../allow.txt` or a resolved absolute path:
  R1's probe rewrites the allow blob into an exemption. Each run was in a
  fresh repo, and plain and `--rerun` both gave rc 1 in both sensors. The
  allow file was read before the probe. But two kinds of read happen after a
  probe runs (blockers 2 and 3), and one plain-mode input is not honoured
  (blocker 4).

Regression:
- **Round 5-7 scan escapes, re-run.** src/app.js holds a committed mock, and
  R1 runs `<trick>; echo temp: 21`. Each sensor ran in its own repo. Every one
  of these tricks gives rc 1 with only `src/app.js:1: `mock`` in both
  `check_live --only R1 --rerun` and `check_tasks --rerun`, and 1 worktree at
  the end:
  - skip-worktree;
  - `sparse-checkout --no-cone /proposals/`;
  - worktree-config sparse + `read-tree -mu`;
  - a post-checkout hook in the common hooks dir;
  - a smudge filter + `info/attributes`;
  - `git replace` of the blob, and of the commit;
  - `core.fsmonitor`;
  - `info/grafts`;
  - `shallow`;
  - the loose-object rewrite.
- **Probe-to-probe, re-run.** R1 plants something, and R2 runs `sh fail.sh`
  (committed `exit 3`) or `sh ok.sh` (untracked). With each of these plants,
  both sensors give rc 1 with only R2 failing (`re-run exited 3`, or `127`
  for ok.sh):
  - skip-worktree;
  - assume-unchanged;
  - sparse;
  - worktree-config sparse;
  - a post-checkout hook;
  - `git replace` of the blob;
  - fsmonitor;
  - `core.untrackedCache`;
  - the worktree's `info/exclude`.
- **Agreement battery.** I ran the 13 cases plain and with `--rerun`.
  check_tasks and `check_live --only R1` agree on the rc and the hit list in
  **26/26**. The cases: the mock alone; an allow file committed; an allow file
  uncommitted (`--rerun`: `--allow allow.txt: not in HEAD`); the mock only in
  the working tree; a committed mock hidden by an edit; a mock inside `--src`
  and one outside it; a mock covered by `--test`; an allow entry for the wrong
  path; a too-broad entry (refused); a whole-file entry; a missing allow file;
  `MOCK_DATA`.
- **The acceptance's exact commands, on the real tree beside check_tasks:**
  - `check_live.py --only <ID>` for each of the 19 IDs, with no `--allow`:
    rc 1 and 89 hits each (check_live.py 82, check_tasks.py 6,
    check_formal.py 1; three more than round 7, from the new self-test
    lines). The list is identical for all 19 IDs. `check_tasks` gives rc 1
    with the same 89 hits (diff empty) and no other hit;
  - with `--allow tools/live-allow.txt`: all 19 give `live: ok`, and
    `check_tasks` gives `tasks: ok`;
  - with `--rerun --allow`: all 19 give `live: ok`;
  - with `--rerun` and no `--allow`: `check_live --only R3` gives rc 1 with
    the same 89-hit list as plain. `check_tasks --rerun` gives rc 1 with the
    same 89 hits and no other hit;
  - `check_formal.py --only <ID>`: all 19 give `formal: ok`. With `--rerun`,
    R12, R13 and R15 also give `formal: ok`;
  - afterwards `git worktree list` shows only the main tree, and `git status`
    is clean.

Blockers:

1. **A link into a pair of HEAD paths that differ only in case reads the
   blob it names, but on a case-insensitive filesystem the kernel reads the
   other one.** `--rerun` therefore scans a clean file and passes, while both
   the plain scan and the `--rerun` probe run the mock. `resolve()` finds an
   exact-case entry, so the C12 rule "another case is reported" never fires.
   The "component by component as the kernel does" docstring is false on the
   filesystem this was found on.
   ```
   git ls-tree -r HEAD:  120000 src/app.sh -> ../tests/X.sh
                         100644 tests/X.sh = 'echo "temp: 22"'
                         100644 tests/x.sh = 'mock_temp() { echo 21; }' / 'echo "temp: $(mock_temp)"'
   R1 local, command `sh src/app.sh`; TASKS `- [x] R1 a`
   checkout (macOS, case-insensitive APFS): tests/ holds one file, x.sh -- the mock
   a fresh `git worktree add` of HEAD: sh src/app.sh                     -> temp: 21
   check_live.py --root . --requirements proposals/x/requirements.md --only R1          -> rc 1  src/app.sh:1: `mock`: mock_temp() { echo 21; }  (2 hits)
   check_tasks.py --root . --tasks proposals/x/TASKS.md                                 -> rc 1  Done but not live: src/app.sh:1: `mock` (+ stale: the checkout differs from HEAD)
   check_live.py ... --only R1 --rerun                                                  -> rc 0  live: ok
   check_tasks.py ... --rerun                                                           -> rc 0  tasks: ok
   ```
   Fix (fail-closed): under `--rerun`, report every pair of HEAD paths that
   fold to the same name (casefold, plus Unicode normalization as APFS does).
   For example: `tests/X.sh and tests/x.sh collide on a case-insensitive
   filesystem -- which one runs depends on the checkout`. Never pick one of
   the two. Add a self-test case.

2. **`--rerun --deployed` runs its version probes in the real tree before
   `files()` reads HEAD's blobs.** A probe that rewrites a loose object
   therefore changes what the scan reads in the same invocation. The
   HeadTree docstring and C12 say "the blobs are read before the first
   probe", which is false here. `_run` calls `probe(cmd, root)` for each
   `--deployed` command, and the first `files()` happens later, in
   `check_evidence` (`get()`) or in `scan`.
   ```
   src/app.js = 'export const t = mockTemp();' (committed); R1 local `echo 'temp: 21'`, evidence at HEAD
   rewrite.py = round 7's loose-object rewrite (chmod, then zlib of `blob N\0<text>` over the object of HEAD:<path>)
   check_live.py --root . --requirements proposals/x/requirements.md --only R1                 -> rc 1  src/app.js:1: `mock`
   check_live.py ... --only R1 --rerun --deployed \
     "curl -fsS -o /dev/null https://github.com/ && python3 rewrite.py src/app.js 'export const t = 3;' && echo <HEAD sha>"
                                                                                               -> rc 0  live: ok
   ```
   Fix (fail-closed): call `tree.files()` at the top of `_run` (before the
   `--deployed` loop) whenever `rerun` is set, so the blobs are read before
   any command runs. Add a self-test case.

3. **A formal source named in a non-canonical form is registered in `want`
   but never pre-read.** It is then read lazily, after the probes, and a
   probe can remove its escape hatch. `files()` matches `want` against HEAD's
   exact entry names, so `./spec/M.tla` is not in the pre-read set.
   `blob("./spec/M.tla")` then runs `cat-file blob <sha>:./spec/M.tla`,
   which resolves, but only after check_live's probes have run. The plain
   scan reads the working tree and catches the hatch.
   ```
   R1: Property "Spec holds", Formal checked, Conformance none; Verify local; TASKS `- [x] R1 a`
   spec/M.tla line 3: `Inv == OMITTED`
   formal/R1.json: sources ["./spec/M.tla"], command "sh spec/check.sh tlc ./spec/M.tla" (prints
     "No error has been found"), vacuity "sh spec/mut.sh ./spec/M.tla" (exit 12, prints "Invariant violated")
   evidence/R1.json: command "python3 rewrite.py spec/M.tla '---- MODULE M ----' && echo 'temp: 21'"
   check_tasks.py --root . --tasks proposals/x/TASKS.md            -> rc 1  Done but not formal: ... escape hatch in M.tla:3 `Inv == OMITTED`
   check_tasks.py --root . --tasks proposals/x/TASKS.md --rerun    -> rc 0  tasks: ok
   the same with sources ["spec/M.tla"]                            -> --rerun rc 1, the same hit (pre-read)
   ```
   Fix (fail-closed): normalize every name in `want` and in `blob()`
   (posixpath.normpath, strip a leading `./`). Once a probe has run, make
   `blob()` refuse any name it did not read up front: return None, which
   becomes `source ... does not exist` or `--allow ...: not in HEAD`. Do not
   read the object store after a probe. Add a self-test case.

4. **`--rerun` does not interpret `--src` the way the plain scan does.** The
   plain scan passes `--src` to `git ls-files` as a pathspec. The re-run
   filters HEAD's names with a prefix/fnmatch test that knows no pathspec
   magic and no `..`. So a `--src` that selects the mock in plain mode
   selects nothing on a re-run. The filter predates this round (816e237),
   but it is part of the gate mode the bar covers.
   ```
   src/a/app.js = mock (committed), lib/m.js clean; R1 local `echo 'temp: 21'`
   check_live.py --root . --requirements proposals/x/requirements.md --only R1 --src <S>   plain / --rerun
     ':!lib'                 rc 1 / rc 0
     ':(exclude)lib'         rc 1 / rc 0
     ':(glob)src/**/*.js'    rc 1 / rc 0
     ':(icase)SRC'           rc 1 / rc 0
     'src/a/../a'            rc 1 / rc 0
   check_tasks.py --root . --tasks proposals/x/TASKS.md --src ':!lib'        rc 1 / --rerun rc 0 tasks: ok
   check_tasks.py ... --src 'src/a/../a'                                     rc 1 / --rerun rc 0 tasks: ok
   (src, ./src, src/, src/*.js, *.js, src/**, /src, ./, a file path: rc 1 in both modes)
   ```
   Fix (fail-closed): on a re-run, let git evaluate the pathspec over HEAD.
   Read HEAD into a temporary index (`GIT_INDEX_FILE=<tmp> git read-tree
   <sha>`), run `git ls-files -z -- <src...>` against it, and use those
   names. Or refuse any `--src` that is not a plain path or glob (`:`
   magic, a `..` component) with a message. Do not filter it lexically.

```yaml
verdict: FAIL
scope: feature (framework)
sensors: {test: pass, live: pass, formal: pass, tasks: pass, models: pass, neutral: pass, repo: pass, diagrams: pass, race: pass}
blockers:
  - "case collision: src/app.sh -> ../tests/X.sh with tests/X.sh clean and tests/x.sh a mock in HEAD; on case-insensitive APFS the checkout holds the mock and sh src/app.sh prints 'temp: 21' (the --rerun probe too); plain check_live --only R1 / check_tasks rc 1 'src/app.sh:1: `mock`', --rerun rc 0 'live: ok' / 'tasks: ok'. resolve() takes the exact-case entry; C12's 'another case is reported' does not fire. Fix: report every case-/normalization-colliding pair of HEAD paths on --rerun"
  - "--rerun --deployed runs its probes in the real tree before files() reads HEAD's blobs: a deployed probe that rewrites HEAD:src/app.js's loose object gives rc 0 'live: ok' while plain gives rc 1 'src/app.js:1: `mock`'. The docstring / C12 'the blobs are read before the first probe' is false. Fix: tree.files() before the --deployed loop"
  - "a formal source named './spec/M.tla' is registered in want but not pre-read (want is matched against exact entry names) and is read lazily after check_live's probes: a probe removing `Inv == OMITTED` from the blob gives check_tasks --rerun rc 0 'tasks: ok' while plain gives rc 1 'escape hatch in M.tla:3'. Fix: normalize want and blob() names; after the first probe blob() refuses anything not read up front"
  - "--rerun filters --src lexically while plain passes it to git ls-files as a pathspec: --src ':!lib', ':(exclude)lib', ':(glob)src/**/*.js', ':(icase)SRC', 'src/a/../a' -> plain rc 1 'src/a/app.js:1: `mock`', --rerun rc 0 (check_live and check_tasks). Fix: evaluate the pathspec with git over HEAD (a temporary index from read-tree), or refuse a pathspec the filter cannot read"
passed_by_hand: [R1, R2, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, N1, N2, N3]
probes:
  - "differential symlink battery, 37 forms x {check_live --only R1, check_tasks} x {plain, --rerun}: 0 forms where plain hits and --rerun does not. Same in all four (rc 1): ../tests, via a dir link, d/.. after a dir link, ./ and //, chains 2/5/39/41, chain inside tests/, nested dir links, dir link inside a real dir, dir link then a link with .., dir link then up -> .., lnk -> sub/.., ../d/../../tests, src2 -> src, link to .txt / docs .md, .env and cfg/.env.local links. Reported on --rerun (plain rc 1): absolute in-repo, absolute outside, ../../ escape, escape and return, ../TESTS, ../PROD, up and back via the repo name. Stricter on --rerun (plain rc 0): loops, self-loop, x -> x/.., dangling, .git/config, code-named link to a dir, file/../file, trailing /. rc 0 in all four: non-code link to a dir, link inside tests/, .txt link to a .sh mock"
  - "case collision tests/X.sh + tests/x.sh -> --rerun weaker (blocker 1)"
  - "files() vs git show HEAD:<path>: 59 names loaded on the real tree, 0 differ, every want name loaded"
  - "allow file as allow.txt, ./allow.txt, sub/../allow.txt, a resolved absolute path; R1's probe rewrites the allow blob into an exemption; fresh repo per run -> rc 1 in all 16 runs (pre-read)"
  - "--rerun --deployed + loose-object rewrite -> rc 0 (blocker 2); formal source './spec/M.tla' + rewrite -> check_tasks --rerun rc 0 (blocker 3); canonical 'spec/M.tla' -> rc 1"
  - "--src forms: src, ./src, src/, src/*.js, *.js, src/**, /src, ./, a file path -> same rc in both modes; pathspec magic and 'src/a/../a' -> --rerun weaker (blocker 4); --src through a dir link (lib -> src) -> rc 0 in all four"
  - "round 5-7 scan escapes x {check_live, check_tasks} --rerun: skip-worktree, sparse, worktree-config sparse, post-checkout, smudge + info/attributes, replace blob/commit, fsmonitor, grafts, shallow, loose-object rewrite -> all rc 1 with only 'src/app.js:1: `mock`', 1 worktree"
  - "probe-to-probe x both sensors: skip-worktree, assume-unchanged, sparse, worktree-config sparse, post-checkout, replace blob, fsmonitor, untrackedCache, worktree info/exclude -> only R2 fails (exit 3 / 127)"
  - "agreement battery 13 cases x {plain, --rerun} -> 26/26 agree on rc and hits"
  - "real tree: check_live --only <ID> (19) no --allow: 89 hits each, identical, = check_tasks 89 (diff empty); --allow 19/19 ok + tasks ok; --rerun --allow 19/19 ok; --rerun alone R3 89 = check_tasks --rerun 89, no other hit; check_formal --only 19/19 ok, --rerun R12/R13/R15 ok"
  - "races (twice): 32 elections -> 1 'only orchestrator'; 20 takeovers -> 1 'Took over'; empty stdin exit=0"
  - "cleanup: every probe repo and the real-tree runs end with 1 worktree and a clean git status"
weak_evidence:
  - "resolve() treats a file prefix as a directory: ../tests/fixture.sh/../clean.sh and a trailing / resolve to a file, where the kernel gives ENOTDIR. --rerun is stricter, not weaker, but 'as the kernel does' is not exact"
  - "a probe's rewrite of a loose object persists across invocations: check_live --rerun (whose probe rewrote the allow blob) followed by check_tasks --rerun in the same repo gives tasks rc 0 while plain gives rc 1. Shared object store across invocations, stated in the HeadTree docstring (C12)"
  - "an unresolved absolute --allow path (under a symlinked directory prefix) gives '--allow ../../..: not in HEAD' on --rerun while plain reads it: fail-closed, a usability note"
  - "a non-code-named link to a directory is not expanded in either mode: carried over from 0.9.6; it matches the plain scan"
  - "6eda50b and 912fe89 (check_live +165/-35 in this round) are not covered by the audit: audit-5 is at the commit before them; N4 is not re-judged here"
  - "carried over unchanged: tools/live-allow.txt keeps 'framework/tools/check_live.py \\S' (C11); the QA-3/QA-4 Done-status misses and false positives; evidence JSON read from the working tree on --rerun; SIGTERM leaves a worktree registered (D12); CI runs only the self-tests"
```

Retrospective:
1. Round 7's differential battery did its job for the forms it listed. All 37
   forms agree, or `--rerun` is stricter. Running the battery as a sweep over
   *what the OS does* rather than *what the link text says* found the one form
   left: a case collision. On a case-insensitive filesystem the name in the
   tree is not the file on disk. The next differential should vary the
   filesystem, not only the link.
2. "Read before the first probe" was checked on the probes that
   `check_evidence` runs. It was not checked on the other commands the
   sensor runs (`--deployed`), or on names that reach `blob()` in a form
   `files()` did not register. An "up front" claim needs one choke point that
   fails closed once a command has run, rather than a list of callers that
   each remember to register.
3. The bar "the gate is never weaker than the plain mode" covers every input
   of the gate, not only the code that changed. `--src` had been filtered
   lexically since 816e237 and no round tested it differentially. Each plain
   input (`--src`, `--test`, `--allow`, the evidence dir) needs a
   differential case of its own.
