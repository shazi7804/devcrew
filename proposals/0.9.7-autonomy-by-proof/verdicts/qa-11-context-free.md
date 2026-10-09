# QA verdict — final 2 (qa role, Claude, at 83603a0)

Judged: the end state of `feat/0.9.7-autonomy-by-proof` at 83603a0 (main..83603a0,
137 files) against `proposals/0.9.7-autonomy-by-proof/requirements.md`
(sha256:7b665be99e78, matching TASKS.md's `Signed:` line; design.md
sha256:7b44072f92d2, matching too), R3's *Threat model* included. Every sensor
ran in a fresh clone; the threat-model probes ran in throwaway toy repositories
driven by the sensors of 83603a0, on APFS (case-insensitive). `verdicts/` was
read only after this pass, as a regression list.

## Requirement table

| Item | Verify | Formal | Evidence / how judged | Verdict |
|---|---|---|---|---|
| R1 | local | none | `contracts/tasks.template.md` has the three sections, line forms, header; SKILL.md ("the run's only ledger") and ARCHITECTURE.md §6 call it the ledger; every "ledger" in framework/hosts/AGENTS resolves to TASKS.md or a host mirror of it | PASS |
| R2 | local | none | self-test: missing / duplicated / unknown ID fail with their reason; Dn in Todo and Cn in Todo/Done pass | PASS |
| R3 | local | none | Acceptance met (self-test: Done without evidence, Done with a status in 13 forms; the re-run green on the proposal). **Threat model fails** (B1, B2) | FAIL |
| R4 | local | none | `check_tasks.py --self-test` 51 cases, every listed reason incl. drifted requirements.md / standards.md and 6/5 | PASS |
| R5 | local | none | three adapters: TASKS.md is the ledger, a host mirror loses; "NOT DEFINED" gone; each installs check_tasks.py and runs its self-test at verify | PASS |
| R6 | local | none | phase table names the batch of every gate; "Former 🔴 gate → Now" table, 11 rows; every 🔴 gate of main's SKILL.md mapped | PASS |
| R7 | local | none | five interrupts, each with its sensor; Cn refused In progress (self-test); orchestrator.md: a judgment is a Cn, the rest waits | PASS |
| R8 | local | none | template *Pre-authorized actions* table (action · condition · environment); Phase 5–6 consult it; `JudgmentRecorded` holds, AidlcJudgmentBroken violates it | PASS |
| R9 | local | none | Property/Formal/Conformance on every example item + definitions; standards.template *Formal verification* (load-bearing, tool per level, bounds) | PASS |
| R10 | local | none | `check_formal.py --self-test` 45 cases, every listed reason and each escape hatch; `--rerun` green on the proposal. Shares the HeadTree re-run checkout of B2 | PASS (B2 noted against R3) |
| R11 | local | none | vacuity block in SKILL.md; self-test: no vacuity run, a vacuity run that passed | PASS |
| R12 | local | checked/none | `check_models.py`: Election, ElectionLive, Aidlc, AidlcLive hold; ElectionV096, ElectionLiveBroken, ElectionOnceBroken, AidlcBroken, AidlcJudgmentBroken fail as expected; every Property name in the cfgs; fairness written in Spec | PASS |
| R13 | local | checked/trace | 5 boot.py traces (scripted, stampede, 3 concurrent seeds) accepted, 3 seeded mutants rejected; `check_repo.py` ok | PASS |
| R14 | local | none | AGENTS.md invariant 11; reviewer.md `invariants_checked: [1..11]` | PASS |
| R15 | local | checked/trace | Election holds; ElectionV096 yields AtMostOneActing; A1–A5 in session-governance.md | PASS |
| N1 | local | none | no bound, gate or trigger loosened; every former gate mapped; removed stops replaced by sensors/Cn per the recorded CEO rulings | PASS |
| N2 | local | none | invariant 10 text byte-identical to 0.9.6's; check_tasks runs both check_live and check_formal for Done | PASS |
| N3 | local | none | check_tasks/check_formal import stdlib + check_live/check_formal only; `check_neutral.py` 0; tla2tools 1.7.4 pinned | PASS |
| N4 | local | none | auditor verdict PASS-WITH-DEBT, no blocker/high (evidence re-run green) | PASS |

```yaml
verdict: FAIL
sensors:
  - "python3 tools/check_neutral.py --self-test -> self-test ok (rc 0)"
  - "python3 tools/check_neutral.py -> neutral: ok (rc 0)"
  - "python3 framework/tools/check_live.py --self-test -> self-test ok (134 cases) (rc 0)"
  - "python3 framework/tools/check_formal.py --self-test -> self-test ok (45 cases) (rc 0)"
  - "python3 framework/tools/check_tasks.py --self-test -> self-test ok (51 cases) (rc 0)"
  - "python3 tools/check_repo.py -> repo: ok (rc 0)"
  - "python3 tools/diagram.py check $(git ls-files '*.md') -> ALIGNED (rc 0)"
  - "python3 tools/check_models.py -> models: ok; 10 model runs as expected, 5 boot.py traces accepted, 3 mutants rejected (rc 0, 4m10s)"
  - "check_tasks.py --tasks proposals/0.9.7-autonomy-by-proof/TASKS.md --allow tools/live-allow.txt -> tasks: ok (rc 0)"
  - "check_tasks.py ... --rerun -> tasks: ok (rc 0, 6m56s)"
  - "check_live.py --requirements <proposal>/requirements.md --allow tools/live-allow.txt -> live: ok (rc 0); --rerun -> live: ok (rc 0)"
  - "check_formal.py --requirements <proposal>/requirements.md -> formal: ok (rc 0); --rerun -> formal: ok (rc 0, 5m08s)"
  - "shasum -a 256 framework/tools/check_live.py = 82508cf949807f44ef3f3ff7c79e460fd80a35ac1aea7b1755aff623ba20487f, the hash the sensor prints"
blockers:
  - requirement: R3
    clause: "Threat model: the sensors SHALL keep accidents out of a re-run: ... a symlink, a name two filesystems spell differently. On a re-run they SHALL never pass what the plain run fails."
    problem: >-
      The fixes for the previous round's collision and out-of-tree-symlink
      blockers report those names only through the code scan, and the code
      scan is narrowed by --src (which SKILL.md tells the Ship batch to pass,
      from standards.md). The probe's checkout is the whole of HEAD, so a
      colliding name or an out-of-tree symlink outside --src is run by the
      probe and never reported: the re-run passes on a case-insensitive
      filesystem what the plain run fails, and passes on a file outside the
      repository.
    repro: >-
      (a) Toy repo: app/main.py; tools/Run.sh "echo broken; exit 1" and
      tools/run.sh "echo ok" committed through the index; evidence R1 local,
      command `sh tools/Run.sh`, expect "ok", at HEAD; TASKS.md `- [x] R1 a`.
      check_tasks --src app -> rc 1 ("stale -- code changed"); check_tasks
      --rerun --src app -> rc 0 "tasks: ok"; check_tasks --rerun (no --src)
      -> rc 1 (both names "collide"). HEAD's tools/Run.sh exits 1.
      (b) Toy repo: committed symlink status.txt -> a file outside the repo
      saying "ready"; evidence `cat status.txt` expect "ready"; R1 Done.
      check_tasks --rerun -> rc 1 ("a symlink that does not resolve");
      check_tasks --rerun --src app -> rc 0 "tasks: ok".
    fix_hint: "report every collision and every unresolvable symlink of HEAD's tree on a re-run, independent of --src (they are facts about the probe's checkout, not the scan)"
  - requirement: R3 (and R10's --rerun, which shares the checkout)
    clause: "Threat model: the sensors SHALL keep accidents out of a re-run: an uncommitted change, an untracked or ignored file, what an earlier probe left behind"
    problem: >-
      HeadTree.get() resets the checkout with checkout -f, reset --hard and
      clean -ffdx, none of which recurse into a submodule. A submodule an
      earlier probe initialised (a common build step) stays populated, with
      whatever untracked files that probe wrote inside it, so a later probe's
      re-run passes only because of what the earlier one left behind.
    repro: >-
      Toy repo with a submodule vendor/lib (not initialised at HEAD). R1
      command `git -c protocol.file.allow=always submodule update -q --init
      && echo built > vendor/lib/out.txt && echo one-ok`; R2 command `cat
      vendor/lib/out.txt` expect "built"; both local, at HEAD, Done.
      check_live --rerun --only R2 -> rc 1 ("No such file or directory");
      check_live --rerun -> rc 0 "live: ok"; check_tasks --rerun -> rc 0
      "tasks: ok" (variant reading vendor/lib/run.sh: same result).
    fix_hint: "on reset, also `git submodule deinit -f --all` / remove populated gitlink dirs (or clean with submodule recursion), plus a self-test case"
debts:
  - "check_live --rerun excuses stale/orphan evidence when a local re-run passes; check_formal --rerun still reports stale. Carried from the last round; state which is meant"
  - "check_formal's run_cmd hands the check the whole environment, while check_live's probe keeps only PATH/HOME/LANG/LC_ALL/TMPDIR/SYSTEMROOT and the variables the command names; the threat model's 'variable the command uses' reading fits only the latter"
  - "check_tasks --self-test still has no case for a [x] with stale live evidence or failing formal evidence (R3 Acceptance is met by the code path and the 'Done without evidence' case)"
notes:
  - "R3 and R10 are honestly In progress in TASKS.md (2/5, stalled 0/3); every other item is Done with evidence at 9131d0a, fresh at 83603a0 (the delta is evidence/formal JSON only, exempt as the run's record)."
  - "Previous round's B1 (records read from the working tree on --rerun) is fixed: evidence and formal records are read from HEAD's blobs. B2/B3 are fixed only when --src is absent (blocker 1)."
  - "Not a blocker, environment-dependent: a probe that names a path in a case only a case-insensitive filesystem resolves (e.g. `sh TOOLS/run.sh` for tools/run.sh) passes a re-run on APFS and fails on Linux; no tree collision exists, so the sensor cannot see it without parsing commands."
  - "Waste is the auditor's lane; nothing noted for it beyond its own D-items."
```

Retrospective: every sensor, self-test and model is green and the earlier
blockers stay fixed on the default invocation; both new gaps sit in the probe's
checkout, where --src and submodules reach what the reset and the reports do
not. Next round: run every threat-model case also with --src set and with a
submodule in the tree.
