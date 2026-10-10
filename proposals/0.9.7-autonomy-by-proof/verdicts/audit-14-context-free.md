# Efficiency audit — final 7 (auditor, at 2c1049f)

**Trigger.** The framework's own tree has no `standards.md` § *Code quality & efficiency
budget*, so I judged against the framework defaults (SKILL.md § *Magnitude floor*) and
invariant 7. That section should be filled in at the next Phase 1 of a framework change.
`git diff --shortstat main..2c1049f`, leaving out proposals' evidence/, formal/ and verdicts/,
reports 79 files changed, +10934 / −740, which is 11674 changed lines (6302 of them Markdown).
Both triggers fire: more than 20 files, and more than 1000 lines even with the docs left out.
The diff also includes 0.9.5 and 0.9.6, which are not merged yet. So `check_live.py` (1920
lines, 892 of them self-test), `boot.py`, `check_neutral.py` and `diagram.py` show up in full.

**The end state, and N4.** This round's delta since 22565c0 is three files, +93 / −47. All of
it is in `check_live.py`, plus CHANGELOG and TASKS. The production code grows by about 20
lines: one `git rev-parse --git-path` call in `unclean()`, one `remote remove` per HeadTree,
one config snapshot and restore per reset, and a per-host `proven` set in place of a boolean.
None of this costs anything measurable next to the per-probe checkout D13 already logs. There
is no new dependency, no new abstraction and no new role. TASKS.md is still one file. The
earlier debts D1–D29 stand as logged, and nothing in this round makes any of them worse. The
self-tests pass: check_live 159 cases, check_tasks 59, check_formal 66, and check_neutral is ok.
The check_live self-test takes about 8 minutes of wall time at about 18% CPU on this machine.
That is the same per-probe reset cost as D13, not a new finding. **N4 holds: no blocker, no
high.**

**Vacuity of the cases added or changed since 22565c0 (mutation-tested in a clone).** For each
rule, I deleted or reverted it and re-ran the self-test:

| Rule removed | Case that should fail | Result |
|---|---|---|
| refusing the repository's own `.git/info/attributes` in `unclean()` | "a re-run beside the repository's own info/attributes" | fails, so the case is real |
| `remote remove origin` on the clone | "a probe that pops a stash or makes a branch" (now with a push) | fails, so the case is real |
| restoring the clone's config before each reset | "git config an earlier probe set in its clone" | fails, so the case is real |
| per-host `proven` (any host proves all; also the old all-or-nothing form) | "a service no version probe asked, on a re-run" | fails, so the case is real |
| HEAD's blobs read once, before any probe (`files()` re-reads every time) | "a --deployed probe that rewrites HEAD's object" | fails, so the case is real |
| same | "a --deployed probe that rewrites HEAD's tree object" | **still passes**: it accepts any hit containing `cannot`. At baseline it gets "cannot reset the checkout of HEAD". With the rule removed it gets "cannot read HEAD's tree". It never reaches the scan, so it proves nothing about the rule it names. |
| dropping the clone's `info/attributes` in the reset | none | **no case fails**: the line is a rule that nothing tests |

The removed case (the `--absolute-git-dir` shim) really was vacuous; dropping it is correct.
The guard it aimed at (`check_live.py`, the "cannot name the git dir" exit) is defensive code
that is now untested. It costs 4 lines, so I am not filing it.

```yaml
verdict: PASS-WITH-DEBT
trigger: "framework defaults (no standards.md budget section): changed files 79 > 20 and changed lines 11674 > 1000"
diff_size: "79 files, +10934 / -740 (main..2c1049f, excluding proposals' evidence/formal/verdicts); this round since 22565c0: 3 files, +93 / -47"
findings:
  - severity: medium
    category: redundancy
    detail: "check_live.py self-test 'a --deployed probe that rewrites HEAD's tree object' is still vacuous. It accepts ('src/app.js:1', 'cannot'). At 2c1049f it passes on 'cannot reset the checkout of HEAD'. With the read-once rule removed (files() re-reading every time) it passes on 'cannot read HEAD's tree'. The rewritten tree object breaks the borrowed object store before the scan runs. This is the residue of audit 13's medium, which 79d1994 reports as fixed. Fix: R3 puts rewriting git's objects out of scope, so delete the case and retree.py (about 25 LOC, one re-run per self-test). Or have retree.py restore the .bak before it exits and require 'src/app.js:1' alone."
    status: "new — log as Dn"
  - severity: low
    category: redundancy
    detail: "HeadTree reset drops the clone's info/attributes (check_live.py, the reset's drop list). With that name removed from the list, all 159 cases still pass, so the rule has no test, although 79d1994's message says 'Mutation checked'. Fix: add one case in which a probe writes .git/info/attributes with a smudge filter in its clone and the next probe's checkout must not use it. Copy the 'git config an earlier probe set' case, about 12 LOC. Or merge the two into one case."
    status: "new — log as Dn"
blocks_gate: false
```

**Retrospective.** *Worked:* mutating each rule added this round showed four of five cases are
real in a few runs. *Failed:* a tuple-of-alternatives `want` (`"cannot"`) let a case pass on
an unrelated refusal, and a "mutation checked" claim covered fewer lines than the commit
changed. *Change next time:* forbid catch-all alternatives in self-test expectations, and
mutate every new line of a fix, not just the line under its headline.
