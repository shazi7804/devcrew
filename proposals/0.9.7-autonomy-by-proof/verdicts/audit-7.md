# Efficiency audit — auditor, round 7 (final tree, at bda2550)

Trigger: the magnitude floor, both size triggers. `git diff --shortstat
main..bda2550` = 130 files changed, 13,323 insertions(+), 720 deletions(-).
That is over 1000 changed lines and over 20 files. Since round 6 (f9aa58d),
leaving out evidence/, formal/ and verdicts/, the diff is 3 files, +105 / -32:

| file | added / removed | what changed |
|---|---|---|
| check_live | +98 / -29 | the case/normalization collision fold in `files()`, `HeadTree.ls()`, `canon()`, `blob()` cut down to a lookup, `check_code` taking the tree, `files()` forced at the start of `_run` on `--rerun`, and +41 self-test lines |
| CHANGELOG | +5 / -2 | |
| TASKS.md | +2 / -1 | C12 reworded, D14 logged |

There is no signed `standards.md` § *Code quality & efficiency budget* for a
framework proposal, so I judged against the framework defaults.

**PASS-WITH-DEBT.** Nothing new is blocker or high. Every new cost is
linear in HEAD's entry count, and on every real repo here it is
milliseconds. It becomes visible only at 200,000 entries, where it is
0.1 s for the fold and 0.3 s for `ls()`. The change also deletes code:
`blob()`'s late `cat-file` fallback (-13 / +3) and `check_code`'s
hand-written prefix/fnmatch pathspec filter are gone. D14 is still open.
One non-efficiency note goes to QA/Security (below).

**How I measured.** I timed one `files()` call and one `ls()` call (peak
RSS of the Python process, 23-28 MB baseline) at f9aa58d and at bda2550 on:
- the six local repos from round 6;
- the round-6 synthetic large repo, rebuilt to the same recipe: 60 × 10 MB
  random assets, 300 nested code files, a directory link, 2,000 code links
  through it, and one link to a 10 MB asset (603 MB of objects, 2,362
  entries);
- a new wide synthetic repo with 200,010 entries (50,005 `.js`, the rest
  `.png`, 10 names that differ only in case). It stresses the per-entry
  costs this round adds.

| repo | entries at HEAD | `files()` before → after | peak RSS before → after | `ls()` (2 calls) | fold |
|---|---|---|---|---|---|
| devcrew | 135 | 0.38 → 0.39 s | 29 → 29 MB | 0.10 / 0.10 s | 0.1 ms |
| a 330-file app | 330 | 0.21 → 0.19 s | 27 → 27 MB | 0.09 / 0.09 s | 0.1 ms |
| a 1,435-file site | 1,435 | 0.44 → 0.32 s | 32 → 32 MB | 0.12 / 0.12 s | 0.4 ms |
| a 1,574-file workshop | 1,574 | 0.19 → 0.18 s | 32 → 32 MB | 0.09 / 0.09 s | 0.4 ms |
| a 1,637-file product | 1,637 | 0.23 → 0.21 s | 44 → 45 MB | 0.09 / 0.09 s | 0.5 ms |
| a 209-file game | 209 | 0.18 → 0.18 s | 24 → 25 MB | 0.09 / 0.09 s | 0.1 ms |
| synthetic large (603 MB) | 2,362 | 1.39 → 1.39 s | 47 → 47 MB | 0.12 / 0.12 s | 2.4 ms |
| synthetic wide | 200,010 | 1.05 → 1.14 s | 174 → 202 MB | 0.28 / 0.30 s | 92 ms |

Bytes loaded did not change on any repo (for example, 16.1 MB on the
product and 10.5 MB on the large synthetic). The round-6 high stays closed.

**Collision fold: right size.** This is one `unicodedata.normalize("NFD")`
plus one `casefold()` per HEAD entry, kept in a dict of lists. It costs
0.1-2.4 ms on every real and large repo here. On 200,010 entries it costs
92 ms and +28 MB peak RSS, about 9% on top of a `files()` whose own
`ls-tree` parse already holds every entry. Folding only the names that are
read would be cheaper, but it would miss a clash between a scanned
`x.js` and an unscanned `X.JS` (the suffix test is case-sensitive). So
whole-tree is the correct scope for what it guards, not waste. It is O(n),
runs once per invocation (inside the cached `files()`), and adds no git
spawn. Clashing targets are left out of `need`, so a collided blob is never
read. No finding.

**HeadTree.ls(): right size, and called once per --rerun.** It does a
`read-tree` of the pinned commit into a temporary index, then `ls-files`
with the user's pathspec. There is one call site, `check_code`. `scan()`
calls `check_code` once per `run()`, and check_tasks calls `scan()` once
per invocation, so each `--rerun` pays for one `ls()`. The cost is about
0.09-0.12 s fixed (two git spawns) on every real repo, and 0.28 s on 200k
entries. The temporary index is about 18 MB on disk at 200k entries,
written and removed within the call; on devcrew it is a few KB. Whole-scan
time in `check_code` on a re-run:

| repo | before | after |
|---|---|---|
| synthetic large | 0.02 s | 0.11 s |
| synthetic wide | 0.51 s | 0.83 s |
| the 1,637-file product | 1.57 s | 1.64 s |

The added time is `ls()`. The other way to do it would be `ls-tree -r
--name-only` with a pathspec, which saves one spawn. But `ls-tree` does not
take the full pathspec magic (`:(glob)`, `:!`) that the plain scan's
`ls-files` takes, and getting the same semantics in both modes is the point
of the change. It also replaces the hand-written prefix/fnmatch filter it
deletes. No finding.

**`files()` forced at the start of every --rerun: no cost.** It is
idempotent (cached in `self.blobs`). Every `--rerun` path ends in `scan()`,
which calls `files()` anyway, and `get()` already forces it before the first
checkout probe. The forced call only moves the read earlier, ahead of the
`--deployed` probes, which run in the user's checkout and not through
`get()`. That is the one path that needed it. The only extra spend is on an
argument error that raises `SystemExit` before `scan()`. No finding.

**`canon()`: right size.** It is one line of `posixpath.normpath` plus a
prefix strip. It is applied to `want` once and to each `blob()` lookup. It
replaces the `strip("/").removeprefix("./")` that was deleted from
`check_code`, so it is not a duplicate. The three
`os.path.relpath(allow, root)` one-liners from round 6 are unchanged and
still below the threshold.

**`blob()`: smaller.** It is now a dict lookup with an `isinstance`. The
on-demand `cat-file blob` spawn is gone, so a name no check registered
costs nothing and spawns nothing. That closes round 6's "a missing file is
re-spawned on each call" note.

**Self-test growth.** check_live went from 118 to 124 cases (+41 lines):
- 3 `--src` pathspecs on a re-run;
- one `--deployed` probe that rewrites HEAD's loose object for `app.js`,
  then puts it back;
- one commit built with `hash-object` + `update-index --cacheinfo` (a case
  collision through a symlink);
- one `blob()` spelling assertion.

Each re-run case builds a worktree, so each one is a few hundred ms. The
object rewrite happens only in the fixture's own `.git`. Same machine,
load average 13-17, runs interleaved:

| self-test | f9aa58d | bda2550 |
|---|---|---|
| check_live | 118 cases: 76 / 68 / 70 s (median 70) | 124 cases: 63 / 90 / 63 s (median 63) |
| check_formal | 45 cases, 23 s | 45 cases, 23 s |
| check_tasks | 51 cases, 3 s | 51 cases, 3 s |

The growth is inside run-to-run noise; no measurable cost. `git worktree
list` shows no leaked tree.

**Non-efficiency note for QA/Security (not a finding here).** `ls()` runs
`read-tree` on HEAD's tree objects when `scan()` runs, which is after the
probes, so it reads the object store after any command. The new docstring
and CHANGELOG say HEAD is read "once, before any command runs ... never
after". The blob bytes are read before the probes. The name list is not.
Because names are filtered by `r in blobs`, a probe that rewrites a *tree*
object could only drop names from the scan, not add them, but dropping a
fake is the failure that matters. The self-test rewrites a blob object, not
a tree object. A fix at no extra cost: pass `src` to `HeadTree` the way
`want` is passed, and run `ls()` inside the first `files()`. That is one
call either way.

**Debt status:**

| Debt | Status |
|---|---|
| D1 | Open, medium, unchanged. SKILL.md is 68,418 B at bda2550 (not in this diff), +18.3% over 57,842 B at 49d78dd. |
| D2 | Open. CI's own models time is not yet recorded. |
| D3 | Unchanged. ElectionV096.tla is not in the diff. |
| D4 | Unchanged. Fold into D9. |
| D5 | Unchanged. The demotion rule is still stated in three places. |
| D9 | Open, medium, unchanged. There are still duplicate TLC runs and a `java -version` per call; check_tasks and check_formal are not in the diff. |
| D10 | Unchanged. boot.py is not in the diff. |
| D12 | Open, low, unchanged. `ls()` uses a `TemporaryDirectory`, which a SIGTERM would also leave behind, but it is a temp index removed on any normal exit and adds nothing registered. Same fix: prune at the start of `get()`. |
| D13 | Open, medium, unchanged in code. `get()` still unlinks the index on every call (check_live.py:360-362). Security's ruling is still pending. |
| D14 | Open, low, unchanged. `or r in dest` is still in the `read` filter (check_live.py:311). On the rebuilt synthetic repo, `bigasset.link` → a 10 MB `.bin` is still 10.0 of the 10.5 MB loaded. The new loop keeps the target's bytes under the link's non-code name, and no check reads them. Same 1-LOC fix. |

Closed this round: none. Round 6 had no blocker or high; the round-5 high
stays closed, and bytes loaded are unchanged on every repo.

```yaml
verdict: PASS-WITH-DEBT
trigger: changed-lines, changed-files
diff_size: {added: 13323, removed: 720, files: 130}
diff_since_round_6: {added: 105, removed: 32, files: 3, excludes: "evidence, formal, verdicts"}
budget_source: framework-default
findings:
  - {severity: low, category: runtime-efficiency, detail: "files() still keeps `or r in dest` in its read filter (check_live.py:311), so a non-code symlink's target is loaded and retained under the link's name though no check reads it (re-measured: a 10 MB .bin via one link = 10.0 of 10.5 MB loaded on the rebuilt synthetic large repo; no local repo has a symlink at HEAD). Fix: drop `or r in dest` (1 LOC)", status: "debt D14"}
  - {severity: medium, category: runtime-efficiency, detail: "get() still unlinks the index on every call (check_live.py:360-362), a full checkout rewrite per probe; unchanged, pending Security", status: "debt D13"}
  - {severity: medium, category: running-cost, detail: "SKILL.md 68,418 B vs 57,842 B at 49d78dd (+18.3%), injected into every role, unchanged", status: "debt D1"}
  - {severity: medium, category: running-cost, detail: "check_tasks --rerun still runs identical commands repeatedly (duplicate TLC runs, java -version per call); not in this diff", status: "debt D9"}
  - {severity: low, category: duplication, detail: "check_formal.run_cmd beside check_live.probe, unchanged", status: "debt D4 (fold into D9)"}
  - {severity: low, category: duplication, detail: "the demotion rule stated in three places, unchanged", status: "debt D5"}
  - {severity: low, category: duplication, detail: "ElectionV096.tla lifecycle layer, unchanged", status: "debt D3"}
  - {severity: low, category: hot-path, detail: "boot.py beat imports subprocess and rewrites hint files, unchanged", status: "debt D10"}
  - {severity: low, category: running-cost, detail: "SIGTERM during a re-run leaks the registered worktree and temp dir (ls()'s temp index too, unregistered); prune at the start of get(), unchanged", status: "debt D12"}
closed: []
measured_new_costs:
  collision_fold: "0.1-2.4 ms on all real and 603 MB synthetic repos; 92 ms and +28 MB peak RSS at 200,010 entries; whole-tree scope required (a case-sensitive suffix test would miss x.js vs X.JS otherwise)"
  ls: "one call per --rerun (single call site, check_code, called once by scan); 0.09-0.12 s fixed, 0.28 s and an 18 MB temp index at 200,010 entries; replaces the deleted hand-written pathspec filter"
  forced_files: "zero: cached, and every --rerun path already reads it in scan(); only moves the read ahead of --deployed"
  self_test: "check_live 118 -> 124 cases; medians 70 s -> 63 s at load 13-17, inside noise"
escalate: "QA/Security: ls() reads HEAD's tree objects at scan time, after the probes, though the docstring and CHANGELOG say HEAD is read once before any command; a probe that rewrites a tree object could drop a name from the scan. Cost-neutral fix: pass src to HeadTree and run ls() in the first files(). D13's index-check soundness is still a Security question."
blocks_gate: false
```

Retrospective:
- Worked: rebuilding the round-6 synthetic large repo and adding a
  200k-entry wide repo split the two cost axes. Tree bytes stayed flat;
  entry count is the only axis this round touches, and it stays small even
  at 200k entries.
- Failed: round 6's synthetic fixture was not kept, so it had to be rebuilt
  from its description; the object count differs slightly (603 MB vs 575 MB).
  The self-test timings swing ±20 s on this loaded machine, so the growth
  can only be bounded, not measured.
- Change next time: keep both synthetic fixtures (large-bytes and
  wide-entries) as a standing benchmark for any HeadTree change, and time
  each new self-test case on its own instead of the whole suite.
