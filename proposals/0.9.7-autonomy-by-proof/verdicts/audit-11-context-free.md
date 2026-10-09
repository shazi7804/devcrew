# Efficiency audit — final 4 (auditor, at ca1433f)

**Trigger.** The framework-default magnitude floor fired on both size triggers.
devcrew's own change has no signed `standards.md`, so its *Code quality &
efficiency budget* is N/A. This audit uses the framework defaults and
recommends that a framework change sign a budget at its next Phase 1.

**Diff size** (`git diff --shortstat main..ca1433f`, leaving out
`proposals/*/evidence|formal|verdicts`): 79 files, +10,764 / −736. The branch
also carries 0.9.2–0.9.6, none of it merged yet. 0.9.7 alone (49d78dd..ca1433f):
67 files, +5,597 / −711. Since the last audited tree (5757e95): 30 files,
+230 / −60.

## What the change spends

The end state adds three stdlib sensors (`check_live.py` 1,807 lines, about
770 of them self-test; `check_formal.py` 543; `check_tasks.py` 518). It also
adds the election hook `boot.py` (608), the CI model runner `check_models.py`
(380), three repo checks, and TLA+ models with their seeded broken configs.

The cost for N4 to check:
- No new role: 12 agents on main, 12 here.
- One ledger file: the only `TASKS.md` in the tree is the proposal's.
- No new dependency: every import across `framework/tools` and `tools` is from
  the standard library.

Static scan (pyflakes, vulture at 80%): one unused import, `posixpath` at
`check_live.py:97`, and one f-string with no placeholder. There is no dead
function: every defined function is referenced. A 6-line exact-window
duplicate scan across the sensors finds nothing.

**The last round (C18, +230/−60) is in proportion.**
- `ScanFail` is one model action, plus one seeded broken cfg
  (`ElectionScanBroken`) in the existing vacuity pattern.
- The git-dir guard and the rmtree guard are a few lines each.
- `check_live.moved()` is written once and reused by `check_formal` and
  `check_tasks`, not copied. `check_tasks` hands its shared tree to
  `check_formal`, so the HEAD-moved check runs once per invocation.
- The new tests do add a fifth copy of the self-test git fixture (D16).

## Where the waste is (all measured or already logged; none blocks)

1. **`drifted()` is not memoized (D23). Medium; re-measured, fix proven.**
   - A plain `check_tasks.py --tasks proposals/0.9.7-autonomy-by-proof/TASKS.md
     --allow tools/live-allow.txt` makes 102 git calls, only 9 of them unique.
     20 `drifted()` calls with one key take 9.76 of 10.1 s (cProfile).
   - With a 5-line per-invocation cache keyed on `(root, sha, evidence)`, in a
     scratch copy of the sensors pointed at the same tree, the run falls from
     10.3 s to 1.4 s and still prints `tasks: ok`.
   - Measured at load average 65 on 8 CPUs, so the absolute seconds are high,
     but the ratio holds.
   - Why medium, not high: there is no signed budget, the cost is per step of
     the team's own tooling and not on a product request, and the fix costs
     the same now as later. It stays debt. Fold D23's second pathspec
     (`.aidlc/tools`, already covered by `.`) into the same fix.
2. **SKILL.md size (D1). Medium.**
   - 38,935 B on main and 57,842 B at 0.9.6; 68,587 B now.
   - That is +18.6% from 0.9.7 alone (about 2.7k tokens) and +76% against
     main, loaded into every role dispatch.
   - The fix stays as logged: move the Formal verification and hash detail
     into `contracts/` files that only orchestrator, qa and the implementers
     load.
3. **Re-run and self-test cost (D9, D13). Medium, unchanged.**
   - `check_live.py --self-test` took 507 s here (152 cases, ok), at load 65 on
     8 CPUs, on every PR. The full per-probe checkout reset (D13) dominates it.
     `check_tasks --rerun` repeats identical commands (D9).
4. **Duplication in the sensors and models (D15, D3, D4, D5). Medium/low,
   unchanged.**
   - Evidence load, `--only` and `expect` compile are duplicated between
     check_live and check_formal (D15).
   - The ElectionV096 lifecycle layer (D3).
   - `run_cmd` sits beside `probe` (D4).
   - The demotion rule is stated three times (D5).
5. **Self-test fixtures (D16). Low, grown.**
   - The new HEAD-moved / unsigned-design.md test in `check_tasks.self_test`
     writes the git init/add/commit fixture once more, making five copies.
   - Fix: one helper in `check_live` that the self-tests import.
6. **Leftovers (D24). Low, partly resolved.**
   - `posixpath` is still unused (`check_live.py:97`), and the f-string with no
     placeholder is still there.
   - `check_tasks`'s `os` import is now used by its self-test's environment
     scrub, so that part of D24 is closed.
7. **Unchanged low debts: D2, D10, D12, D14.**
   - CI time is still not recorded (D2).
   - The boot.py beat: about 115 ms wall per beat, interpreter start included,
     here (D10).
   - A SIGTERM leaks the worktree (D12).
   - HeadTree still reads the targets of non-code symlinks (D14).

There are no new categories of waste. There is no N+1 or O(n²) on a hot path
(the case-fold pass in `HeadTree.files()` is linear in tree entries), and no
new runtime dependency or cost to the product's bill. The HeadTree machinery is
large, but each part traces to the signed R3 threat model. I am not
re-litigating it here; the escalation logged in audit 9 stands.

```yaml
verdict: PASS-WITH-DEBT
trigger: "framework default magnitude floor, both triggers (changed lines > 1000, changed files > 20); standards.md budget N/A for a framework change -- defaults applied"
diff_size: "main..ca1433f excluding proposals/*/evidence|formal|verdicts: 79 files, +10764/-736 (carries unmerged 0.9.2-0.9.6); 0.9.7 alone (49d78dd..ca1433f): 67 files, +5597/-711; since 5757e95: 30 files, +230/-60"
findings:
  - {severity: medium, category: runtime-efficiency, detail: "drifted() not memoized: 102 git calls, 9 unique; 20 identical drifted() calls = 9.76 of 10.1 s of a plain check_tasks (cProfile). A 5-line per-invocation cache: 10.3 s -> 1.4 s, same 'tasks: ok' (load 65/8 CPUs; ratio holds). Also drop the redundant .aidlc/tools pathspec", status: "debt D23 (re-measured; fix demonstrated)"}
  - {severity: medium, category: running-cost, detail: "SKILL.md 57,842 -> 68,587 B (+18.6%, ~2.7k tokens) from 0.9.7, +76% vs main (38,935 B), in every role dispatch; move Formal verification and hash detail to contracts/ files loaded only by orchestrator, qa, implementers", status: "debt D1"}
  - {severity: medium, category: runtime-efficiency, detail: "check_live --self-test 507 s (152 cases) at load 65/8 CPUs, on every PR, dominated by full per-probe checkout reset; --rerun repeats identical commands", status: "debts D13, D9 (unchanged)"}
  - {severity: medium, category: duplication, detail: "evidence load / --only / expect compile duplicated across check_live and check_formal; ElectionV096 lifecycle layer; run_cmd beside probe; demotion rule stated three times", status: "debts D15, D3, D4, D5 (unchanged)"}
  - {severity: low, category: duplication, detail: "C18's new check_tasks self-test adds a fifth copy of the git init/add/commit fixture; fix: one shared fixture helper", status: "debt D16 (grown)"}
  - {severity: low, category: redundancy, detail: "posixpath still unused (check_live.py:97); f-string without placeholder; check_tasks's os import is now used (that part closed)", status: "debt D24 (partly resolved)"}
  - {severity: low, category: running-cost, detail: "CI time unrecorded; boot.py beat ~115 ms wall incl. interpreter start; SIGTERM worktree leak; non-code symlink targets read", status: "debts D2, D10, D12, D14 (unchanged)"}
blocks_gate: false
```

N4 holds: no blocker or high finding, no new role, one TASKS.md, stdlib only.
Every finding is already a logged Dn; D16, D23 and D24 have updated
measurements.

**Retrospective**
- Worked: profiling one real sensor run, then proving the fix in a scratch copy,
  turned D23 from an estimate into a demonstrated 7x saving.
- Failed: the machine was at load 65 on 8 CPUs, so the absolute timings (the
  self-test's 507 s) are not CI's. CI's own job times are still not recorded.
- Change next time: give devcrew's own changes a signed efficiency budget, so a
  per-step sensor cost has a number to judge against rather than defaults.
