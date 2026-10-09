# Efficiency audit — final (auditor, at b572f8f)

## What put me here, and what I measured

**Trigger:** the default magnitude floor. Both size triggers fire, by a wide margin.
I used `git diff --shortstat`, leaving out `proposals/*/evidence/*`, `proposals/*/formal/*`
and `proposals/*/verdicts/*`. The trailing `/*` matters: without it git's pathspec does not
exclude those directories.

- `main..b572f8f`: **77 files, +10,037 / −720**. `main` is still at 0.9.1, so this range also
  carries 0.9.2–0.9.6. They are unmerged dependencies; the contract says 0.9.7 depends on 0.9.6.
- 0.9.7's own range, `49d78dd..b572f8f` (0.9.6's last commit to HEAD): **62 files, +4,835 / −660**.
  Of that, 22 code, model and CI files account for +2,995 / −203. Markdown outside the
  verdicts and the CHANGELOG accounts for +1,716 / −456.

**Budget:** framework changes have no `standards.md` (this proposal has none), so the
*Code quality & efficiency budget* is N/A. I judged against the framework defaults and
invariant 7. Recommendation: the next framework proposal should state a budget for itself,
for example a SKILL.md byte ceiling and a CI-minutes ceiling for the models job.

## What the change spends

- **Sensors (stdlib Python).**
  - `check_tasks.py`: 441 lines, 247 of them code and 161 self-test.
  - `check_formal.py`: 496 lines, 328 code and 144 self-test.
  - `check_live.py`: 767 → 1,328 lines. Code went from 482 to 794 lines, and the self-test
    from 284 to 496.
  - Most of the check_live growth is `HeadTree`, about 190 lines. It reads HEAD's blobs once,
    resolves symlinks through HEAD's tree, detects case-fold and normalisation collisions, and
    provides a reset throwaway worktree for probes. Each piece maps to a clause of R3's signed
    threat model (uncommitted change, untracked/ignored file, probe leftovers, symlink, two
    spellings of one name). A smaller design that met the same clause did not present itself:
    `git archive` into a fresh directory per probe still needs the symlink and case-fold logic.
    I accept it as the cost of the contract, not as speculative generality.
- **Models.** `Aidlc.tla` has 194 lines and `Election.tla` 215. `ElectionV096.tla` (140 lines)
  is the seeded broken model of the old `boot.py` that R15 requires. There are also
  `ElectionTrace.tla` and 9 small `.cfg` files.
  - I ran `tools/check_models.py --models` (pinned TLC 1.7.4, JDK 21). All 10 runs gave their
    expected verdict, in **352 s wall** (228 s user).
  - The machine's load average was about 295 during the run, so the times are upper bounds.
    `Election.cfg`, at 3.57 M states and 170 s, dominates.
  - The models job is path-filtered and has a 45-minute timeout. Within that, CI time is
    acceptable (already debt D2).
- **`check_models.py`** (368 lines) adds trace validation: 5 real runs, 3 mutants, and retries
  only on a broken assumption. It is CI for the framework only, and nothing in it is installed
  into projects.
- **`boot.py` hot path.** The beat now also fires async on every tool call (assumption A2).
  I measured 20 beats at about 67 ms CPU each (user + sys), with the claims directory staying
  at one generation plus the hint file. For a 200-tool-call session that is about 13 s of CPU,
  async and with no latency. The cost is negligible and justified by A2. The remaining
  rewrites are already debt D10.
- **Prompt payload.** SKILL.md grew from 57,842 to 68,418 B (+18.3%), and it is loaded by
  every role. That is real recurring token cost, already logged as debt D1.
- **Dependencies:** none new. The sensors import only the stdlib, and TLC is pinned by
  sha256 in CI.

## N4 — "small on purpose"

Every component traces to a signed item:

- `check_tasks.py` covers R1–R4.
- `check_formal.py` covers R10 and R11.
- `HeadTree` covers R3's threat model.
- The models cover R12 and R15.
- Trace validation and `check_repo.py`'s set comparison cover R13.

TASKS.md is one file, and no role was added. None of what I found is a duplicated subsystem,
an unused dependency, a one-implementation layer, or a measured hot-path or bill problem. So
nothing is blocker or high, and **N4's acceptance holds**.

The diff is large because the signed contract is large (15 requirements, three sensors, two
protocol models, trace validation). What is left is local: duplicated helpers between the two
sensors, duplicated self-test fixtures, one repeated state-space exploration, and the debts
already logged.

## New findings (not in the TASKS.md debt list)

1. **Duplication (medium).** `check_live._check_evidence` repeats the logic of
   `check_formal.pattern()` (check_formal.py:140-155):
   - It compiles `expect`, rejects one that matches `""`, and checks that `observed` matches,
     inline at check_live.py:573-582.
   - It also repeats the `--only` unknown-ID filter, character for character, at
     check_live.py:534-538 and check_formal.py:185-189.
   - It also repeats the evidence load ("not a JSON object", then the missing fields).

   `check_formal` already imports `check_live`. **Fix:** move `pattern()`, an `only_filter()`
   and a `load_evidence()` into `check_live` and call them from both. That saves about 25 lines,
   and the two sensors cannot drift apart on what "an expect that proves nothing" means.
2. **Duplication (low).** The self-test git fixture is written four times: check_live.py:800-814,
   check_formal.py:330-347, check_tasks.py:345-348 and check_tasks.py:384-387. Each is the same
   `-c user.name/-c user.email/-c commit.gpgsign` list, then init, add and commit.
   **Fix:** one `check_live._fixture(d, files)` used by all three self-tests. That saves about
   20 lines, and one place to add `core.hooksPath=/dev/null`, which check_tasks' two copies lack.
3. **Redundancy (low).** check_tasks.py:294 (`"4/3 stalled"`) is the same case as
   check_tasks.py:283 (`"a stalled count past its bound"`): same edit, same expected reason.
   **Fix:** delete line 294.
4. **Running cost (low, measured).** `Aidlc.cfg` and `AidlcLive.cfg` use the same `Spec`, the
   same constants and the same bounds, and both explore the identical **134,464-state** space.
   `Aidlc.cfg` already checks temporal properties. **Fix:** move AidlcLive's four temporal
   properties into `Aidlc.cfg`'s `PROPERTY` line and drop the second run. That saves one
   full exploration per models job (6 s of the 46 s the pair took here) and one `.cfg` file.
5. **Redundancy (low).** HEAD is read with a fresh `git rev-parse HEAD` at check_live.py:539
   (`_check_evidence`) and :765 (`_run`), although `HeadTree.head()` already holds the pinned
   sha for the same invocation. **Fix:** use `tree.head()` there. It saves one git spawn per call
   and keeps "HEAD is read once" true in one place. QA should confirm the recorded sha is meant
   to be the pinned one.
6. **Runtime (low; fold into D13).** `HeadTree.get()` resets with `checkout -f`, then
   `reset --hard` of the same sha, then `clean` (check_live.py:386-388), and calls
   `rev-parse --absolute-git-dir` on every reset (:381). After a forced checkout to the same sha
   with the index already removed, the `reset --hard` adds nothing; the gitdir is constant.
   **Fix:** cache the gitdir in `get()`'s first branch, and drop the `reset` if Security agrees
   it is redundant. That saves two git spawns per probe.

## Already-logged debt, re-checked at b572f8f (unchanged; not re-counted)

D1, D2, D3, D4, D5, D9, D10, D12, D13 and D14 are still accurate at this commit, and still medium
or low. None got worse in the last rounds.

```yaml
verdict: PASS-WITH-DEBT
trigger: "magnitude floor (default): > 1000 changed lines AND > 20 changed files; standards.md budget N/A for a framework change -- framework defaults applied"
diff_size: "main..b572f8f (carries unmerged 0.9.2-0.9.6): 77 files, +10037/-720; 0.9.7 alone (49d78dd..b572f8f): 62 files, +4835/-660 (code/models/CI: 22 files, +2995/-203); evidence, formal and verdicts excluded"
findings:
  - {severity: medium, category: duplication, detail: "check_live._check_evidence repeats check_formal.pattern() inline (expect compile / matches-empty / observed match, check_live.py:573-582 vs check_formal.py:140-155), plus the identical --only unknown-ID filter (check_live.py:534-538 = check_formal.py:185-189) and the evidence JSON load; fix: move pattern(), an only-filter and the load into check_live and call them from both (~25 LOC)", status: "new -- log as Dn"}
  - {severity: low, category: duplication, detail: "self-test git fixture (identity/gpgsign config, init, add, commit) written 4 times: check_live.py:800-814, check_formal.py:330-347, check_tasks.py:345-348 and :384-387; fix: one shared fixture helper in check_live (~20 LOC)", status: "new -- log as Dn"}
  - {severity: low, category: redundancy, detail: "check_tasks.py:294 '4/3 stalled' duplicates check_tasks.py:283 (same edit, same expected reason); fix: delete :294", status: "new -- log as Dn"}
  - {severity: low, category: running-cost, detail: "Aidlc.cfg and AidlcLive.cfg use the same Spec, constants and bounds, so the 134,464-state space is explored twice per models job; fix: move AidlcLive's PROPERTY list into Aidlc.cfg and drop one run (measured 6 s of 46 s for the pair under load; one cfg file)", status: "new -- log as Dn"}
  - {severity: low, category: redundancy, detail: "check_live.py:539 and :765 re-run `git rev-parse HEAD` though HeadTree.head() holds the pinned sha for the invocation; fix: use tree.head()", status: "new -- log as Dn"}
  - {severity: low, category: runtime-efficiency, detail: "HeadTree.get() runs `reset --hard` after `checkout -f` of the same sha and re-reads `rev-parse --absolute-git-dir` on every reset (check_live.py:381-388); fix: cache the gitdir, drop the redundant reset if Security agrees (2 git spawns per probe)", status: "new -- fold into D13"}
  - {severity: medium, category: running-cost, detail: "SKILL.md 57,842 -> 68,418 B (+18.3%), in every role's prompt", status: "debt D1 (unchanged)"}
  - {severity: medium, category: running-cost, detail: "check_tasks --rerun runs identical commands repeatedly", status: "debt D9 (unchanged)"}
  - {severity: medium, category: runtime-efficiency, detail: "per-probe index drop rewrites the whole checkout", status: "debt D13 (unchanged)"}
  - {severity: low, category: running-cost, detail: "models job wall time: re-measured 352 s for the 10 model runs on a machine at load average ~295; CI's own time still unrecorded", status: "debt D2 (unchanged)"}
  - {severity: low, category: duplication, detail: "ElectionV096.tla lifecycle layer; run_cmd beside probe; the demotion rule in three places", status: "debts D3, D4, D5 (unchanged)"}
  - {severity: low, category: runtime-efficiency, detail: "boot.py beat: ~67 ms CPU per beat measured, async, now per tool call (A2) -- negligible; lazy import and write-on-change still open", status: "debt D10 (unchanged)"}
  - {severity: low, category: running-cost, detail: "SIGTERM leaks the registered worktree; non-code symlink targets read", status: "debts D12, D14 (unchanged)"}
blocks_gate: false
```

Every TLC run gave its expected verdict, and the check_tasks and check_formal self-tests
passed at b572f8f (51 and 45 cases). That is context, not something this gate judges.

**Retrospective**
- Worked: re-running the pinned TLC showed that two configs explore the same state space,
  which reading the files alone would have left as a guess.
- Failed: the timings are upper bounds only. The machine's load average was around 295, so
  absolute times say little until CI's own time is recorded.
- Change next time: framework proposals should carry their own *Code quality & efficiency
  budget* (prompt bytes, CI minutes), so N4-style items are judged against signed numbers, not
  defaults.
