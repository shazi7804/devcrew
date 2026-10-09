# Efficiency audit — final 2 (auditor, at fe47490)

SITREP: Phase 4 efficiency gate for `feat/0.9.7-autonomy-by-proof` at fe47490.
I judged it against `proposals/0.9.7-autonomy-by-proof/requirements.md` (N4:
"the auditor's verdict has no blocker/high finding"). I measured everything
read-only, in a throwaway clone. **Verdict: PASS-WITH-DEBT.** There is no
blocker or high finding. Three findings are new, and three logged debts were
re-measured with numbers that are now larger.

## Why the auditor ran, and against which budget

- **Trigger:** both size triggers in the framework floor fired. Measured with
  `git diff --shortstat main..fe47490`, leaving out
  `proposals/*/evidence/*`, `proposals/*/formal/*` and
  `proposals/*/verdicts/*`: **77 files changed, +10,576 / −720**. Both
  limits (1000 lines, 20 files) are exceeded several times over.
  - Local `main` is still at 0.9.1, so this diff also carries the unmerged
    0.9.2–0.9.6 work.
  - 0.9.7 on its own (49d78dd..fe47490, same exclusions) is 62 files,
    +5,389 / −675.
- **Budget:** framework-default. devcrew's own change has no `standards.md`;
  TASKS.md signs only `requirements.md` and `design.md`. Recommendation: the
  next framework proposal should state a sensor-runtime budget, meaning the
  wall time allowed for `--self-test` and `--rerun` in CI.

## What the change spends

Tool code at fe47490:

| File | Lines |
|---|---|
| `check_live.py` | 1,769 |
| `check_formal.py` | 526 |
| `check_tasks.py` | 475 |
| `boot.py` | 603 |
| `tools/check_models.py` | 368 |

Six TLA+ specs plus their cfgs; SKILL.md is 68,512 B.

The largest single growth is `check_live.py`, +1,060 lines in 0.9.7:
- the logic part went from 483 to 985 lines, and about 260 of the new lines
  are `HeadTree`;
- the self-test went from 247 to 747 lines.

That is the cost of R3's signed threat model. Each guard traces to an
accident class that R3 names (uncommitted, untracked or ignored files, probe
leftovers, symlinks, names that differ only by case on some filesystems) and
to a QA or Security blocker. It is not speculative generality. The guards
do overlap, though:
- `unclean()` refuses a dirty tree;
- `at_head()` checks the contract files byte for byte;
- the scan reads blobs from the object store;
- every probe gets a reset checkout.

I raise that overlap once, as an ESCALATE note for the Architect at the next
Phase 1. I do not re-litigate it here.

## Measurements (this machine, macOS; each `git` spawn costs about 0.1 s here)

**Gate re-run on this repo**

`check_tasks.py --rerun --allow tools/live-allow.txt`:
- **530 s wall** (8 m 50 s), exit 0, `tasks: ok`;
- 399 s user, 189 s sys;
- max RSS 1.87 GB. That is the TLC JVM child (`-workers auto`, default
  heap), not the sensor.

Without `--allow`, the same run took 585 s and failed only on the scan's
self-references, as expected.

Each distinct model command, timed on its own:

| Command | Time |
|---|---|
| `--models` | 210 s |
| `--trace` | 74 s |
| `--holds Election:Election` | 45 s |
| `--accepts real` | 10 s |
| `--accepts mutant` | 10 s |
| `--holds ElectionV096` | 2 s |
| `--holds Aidlc:Aidlc` | 2 s |
| `--holds Aidlc:AidlcBroken` | 1 s |

Self-tests:

| Self-test | Time | Cases | At 0.9.6 |
|---|---|---|---|
| `check_tasks` | 17 s | 54 | — |
| `check_formal` | 65 s solo | 47 | — |
| `check_live` | 254 s | 151 | 89 s for 89 cases |

**Plain run on this repo**

`check_tasks.py` without `--rerun`: **9.0 s**.
- 102 git calls; 100 of them come from 20 `drifted()` calls, about 10 s
  cumulative under the profiler.
- The code scan takes 0.19 s.

**Larger local repo**

A clone of a 1,637-tracked-file, 270 MB repo (1,113 code files, 15.8 MB,
396k lines), with a synthetic `.aidlc/` holding 10 Done items. Each item has
a local probe that does almost nothing.

| Run | Wall | Max RSS | Where the time goes |
|---|---|---|---|
| plain | 4.7 s | 37 MB | the code scan, 4.5 s |
| `--rerun` | 49.9 s | 152 MB | per-probe checkout resets |

- `HeadTree.files()` holds 15.8 MB, the code blobs only. That confirms the
  earlier "every blob in memory" high is fixed.
- First `get()` (adding the worktree): 4.4 s.
- Each later reset: 6.7–7.7 s in isolation, about 4.5 s per probe inside the
  run.

## Findings

1. **New, medium (hot path): `drifted()` is not memoized.**
   - It is called once per evidence record (`check_live.py:775`,
     `check_formal.py:293`). Each call runs 1 `merge-base` and up to 4
     `git diff --quiet`.
   - All 22 records here carry the same sha, `320fae8`, so 100 of the 102
     git calls give only two distinct answers: one for the evidence dir,
     one for the formal dir.
   - **Fix:** memoize `drifted` per invocation on
     `(sha, evidence, contract paths)`, for example with `functools.lru_cache`
     or a dict on the `HeadTree`.
   - **Saving:** about 8 s of the 9 s plain `check_tasks` run here (about
     110 → 10 git spawns), and the same again inside every `--rerun`.

2. **Re-measured, medium (running cost): D9, repeated commands in
   `check_tasks --rerun`.** The 530 s re-run repeats:
   - `check_tasks --self-test` 4 times (the R2, R4, R7 and N2 commands):
     about 51 s wasted;
   - `--accepts real` 3 times: about 20 s;
   - `--holds ElectionV096` 3 times;
   - `--holds Election:Election` (45 s), which `--models` already ran.

   **Fix:** D9's per-invocation memo removes about 75 s of exact repeats.
   Pointing R15's check at a result `--models` already produced, instead of
   re-running TLC, would save another 45 s.

3. **Re-measured, medium (hot path): D13, per-probe index drop.**
   - On a 1,637-file, 270 MB tree: 4.5 s per probe inside the run, 6.7–7.7 s
     per reset in isolation.
   - `--rerun` costs 10.6 times the plain run (49.9 s vs 4.7 s) for 10
     trivial probes.
   - The Security-conditioned fix logged as D13 stands.

4. **New, low (running cost): C11 doubles the code scan.** C11 put the full
   code scan into `check_tasks`, so a gate that runs both `check_live` and
   `check_tasks` scans the tree twice.
   - On the larger repo the scan is 4.5 s of the 4.7 s plain run.
   - **Fix:** let `check_tasks` reuse `check_live`'s scan result when both
     run in one gate, or run one per-file pre-filter regex before the
     per-line loop.

5. **New, low (redundancy): `check_formal` repeats the clean-tree checks.**
   - `check_formal.check` re-runs `unclean()` and `at_head()`
     (`check_formal.py:173`) even when `check_tasks` already ran both and
     passes a shared tree.
   - That is two extra `git status` / `ls-files` runs per `--rerun`.
   - **Fix:** skip them when a `tree` is passed in.

6. **New, low (redundancy): unused imports, reported by pyflakes.**
   - `posixpath` at `check_live.py:97`.
   - `os` at `check_tasks.py:63`.
   - There is also an f-string with no placeholder at `check_live.py:1691`.
   - **Fix:** delete them.

7. **Re-measured, medium (running cost): D1, SKILL.md size.**
   - 68,512 B vs 57,842 B at 49d78dd (+18.4%), and +76% against `main`'s
     38,935 B.
   - It is loaded into all 12 roles.

8. **Low, ESCALATE (over-abstraction): overlapping clean-tree guards.** The
   guards in `check_live.py` (`unclean` refusal, `at_head`, the object-store
   read, the per-probe reset) overlap. Each one traces to signed R3 text. I
   recommend the Architect consider one mechanism at the next Phase 1 rather
   than four layers. Not re-litigated here.

9. **Unchanged debts:** D2, D3, D4, D5, D10, D12, D14, D15, D16.

## Retrospective

- **Worked:** timing every distinct model command on its own turned D9 from
  a vague complaint into concrete seconds that can be removed.
- **Failed:** the self-test and git-spawn timings depend heavily on this
  machine (about 0.1 s per git call), so CI's own times are still
  unrecorded (D2).
- **Next time:** record a sensor-runtime budget in the proposal so these
  numbers have a signed ceiling to be judged against.

```yaml
verdict: PASS-WITH-DEBT
trigger: changed-lines, changed-files
diff_size:
  added: 10576
  removed: 720
  files: 77
  excluded: [proposals/*/evidence/*, proposals/*/formal/*, proposals/*/verdicts/*]
budget_source: framework-default   # devcrew's own change signs no standards.md
findings:
  - severity: medium
    category: hot-path
    detail: "drifted() is called once per evidence record (check_live.py:775, check_formal.py:293); each call runs merge-base plus 4 git diffs. 22 records share one sha, giving 100 of 102 git calls and about 8 s of a 9 s plain check_tasks run here. Fix: memoize per (sha, evidence, contract)"
    status: "new -- log as Dn"
  - severity: medium
    category: running-cost
    detail: "check_tasks --rerun took 530 s here. It runs check_tasks --self-test 4 times (17 s each), --accepts real 3 times (10 s), ElectionV096 3 times, and Election:Election (45 s), which --models already covers"
    status: "debt D9 (re-measured)"
  - severity: medium
    category: hot-path
    detail: "per-probe index drop: 4.5 s per probe on a 1,637-file, 270 MB tree (--rerun 49.9 s vs 4.7 s plain, 10 trivial probes); a reset alone takes 6.7-7.7 s"
    status: "debt D13 (re-measured)"
  - severity: medium
    category: running-cost
    detail: "SKILL.md is 68,512 B vs 57,842 B at 49d78dd (+18.4%; +76% vs main) and is loaded into every role"
    status: "debt D1"
  - severity: low
    category: running-cost
    detail: "C11 put the full code scan in check_tasks, so a gate that runs check_live and check_tasks scans twice (4.5 s of a 4.7 s plain run on the larger repo). Fix: share the scan result, or pre-filter each file before the per-line loop"
    status: "new -- log as Dn"
  - severity: low
    category: redundancy
    detail: "check_formal.check re-runs unclean() and at_head() (check_formal.py:173) when check_tasks already ran both and passes a shared tree. Fix: skip them when a tree is passed"
    status: "new -- log as Dn"
  - severity: low
    category: redundancy
    detail: "unused imports: posixpath (check_live.py:97), os (check_tasks.py:63); an f-string with no placeholder at check_live.py:1691"
    status: "new -- log as Dn"
  - severity: low
    category: over-abstraction
    detail: "four overlapping clean-tree guards (unclean, at_head, object-store read, per-probe reset); each traces to signed R3 text. ESCALATE to the Architect at the next Phase 1: consider one mechanism"
    status: "escalate, not re-litigated"
  - severity: low
    category: duplication
    detail: "unchanged: ElectionV096 lifecycle layer, run_cmd beside probe, demotion rule stated 3 times, boot.py beat, SIGTERM worktree leak, non-code symlink reads, evidence-loader duplication, self-test fixtures and Aidlc/AidlcLive, CI time unrecorded"
    status: "debts D2, D3, D4, D5, D10, D12, D14, D15, D16"
blocks_gate: false
```
