# Efficiency audit — final 5 (auditor, at 2bf32b9)

**Warrant.** `git diff --shortstat main..2bf32b9`, leaving out
`proposals/*/evidence/*`, `proposals/*/formal/*` and `proposals/*/verdicts/*`:
79 files changed, 10,850 insertions, 740 deletions (11,590 changed lines).
Both framework-default triggers fire: more than 1000 lines and more than 20
files. devcrew has no `standards.md` of its own and the 0.9.7 contract signs no
§ *Code quality & efficiency budget*, so this audit uses the framework defaults
in SKILL.md § *Magnitude floor*. Recommendation: the next Phase 1 should sign a
budget for devcrew itself, covering prompt bytes per role and CI minutes per PR.
`main` is at 0.9.1, so the diff includes 0.9.2 through 0.9.6. 0.9.7's own share
(0.9.6 to 2bf32b9, same exclusions) is 68 files, +5,684 / -716.

**N4 (small on purpose: TASKS.md is one file, no new role).** It holds.
`framework/agents/` still has the same 12 roles, and 0.9.6..2bf32b9 adds no role
or doc page under `docs/agents/`. The ledger is one file with one template
(`contracts/tasks.template.md`). Each host maps its ledger onto TASKS.md and
treats a native store (missions.json `taskHistory`, `session_ledger`) as an
optional mirror only. There is no second ledger to keep in sync. The new sensors
reuse code instead of copying it: `check_formal` and `check_tasks` import
`check_live` (`fields`, `HeadTree`, `drifted`, `contract`, `unclean`, `at_head`,
`moved`, `run_shell`, `probe_env`, `scan`). Nothing was written twice at the
subsystem level.

**What I ran (own clone at 2bf32b9).** Every CI step in `checks.yml` is green:
neutral self-test and scan, `check_live --self-test` (153 cases, 262 s),
`check_formal --self-test` (66 cases, 86 s), `check_tasks --self-test` (59 cases,
12 s), `check_repo`, and `diagram check`. A plain `check_tasks` on the
proposal's TASKS.md with `--allow tools/live-allow.txt` printed `tasks: ok` in
2.4 s wall. Earlier rounds measured 10 to 22 s for the same run, so the
per-invocation `drifted()` cache (D23) is in place and works. The redundant
`.aidlc/tools` pathspec is also gone.

**What this change spends.** The measurable recurring cost is still the prompt.
SKILL.md is 68,587 B against 0.9.6's 57,842 B (+18.6%, about 2.7k tokens), and
it goes into every role dispatch (D1). Next is `--rerun` wall time. Every probe
gets a full checkout rewrite (D13). Identical commands run again: of 27 recorded
check, vacuity and conformance commands, 23 are distinct. `check_tasks
--self-test` runs 3 times, and `check_formal --self-test` and `--accepts real`
run 2 times each (D9). Last is the CI checks job, about 6 min of self-tests per
PR on this machine. None of these is measured against a budget anyone signed, so
none is above medium. All of them are already logged.

**New this round (since 01d1c3a), all low.**
- Round 2 copied the self-test environment scrub (delete `GIT_*`, set
  `GIT_CONFIG_COUNT`/`core.hooksPath`) verbatim into all three sensors:
  check_live.py:1018, check_formal.py:348, check_tasks.py:272. This grows the
  fixture duplication already logged as D16.
- Removing the second pathspec left a one-element loop in `_drifted`:
  `for s in (spec,)` (check_live.py:574-575). Fix: pass `*spec` directly
  (-1 line). This belongs with the D24 cleanups.

Removing the waste would save roughly 10 KB of prompt per role dispatch (D1),
2 to 3 s per probe on a large tree (D13), and the duplicate self-test and TLC runs
per `--rerun` (D9). Everything else is a few LOC. Nothing is a duplicated
subsystem, an unused dependency (all sensors are stdlib only) or a measured
breach of a budget.

```yaml
efficiency_audit:
  verdict: PASS-WITH-DEBT
  trigger: "changed lines 11,590 > 1000 AND changed files 79 > 20 (framework defaults; no signed standards.md budget for devcrew itself)"
  diff_size: "main..2bf32b9 excluding proposals/*/evidence|formal|verdicts: 79 files, +10,850 / -740 (0.9.7's own share from 0.9.6: 68 files, +5,684 / -716)"
  findings:
    - {severity: medium, category: running-cost, detail: "SKILL.md 57,842 -> 68,587 B (+18.6%, ~2.7k tokens) since 0.9.6, injected into every role dispatch; fix: move Formal verification and the hash detail into contracts/ files loaded only by orchestrator, qa and implementers", status: "debt D1 (unchanged)"}
    - {severity: medium, category: runtime-efficiency, detail: "HeadTree.get() unlinks the index on every probe, so checkout -f rewrites the whole tree per probe (2.3-3.1 s on a 124 MB tree in earlier rounds); also dominates check_live --self-test (262 s here) on every PR", status: "debt D13 (unchanged, pending Security's conditions)"}
    - {severity: medium, category: running-cost, detail: "check_tasks --rerun repeats identical commands: 27 recorded commands, 23 distinct (check_tasks --self-test x3, check_formal --self-test x2, check_models --accepts real x2); fix: memoize (cmd -> rc, output) per invocation", status: "debt D9 (unchanged)"}
    - {severity: medium, category: duplication, detail: "evidence JSON load, the --only unknown-ID filter and expect compile/empty-match/observed-match are written in both check_live._check_evidence and check_formal (pattern()); fix: one helper in check_live (~25 LOC)", status: "debt D15 (unchanged)"}
    - {severity: low, category: duplication, detail: "the self-test environment scrub (del GIT_*, GIT_CONFIG_COUNT/core.hooksPath) added in round 2 is copied verbatim at check_live.py:1018, check_formal.py:348, check_tasks.py:272, alongside the git init/add/commit fixture copies; fix: one fixture helper in check_live", status: "debt D16 (grown this round)"}
    - {severity: low, category: redundancy, detail: "one-element loop `for s in (spec,)` left in check_live._drifted (l.574-575) after the .aidlc/tools pathspec was dropped; posixpath import unused (l.97); f-string without placeholder (l.1770); check_formal.check re-runs unclean()/at_head() when check_tasks already did and passed its tree", status: "debt D24 (loop is new this round)"}
    - {severity: low, category: duplication, detail: "ElectionV096.tla repeats Election.tla's lifecycle layer; check_formal.run_cmd beside check_live.probe; the demotion rule stated in three places; Aidlc.cfg and AidlcLive.cfg explore one state space twice", status: "debts D3, D4, D5, D16 (unchanged)"}
    - {severity: low, category: runtime-efficiency, detail: "boot.py beat rewrites the hint file on every beat (do_beat: hint.write_text(role) unconditional) and imports subprocess eagerly; SIGTERM during a re-run leaks the registered worktree; files() still reads non-code symlink targets (`or r in dest`)", status: "debts D10, D12, D14 (unchanged)"}
    - {severity: low, category: running-cost, detail: "CI wall time unrecorded: checks job self-tests ~6 min here (262 + 86 + 12 s), models job not re-measured", status: "debt D2 (unchanged)"}
    - {severity: low, category: runtime-efficiency, detail: "drifted() memoized per invocation and redundant .aidlc/tools pathspec removed: plain check_tasks 2.4 s, `tasks: ok` (was 10-22 s)", status: "resolved (D23)"}
  blocks_gate: false
```

**Retrospective.**
- Worked: running every CI sensor in a clean clone and re-timing `check_tasks`
  confirmed D23 is fixed instead of taking the commit message's word for it.
- Failed: there is no signed budget for devcrew itself, so every cost finding
  stops at medium by rule, and D1/D9/D13 have carried over through many rounds.
- Change next time: sign a framework budget (prompt bytes per role, CI minutes
  per PR) at the next Phase 1 so these items have a threshold to be judged against.
