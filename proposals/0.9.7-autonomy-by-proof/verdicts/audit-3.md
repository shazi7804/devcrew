# Efficiency audit — auditor, round 3 (final tree, at 1d76120)

Trigger: the magnitude floor, both size triggers. `git diff --shortstat
main..1d76120` = 118 files changed, 10,890 insertions(+), 720 deletions(-),
which is over 1000 changed lines and over 20 files. Since round 2 (591cf96),
leaving out evidence/, formal/ and verdicts/: 32 files, +467 / -216. The
tools account for +176 / -54 of that (check_live, check_formal, check_tasks,
check_models). There is no signed `standards.md` § *Code quality & efficiency
budget* for a framework proposal, so I judged against the framework defaults.

PASS-WITH-DEBT, no blocker or high finding.

**HeadTree (a throwaway worktree per call).** It is created lazily. `get()`
only runs on a `--rerun` path for an item that is actually re-run, so a plain
check costs nothing. `close()` sits in a `finally`. Measured on a clone of
this repo at 1d76120 (123 tracked files, 2.4 MB): `worktree add` took
0.31-0.56 s and `worktree remove` took 0.17-0.30 s, so about 0.5-0.8 s per
tree. All three self-tests pass, and `git worktree list` shows no leaked tree
afterwards.

- The cost is per call, not per item. `check_tasks.check` gives its whole
  `done` list to a single `check_live.check_evidence` and a single
  `check_formal.check`. A `check_tasks --rerun` therefore makes two worktrees
  (one live, one formal), not one per Done item.
- `check_live.main` makes one worktree per requirements file.
- Both are redundant: one tree per invocation would do, because every re-run
  in a call runs against the same HEAD.
- Next to the re-runs themselves this is noise. The formal re-runs alone are
  TLC jobs that take minutes (D2: 9 m 56 s). So this is low.
- The cost grows with checkout size, and a product repo is much bigger than
  this one. The fix is small: give `check_evidence` / `check_formal.check` an
  optional `tree=` argument, and have `check_tasks` (and `check_live.main`
  across requirements files) open one `HeadTree` and pass it to both. That
  saves one checkout per `check_tasks --rerun` and N-1 per multi-feature
  `check_live` run, at about 8 LOC.
- Reuse is right: check_formal imports `check_live.HeadTree` rather than
  copying it.

**A worktree has no ignored files.** C8 accepted this. The running cost it
moves onto a project: a `local` probe that needs a build or installed
dependencies (node_modules, a venv, a compiled artifact) must now rebuild or
reinstall inside the fresh tree on every re-run, or it fails. That is the
point of the change, so it is not waste. It is a cost a project will pay, and
it should be stated where the probe is written. Low.

**Staleness got stricter.** `drifted` no longer exempts `:!*.md`. Only the
evidence dirs, the feature contract dir, the state dir and `TASKS.md` are
exempt now. A prompt edit now makes evidence stale, which means more re-runs.
That is correct (a Markdown prompt is code here) and not waste.

**check_formal.run_cmd vs check_live.probe (D4).** Not changed. Both now take
`tree.get()`, but they are still two subprocess wrappers:
- `probe`: scrubbed env, 300 s timeout, raises on timeout;
- `run_cmd`: full env, 3600 s timeout, returns None on timeout.

The fold into D9 stands: one helper `run(cmd, cwd, env=None, timeout=...)`
returning `(rc|None, text)`.

**Repeated identical commands (D9).** Still open, and slightly bigger. Across
the 9 formal evidence commands:
- `--accepts real` appears twice, and runs a third time inside `--trace`;
- `--holds Election:Election` runs again inside `--models`;
- `--models` now also runs the new AidlcJudgmentBroken seed.

On top of that, `check_models` now spawns `java -version` once per invocation
before it does any work. That is about 0.1-0.5 s, nine times per
`check_tasks --rerun`. It is cheap, but memoizing per invocation (D9) would
remove it along with the duplicate TLC runs. Of the 19 live probes, 16 are
distinct: `check_tasks --self-test` appears 3 times and `check_formal
--self-test` twice.

**The new Done-status regex in check_tasks.** It is linear. There are no
nested quantifiers, so it has no backtracking risk. It replaces a broader
inline regex plus a `"·" in rest` test, and the 5 new self-test cases cover
both directions.

One small piece of duplication: the three status words (building, verifying,
fixing) are now listed in both `STATUS` and `DONE_STATUS`. Fix: build both
from one `WORDS = "building|verifying|fixing"` constant (saves nothing in LOC,
removes a place to forget). Low. I am not logging it as debt.

**The `"!x"` negative-expectation form in the self-test runner** is three
lines and has several users. It is fine.

**The AidlcJudgmentBroken seed** is minimal:
- one constant (`DropRecord`) on one action conjunct in Aidlc.tla;
- a 12-line cfg with `Items = {i1}`;
- one MODELS entry.

It reuses the Aidlc spec instead of copying it, which is the right shape.
I could not time it: the pinned jar is present, but this machine has no Java runtime, and check_models exits 2 (no verdict), as designed. With one
item and the base Aidlc state space it should be far below Election's
199 s. Its real cost belongs in CI's time under D2.

**check_models' exit-2 "no verdict" path** (`nothing()`) replaces two
`startswith("outside")` tests with one helper. That is net reuse.

**Debt status:**

| Debt | Status |
|---|---|
| D1 | Grew a little. SKILL.md is 68,347 B at 1d76120, against 67,699 B at 591cf96 (+648 B, +1%) and 57,842 B at 49d78dd (+18.2% overall). Still injected into every role. Still medium, still open. |
| D2, D3, D5, D10 | Unchanged (ElectionV096.tla and boot.py are not in the diff since 591cf96). |
| D4 | Unchanged (see above). |
| D9 | Unchanged, now covers one more TLC run plus a `java -version` per call. |

New debt to log: D11 (one HeadTree per invocation, shared between check_live
and check_formal).

```yaml
verdict: PASS-WITH-DEBT
trigger: changed-lines, changed-files
diff_size: {added: 10890, removed: 720, files: 118}
diff_since_round_2: {added: 467, removed: 216, files: 32, excludes: "evidence, formal, verdicts"}
budget_source: framework-default
findings:
  - {severity: medium, category: running-cost, detail: "SKILL.md 68,347 B vs 57,842 B at 49d78dd (+18.2%; +648 B since 591cf96), injected into every role", status: "debt D1"}
  - {severity: medium, category: running-cost, detail: "check_tasks --rerun runs identical commands repeatedly (--accepts real 3x, Election 2x, now + AidlcJudgmentBroken in --models, + java -version per check_models call)", status: "debt D9"}
  - {severity: low, category: running-cost, detail: "HeadTree: check_tasks --rerun makes two worktrees (check_live + check_formal), check_live makes one per requirements file; measured 0.5-0.8 s each on this repo, scales with checkout size; fix: open one HeadTree per invocation and pass it as tree=", status: "new debt D11"}
  - {severity: low, category: duplication, detail: "check_formal.run_cmd beside check_live.probe, unchanged; both now take tree.get()", status: "debt D4 (fold into D9)"}
  - {severity: low, category: duplication, detail: "ElectionV096.tla lifecycle layer, unchanged", status: "debt D3"}
  - {severity: low, category: hot-path, detail: "boot.py beat imports subprocess and rewrites hint files, unchanged", status: "debt D10"}
  - {severity: low, category: duplication, detail: "status words listed in both STATUS and DONE_STATUS in check_tasks.py; build both from one constant", status: "not logged"}
  - {severity: low, category: running-cost, detail: "a local probe re-run in a fresh worktree has no ignored files: a probe that needs a build or deps rebuilds per re-run (accepted in C8)", status: "noted"}
blocks_gate: false
```

Retrospective:
- Worked: timing HeadTree on a real clone settled its cost (under 1 s per
  tree, per call, not per item) instead of guessing.
- Failed: this machine has no Java runtime, so the new seed's model time is
  unmeasured and left to CI (D2).
- Change next time: give the auditor the evidence-exclusion pathspec with a
  trailing `/*`. `':!proposals/*/evidence'` does not exclude the files under
  it.
