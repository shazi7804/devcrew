# Efficiency audit — final 6 (auditor, at 22565c0)

**Trigger.** Both default magnitude floors: `git diff --shortstat main..22565c0`
(leaving out `proposals/*/evidence/*`, `proposals/*/formal/*`,
`proposals/*/verdicts/*`) is 79 files changed, 10888 insertions(+), 740
deletions(-). That is 11628 changed lines (floor: 1000) over 79 files (floor: 20).
The range still carries the unmerged 0.9.6 work (`check_live.py` and the
`0.9.6-*` proposals), since 0.9.7 depends on it.

**Budget.** This is a framework change, so there is no project
`standards.md`. I judged against invariant 7 and N4 ("small on purpose: TASKS.md
is one file; no new role"), using the skill's default magnitude floor.

## End state against N4
- TASKS.md is one file: `contracts/tasks.template.md` plus one ledger per run.
  No new role: there are still 12 agents in `framework/agents/`.
- The sensor code is `check_live.py` 1879, `check_formal.py` 559,
  `check_tasks.py` 527 and `boot.py` 608 lines, plus `tools/` 878 lines. All of
  it is stdlib. None of this changed in size since the last audit, apart from
  `check_live.py` (below).
- Since the last audited tree (97a8673), the delta is 5 files, +81/-43. Most of
  it is in `check_live.py`: the probe checkout went from a linked worktree to a
  shared clone, and the reset now cleans first. The rest: `designer.md` pins
  `impeccable@4.1.0`, R3 gains one clause, and TASKS.md and CHANGELOG are
  updated.
- The clone is a net simplification of `HeadTree`. It removes the
  `--absolute-git-dir` / `--git-common-dir` probing, the `<common>/worktrees/`
  guard, the saved `.git` file bytes (`dotgit`) and both `worktree remove`
  calls. As a result `close()` is plain `rmtree`. It also closes the old D12:
  SIGTERM can no longer leak a worktree registered in the user's repository,
  because nothing is registered there.

## Cost of the shared clone vs the worktree it replaced (measured)
I timed the exact git commands `_add()` and `get()` issue, in a throwaway copy:

| tree | setup: worktree add | setup: clone --shared + checkout | one per-probe reset (wt / clone) | git dir |
|---|---|---|---|---|
| devcrew (2.7 MB .git, 171 files) | 0.38-0.59 s | 0.58-0.84 s | 1.0-1.6 / 1.0-1.2 s | 40 KB / 128 KB |
| 1637-file repo (148 MB .git) | 2.35-2.83 s | 3.08-3.51 s | 4.2-6.9 / 5.9-7.4 s | 236 KB / 324 KB |

- **Setup** costs about +0.25 s on devcrew and +0.6 s (about +24%) on the
  larger tree. It is paid once per sensor invocation, because one HeadTree is
  shared per invocation (C9).
- **The per-probe reset** costs the same either way, within noise. It is still
  dominated by dropping the index (D13).
- **The extra `clean -qffdx`** before checkout is in the noise.
- **Disk**: about +88 KB per run, mostly git's sample hooks copied from the
  template. Nothing is copied from the object store.
- **Self-test**: `check_live.py --self-test` took 4:33 wall for 155 cases at
  22565c0, vs 3:50 for 153 cases at 97a8673. CPU time went from 78.0 s to
  82.5 s (+6%), so most of the wall-clock difference is machine load.

Verdict on the swap: the cost is small and bounded, and it removes about 20
lines of guard code. No finding beyond a low one.

## New finding: worktree-era self-test cases are now vacuous
- **"a git that cannot name the checkout's git dir"** (`check_live.py:1650-1673`).
  Its shim fails `rev-parse --absolute-git-dir`, which the code no longer calls.
  `refused` is assigned and never read; the round-3 edit dropped it from the
  assertion. The case can no longer fail. That is about 24 lines of dead test,
  and it builds a repo and checkout on every self-test run.
- **The two object-rewrite `--deployed` cases** (`check_live.py:1333-1373`).
  These are `rewrite.py` and `retree.py`. They find loose objects at
  `$(git rev-parse --git-common-dir)/objects/..`. In a shared clone that path is
  the clone's own `.git/objects`, which holds no objects, because they come via
  alternates. I confirmed the path does not exist. So the helper crashes, and
  the case passes on the scan hit it would get anyway. The `.bak` restore loop
  finds nothing.
- The threat these cases test is one R3 already rules out of scope ("rewriting
  git's objects"). Fix: delete the three cases, about 65 lines and three
  re-runs off every self-test. If they are wanted, re-aim them at the
  alternates path in a re-signed scope.
- The post-checkout-hook case at 1451 still applies: it writes into the clone's
  own hooks, and `core.hooksPath=/dev/null` is what defeats it.

## Not my category (for Security / QA, not a finding here)
The clone's own `.git/config` and `.git/info/attributes` now persist between
probes. The reset drops `index`, `info/sparse-checkout` and `config.worktree`,
but not `config`. Before the swap these were the user's shared files, which R3
rules out of scope. Whether "an earlier probe left behind" now covers the
clone's config is for Security and QA to rule on.

```yaml
verdict: PASS-WITH-DEBT
trigger: "magnitude floor: 11628 changed lines > 1000 and 79 changed files > 20 (git diff --shortstat main..22565c0, evidence/formal/verdicts excluded)"
diff_size: "79 files, +10888 / -740; since the last audited tree (97a8673): 5 files, +81 / -43"
findings:
  - {severity: medium, category: redundancy, detail: "three self-test cases left vacuous by the worktree-to-clone swap: check_live.py:1650-1673 shims rev-parse --absolute-git-dir (no longer called; `refused` assigned, never read); check_live.py:1333-1373 rewrite.py/retree.py look for loose objects under the clone's own git dir, which holds none (alternates), so they crash and pass on the scan hit regardless; fix: delete them (~65 LOC, three re-runs per self-test) or re-aim them at the alternates path", status: "new — log as Dn"}
  - {severity: low, category: runtime-efficiency, detail: "shared clone vs worktree measured: setup +0.25 s (devcrew) / +0.6 s, +24% (1637-file, 148 MB .git), once per invocation; per-probe reset unchanged within noise; +88 KB per run, mostly sample hooks; fix: `git clone --template=` (empty) to skip the hook samples", status: "new — log as Dn (cheap to leave)"}
  - {severity: low, category: redundancy, detail: "HeadTree.close() no longer needs git; SIGTERM can no longer leak a registered worktree, because nothing is registered in the user's repo", status: "resolved (D12)"}
  - {severity: medium, category: running-cost, detail: "SKILL.md +18.6% since 0.9.6, injected into every role dispatch", status: "debt D1 (unchanged)"}
  - {severity: medium, category: runtime-efficiency, detail: "per-probe reset drops the index, so checkout rewrites the whole tree on every probe; still dominates the self-test (4:33 wall here)", status: "debt D13 (unchanged)"}
  - {severity: medium, category: running-cost, detail: "check_tasks --rerun repeats identical commands; memoize per invocation", status: "debt D9 (unchanged)"}
  - {severity: medium, category: duplication, detail: "evidence load / --only filter / expect compile in both check_live and check_formal", status: "debt D15 (unchanged)"}
  - {severity: low, category: duplication, detail: "self-test git fixture and env scrub copied across three sensors; repeated cases; Aidlc.cfg/AidlcLive.cfg explore one state space twice; ElectionV096 lifecycle layer; run_cmd beside probe; demotion rule in three places", status: "debts D3, D4, D5, D16, D28 (unchanged)"}
  - {severity: low, category: redundancy, detail: "one-element loop in _drifted, unused import, repeated clean-tree guards in check_formal", status: "debt D24 (unchanged)"}
  - {severity: low, category: runtime-efficiency, detail: "boot.py beat rewrites the hint file every beat and imports subprocess eagerly; files() reads non-code symlink targets", status: "debts D10, D14 (unchanged)"}
  - {severity: low, category: running-cost, detail: "CI wall time not recorded in evidence", status: "debt D2 (unchanged)"}
blocks_gate: false
```

N4 holds: no blocker or high finding. TASKS.md is one file and there is no new
role.

**Retrospective.**
- Worked: timing the exact git commands both ways gave the swap a number, not
  an assertion.
- Failed: the round-3 diff changed the mechanism and left three self-test
  cases aimed at the old mechanism. Nothing flagged them, because a vacuous
  case still passes.
- Change next time: when a mechanism is replaced, grep the self-tests for the
  removed calls (`--git-common-dir`, `--absolute-git-dir`, `worktree`) as part
  of the audit.
