# Efficiency audit — final 8 (auditor, at 13c8936)

**Trigger.** The project has no `standards.md` § *Code quality & efficiency budget*
(this is a framework change), so the framework's default magnitude floor applies.
`git diff --shortstat main..13c8936`, leaving out proposals' evidence/formal/verdicts:
**79 files, +11024 / -740**. That trips both triggers (more than 20 files, more than 1000 lines).
`main` is still at 0.9.1, so this range also carries 0.9.2 to 0.9.6. The 0.9.7 part alone
(6e0c443..13c8936) is 68 files, +5876 / -734. This round (2c1049f..13c8936) is 4 files, +133 / -43.
Recommendation, repeated: fill in the budget section at the next Phase 1.

**What this round spends.** check_live.py goes from 1920 to 1960 lines, check_tasks.py from
527 to 575, and CHANGELOG and TASKS.md change a few lines. The production code change is about 25 lines:
- a filtered file is scanned raw and filtered (`scan_lines` is pulled out of `check_code`, a
  straight extraction with no new concept);
- the clone's config is unlinked before it is rewritten;
- a ticked `Cn` is checked for a status;
- `LEAD` takes `;`, `→`, `=` and `~`;
- `check_tasks` passes `frozenset()` for `proven` where it passed `False`. That was a real crash
  on a live Done item under `--rerun`.

One self-test case and its helper script go: the retree case, about 25 lines. That closes
audit 14's medium. The rest is new self-test cases. The run-time cost is three more
temp-repo cases in check_live (its self-test takes 5 m 16 s on this machine) and two in
check_tasks (27 s). Each case pins a fix a reviewer asked for, so this is not waste.

**N4 (small on purpose, invariant 7).** The end state has one ledger file (TASKS.md) and no new role.
This round adds no new dependency or module, and no layer with a single caller. The sensors are still
stdlib-only. Production code in check_live.py has grown from 482 to about 1042 lines in 0.9.7. Each
increment traces to a Security finding under the CEO-signed threat model (R3, 2026-10-09), and
D13/D14/D15/D24/D28/D29 already log the parts that can be trimmed. That is debt, not a
blocker. No finding is blocker or high, so N4's acceptance holds.

**Vacuity check: every self-test case added since 2c1049f, with the rule it names removed.**
Each was run in its own clone:

| Case (file) | Rule removed | Result |
|---|---|---|
| a ticked decision that still carries a status (check_tasks) | the `Cn` Done `DONE_STATUS` check | FAILS: got clean |
| a Done line with a status after a semicolon (check_tasks) | `;` in `LEAD` | FAILS |
| a Done line with a status after an arrow (check_tasks) | `→` in `LEAD` | FAILS |
| a live Done item: --rerun judges it, does not crash (check_tasks) | `frozenset()` back to `False` | FAILS: TypeError |
| a Done item without formal evidence (check_tasks) | the `Done but not formal` line | FAILS: got clean |
| a filter defined after checkout, plain / on a re-run (check_live) | raw+filtered tuple, back to filtered only | FAILS on the re-run |
| a clone config a probe replaced with a symlink (check_live) | unlink before `write_bytes` | FAILS: wrote through the link |
| an attributes file an earlier probe left in its clone (check_live) | `info/attributes` in the reset's drop list | FAILS: converted bytes |

None is vacuous. Audit 14's low (the info/attributes drop had no test) is closed by the last row.
The "plain" half of the filter case passes with or without the rule, because the plain run
reads the checkout on disk. Its re-run half is the half that bites, and that is enough.

**Findings (all debt).**
1. *Over-abstraction, low.* HeadTree's blob map now holds three types: `str` for a refusal,
   `bytes` for content, and `(raw, filtered)` for a filtered file. Two places have to unwrap
   the tuple (`blob()` and `check_code`). `blob()` silently keeps only the raw half, which
   changes what it returned before this round (the filtered read). Fix: keep filtered reads
   in their own `self.filtered` dict. `check_code` scans `blobs[rel]` plus `filtered.get(rel)`,
   and `blob()` goes back to one `isinstance`. That is about 4 lines fewer and one type fewer.
   *ESCALATE (Security, not judged here):* on a re-run, evidence JSON and formal sources read through `blob()`
   now see the raw blob, while the plain run reads the smudged file on disk. Security should confirm
   that this never passes what the plain run fails (R3).
2. *Redundancy, low.* `LEAD` gained `=` and `~`, but no case pins them. With both removed, all
   64 check_tasks cases still pass. Fix: add one case each, about 4 lines (`- [x] N1 login = fixing`,
   `~ fixing`), or drop the two characters.
3. *Duplication, low.* The new check_tasks case is the fourth inline copy of the git fixture
   (`q = [...]` plus init/add/commit). Fix: one `repo(d)` / `commit(d)` helper in the self-test,
   about 12 lines fewer. This is already logged as D16. Its count should now read 4 in check_tasks alone.

Audit 14's medium (the vacuous retree case) and low (info/attributes untested) are both
resolved at 13c8936.

```yaml
verdict: PASS-WITH-DEBT
trigger: "framework defaults (no standards.md budget section): changed files 79 > 20 and changed lines 11764 > 1000"
diff_size: "79 files, +11024 / -740 (main..13c8936, excluding proposals' evidence/formal/verdicts); 0.9.7 only (6e0c443..13c8936): 68 files, +5876 / -734; this round (2c1049f..13c8936): 4 files, +133 / -43"
findings:
  - severity: low
    category: over-abstraction
    detail: "HeadTree blob values are str | bytes | (raw, filtered); blob() and check_code each unwrap the tuple, and blob() now keeps only the raw half (it returned the filtered read before). Fix: a separate self.filtered dict scanned beside blobs[rel] in check_code; blob() unchanged (~-4 LOC, one type fewer). ESCALATE to Security: re-run reads of evidence/formal sources via blob() now see raw while the plain run reads smudged disk."
    status: "new — log as Dn"
  - severity: low
    category: redundancy
    detail: "check_tasks LEAD gained '=' and '~' with no case pinning them: removing both leaves all 64 self-test cases passing. Fix: one case each (~4 LOC) or drop the two characters."
    status: "new — log as Dn"
  - severity: low
    category: duplication
    detail: "the new check_tasks live-Done case adds a fourth inline git fixture copy (q list + init/add/commit) in check_tasks' self-test. Fix: one commit(d) helper (~-12 LOC)."
    status: "logged — D16 (count grows)"
blocks_gate: false
```

Retrospective
- Worked: removing each rule in its own clone, with the check_live runs in parallel, gave a
  vacuity verdict on all 8 new cases in one pass of about 5 minutes.
- Failed: the size floor fires on the whole main..HEAD range (main at 0.9.1), so the measured diff
  hides how small this round is. Both have to be stated by hand.
- Change next time: rebase the proposal branch onto a merged 0.9.6 so that main..HEAD is the
  change under audit.
