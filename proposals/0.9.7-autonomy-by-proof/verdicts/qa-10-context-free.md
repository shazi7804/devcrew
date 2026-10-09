# QA verdict — final (qa role, Claude, at d74ff6a)

Judged: the end state of `feat/0.9.7-autonomy-by-proof` at d74ff6a (main..d74ff6a)
against `proposals/0.9.7-autonomy-by-proof/requirements.md` (signed
sha256:040a58119cd0, R3's *Threat model* included). Run in a fresh clone; the
threat-model probes ran in throwaway toy repositories driven by the sensors of
d74ff6a. `verdicts/` was read only after this pass, as a regression list.

## Requirement table

| Item | Verify | Formal | Evidence / how judged | Verdict |
|---|---|---|---|---|
| R1 | local | none | `contracts/tasks.template.md`; SKILL.md, ARCHITECTURE.md §6 and every adapter call TASKS.md the ledger; no other ledger left | PASS |
| R2 | local | none | self-test cases: missing / duplicated / unknown ID, Dn, Cn | PASS |
| R3 | local | none | Acceptance met (formal break and stale code each fail a `[x]`, by hand; `[x]` with a status fails). **Threat model fails** (B1-B3) | FAIL |
| R4 | local | none | `check_tasks.py --self-test` 51 cases, every listed reason; drift of requirements/standards; 6/5 | PASS |
| R5 | local | none | three adapters: TASKS.md wins, install + self-test at verify; "NOT DEFINED" gone | PASS |
| R6 | local | none | batch table + old-gate map; every 🔴 gate in main's SKILL.md mapped | PASS |
| R7 | local | none | five interrupts with sensors; Cn refused in progress; orchestrator.md Cn rule | PASS |
| R8 | local | none | template table; Phase 5 IN + rule; `AidlcJudgmentBroken` yields `JudgmentRecorded` | PASS |
| R9 | local | none | Property/Formal/Conformance on every example item; standards *Formal verification* | PASS |
| R10 | local | none | `check_formal.py --self-test` 45 cases; `--rerun` green on the proposal; re-run reads uncommitted evidence (B1) | FAIL (via B1) |
| R11 | local | none | vacuity block in SKILL.md schema; self-test cases | PASS |
| R12 | local | checked/none | `check_models.py`: all models hold, 3 broken variants fail | PASS |
| R13 | local | checked/trace | 5 traces accepted, 3 mutants rejected; `check_repo.py` fails on a set difference (tried) | PASS |
| R14 | local | none | AGENTS.md invariant 11; reviewer.md `[1..11]` | PASS |
| R15 | local | checked/trace | Election holds; ElectionV096 yields AtMostOneActing; A1-A5 in session-governance.md | PASS |
| N1 | local | none | no bound or gate loosened; mapping complete | PASS |
| N2 | local | none | invariant 10 text identical to 0.9.6's; check_tasks requires both sensors | PASS |
| N3 | local | none | stdlib imports only; `check_neutral.py` 0; tla2tools 1.7.4 pinned by sha256 | PASS |
| N4 | local | none | auditor round 7: PASS-WITH-DEBT, no blocker/high | PASS |

```yaml
verdict: FAIL
sensors:
  - "python3 tools/check_neutral.py --self-test -> self-test ok (rc 0)"
  - "python3 tools/check_neutral.py -> neutral: ok (rc 0)"
  - "python3 framework/tools/check_live.py --self-test -> self-test ok (126 cases) (rc 0)"
  - "python3 framework/tools/check_formal.py --self-test -> self-test ok (45 cases) (rc 0)"
  - "python3 framework/tools/check_tasks.py --self-test -> self-test ok (51 cases) (rc 0)"
  - "python3 tools/check_repo.py -> repo: ok (rc 0)"
  - "python3 tools/diagram.py check $(git ls-files '*.md') -> ALIGNED (rc 0)"
  - "python3 tools/check_models.py -> models: ok; 9 model runs as expected, 5 boot.py traces accepted, 3 mutants rejected (rc 0, 3m22s)"
  - "check_tasks.py --tasks proposals/0.9.7-autonomy-by-proof/TASKS.md --allow tools/live-allow.txt -> tasks: ok (rc 0)"
  - "check_tasks.py ... --rerun -> tasks: ok (rc 0, 5m57s)"
  - "check_live.py --requirements <proposal>/requirements.md --allow tools/live-allow.txt -> live: ok (rc 0)"
  - "check_formal.py --requirements <proposal>/requirements.md -> formal: ok (rc 0); --rerun -> formal: ok (rc 0, 7m00s)"
blockers:
  - requirement: R3 (and R10's --rerun)
    clause: "Threat model: the sensors SHALL keep accidents out of a re-run: an uncommitted change"
    problem: >-
      A re-run takes the probe's command and expect from the working tree's
      evidence/<ID>.json and formal/<ID>.json, never from HEAD. An uncommitted
      edit to a record decides what the re-run executes, and it is not in any
      diff a reviewer reads (the trust the threat model rests on). At a clean
      HEAD the re-run fails; with the uncommitted edit it passes.
    repro: >-
      Toy repo, R1 local, committed probe.sh exits 1, committed evidence
      command `sh probe.sh`: check_live --rerun rc 1 ("re-run exited 1").
      Edit evidence/R1.json's command to `echo ready` without committing:
      check_live --rerun rc 0 "live: ok", check_tasks --rerun rc 0 "tasks: ok".
      Same for formal: committed checker exits 1 -> check_formal --rerun rc 1;
      uncommitted formal/R1.json command `python3 checker.py spec.tla; echo No
      error has been found` -> rc 0 "formal: ok".
  - requirement: R3
    clause: "Threat model: ... a name two filesystems spell differently. On a re-run they SHALL never pass what the plain run fails."
    problem: >-
      HeadTree detects case/normalisation collisions over the whole tree but
      reports them only for names the scan reads (code, want, symlinks). A
      colliding data file the probe reads is checked out as whichever spelling
      the filesystem keeps, so the re-run passes on a case-insensitive
      filesystem what the plain run fails, and what the same re-run fails on a
      case-sensitive one.
    repro: >-
      Toy repo: commit data/Value.txt "alpha" and (through the index)
      data/value.txt "beta"; evidence `cat data/Value.txt` expect "beta" at
      HEAD; TASKS.md R1 Done. On APFS: check_tasks rc 1 ("stale -- code
      changed"), check_tasks --rerun rc 0 "tasks: ok"; check_live likewise
      (rc 1 plain, rc 0 --rerun). HEAD's data/Value.txt is "alpha".
  - requirement: R3
    clause: "Threat model: the sensors SHALL keep accidents out of a re-run: ... a symlink"
    problem: >-
      A committed symlink with a non-code name that leaves the tree (absolute
      target) is followed by the re-run's probe and never reported; the
      verdict then depends on a file outside the repository. The same symlink
      under a code name is reported, so the detection exists and is not applied.
    repro: >-
      Toy repo: `ln -s <a dir outside the repo>/status.txt status.txt`, committed;
      evidence `cat status.txt` expect "ready"; R1 Done. check_tasks --rerun
      rc 0 "tasks: ok" while <a dir outside the repo>/status.txt says ready, rc 1 when it
      says gone; HEAD unchanged, no hit names the symlink.
debts:
  - "check_tasks --self-test has no case for a [x] with STALE live evidence or failing FORMAL evidence (R3/R4 Acceptance); both behave correctly by hand (a committed code change -> 'stale', a committed vacuity result 'pass' -> 'Done but not formal')"
  - "--rerun excuses stale/orphan evidence in check_live when the re-run passes, but not in check_formal (still 'stale'); state which is meant"
  - "R8: Phase 6's block does not cite the pre-authorized list itself (Phase 5's does; Phase 6's irreversible steps are in the ship batch)"
  - "R11: SKILL.md's schema names the vacuity run but not its fields (command, observed, result: fail) -- they are only in check_formal's docstring"
notes:
  - "R3 and R10 are honestly In progress in TASKS.md; every other item is Done with evidence at 7483bbd, fresh at d74ff6a (the delta is evidence only)."
  - "QA round 9's three blockers re-checked: read-tree before probes, `..` not collapsed (canon -> None), prefix case collision now reported (TESTS -> e beside tests/x.sh: rc 1 on --rerun)."
  - "Leftovers from an earlier probe (untracked, ignored, nested .git, a tracked dir replaced by a symlink) are gone before the next probe: confirmed."
  - "TASKS.md header signs design.md (no standards.md on a framework change); the template's 'each signed contract' allows it."
  - "B1-B3 share one fix point (HeadTree / the record read): read the records from HEAD's blobs on --rerun, and report every collision and every out-of-tree symlink of HEAD's tree, not only those the scan reads."
```

Retrospective: the sensors and models are green and the earlier blockers stay
fixed; the remaining gaps are all where a re-run reads something HEAD does not
pin. Next round: QA should probe each threat-model accident from the probe's
side as well as the scan's.
