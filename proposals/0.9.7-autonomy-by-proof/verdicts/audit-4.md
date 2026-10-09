# Efficiency audit — auditor, round 4 (final tree, at 93d1d60)

Trigger: the magnitude floor, both size triggers. `git diff --shortstat
main..93d1d60` = 123 files changed, 11,659 insertions(+), 720 deletions(-),
which is over 1000 changed lines and over 20 files. Since round 3 (1d76120),
leaving out evidence/, formal/ and verdicts/: 7 files, +236 / -46. The three
sensor tools account for +213 / -38 of that (check_live +117/-21, check_tasks
+76/-11, check_formal +20/-6). There is no signed `standards.md`
§ *Code quality & efficiency budget* for a framework proposal, so I judged
against the framework defaults.

PASS-WITH-DEBT, no blocker or high finding.

**HeadTree, now shared and reset on every get().** One tree per invocation:
`check_live.run` opens it once across all requirements files, and
`check_tasks.check` opens one and hands it to `check_evidence`, the code scan
and `check_formal.check` through the new `tree=` argument. That is exactly
the round-3 fix, so **D11 is closed** (verified in the code, not just in
TASKS.md C9). The price moved: the first `get()` runs `worktree add` on a
pinned sha, and every later `get()` deletes siblings in the temp dir and runs
three git processes (`checkout -f`, `reset --hard`, `clean -ffdx`).

Measured on a clone of this repo at 93d1d60 (128 tracked files, 3.1 MB),
20 calls:

| step | time |
|---|---|
| first get (worktree add) | 0.17 s |
| each later get (reset) | 0.146 min / 0.155 median / 0.261 max s |
| close | 0.08 s |

Gets per `check_tasks --rerun` on this proposal: 19 live probes + 1 code
scan + 3 formal source reads + 8 formal commands (3 checks, 3 vacuity runs,
2 conformance checks) = 31, so about 30 resets, about 4.5-5 s. The formal
re-runs are TLC jobs measured in minutes (D2), so on this repo this is noise.
It is a per-probe cost, though, and it grows with the tracked-file count
(the index stat in checkout/reset, the walk in clean). On a large product
repo that is seconds per probe instead of 0.15 s. Not measured there, so
low. QA and the reviewer asked for the reset (C9): a probe must not see what
an earlier probe planted. So the cost is not waste. One part of it is:

- **A redundant reset per formal item.** `check_formal._check` calls
  `tree.get()` to read the sources (line 247) and then calls `tree.get()`
  again for the check command (line 280). Nothing runs between the two, only
  file reads, so the second reset cannot undo anything. Fix: on a re-run,
  pass the `base` already returned for the check command, and reset only
  before the vacuity and conformance commands (the ones that follow a
  command that ran). That saves 1 reset per formal item (3 here, about
  0.45 s) at no LOC cost. Low. I am not logging it as debt; it fits under
  D9's memoize pass.

**`clean -ffdx` before every probe** also removes build products and
installed dependencies a `local` probe made. In round 3 that was a cost per
tree. Now it is a cost per probe: two probes that both need `node_modules`
or a venv each reinstall it. That is the isolation C9 asked for, so it is not
waste, but a project will pay it on every probe. It should be stated where
the probe is written. Low, noted, same as round 3's C8 note.

**check_tasks running the code scan.** `check_tasks.check` now repeats
`check_live._run`'s scan wiring:
- `base = tree.get() if rerun else root`;
- the `allow` path remapped into the tree with `os.path.relpath`;
- `check_code(base, src, tests, allowed(...))`.

That is the same three steps in two places, and the remap rule in particular
is a place to forget. Fix: one `check_live.scan(root, tree, rerun, src,
tests, allow)` that both call (about -4 LOC net). Low, not logged. The scan
itself costs one `get()` and one walk of `--src`. It is cheap, and R3
requires it.

**contract() / drifted() narrowing.** `contract()` now returns a list of
pathspecs (the requirements, design.md, standards.md and TASKS.md beside it,
plus verdicts/**, evidence and formal for a feature dir). `drifted()` turns
an evidence dir into an `exclude,glob` on `/**/*.json`. It is still the same
three git spawns per item, so it adds no runtime cost. It is correct to make
a model or helper kept beside the requirements count as code (C10). No
finding.

**Done-status regex.** `LEAD` / `TAIL` with a single lookbehind, no nested
quantifiers, linear. It now also catches a bare `blocked`, a bracketed
status, a capitalised status, `stalled k/n` and `attempt n/m`, and has six
new self-test cases including a negative one (`re-verifying`). The round-3
low still stands, now a little wider: the status words are spelled in both
`STATUS` and `DONE_STATUS`. Fix: one `WORDS` constant. Also, the label "a
Done line with an attempt count" is used by two different cases, so a
failure message would not say which one. Low, not logged.

**check_formal reading HEAD's sources on --rerun.** A one-line `base`
switch, with one self-test case that plants a hatch at HEAD and hides it in
the working copy. Right size.

**tools/live-allow.txt.** Five lines, three exemptions, one per sensor file.
It is needed because check_tasks now scans devcrew's own tree. It adds no
cost. Whether `framework/tools/check_live.py \S` (the whole file exempt) is
too broad a hole is a scope question for Security and the reviewer, not an
efficiency finding. I am raising it there and not judging it.

**Self-test additions.**
- check_live: 93 to 104 cases, timed at 48.8 s (at 1d76120) and 72.6 s (at
  93d1d60) on the same clone. That is one sample each on a shared machine,
  so it is indicative only, about +24 s. The new cases each build a git repo
  and some run `run()` twice. The case count is now computed (`len(ran)`)
  instead of hand-counted, which removes a number to keep in sync. Good.
- check_formal: 45 cases, 28.6 s.
- check_tasks: 51 cases, 2.8-4.7 s. The new code-scan block builds its git
  fixture with raw `subprocess.run` calls rather than the module's helpers.
  That is minor local duplication, not logged.
- `git worktree list` shows no leaked tree after all three self-tests.

These self-tests are themselves live probes in the evidence: `check_tasks
--self-test` 3x and `check_formal --self-test` 2x, as counted in round 3.
So the check_live growth is paid again on every `--rerun` in which they
appear. That belongs under D9.

**Debt status:**

| Debt | Status |
|---|---|
| D1 | Open, medium. SKILL.md is 68,418 B at 93d1d60: +71 B since 1d76120, +18.3% over 57,842 B at 49d78dd. Still injected into every role. |
| D2 | Open. CI's own models time is still not recorded; this machine has no Java runtime. |
| D3 | Unchanged. ElectionV096.tla is not in the diff. |
| D4 | Unchanged. `run_cmd` beside `probe`; both now take a reset `tree.get()`. Still fold into D9. |
| D5 | Unchanged. The demotion rule is still stated in three places. |
| D9 | Open, medium, slightly bigger. Same duplicate TLC runs and per-call `java -version`. On top of that: about 30 checkout resets per `--rerun` (0.15 s each here), a redundant reset per formal item, and a check_live self-test that is about +24 s and runs as a probe. Memoizing identical commands per invocation is still the fix. It is safe now that the sha is pinned for the whole invocation. |
| D10 | Unchanged. boot.py is not in the diff. |
| D11 | **Closed, verified.** One HeadTree per invocation, passed as `tree=` to check_evidence, the code scan and check_formal; one across requirements files in `check_live.run`. |
| D12 | Open, low, confirmed. `close()` sits only in `finally`, and there is no signal handler. A SIGTERM leaves the worktree registered and the temp dir behind. The fix still stands: `git worktree prune` plus removing stale devcrew temp trees at the start of `get()`, about 3 LOC. |

No new debt to log. The new findings are low and fit under D9 or are noted
above.

```yaml
verdict: PASS-WITH-DEBT
trigger: changed-lines, changed-files
diff_size: {added: 11659, removed: 720, files: 123}
diff_since_round_3: {added: 236, removed: 46, files: 7, excludes: "evidence, formal, verdicts"}
budget_source: framework-default
findings:
  - {severity: medium, category: running-cost, detail: "SKILL.md 68,418 B vs 57,842 B at 49d78dd (+18.3%; +71 B since 1d76120), injected into every role", status: "debt D1"}
  - {severity: medium, category: running-cost, detail: "check_tasks --rerun runs identical commands repeatedly (duplicate TLC runs, java -version per call), now plus ~30 HeadTree resets at 0.15 s each on this repo and a check_live self-test that is ~+24 s and runs as a probe", status: "debt D9"}
  - {severity: low, category: running-cost, detail: "HeadTree reset per get(): 3 git spawns, 0.146-0.261 s measured on this repo; scales with tracked-file count; clean -ffdx makes a local probe that needs a build or deps rebuild per probe (C9, accepted)", status: "noted"}
  - {severity: low, category: redundancy, detail: "check_formal._check resets the tree to read sources (l.247) and again for the check command (l.280) with nothing run between; reuse base for the check command", status: "fold into D9"}
  - {severity: low, category: duplication, detail: "check_tasks.check repeats check_live._run's scan wiring (base, allow remap, check_code); extract check_live.scan()", status: "not logged"}
  - {severity: low, category: duplication, detail: "status words in both STATUS and DONE_STATUS; one self-test label used for two cases", status: "not logged"}
  - {severity: low, category: duplication, detail: "check_formal.run_cmd beside check_live.probe, unchanged", status: "debt D4 (fold into D9)"}
  - {severity: low, category: duplication, detail: "ElectionV096.tla lifecycle layer, unchanged", status: "debt D3"}
  - {severity: low, category: hot-path, detail: "boot.py beat imports subprocess and rewrites hint files, unchanged", status: "debt D10"}
  - {severity: low, category: running-cost, detail: "SIGTERM during a re-run leaks the registered worktree and temp dir; prune at the start of get()", status: "debt D12"}
closed: [D11]
escalate: "tools/live-allow.txt exempts all of framework/tools/check_live.py from the code scan (pattern \\S) -- a scope question for Security/reviewer, not efficiency"
blocks_gate: false
```

Retrospective:
- Worked: timing 20 `get()` calls on a real clone put a number on the
  per-probe reset (0.15 s) and on the total per `--rerun` (about 5 s here),
  instead of guessing at three git spawns per probe.
- Failed: still no Java runtime here, so the models' time stays unmeasured
  (D2). The self-test timings are single samples on a loaded machine.
- Change next time: give the auditor the item counts (probes and formal
  commands per `--rerun`) with the dispatch, so the per-probe cost turns into
  a total without re-deriving it from the evidence dirs.
