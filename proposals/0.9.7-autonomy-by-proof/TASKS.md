Signed: requirements.md sha256:e4468b647089
Gate: 🔴 intent — awaiting CEO

## Done
- [x] R1 TASKS.md defined as the only ledger
- [x] R2 every requirement ID exactly once
- [x] R3 Done only with live + formal evidence
- [x] R4 check_tasks.py, the drift halt as code
- [x] R5 every host uses TASKS.md
- [x] R6 three batches, every former gate mapped
- [x] R7 six interrupts, each raised by a sensor
- [x] R8 pre-authorized actions
- [x] R9 Property · Formal · Conformance
- [x] R10 check_formal.py
- [x] R11 vacuity runs
- [x] R12 the protocol models, checked in CI
- [x] R13 boot.py trace-validated; sets in sync
- [x] R14 invariant 11
- [x] R15 the model's finding fixed, assumptions stated
- [x] N2 formal never replaces live
- [x] N3 stdlib sensors, neutral, pinned checker
- [x] N4 small on purpose (auditor: PASS-WITH-DEBT)

## In progress
- [~] N1 no gate weakened — verifying · reviewer · 3/5 stalled 0/3 · next: reviewer round 3 on the fixed tree

## Todo
- [ ] D1 SKILL.md grew 17% and is in every role's prompt: move Formal verification and the hash detail to contracts/ files only orchestrator, qa and implementers load (R6 keeps the gate map)
- [ ] D2 the models job ran 9 m 56 s on a loaded machine: record CI's own time in the R12/R13 evidence once it has run
- [ ] D3 ElectionV096.tla repeats Election.tla's lifecycle layer
- [ ] D4 check_formal.run_cmd beside check_live.probe -- fold into D9
- [ ] D5 the demotion rule is stated in three places
- [ ] D6 mechanise `unauthorized`: a host guard on irreversible commands, checked against the pre-authorized list
- [ ] D7 mechanise the budget part of `loop-bound`: a token/time counter the run cannot skip
- [ ] D9 check_tasks --rerun runs identical commands repeatedly: memoize per invocation
- [ ] D10 boot.py beat: import subprocess lazily; write the hint files only on change
- [ ] D8 mechanise the judgment part of `cross-design`: code that departs from an unchanged design
