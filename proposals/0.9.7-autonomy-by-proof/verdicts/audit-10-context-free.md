# Efficiency audit — final 3 (auditor, at 67b05bf)

## Warrant and budget

- Trigger: the framework default magnitude floor, BOTH triggers. Measured with
  `git diff --shortstat main 67b05bf`, excluding `proposals/*/evidence/*`,
  `proposals/*/formal/*` and `proposals/*/verdicts/*` as instructed:
  **78 files changed, 10688 insertions(+), 720 deletions(-)** (11408 changed
  lines > 1000; 78 files > 20). `main` does not contain 0.9.5 or 0.9.6 yet, so
  this range carries those changes as well. The 0.9.7 part alone
  (49d78dd..67b05bf, same exclusions) is 64 files, +5502 / -676.
- Budget: this framework change has no `standards.md` with a *Code quality &
  efficiency budget*. I judged against the framework defaults in SKILL.md
  § *Magnitude floor* and invariant 7. Recommendation: a framework proposal
  should state a sensor runtime budget (see finding 1). Without one, no runtime
  finding here can reach blocker.

## What the change spends

The code cost is in four stdlib sensors: `check_live.py` (1769 lines, about
985 of them production and the rest the self-test; 0.9.7 added 1118),
`check_formal.py` (540), `check_tasks.py` (512) and `boot.py` (608, +110 net),
plus `tools/check_models.py` (380) and two TLA+ models with 9 cfg variants.
Most of the growth in `check_live.py` is `HeadTree`, about 260 lines covering
the throwaway checkout, the HEAD-blob scan, symlink resolution and case-fold
clashes. Each of those parts traces to a clause of R3's signed threat model
(untracked or ignored files, probe leftovers, symlinks, names two filesystems
spell differently). All three sensors share the one class, so it is a shared
mechanism rather than a speculative layer, and I do not charge it as
over-abstraction. N4's structural clauses hold: one TASKS.md, still 12 roles,
no new runtime dependency (pyflakes and a stdlib import check show only stdlib).

Measured (on a machine that other review agents were loading at the same time,
so absolute times are high):
- A plain `check_tasks.py` on this proposal's TASKS.md took 22.2 s and made 102
  subprocess calls. 100 of them are in `check_live.drifted()`: 80 `git diff
  --quiet` (17.2 s) and 20 `merge-base` (4.0 s). All 22 evidence records carry
  the same sha, so 19 of the 20 `drifted()` calls repeat the first one.
- Inside each `drifted()` call, 2 of the 4 `git diff` calls are dead (new
  finding, below).
- Self-tests all pass: check_live 151 cases in 402 s, check_formal 56 in 28 s,
  check_tasks 51 in 99 s.
- boot.py beat costs about 140 ms over a bare interpreter start, of which about
  67 ms is importing `subprocess` (already D10).
- SKILL.md grew from 57.8 KB to 68.6 KB in 0.9.7 (+10.7 KB, +19%, roughly 2.7k
  tokens). It is loaded into every role dispatch (already D1).

## Findings

1. **medium · redundancy (new).** `check_live.drifted()` (framework/tools/check_live.py:548-549)
   still diffs `.aidlc/tools` as a second pathspec. That spec dates from when
   the first spec excluded the whole state dir (`:!.aidlc`). C10 replaced that
   exclusion with fine-grained globs, none of which match `.aidlc/tools/**`, so
   the first spec (`.`) already covers it. I checked this on a scratch repo:
   with the tools spec forced to report "no change", a change under
   `.aidlc/tools/` still reads `stale`. This dead spec accounts for 40 of the
   80 diff calls, about 8.6 s of the 22 s run.
   Fix: change `for s in (spec, ["--", f"{STATE}/tools"])` to iterate only over
   `spec`. Net -1 line; it halves `drifted()`'s diff calls. Fold it into D23.
2. **medium · runtime (logged as D23, confirmed).** `drifted()` is not memoized.
   It runs 20 times per plain check_tasks for one (sha, contract) key, which is
   21.2 of 22.2 s. The cost grows linearly with the number of requirements.
   Fix: cache on (root, sha, evidence tuple) per invocation. Together with
   finding 1, this should bring the run to about 1 s.
3. **medium · running cost (logged as D1).** SKILL.md +10.7 KB in every role's
   prompt. Fix as D1 says.
4. **medium · duplication (logged as D15, D3, D5, D9).** Still present.
5. **low · dead code (logged as D24).** Unused imports `posixpath`
   (check_live.py:97) and `os` (check_tasks.py:63), and an f-string with no
   placeholder (check_live.py:1691). The clean-tree guards and the code scan
   run twice when check_tasks calls check_formal.
6. **low · runtime (logged as D13).** The check_live self-test takes 402 s under
   load, dominated by full per-probe checkout resets. It runs on every PR in
   checks.yml.
7. **low (logged as D10, D14, D16).** Still present; nothing new.

No blocker or high. Nothing I measured breaks a signed budget, and the largest
waste (findings 1 and 2) is a few lines to fix, no harder to fix later than now.

```yaml
verdict: PASS-WITH-DEBT
trigger: "framework default magnitude floor, both triggers: changed lines > 1000 and changed files > 20 (standards.md budget absent for a framework change)"
diff_size: "78 files changed, 10688 insertions(+), 720 deletions(-) (main..67b05bf, excluding proposals/*/evidence|formal|verdicts); 0.9.7 alone: 64 files, +5502/-676"
findings:
  - severity: medium
    category: redundancy
    detail: "check_live.drifted() still diffs .aidlc/tools as a second pathspec; since C10 dropped ':!.aidlc' the first spec ('.') covers it (verified on a scratch repo). 40 of 80 git diff calls, ~8.6 s of a 22 s plain check_tasks. Fix: iterate only over spec (-1 line)."
    status: new (fold into D23)
  - severity: medium
    category: runtime
    detail: "drifted() is not memoized: 20 calls for one (sha, contract) key, 100 of 102 subprocess calls, 21.2 of 22.2 s; linear in requirement count. Fix: cache per invocation."
    status: logged D23 (confirmed, measured)
  - severity: medium
    category: running-cost
    detail: "SKILL.md 57.8 KB -> 68.6 KB (+19%, ~2.7k tokens) in every role dispatch."
    status: logged D1
  - severity: medium
    category: duplication
    detail: "evidence load/--only/expect compile duplicated across check_live and check_formal; ElectionV096 repeats the lifecycle layer; demotion rule stated three times; identical re-run commands not memoized."
    status: logged D15, D3, D5, D9
  - severity: low
    category: redundancy
    detail: "unused imports posixpath (check_live.py:97) and os (check_tasks.py:63); f-string without placeholder (check_live.py:1691); duplicate clean-tree guards and code scan when check_tasks calls check_formal."
    status: logged D24
  - severity: low
    category: runtime
    detail: "check_live --self-test 402 s under load, dominated by full per-probe checkout resets; runs on every PR."
    status: logged D13
  - severity: low
    category: runtime
    detail: "boot.py beat imports subprocess eagerly (~67 ms) and rewrites hint files every beat; HeadTree reads non-code symlink targets; self-test fixture copies."
    status: logged D10, D14, D16
blocks_gate: false
```

## Retrospective
- Worked: profiling the real check_tasks run per git subcommand found the cost
  and led straight to the dead pathspec.
- Failed: the machine was shared with parallel QA runs, so absolute timings are
  inflated. Ratios and call counts are the reliable numbers.
- Change next time: give framework proposals a sensor runtime budget in a
  standards section, so a regression like 22 s becomes something to judge
  rather than only describe.
