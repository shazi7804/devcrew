# Efficiency audit — auditor, round 6 (final tree, at f9aa58d)

Trigger: the magnitude floor, both size triggers. `git diff --shortstat
main..f9aa58d` = 128 files changed, 12,809 insertions(+), 720 deletions(-).
That is over 1000 changed lines and over 20 files. Since round 5 (6d199e5),
leaving out evidence/, formal/ and verdicts/, the diff is 5 files, +152 / -49:

| file | added / removed | what changed |
|---|---|---|
| check_live | +124 / -41 | `_cat`, the filtered `files()`, the component-wise resolver, `blob()`, `is_code()`, and about +29 self-test lines |
| check_formal | +19 / -4 | `sources()` |
| check_tasks | +4 / -1 | |
| CHANGELOG | +3 / -2 | |
| TASKS.md | +2 / -1 | C12 reworded, D13 logged |

There is no signed `standards.md` § *Code quality & efficiency budget* for a
framework proposal, so I judged against the framework defaults.

**PASS-WITH-DEBT.** Round 5's high is fixed, and I measured it. Peak memory
of `files()` now follows HEAD's code, not HEAD's tree. Nothing new is
blocker or high. One new low (D14): the target of a non-code symlink is
still read and kept.

**HeadTree.files(), round-5 high: closed, measured.** `files()` now keeps
only what a check reads:
- every path that passes `is_code` (CODE suffixes and `.env*`);
- every path in `want`, which is the `--allow` file plus the formal
  `sources`, named before the first probe;
- every symlink, resolved to its target.

It reads them in two `cat-file --batch` passes: the link blobs first, then
the deduplicated targets. Each pass streams one object at a time, so the
3.3x buffering factor is gone. I timed one `files()` call (peak RSS of the
Python process, about 23-28 MB baseline) on the same local repos as
round 5, at 6d199e5 and then at f9aa58d:

| repo | loaded before → after | time before → after | peak RSS before → after |
|---|---|---|---|
| devcrew (133 files) | 0.9 → 0.2 MB | 0.16 → 0.19 s | 30 → 29 MB |
| a 330-file app | 13.9 → 2.4 MB | 0.21 → 0.20 s | 69 → 26 MB |
| a 1,435-file site | 68.4 → 5.2 MB | 0.76 → 0.35 s | 244 → 31 MB |
| a 1,574-file workshop | 33.9 → 3.7 MB | 0.24 → 0.18 s | 117 → 32 MB |
| a 1,637-file product | 123.7 → 16.1 MB | 0.49 → 0.24 s | 396 → 45 MB |
| a 209-file game | 55.4 → 0.5 MB | 0.28 → 0.16 s | 195 → 25 MB |

The bytes now loaded match exactly the CODE-suffix bytes I measured in
round 5 (for example 16.1 MB on the product), so nothing outside the
predicate is read.

Round 5 had to extrapolate to a large tree. This time I built a synthetic
575 MB repo:
- 60 × 10 MB random binary assets;
- 300 code files under a nested directory;
- a directory symlink, and 2,000 code symlinks that go through it;
- one symlink to a 10 MB asset.

On that repo, before → after:
- peak RSS: 2,054 MB → 45 MB;
- time: 3.6 s → 2.3 s, of which 0.9 s is profiled and warm;
- bytes loaded: 610 MB → 10.1 MB.

So the cost is now bounded by code plus symlink targets, not by tree bytes.
The profile shows the time is all `cat-file` I/O: `readline`/`read` take
0.75 s of 0.92 s, and resolving 2,000 links costs about nothing.

**Streaming `_cat` (tempfile stdin + Popen): right size.** It writes the
oid list to a `TemporaryFile` and passes that as stdin. That avoids the
pipe deadlock that writing stdin while reading stdout would cause, with no
thread. Each object is read with `readline` plus `read(size+1)`, so only
the result list is held in memory. That is the minimum. It is about 19
lines, and the old inline parse (-20) is deleted. Two non-efficiency notes
for the owners, not findings here:
- `cat.wait()`'s return code is not checked. A short read is caught by the
  header check, so this is harmless.
- An exception other than `SystemExit` inside the loop would leave the
  child process unreaped.

**Component-wise resolver: right size.** It replaces round 5's
`normpath`-and-dict-lookup. That lookup silently dropped links that go
through a directory link, which is why the synthetic repo listed 361
entries before and 2,301 after. So the new code is a correctness fix
(QA round 7) as well as a cost change. It is about 20 LOC, is bounded at
40 hops, and spawns no git; each link costs O(depth) list work. An
unresolvable code link now maps to `None`, and `check_code` reports it,
which costs one `if`. No duplicate exists in the repo; `os.path.realpath`
cannot do this, because it would resolve against the filesystem, not
HEAD's tree.

**D14, new, low: a non-code symlink's target is still read.** The
`read` filter includes `or r in dest`, so every symlink is resolved and its
target loaded and kept, whatever its name. `check_code` then skips any
name that is not code, and a formal source or the allow file is already
covered by `r in self.want`. So the clause loads bytes no consumer reads.
On the synthetic repo, `bigasset.link` → a 10 MB `.bin` was the entire
10.1 MB of non-code bytes loaded (about 99% of the total). No repo on
this machine has a symlink at HEAD, so in practice it costs nothing today.
Its bound is "assets reached through symlinks", which is far smaller than
round 5's "the whole tree".

Fix, 1 LOC: drop `or r in dest` from the `read` filter. Links stay in
`dest`, so directory links still resolve. A link named in `want` is still
read.

**check_formal.sources(): right size.** It reads each formal JSON a second
time, once to name the sources up front and once in `_check`. On this
proposal that is 3 files and 12 KB, and `sources()` took 6.6 ms. That is
the price of reading the sources before the first probe, which is the
isolation C12 accepted. Passing the parsed evidence through would save
milliseconds and couple the two passes. Not worth it. In check_tasks the
up-front list is computed once and the shared tree is passed in, so
`check_formal.check` does not call `sources()` again. The repeated
`tools/check_models.py` in the list is deduplicated by `set()`.

**blob() on-demand reads: right size.** On every normal path the file is
already in `files()`: the allow file is in `want` for both `run()` and
check_tasks, and the formal sources are in `want`. In those cases it is a
dict lookup and spawns no git. The `cat-file blob` fallback runs only for
a file nobody named up front, which the docstring states as a limit. A
missing file is re-spawned on each call and not cached. That costs
milliseconds, and only on an error path.

Small duplication, below the threshold: `os.path.relpath(allow, root)` is
now computed in `check_live.run`, `check_live.scan` and check_tasks. That
is three one-liners, logged nowhere.

**Self-test growth.** Same machine, run back to back:

| self-test | 6d199e5 | f9aa58d |
|---|---|---|
| check_live | 112 cases, 61 s | 118 cases, 54 s (inside run-to-run noise; no measurable cost) |
| check_formal | 45 cases, 20 s | 45 cases, 22 s |
| check_tasks | 51 cases, 3 s | 51 cases, 3 s |

The new check_live cases are 5 symlink forms in one shared fixture commit,
plus one assertion that `files()` reads the code and the named files and
not a 4 KB asset. That assertion is the regression guard for round 5's
high. `git worktree list` shows no leaked tree.

**Debt status:**

| Debt | Status |
|---|---|
| D1 | Open, medium, unchanged. SKILL.md is 68,418 B at f9aa58d (not in this diff), +18.3% over 57,842 B at 49d78dd. |
| D2 | Open. CI's own models time is not yet recorded. |
| D3 | Unchanged. ElectionV096.tla is not in the diff. |
| D4 | Unchanged. Fold into D9. |
| D5 | Unchanged. |
| D9 | Open, medium, unchanged. There are still duplicate TLC runs and a `java -version` per call. The self-test probe did not grow this round. |
| D10 | Unchanged. boot.py is not in the diff. |
| D12 | Open, low, unchanged. `get()`/`close()` are not in the diff. |
| D13 | Open, medium, unchanged in code; now logged in TASKS.md. `get()` still unlinks the index on every call (check_live.py:336-338). Security's ruling is still pending. |
| D14 | **New, low.** A non-code symlink's target is read and kept by `files()`. Drop `or r in dest` from the `read` filter. |

Closed this round: round 5's high (`files()` loaded every blob at HEAD).

```yaml
verdict: PASS-WITH-DEBT
trigger: changed-lines, changed-files
diff_size: {added: 12809, removed: 720, files: 128}
diff_since_round_5: {added: 152, removed: 49, files: 5, excludes: "evidence, formal, verdicts"}
budget_source: framework-default
findings:
  - {severity: low, category: runtime-efficiency, detail: "files() keeps `or r in dest` in its read filter, so every symlink's target is loaded and retained even when the link name is not code; check_code skips non-code names and want covers named files, so these bytes are unread (measured: a 10 MB .bin via one link = ~99% of the bytes loaded on a synthetic 575 MB repo; no local repo has a symlink at HEAD). Fix: drop `or r in dest` (1 LOC); links stay in dest, so directory links still resolve", status: "debt D14"}
  - {severity: medium, category: runtime-efficiency, detail: "get() still unlinks the index on every call (check_live.py:336-338), a full checkout rewrite per probe, 2.3-3.1 s vs 0.26-0.43 s on a 124 MB tree; unchanged since round 5, pending Security", status: "debt D13"}
  - {severity: medium, category: running-cost, detail: "SKILL.md 68,418 B vs 57,842 B at 49d78dd (+18.3%), injected into every role, unchanged", status: "debt D1"}
  - {severity: medium, category: running-cost, detail: "check_tasks --rerun still runs identical commands repeatedly (duplicate TLC runs, java -version per call); self-test probe unchanged this round (118 cases, 54 s)", status: "debt D9"}
  - {severity: low, category: duplication, detail: "check_formal.run_cmd beside check_live.probe, unchanged", status: "debt D4 (fold into D9)"}
  - {severity: low, category: duplication, detail: "ElectionV096.tla lifecycle layer, unchanged", status: "debt D3"}
  - {severity: low, category: hot-path, detail: "boot.py beat imports subprocess and rewrites hint files, unchanged", status: "debt D10"}
  - {severity: low, category: running-cost, detail: "SIGTERM during a re-run leaks the registered worktree and temp dir; prune at the start of get(), unchanged", status: "debt D12"}
closed: ["round-5 high: HeadTree.files() loaded every blob at HEAD (now code + named files + symlink targets, streamed; peak RSS 396 -> 45 MB on a 124 MB tree, 2,054 -> 45 MB on a 575 MB synthetic tree)"]
escalate: "unchanged from round 5: whether D13's cheaper index check (ls-files -v plus pinned trustctime/checkStat) is as sound as the unconditional unlink is a Security question."
blocks_gate: false
```

Retrospective:
- Worked: re-running the exact round-5 harness on the same six repos at
  both commits gave a direct before/after. The loaded bytes now equal the
  round-5 CODE-suffix column, which confirms the filter matches the scan
  predicate exactly.
- Failed: round 5 recommended a large reference repo and none was
  provided, so I built a synthetic 575 MB one. That repo also exposed the
  non-code-link waste (D14). Real repos here have no symlinks at HEAD. As
  before, self-test timings are single samples on a loaded machine.
- Change next time: keep a synthetic large-tree fixture with assets and
  symlinks as a standing auditor benchmark for any change to HeadTree, so
  a tree-size-linear cost is caught in the round it is introduced.
