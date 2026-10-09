# QA verdict — round 7 (qa role, Claude, at 6d199e5)

I ran every sensor at 6d199e5 in clean clones. The adversarial probes ran in
throwaway repos that import the tools of a separate clean clone, so the trees
the sensors ran on were never touched. Results:
- all three self-tests pass: check_live 112 cases, check_formal 45, check_tasks 51;
- check_neutral (and its self-test), check_repo and the diagram check pass (`ALIGNED`);
- the full `check_models.py` passes: 9 models, 5 real traces accepted, 3 mutants
  rejected, 2 min 49 s;
- `check_tasks --allow tools/live-allow.txt --rerun` on the proposal passes
  (`tasks: ok`) in 6 min 3 s. No worktree is left behind and the tree is
  clean afterwards;
- the 32-way election race gives exactly 1 orchestrator and the 20-way takeover
  race gives exactly 1 winner, twice each. Empty stdin exits 0.

QA round 6's blocker, checked against fe38c4c:
- **The round-6 repro: fixed.** `src/app.js -> ../tests/fixture.js`, where the
  fixture holds `export const t = mockTemp();`. R1 is `local`, its command is
  `echo temp: 21`, and TASKS has `- [x] R1 a`. In all four runs (check_live
  `--only R1` and check_tasks, plain and `--rerun`) the result is rc 1 with
  `src/app.js:1: `mock``.
- **Symlink forms where `--rerun` matches or beats the plain scan.** Each form
  below gives the same rc and hits in all four runs, unless noted:
  - a chain of 2 links, and a chain of 5: rc 1;
  - a link to a `.txt` file, and a link to a `.md` file under `docs/`: rc 1.
    The target is scanned under the link's path;
  - `./../tests/./fixture.js` and `..//tests//fixture.js`: rc 1;
  - `.env -> tests/env` holding `API=mock`: rc 1;
  - a two-link loop and a self-loop: rc 0 in all four runs. Neither has
    content;
  - a link to a directory (`src/lib -> ../tests/d`): rc 0 in all four runs.
    Neither mode lists files under a link;
  - `src/app.txt -> ../tests/f.js`, `tests/x.js -> ../src/app.js`, a dangling
    link, and `src/app.js -> ../.git/config`: rc 0 in all four runs;
  - a 39-link chain: plain rc 0, `--rerun` rc 1. macOS stops following links
    at 32 hops; the sensor follows up to 40. A 41-link chain: rc 0 in all four
    runs.
- **But `--rerun` is still weaker than the plain scan for six link forms**
  (blockers 1 and 2).
- **Object-store rewrite: fixed within one invocation.** src/app.js holds a
  committed mock. R1's command rewrites the loose object of `HEAD:src/app.js`
  under the same oid (chmod, then zlib of `blob N\0export const t = 3;`), and
  then runs `echo temp: 21`. Each sensor ran in its own fresh repo:
  - `check_live --only R1 --rerun`: rc 1, `src/app.js:1: `mock``;
  - `check_tasks --rerun`: rc 1, the same hit.

  The rewrite stays in the store. A second `check_live --rerun` in the same
  repo then gives rc 0, while plain still gives rc 1. That is shared repo
  state across invocations. The docstring now names the object store as part
  of the limit, so this is weak evidence.
- **Round 6's other weak findings: fixed.**
  - Non-UTF-8 paths: a tree built with mktree holds `src/a\376.js` (mock) and
    `src/a\377.js` (clean). `files()` now keeps 2 entries, and `check_code`
    hits `src/a\udcfe.js:1: `mock``.
  - A deleted loose object: the result is `cannot read HEAD's objects in ...
    -- the repository is incomplete`, rc 1, with no traceback.

Regression:
- **Round 5/6 scan escapes, re-run.** src/app.js holds a committed mock, and
  R1 runs `<trick>; echo temp: 21`. Each sensor ran in its own repo. Every one
  of these tricks gives rc 1 `src/app.js:1: `mock`` in both
  `check_live --only R1 --rerun` and `check_tasks --rerun`, with no other hit
  and 1 worktree at the end:
  - skip-worktree;
  - `sparse-checkout --no-cone /proposals/`;
  - worktree-config sparse + `read-tree -mu`;
  - a post-checkout hook in the shared hooks dir;
  - a smudge filter + `info/attributes`;
  - `git replace` of the blob, and of the commit;
  - `core.fsmonitor`;
  - `info/grafts`;
  - `shallow`;
  - the loose-object rewrite.
- **Probe-to-probe, re-run.** R1 plants something; R2 runs `sh fail.sh`
  (committed `exit 3`), `test ! -e fail.sh`, or `sh ok.sh`. With each of these
  plants, both sensors give rc 1 with only R2 failing (`re-run exited 3`, `1`
  or `127`):
  - skip-worktree;
  - sparse;
  - worktree-config sparse;
  - a post-checkout hook;
  - assume-unchanged;
  - `git replace` of the blob;
  - fsmonitor;
  - `core.untrackedCache`;
  - the worktree's `info/exclude`.
- **Agreement battery.** I ran the 13 cases plain and with `--rerun`.
  check_tasks and `check_live --only R1` agree on the rc and the hit list in
  **26/26**. The cases: the mock alone; an allow file committed; an allow file
  uncommitted (`--rerun` gives `--allow allow.txt: not in HEAD` in both); the
  mock only in the working tree; a committed mock hidden by an edit; a mock
  inside `--src` and one outside it; a mock covered by `--test`; an allow
  entry for the wrong path; a too-broad entry (both refuse it); a whole-file
  entry; a missing allow file; `MOCK_DATA`. I added two symlink cases, which
  makes 30/30 agreement between the two sensors. The two sensors agree with
  each other even where both are wrong in `--rerun` (blocker 1).
- **The acceptance's exact commands, on the real tree beside check_tasks:**
  - `check_live.py --only <ID>` for each of the 19 IDs, with no `--allow`:
    rc 1 and 86 hits each (check_live.py 79, check_tasks.py 6,
    check_formal.py 1; one more than round 6, from the new self-test line).
    `check_tasks` gives rc 1 with the same 86 hits (diff empty) and no other
    hit;
  - with `--allow tools/live-allow.txt`: all 19 give `live: ok`, and
    `check_tasks` gives `tasks: ok`;
  - with `--rerun --allow`: all 19 give `live: ok`, and `check_tasks` gives
    `tasks: ok`;
  - with `--rerun` and no `--allow`: `check_live --only R3` gives rc 1 with
    86 hits, the same list as plain. `check_tasks --rerun` gives rc 1 with 86
    code-scan hits and no other hit;
  - `check_formal.py --only <ID>`: all 19 give `formal: ok`. With `--rerun`,
    R12, R13 and R15 also give `formal: ok`;
  - afterwards `git worktree list` shows only the main tree, and `git status`
    is clean.

Blockers:

1. **A symlink whose target is in HEAD's tree is still not read as that
   target when the path runs through a directory symlink, so `--rerun` passes
   a shipped fake that the plain scan catches.** `target()` resolves a link
   by applying `os.path.normpath` to the link text, which works on the text
   alone. It then looks the result up among the file entries. The kernel
   instead resolves each path component in turn, and follows a directory
   symlink before it applies `..`. This causes two misses:
   - **through a directory link**: the path names a directory link, which is
     not a file entry, so the link is dropped;
   - **`d/..` after a directory link**: normpath gives a different, clean
     file, which is scanned in place of the mock.

   In both cases the probe itself runs in HEAD's checkout and executes the
   mock. C12 claims "a symlink at HEAD reads as its in-tree target", and the
   `files()` docstring says the link "reads as its target (what runs is the
   target)". Both claims are false here, and the gate mode is weaker than the
   plain mode. 93d1d60's checkout-based `--rerun` caught both (rc 1, 2 hits
   each).

   Repro, throwaway repos. R1 is `local` and its command is `sh src/app.sh`.
   The evidence is at HEAD and TASKS has `- [x] R1 a`.
   ```
   (a) through a directory link
     git ls-tree -r HEAD:  120000 prod -> tests
                           120000 src/app.sh -> ../prod/fixture.sh
                           100644 tests/fixture.sh = 'mock_temp() { echo 21; }' / 'echo "temp: $(mock_temp)"'
     sh src/app.sh                                                          -> temp: 21
     check_live.py --root . --requirements proposals/x/requirements.md --only R1        -> rc 1  src/app.sh:1: `mock`: mock_temp() { echo 21; }  (2 hits)
     check_tasks.py --root . --tasks proposals/x/TASKS.md                               -> rc 1  Done but not live: src/app.sh:1: `mock` (2 hits)
     check_live.py ... --only R1 --rerun                                                -> rc 0  live: ok
     check_tasks.py ... --rerun                                                         -> rc 0  tasks: ok
   (b) `..` after a directory link: normpath reads a different, clean file
     git ls-tree -r HEAD:  120000 d -> tests/sub     (tests/sub/.keep tracked)
                           120000 src/app.sh -> ../d/../clean.sh
                           100644 clean.sh = 'echo "temp: 22"'
                           100644 tests/clean.sh = the mock above
     the kernel resolves src/app.sh to tests/clean.sh; normpath gives clean.sh
     sh src/app.sh -> temp: 21;  plain rc 1 (2 hits) in both sensors;  --rerun rc 0 live: ok / tasks: ok
   ```
   Fix: resolve the way the kernel does, one component at a time over HEAD's
   tree. If a prefix is a `120000` entry, replace it with its target and
   continue, counting the hops. Apply `..` only after the prefix before it
   has been resolved. Add self-test cases for (a) and (b).

2. **A link that leaves the tree, or does not match its target's case, is
   dropped without a word under `--rerun`, while the plain scan reads the
   file the OS resolves.** The docstring says such a link "is left out, as a
   dangling link is by the plain scan". That holds only for links that
   dangle on this machine. For every form below, the plain scan follows the
   link and catches the mock (rc 1 in both sensors), while `--rerun` gives
   rc 0 `live: ok` / `tasks: ok`:
   - an absolute link into the repo's own tree
     (`src/app.sh -> <repo>/tests/fixture.sh`): the `--rerun` probe in HEAD's
     checkout runs the mock and prints `temp: 21`;
   - an absolute link outside the repo;
   - a `../../` escape to a file beside the repo;
   - an escape and return (`../../<repo>/tests/fixture.js`);
   - on a case-insensitive filesystem (macOS default),
     `src/app.sh -> ../TESTS/fixture.sh` with `tests/fixture.sh` committed:
     `sh src/app.sh` prints `temp: 21`, and the `--rerun` probe passes too.

   93d1d60's `--rerun` gives rc 1 for the absolute in-repo form. Round 6's
   own fix text offered "skip it, or report it". The skip is what makes the
   gate mode weaker than the plain mode here, so that suggestion was wrong.

   Fix: under `--rerun`, report a link on a code path that does not resolve
   to a blob at HEAD, for example `src/app.sh: symlink leaves HEAD's tree`.
   Do not skip it. This fails closed, makes `--rerun` at least as strict as
   plain in every case, and the docstring then becomes true.

```yaml
verdict: FAIL
scope: feature (framework)
sensors: {test: pass, live: pass, formal: pass, tasks: pass, models: pass, neutral: pass, repo: pass, diagrams: pass, race: pass}
blockers:
  - "--rerun symlink resolution is lexical (os.path.normpath of the link text, then a lookup among file entries) and does not follow directory symlinks: (a) prod -> tests, src/app.sh -> ../prod/fixture.sh (a mock) and (b) d -> tests/sub, src/app.sh -> ../d/../clean.sh (the kernel reads tests/clean.sh, a mock; normpath reads clean.sh, which is clean). sh src/app.sh prints 'temp: 21' (the mock); plain check_live --only R1 / check_tasks rc 1 'src/app.sh:1: `mock`'; --rerun rc 0 'live: ok' / 'tasks: ok', and the --rerun probe itself runs the mock. 93d1d60's --rerun rc 1. C12 ('a symlink at HEAD reads as its in-tree target') and the files() docstring are false here. Fix: resolve component by component over HEAD's tree; self-test cases"
  - "--rerun drops links that leave the tree or differ in case, which the plain scan reads: an absolute link into the repo's own tree, an absolute link outside it, a ../../ escape, an escape and return, and ../TESTS/fixture.sh on a case-insensitive FS -> plain rc 1, --rerun rc 0 in both sensors (for the absolute in-repo and the case forms, the --rerun probe runs the mock). The docstring's 'left out, as a dangling link is by the plain scan' is false for these. Fix: report an unresolved link on a code path as a hit, do not skip it"
passed_by_hand: [R1, R2, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, N1, N2, N3]
probes:
  - "round-6 repro src/app.js -> ../tests/fixture.js: plain and --rerun, check_live --only R1 and check_tasks -> all rc 1 'src/app.js:1: `mock`'"
  - "symlink forms where --rerun matches or beats plain: chains of 2/5, link to .txt, link to docs/*.md, ./ and // in the target, .env link -> rc 1 in all four runs; loops, self-loop, link to a dir, a .txt link to a .js mock, a link inside tests/, dangling, link into .git -> rc 0 in all four runs; a 39-hop chain: plain rc 0 (macOS stops at 32), --rerun rc 1; 41 hops: rc 0 in all four runs"
  - "symlink forms where --rerun is weaker (blockers 1-2): via a dir link, d/.. after a dir link, absolute in-repo, absolute outside, ../../ escape, escape and return, wrong case on a case-insensitive FS -> plain rc 1, --rerun rc 0"
  - "loose-object rewrite by R1's probe: check_live --rerun rc 1 and check_tasks --rerun rc 1 (each in a fresh repo); a second --rerun in the same repo rc 0, plain rc 1"
  - "non-UTF-8 paths a\\376.js (mock) + a\\377.js (clean): files() keeps 2 entries, scan hits; a deleted loose object -> 'cannot read HEAD's objects ... the repository is incomplete', rc 1"
  - "round 5/6 scan escapes x {check_live, check_tasks} --rerun: skip-worktree, sparse, worktree-config sparse, post-checkout hook, smudge + info/attributes, replace blob/commit, fsmonitor, grafts, shallow, loose-object rewrite -> all rc 1 'src/app.js:1: `mock`', 1 worktree"
  - "probe-to-probe x both sensors: skip-worktree, sparse, worktree-config sparse, post-checkout, assume-unchanged, replace blob, fsmonitor, untrackedCache, worktree info/exclude -> R2 fails (exit 3/1/127), R1 passes"
  - "agreement battery 13 cases x {plain, --rerun} -> 26/26 agree on rc and hits; with 2 symlink cases added, 30/30"
  - "real tree: check_live --only <ID> (19) no --allow 86 hits = check_tasks 86 (diff empty); --allow 19/19 ok + tasks ok; --rerun --allow 19/19 ok; --rerun alone R3 86 = check_tasks --rerun 86, no other hit; check_formal --only 19/19 ok, --rerun R12/R13/R15 ok"
  - "races (twice): 32 elections -> 1 'only orchestrator'; 20 takeovers -> 1 'Took over'; empty stdin exit=0"
  - "cleanup: every probe repo and the real-tree runs end with 1 worktree and a clean git status"
weak_evidence:
  - "a probe's rewrite of a loose object persists: the next --rerun invocation in the same repo reads the rewritten blob (rc 0) while plain reads the checkout (rc 1). Shared object store across invocations; the HeadTree docstring now names the object store as part of the limit (C12)"
  - "fe38c4c (check_live +41/-12) and 816e237 are not covered by the audit: audit-4 is at 93d1d60; N4 is not re-judged here"
  - "a link to a directory is not expanded in either mode (src/lib -> ../tests/d): carried over from 0.9.6; it matches the plain scan"
  - "carried over unchanged from round 6: tools/live-allow.txt keeps 'framework/tools/check_live.py \\S' (C11); the QA-3/QA-4 Done-status misses and false positives; evidence JSON read from the working tree on --rerun; SIGTERM leaves a worktree registered (D12); CI runs only the self-tests"
```

Retrospective:
1. Round 6's blocker is fixed for the case it reported, and round 6's other
   weak findings are closed: the blobs are read before any probe, the paths
   are decoded with surrogateescape, and a missing object gives a message.
   The self-test case is the one round 6 asked for. It covers only the plain
   `../tests/` form.
2. A link's text was resolved on its own, without asking how the OS resolves
   it. Turning a checkout into a blob map means the sensor now does path
   resolution itself, and the kernel's rules (directory links, `..` applied
   after them, case folding) are part of what the old reader got for free.
   The test for "gate is not weaker than plain" should be differential: run
   every symlink form in both modes and fail on any form where plain hits and
   `--rerun` does not.
3. Round 6's suggested fix ("skip it, or report it") gave the author an option
   that breaks the bar. QA's suggested fixes should offer only fail-closed
   options.
