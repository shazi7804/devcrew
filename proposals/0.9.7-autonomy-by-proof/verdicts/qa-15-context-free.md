# QA verdict — final 6 (qa role, Claude, at f65222c)

What I judged: the end state of `feat/0.9.7-autonomy-by-proof` at f65222c (main..f65222c),
against `proposals/0.9.7-autonomy-by-proof/requirements.md`. I checked every R and N
item, including R3's *Threat model*. I ran everything in a fresh clone of the repo,
with JAVA = openjdk 21 and TLA2TOOLS_JAR = tla2tools 1.7.4. I read `verdicts/` only
after my own pass was done, and then only as a regression list.

```yaml
verdict: PASS
scope: feature (framework)
sensors:
  lint: n/a
  typecheck: n/a
  test: pass    # every step of checks.yml, run locally
  build: n/a
  live: pass    # check_live --rerun over the whole requirements file -> live: ok
  formal: pass  # check_formal --rerun over the whole requirements file -> formal: ok
  tasks: pass   # check_tasks --rerun -> tasks: ok (8 min 40 s)
  models: pass  # check_models.py -> models: ok (3 min 52 s)
  hashes: "shasum -a 256, all 64 hex: check_live.py ff4873ef71325c86b84b14079e6a1fdcea07a7bb4c648856f9417bc769ce7dab (the same as its printed line); check_formal.py ff0c02f32890c8341aee62f15373d1196ba0b45127919f6814c4ebff4e1cf9e0; check_tasks.py fdbf28ca9173bbbb5e93e890b9ae6cece140cec57f43b8ed63178e3c7f5ee5e4. The framework copy is the only copy here."
  commands:
    - "python3 tools/check_neutral.py --self-test -> self-test ok (rc 0)"
    - "python3 tools/check_neutral.py -> neutral: ok (rc 0)"
    - "python3 framework/tools/check_live.py --self-test -> self-test ok (149 cases) (rc 0)"
    - "python3 framework/tools/check_formal.py --self-test -> self-test ok (46 cases) (rc 0)"
    - "python3 framework/tools/check_tasks.py --self-test -> self-test ok (54 cases) (rc 0)"
    - "python3 tools/check_repo.py -> repo: ok (rc 0)"
    - "python3 tools/diagram.py check $(git ls-files '*.md') -> ALIGNED (rc 0)"
    - "python3 tools/check_models.py -> models: ok. Election, ElectionLive, Aidlc and AidlcLive hold. ElectionV096, ElectionLiveBroken, ElectionOnceBroken, AidlcBroken, AidlcJudgmentBroken and AidlcLiveBroken fail as expected. 5 boot.py traces are accepted and 3 mutants are rejected (rc 0)"
    - "python3 framework/tools/check_tasks.py --tasks proposals/0.9.7-autonomy-by-proof/TASKS.md --allow tools/live-allow.txt -> tasks: ok"
    - "python3 framework/tools/check_tasks.py --tasks proposals/0.9.7-autonomy-by-proof/TASKS.md --rerun --allow tools/live-allow.txt -> tasks: ok (rc 0)"
    - "python3 framework/tools/check_live.py --requirements proposals/0.9.7-autonomy-by-proof/requirements.md --allow tools/live-allow.txt -> live: ok"
    - "python3 framework/tools/check_live.py --requirements proposals/0.9.7-autonomy-by-proof/requirements.md --rerun --allow tools/live-allow.txt -> live: ok. Every item's acceptance command is re-executed in HEAD's checkout, R3 and R10 included"
    - "python3 framework/tools/check_formal.py --requirements proposals/0.9.7-autonomy-by-proof/requirements.md --rerun -> formal: ok. R12, R13 and R15 are re-run: each check, its vacuity run and its conformance check"
    - "tools/check_repo.py with one interrupt dropped from SKILL.md's set, and again with one added to Aidlc.tla's set -> rc 1 both times. The R13 negative test"
    - "the working tree stayed clean after all of the above (only an ignored __pycache__ remained, written by my own import)"
requirements:
  - {id: R1, verdict: PASS, verify: local, formal: none, evidence: "evidence/R1.json re-run; tasks.template.md has the three sections, the header and the line forms; SKILL.md and ARCHITECTURE.md §6 call it the only ledger; every 'ledger' mention in framework/, hosts/, AGENTS.md and docs resolves to TASKS.md or to a mirror of it", traces_to: [6ce380f, 60c3283]}
  - {id: R2, verdict: PASS, verify: local, formal: none, evidence: "evidence/R2.json; the self-test has the missing, duplicated and unknown ID cases, and passes Dn in Todo and Cn in Todo and Done", traces_to: [main..f65222c]}
  - {id: R3, verdict: PASS, verify: local, formal: none, evidence: "evidence/R3.json re-run. My own toy: a [x] whose formal evidence is missing fails check_tasks plain and --rerun ('Done but not formal'); a [x] whose live result is fail fails it; the self-test covers a [x] carrying a status. Threat model: the QA-14 TMPDIR repro now fails as it should ('No such file' in a fresh per-probe scratch dir); every listed accident is refused or does not take part (see notes)", traces_to: [ff1d41a, cfee3f4, f50e477]}
  - {id: R4, verdict: PASS, verify: local, formal: none, evidence: "self-test 54 cases, each asserting its reason: a missing section, out of order, a bad status, blocked with no reason, missing/duplicated/unknown ID, Done without evidence, Done with a status, requirements.md and standards.md drift, 6/5; a clean file is clean", traces_to: [main..f65222c]}
  - {id: R5, verdict: PASS, verify: local, formal: none, evidence: "all three adapters name TASKS.md as the ledger; kirocrew and mission-control say a mirror MAY exist and TASKS.md wins; no 'NOT DEFINED' remains in claude-code.md; each adapter installs check_tasks.py and runs its self-test at verify", traces_to: [main..f65222c]}
  - {id: R6, verdict: PASS, verify: local, formal: none, evidence: "the phase table names a batch per former gate; the 'Former 🔴 gate' table maps every 🔴 gate in main's SKILL.md (P0, platform, P0.5, P1 standards, P2, P6 signing, P6 submission, ∞ proposal, ∞ merge, architecture escalation, high-risk actions); none is unmapped", traces_to: [main..f65222c]}
  - {id: R7, verdict: PASS, verify: local, formal: none, evidence: "SKILL.md lists exactly 5 interrupts, each with the sensor that raises it; check_tasks refuses a Cn in progress (self-test); orchestrator.md says a judgment is decided and recorded as a Cn, and anything else waits for the next batch", traces_to: [main..f65222c]}
  - {id: R8, verdict: PASS, verify: local, formal: none, evidence: "requirements.template.md has the Pre-authorized actions table (action · condition · environment, plus blast radius); Phase 5 consults it; JudgmentRecorded holds in Aidlc.cfg and AidlcJudgmentBroken violates it", traces_to: [main..f65222c]}
  - {id: R9, verdict: PASS, verify: local, formal: none, evidence: "every example item in requirements.template.md has Property, Formal and Conformance (checked via fields()), plus the definitions and the load-bearing rule; standards.template.md § Formal verification names the load-bearing components, the tool per level and the bounds", traces_to: [main..f65222c]}
  - {id: R10, verdict: PASS, verify: local, formal: none, evidence: "self-test 46 cases: every reason in the Acceptance plus the 14 escape hatches; --rerun re-executes the check, the vacuity run and the conformance check (seen on R12, R13 and R15); the QA-14 B2 path through run_cmd is closed", traces_to: [ff1d41a, cfee3f4]}
  - {id: R11, verdict: PASS, verify: local, formal: none, evidence: "SKILL.md's evidence sketch has the 'vacuity:' entry (a run that MUST fail, and did, printing its expect); the self-test fails evidence with no vacuity run, and evidence whose vacuity run passed", traces_to: [main..f65222c]}
  - {id: R12, verdict: PASS, verify: local, formal: checked, evidence: "formal/R12.json re-run; every property named in the signed Property is in a cfg at the stated bounds (Election 3 sessions; ElectionLive 2; Aidlc and AidlcLive with 2 items); the fairness is written down (Aidlc WF Agent; Election WF/SF, A5); models.yml runs the seeded broken variants", traces_to: [main..f65222c]}
  - {id: R13, verdict: PASS, verify: local, formal: checked, evidence: "formal/R13.json re-run; 5 sampled traces accepted, 3 mutants rejected; check_repo fails on a difference between the sets (both directions tried)", traces_to: [main..f65222c]}
  - {id: R14, verdict: PASS, verify: local, formal: none, evidence: "AGENTS.md invariant 11; reviewer.md invariants_checked [1..11]", traces_to: [main..f65222c]}
  - {id: R15, verdict: PASS, verify: local, formal: checked, evidence: "formal/R15.json re-run; ElectionV096 yields an AtMostOneActing counterexample; session-governance.md's table names A1-A5", traces_to: [main..f65222c]}
  - {id: N1, verdict: PASS, verify: local, formal: none, evidence: "the R6 mapping is complete (above); I found no loosened gate; the latest reviewer round lists N1 as independently satisfied", traces_to: [SKILL.md]}
  - {id: N2, verdict: PASS, verify: local, formal: none, evidence: "invariant 10's text is byte-identical to 0.9.6's; check_tasks runs both check_live and check_formal for each Done item", traces_to: [AGENTS.md, check_tasks.py]}
  - {id: N3, verdict: PASS, verify: local, formal: none, evidence: "check_tasks.py and check_formal.py import only the stdlib plus their sibling check_live/check_formal; check_neutral exits 0; models.yml pins tla2tools 1.7.4, and check_models.py checks its sha256", traces_to: [framework/tools, models.yml]}
  - {id: N4, verdict: PASS, verify: local, formal: none, evidence: "the latest auditor verdict (audit-8, at b572f8f) is PASS-WITH-DEBT with no blocker or high finding", traces_to: [audit-8]}
blockers: []
debts:
  - "R3 Threat model, read literally: a lossy clean filter (the user's own git config) lets a re-run pass what the plain run fails. Repro: in a toy repo, set `filter.strip.clean 'grep -v DEVONLY'` and `smudge cat`, with `*.js filter=strip`. Commit src/app.js and local R1 evidence. Then add `const mockApi = 1; // DEVONLY` to src/app.js and `git add` it, so git status is empty. Plain check_live -> rc 1 `src/app.js:2: mock`; check_live --rerun -> rc 0 live: ok. This is not a blocker: the re-run judges HEAD correctly, the content never ships, and the filter is the user's config, which is the environment. Still, state it next to the stale-evidence asymmetry below, or have unclean() compare raw bytes for filtered names."
  - "Carried: check_live --rerun accepts stale or orphan evidence once a local re-run passes, while check_formal --rerun still reports it stale. Read literally, this is a second way a re-run passes what the plain run fails. Say which reading R3 means."
  - "Carried: check_tasks --self-test has no case that asserts the reason 'Done but not formal'. The behaviour is correct: my toy got that exact hit, both plain and --rerun."
  - "N4.json probes verdicts/audit.md (the first audit), not the latest one. No audit covers the code changed since b572f8f (cfee3f4 and ff1d41a included). N4's clause is met by audit-8, but the final tree is not audited."
  - "No 0.9.7 commit carries a `Closes Rn` line (only 0.9.5 and 0.9.6 do). SKILL.md's Traceability rule asks for one. Add it to the squash or merge message."
  - "Carry forward D1-D5, D9, D10 and D12-D22 as listed in TASKS.md."
notes:
  - "Regression list (QA-14 B1/B2, Security-5): the per-probe TMPDIR repro now fails as it should. The .aidlc/features/<slug>/spec edit after the sha is now reported stale. The virtualenv-on-PATH case is ruled environment in R3's signed text, and the plain check_tasks run confirms the hash."
  - "Threat-model probes that held: an untracked file and a --skip-worktree edit are refused. A ledger HEAD lacks is refused. A Done item whose formal evidence is missing fails, and so does one whose live result fails. Leftovers in TMPDIR are gone. Case and symlink handling is covered by the self-test; the cases I read are in the source."
  - "R8: Phase 6's SKILL.md block does not name the pre-authorized list itself. Phase 5's paragraph applies to every high-risk action, release.md consults the list, and Phase 6's irreversible steps sit in the ship batch. This is a note, as in QA-10."
  - "R11: SKILL.md's sketch says 'vacuity: one run that MUST fail ... and did, printing its own expect' without spelling the fields command/observed/result. The docstring has the full JSON. This is a note."
  - "A process that a probe detaches with setsid escapes the process-group kill. That is deliberate, not an accident, so it is not a gap under R3."
  - "CI was not observable from here. Every step of checks.yml and models.yml ran locally at f65222c and was green."
  - "TASKS.md still lists R3 and R10 as In progress (3/5, stalled 0/3). This PASS is the verifying step that lets them move to Done."
```

Retrospective: every sensor, every model and every acceptance command is green at
f65222c. The threat model's listed accidents are kept out, and the last round's
regressions are closed. The one new gap is git's own view of "clean" (a lossy clean
filter), and it errs toward HEAD. Next time, test content that git status hides on
purpose before content it misses by accident.
