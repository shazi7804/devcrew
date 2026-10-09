# Efficiency audit — auditor, round 5 (final tree, at 6d199e5)

Trigger: the magnitude floor, both size triggers. `git diff --shortstat
main..6d199e5` = 126 files changed, 12,299 insertions(+), 720 deletions(-),
which is over 1000 changed lines and over 20 files. Since round 4 (93d1d60),
leaving out evidence/, formal/ and verdicts/: 5 files, +172 / -41.
check_live accounts for +155 / -25 of that: HeadTree.files(), QUIET_GIT, the
hardened reset, scan(), and +49 self-test lines. check_formal is +9/-10,
check_tasks +1/-4, CHANGELOG +6/-2 and TASKS.md +1 (C12). There is no signed
`standards.md` § *Code quality & efficiency budget* for a framework
proposal, so I judged against the framework defaults.

**FAIL: one high finding.** HeadTree.files() reads every blob at HEAD into
memory on every `--rerun`, and peak memory comes to about 3.3x the size of
HEAD's tree. 78-99% of those bytes, measured, are never read by anything.
The hardened reset also adds a second measured cost, logged as medium debt
(D13). Everything else in the round is right-sized, and two of round 4's
lows are closed.

**HeadTree.files() — high, measured.** On the first `get()` or scan of a
re-run, `ls-tree -r` lists every file at HEAD. Then one `cat-file --batch`
over all of them goes through `subprocess.run(capture_output=True)`. The
whole stream is buffered, and each blob is then copied out by slicing
(check_live.py:249-258). The isolation does not need this. The eager read
stops a probe from rewriting an object under the scan, and that holds for
the subset that is actually read. Nothing reads the rest: `check_code`
keeps only CODE suffixes and `.env`, and check_formal reads the few
`sources` its evidence names.

I measured one `files()` call (peak RSS, Python baseline 15 MB) on local
repos at HEAD:

| repo | files | loaded | CODE-suffix bytes | time | peak RSS |
|---|---|---|---|---|---|
| devcrew | 131 | 0.9 MB | 0.2 MB (22%) | 0.16 s | 30 MB |
| a 330-file app | 330 | 13.9 MB | 2.4 MB (17%) | 0.28 s | 69 MB |
| a 1,435-file site | 1,435 | 68.4 MB | 5.2 MB (7.6%) | 1.71 s | 250 MB |
| a 1,574-file workshop | 1,574 | 33.9 MB | 3.7 MB (11%) | 0.29 s | 117 MB |
| a 1,637-file product | 1,637 | 123.7 MB | 16.1 MB (13%) | 0.66 s | 420 MB |
| a 209-file game | 209 | 55.4 MB | 0.5 MB (0.9%) | 0.29 s | 195 MB |

The cost is linear in HEAD's total blob bytes, at about 3.3x, and it has no
bound. A large product repo with assets committed is the case that matters.
Assume a 2 GB tree, which is ordinary for a game, an ML repo, or a monorepo
with vendored binaries. Then the sensor needs about 7 GB just to start a
re-run, so it can OOM a CI runner and the gate cannot run at all. That is an
unbounded in-memory collection on the gate's own path, and almost all of it
is unread. The time (0.2-1.7 s once per invocation) is not the issue.

Fix, about 6-10 LOC with no loss of isolation:
- Filter `ents` before `cat-file` to what a consumer reads:
  - the scan's name predicate (suffix in CODE, or a name starting `.env`);
  - every `120000` entry plus the target it resolves to (two short passes:
    link blobs first, then their targets);
  - the `--allow` file;
  - the formal `sources` named in the evidence. These are known before the
    first probe: read them from the evidence JSON, or pass them as
    `files(extra=...)`.
- Optionally, stream with `Popen` and read one object at a time. That drops
  the 3.3x factor to about 1x of the subset.

Measured saving: 78-99% of the loaded bytes on the six repos above, for
example 420 MB to about 55 MB on the 1,637-file product.

**Hardened reset: the index unlink, medium, logged as D13.** Every
`get()` after the first now runs `rev-parse --absolute-git-dir` and unlinks
`index`, `info/sparse-checkout` and `config.worktree` (check_live.py:289).
After that come `checkout -f`, `reset --hard` and `clean`, all with
QUIET_GIT. With no index, `checkout -f` has no stat cache, so it rewrites
every tracked file on every probe. Timed over 20 `get()` calls each:

| tree | reset at 93d1d60 | reset at 6d199e5 | 6d199e5 with the index kept |
|---|---|---|---|
| devcrew (131 files) | 0.27 s median | 0.26 s median | — |
| 1,637-file / 124 MB product | 0.43 s median | 2.3-3.1 s median (max 4.6 s) | 0.26-0.29 s median |

Unlinking the index alone accounts for the difference, which I confirmed by
removing only that one unlink in a copy. A `--rerun` of this proposal makes
27 `get()` calls (19 live probes + 8 formal commands; the scan and the
formal sources no longer call `get()`). At the 1,637-file size that is
about +50-70 s per re-run, and it grows with tree bytes, so a multi-GB tree
pays minutes per probe. The extra `rev-parse` (~10 ms) and the other two
unlinks cost nothing that matters.

Fix: drop the index only when a probe can have tainted it. `git ls-files -v`
(0.04 s on the 124 MB tree) shows a lowercase or `S` flag for assume-unchanged
or skip-worktree. Keep the sparse/worktree-config unlinks. Pin
`-c core.trustctime=true -c core.checkStat=default` in QUIET_GIT so a forged
mtime cannot pass as clean. That brings back round 4's per-probe cost.

I am logging this as medium, not high. The unconditional unlink is the
simplest sound defence against a probe that forges the index's stat data.
Whether the cheaper check is equally sound is a Security question, not an
efficiency one (ESCALATE below). If Security says yes, the full rewrite is
waste and should go.

**Symlink resolution.** `target()` follows a `120000` blob through the
in-memory map, bounded at 40 hops. A link to a directory, a link out of the
tree, or a dangling link is left out, the same as `p.is_file()` in the
plain scan. It costs one dict lookup per link and no git spawn. Right size.

**check_live.scan() — round-4 duplication closed.** `_run` and
`check_tasks.check` now both call `check_live.scan(root, tree, rerun, src,
tests, allow)`. The `base`/`relpath` remap is gone from both, and
check_tasks drops its `os` import (-4 LOC there). `check_code` gained a
`blobs=` branch for the name list and the byte source, which is the minimum
needed to scan blobs instead of files. `allowed(allow, text=None)` reads the
allow file from HEAD on a re-run. No duplication left. **Closed.**

**check_formal reading blobs — round-4 redundant reset closed.** On a
re-run, sources come from `tree.files()` (memoized, free after the first
call), not from `tree.get()`. That removes the reset per formal item that
round 4 flagged, as a side effect. `hatches(path, text)` now takes the text
it is given, and the existence check is `src not in texts`. Net -1 LOC.
Right size.

**Self-test growth.** Same machine, run back to back:
- check_live: 104 to 112 cases, 55 s to 70 s (+15 s). The new cases are:
  - a symlink to a fixture, run and re-run;
  - three probe tricks against the scan (skip-worktree, sparse checkout, a
    smudge filter);
  - three carry-over tricks against the next probe (skip-worktree, sparse
    checkout, a post-checkout hook).

  Each case builds or reuses a git fixture. That is proportionate to the
  hardening C12 accepted. The +15 s is paid again wherever the check_live
  self-test is a probe (D9).
- check_formal: 45 cases, 21-23 s, unchanged.
- check_tasks: 51 cases, 3 s, unchanged.
- `git worktree list` shows no leaked tree after all three self-tests.

**Debt status:**

| Debt | Status |
|---|---|
| D1 | Open, medium, unchanged. SKILL.md is 68,418 B at 6d199e5 (not in this diff), +18.3% over 57,842 B at 49d78dd. Still injected into every role. |
| D2 | Open. CI's own models time is still not recorded; still no Java runtime here. |
| D3 | Unchanged. ElectionV096.tla is not in the diff. |
| D4 | Unchanged. `check_formal.run_cmd` beside `check_live.probe`. Fold into D9. |
| D5 | Unchanged. The demotion rule is still stated in three places. |
| D9 | Open, medium, changed shape. Fewer gets per `--rerun` (31 to 27), and the redundant formal reset is gone. Still there: the same duplicate TLC runs and per-call `java -version`. The check_live self-test probe is another +15 s. Memoizing identical commands per invocation is still the fix. |
| D10 | Unchanged. boot.py is not in the diff. |
| D12 | Open, low, unchanged. `close()` still sits only in `finally`, with no prune at the start of `get()`. A SIGTERM leaks the registered worktree and temp dir. Fix: about 3 LOC. |
| D13 | **New, medium.** The index unlink on every `get()` forces a full checkout rewrite per probe: 2.3-3.1 s vs 0.26-0.43 s on a 124 MB tree. Drop the index only when `ls-files -v` shows a flag, and pin trustctime/checkStat (pending Security's view). |

Closed this round: the round-4 low on scan-wiring duplication and the
round-4 low on the redundant formal reset.

```yaml
verdict: FAIL
trigger: changed-lines, changed-files
diff_size: {added: 12299, removed: 720, files: 126}
diff_since_round_4: {added: 172, removed: 41, files: 5, excludes: "evidence, formal, verdicts"}
budget_source: framework-default
findings:
  - {severity: high, category: runtime-efficiency, detail: "HeadTree.files() (check_live.py:249-258) loads every blob at HEAD into memory on every --rerun via one buffered cat-file --batch plus slice copies; peak RSS ~3.3x HEAD's blob bytes, unbounded (measured 420 MB on a 124 MB tree, 195 MB on a 55 MB tree), of which 78-99% is never read (the scan keeps CODE suffixes/.env; check_formal reads only named sources). Fix: filter ents before cat-file to the scan predicate + symlinks and their targets + --allow + the evidence's formal sources (all known before the first probe), optionally stream with Popen; ~6-10 LOC, -78..99% memory, isolation unchanged", status: "blocks"}
  - {severity: medium, category: runtime-efficiency, detail: "the reset unlinks the index on every get() (check_live.py:289), so checkout -f rewrites the whole tree per probe: 2.3-3.1 s vs 0.26-0.43 s median on a 1,637-file/124 MB tree, ~+50-70 s per --rerun at 27 gets, scales with tree bytes; drop the index only when ls-files -v shows a flag, and pin trustctime/checkStat", status: "debt D13"}
  - {severity: medium, category: running-cost, detail: "SKILL.md 68,418 B vs 57,842 B at 49d78dd (+18.3%), injected into every role, unchanged", status: "debt D1"}
  - {severity: medium, category: running-cost, detail: "check_tasks --rerun runs identical commands repeatedly (duplicate TLC runs, java -version per call); gets down 31 to 27, but the check_live self-test probe is +15 s (55 s to 70 s, 104 to 112 cases)", status: "debt D9"}
  - {severity: low, category: duplication, detail: "check_formal.run_cmd beside check_live.probe, unchanged", status: "debt D4 (fold into D9)"}
  - {severity: low, category: duplication, detail: "ElectionV096.tla lifecycle layer, unchanged", status: "debt D3"}
  - {severity: low, category: hot-path, detail: "boot.py beat imports subprocess and rewrites hint files, unchanged", status: "debt D10"}
  - {severity: low, category: running-cost, detail: "SIGTERM during a re-run leaks the registered worktree and temp dir; prune at the start of get()", status: "debt D12"}
closed: ["round-4 low: scan wiring duplicated in check_tasks (now check_live.scan())", "round-4 low: redundant reset per formal item (sources now read from tree.files())"]
escalate: "D13's fix keeps the index unless ls-files -v shows a flag, and relies on core.trustctime/checkStat to defeat a forged-stat index; whether that is as sound as the unconditional unlink is a Security question. If it is, the full per-probe rewrite is waste."
blocks_gate: true
```

Retrospective:
- Worked: running `files()` and `get()` against real local repos of
  increasing size, not only devcrew's 131 files, exposed both costs. On
  devcrew they are invisible: 30 MB, and 0.26 s against 0.27 s.
- Failed: there is no truly large (multi-GB) repo on this machine, so the
  2 GB figure is extrapolated from a linear fit over six repos (stated as
  an assumption). Self-test timings are single samples on a loaded machine.
- Change next time: dispatch the auditor with one large reference repo to
  measure the sensors against. A per-probe or per-invocation cost that
  scales with tree size cannot be judged on the framework's own small tree.
