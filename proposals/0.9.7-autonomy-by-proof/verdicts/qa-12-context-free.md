# QA verdict — final 3 (qa role, Claude, at ba572c4)

Judged: the end state of `feat/0.9.7-autonomy-by-proof` at ba572c4 (main..ba572c4,
139 files; 0.9.6 is an ancestor) against `proposals/0.9.7-autonomy-by-proof/requirements.md`
(sha256:7b665be99e78, which matches TASKS.md's `Signed:` line; design.md sha256:7b44072f92d2
matches as well), R3's *Threat model* included. Every sensor ran in a fresh clone. The
threat-model probes ran in throwaway toy repositories, driven by ba572c4's sensors copied
outside the toy tree, on APFS (case-insensitive). I read `verdicts/` only after this pass,
and only as a regression list.

## Requirement table

| Item | Verify | Formal | Evidence / how judged | Verdict |
|---|---|---|---|---|
| R1 | local | none | `contracts/tasks.template.md` has the three sections, line forms and two-line header. SKILL.md ("the run's only ledger") and ARCHITECTURE.md §6 call it the ledger. Every "ledger" in framework/, hosts/ and AGENTS.md resolves to TASKS.md or a host mirror of it | PASS |
| R2 | local | none | the self-test fails on missing, duplicated and unknown IDs, and passes Dn (Todo) and Cn (Todo/Done) | PASS |
| R3 | local | none | Acceptance holds. The self-test case "Done without evidence" covers it, and a toy run shows `[x]` with no formal evidence -> "Done but not formal". The *Threat model* does not hold: a re-run reads the contract from the working tree (B1) | FAIL (B1) |
| R4 | local | none | `check_tasks.py --self-test` passes 51 cases, each listed reason included (drifted requirements.md/standards.md, 6/5). It passes a clean file | PASS |
| R5 | local | none | the three adapters use TASKS.md and state "TASKS.md wins" over any mirror. The "NOT DEFINED" line is gone. Each adapter installs check_tasks.py and self-tests it | PASS |
| R6 | local | none | the phase table names a batch for each gate. The "Former 🔴 gate -> Now" table has 11 rows and covers every 🔴 on main (P0, platform, P0.5, P2, P6 ×2, ∞ ×2, architect escalation) plus 0.9.6's P1 standards | PASS |
| R7 | local | none | SKILL.md lists the five interrupts, each with the sensor that raises it. check_tasks refuses a Cn in progress (self-test). orchestrator.md: a judgment becomes a Cn, everything else waits for the next batch | PASS |
| R8 | local | none | the template has a Pre-authorized actions table. Phases 5–6 consult it. JudgmentRecorded holds, and AidlcJudgmentBroken violates it | PASS |
| R9 | local | none | every example item in the template carries Property/Formal/Conformance, and the definitions are present. standards.template.md has a § Formal verification | PASS |
| R10 | local | none | `check_formal.py --self-test` passes 45 cases with every listed reason and hatch. `--rerun` is green on the proposal. It shares B1 (the property text is read from the working tree's requirements on a re-run) | FAIL (via B1) |
| R11 | local | none | SKILL.md's evidence schema has the vacuity block. The self-test fails a missing vacuity run and one that passed | PASS |
| R12 | local | checked/none | `tools/check_models.py`: Election (3 sessions), ElectionLive (2), Aidlc and AidlcLive all hold. Every R12 property name is in a cfg. The ElectionV096, LiveBroken, OnceBroken, AidlcBroken, JudgmentBroken and AidlcLiveBroken variants each yield the expected counterexample. TLC 1.7.4 is pinned by sha256 (it matches) | PASS |
| R13 | local | checked/trace | boot.py traces are accepted: scripted, stampede and three seeded concurrent runs. The three mutants are rejected. check_repo.py fails when SKILL.md's interrupts or batches differ from Aidlc.tla (mutated and checked) | PASS |
| R14 | local | none | AGENTS.md has invariant 11; reviewer.md has `invariants_checked: [1..11]` | PASS |
| R15 | local | checked/trace | the shipped model holds and the 0.9.6 model fails AtMostOneActing. session-governance.md states A1–A5, matching Election.tla's header. TakeOnBeat is a switch for the broken variant, not an assumption | PASS |
| N1 | local | none | the mapping table is complete. The removed judgment stops became Cn records under the CEO's recorded second ruling | PASS |
| N2 | local | none | invariant 10's text is identical to 0.9.6's. check_tasks requires both check_live and check_formal for Done | PASS |
| N3 | local | none | the sensors import only the standard library. check_neutral exits 0 and CI pins TLC | PASS |
| N4 | local | none | evidence: the audit verdict is PASS-WITH-DEBT with no blocker/high (the evidence probe re-ran green) | PASS |

```yaml
verdict: FAIL
sensors:
  - "python3 tools/check_neutral.py --self-test -> self-test ok (rc 0)"
  - "python3 tools/check_neutral.py -> neutral: ok (rc 0)"
  - "python3 framework/tools/check_live.py --self-test -> self-test ok (138 cases) (rc 0)"
  - "python3 framework/tools/check_formal.py --self-test -> self-test ok (45 cases) (rc 0)"
  - "python3 framework/tools/check_tasks.py --self-test -> self-test ok (51 cases) (rc 0)"
  - "python3 tools/check_repo.py -> repo: ok (rc 0)"
  - "python3 tools/diagram.py check $(git ls-files '*.md') -> rc 0"
  - "python3 tools/check_models.py (TLC 1.7.4, sha256 936a2620...) -> models: ok (rc 0, 3m16s): 10 model runs as expected, 5 traces accepted, 3 mutants rejected"
  - "check_tasks.py --tasks <proposal>/TASKS.md --allow tools/live-allow.txt -> tasks: ok (rc 0); --rerun -> tasks: ok (rc 0, 6m00s)"
  - "check_live.py --requirements <proposal>/requirements.md --allow tools/live-allow.txt -> live: ok; --rerun -> live: ok (rc 0; re-runs every Acceptance command recorded in evidence/)"
  - "check_formal.py --requirements <proposal>/requirements.md -> formal: ok; --rerun -> formal: ok (rc 0)"
  - "shasum -a 256 requirements.md / design.md -> 7b665be99e78 / 7b44072f92d2 = TASKS.md Signed:"
blockers:
  - requirement: R3 (and R10's --rerun, which reads the same file)
    clause: "Threat model: the sensors SHALL keep accidents out of a re-run: an uncommitted change"
    problem: >-
      A re-run reads the evidence and formal records, the allow file and the
      code from HEAD, but it reads the requirements file (which items exist,
      each Verify level, each signed Property, Formal and Conformance) from the
      working tree. An uncommitted edit to requirements.md therefore decides what
      a re-run judges HEAD against. At a clean HEAD the re-run fails; with the
      uncommitted edit it passes. check_live --rerun and check_formal --rerun
      have no guard. check_tasks --rerun is guarded by the Signed: hash only
      while TASKS.md is itself committed. An uncommitted re-sign, which is how
      the orchestrator writes Signed: at a batch, also takes part.
      Final 1's B1 fixed this for the records but not for the contract they are
      judged against.
    repro: >-
      Toy repo: R1 `Verify: live` committed, evidence R1.json local
      (target "this checkout", `grep -c export src/app.js`), committed.
      `check_live.py --requirements req/requirements.md --rerun` -> rc 1
      ("requires live, evidence is 'local'"). Edit requirements.md to
      `Verify: local` without committing (git status: M req/requirements.md):
      the same command -> rc 0 "live: ok". Also write the new Signed: line into
      TASKS.md, uncommitted: `check_tasks.py --tasks req/TASKS.md --rerun` -> rc 0
      "tasks: ok". At the clean HEAD it is rc 1. Same for check_formal: the
      property text is compared with the working tree's Property line.
    fix_hint: "on --rerun read the requirements file (and the TASKS.md whose Signed: line vouches for it) from HEAD's blobs, as the records are, or refuse when either differs from HEAD; plus a self-test case for each sensor"
debts:
  - "check_tasks --self-test still has no case for a [x] with stale live evidence or failing formal evidence. The code path works (a toy run shows 'Done but not formal'), but R4's 'a [x] without fresh evidence' is sampled only by the no-evidence case"
  - "check_tasks --rerun reads TASKS.md from the working tree, so an uncommitted move of a Done item back to Todo removes it from the re-run. This is weaker than B1: a ledger that says 'not done' is true. It is listed here because it is the same read path"
  - "canon() turns an absolute source path ('/x/y.lean') into a repo-relative one ('x/y.lean') on a re-run, while the plain run reads the absolute file. In practice the re-run is stricter (source not found). It is not an accident case, but say which is meant"
  - "the evidence dir reached through a committed directory symlink reads as 'no evidence' on a re-run but passes the plain run. That is fail-closed, so it is a false FAIL, not a false PASS"
notes:
  - "R3 and R10 are honestly In progress in TASKS.md (4/5, stalled 0/3). Fixing B1 is the fifth attempt. If it does not land, the next state is 5/5, which raises the loop-bound interrupt"
  - "Regressions from final 2 are fixed and re-tested here. A submodule initialised by an earlier probe no longer survives into a later one (R2 fails as it should). An out-of-tree symlink is reported under --src app"
  - "Accident probes that held on a re-run, each as a two-probe toy (R1 leaves it, R2 passes only if it is still there), and R2 failed every time: an untracked file, chmod 000 on a tracked file, a tracked file replaced by a symlink, the checkout's .git replaced by `git init`, an ignored dir, a staged edit, assume-unchanged plus an edit, sparse-checkout, an orphan branch with `git rm`. A read-only directory fails closed ('cannot reset the checkout')"
  - "The second threat-model sentence ('never pass what the plain run fails') cannot be literal next to the first: an uncommitted mock in src fails the plain scan and passes the HEAD re-run, and a stale local item passes when its re-run is fresh. I read it as 'for what HEAD holds', and on a clean HEAD I found no case where the re-run is weaker"
  - "Waste is the auditor's lane; nothing to add beyond its D-items"
```

Retrospective: the probe checkout is now robust against every leftover I could make by accident. The remaining hole sits one level up, in the contract the re-run judges against. Next round: give every input of a re-run (records, contract, ledger) one rule, "read from HEAD".
