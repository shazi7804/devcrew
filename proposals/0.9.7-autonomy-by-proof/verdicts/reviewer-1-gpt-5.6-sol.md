# Review result: REJECT

This change cannot safely replace CEO stops with the proposed sensors and models. Several checks are green only because the encoded properties are weaker than the signed requirements.

The author’s local outputs are claims, not CI evidence. `framework/agents/reviewer.md:25-31` explicitly requires readable CI results before review. I did not run commands, consistent with the reviewer role.

## Blocking findings

1. **BLOCKER — the AIDLC model permits build before the Intent batch.**  
   `framework/formal/Aidlc.tla:24-43,73-83,146` makes `arch` and `design` optional, treats the Design batch as unnecessary when both are skipped, and defines `Before("build") = "design"`. Therefore a bugfix/hotfix/docs path can advance directly from `intent` to `build` while `signed["intent"]` is still false. `NoPhasePastUnsignedBatch` nevertheless passes because it asks only whether the now-unneeded Design batch is signed. This violates R12(a), invariants 1/8/11, and the rule that Phase 0 is never skipped.

2. **BLOCKER — Loop A does not interrupt at its signed bound.**  
   `framework/tools/check_tasks.py:177-185` rejects only `n > cap` and stalled counts greater than 3. It accepts exactly `5/5` and `stalled 3/3`, although `tasks.template.md:43` and `SKILL.md:813` say those exact states raise `loop-bound`. Its self-tests cover `6/5` and `4/3`, not the boundary (`check_tasks.py:213-215`).  
   The model has the same semantic hole: at equality, `Bound`, `Prove`, `Close`, and potentially `Advance` remain alternatives (`Aidlc.tla:92-107,139-142`). Weak fairness is applied to their disjunction, so it does not force `Bound`. `LoopBounded` merely proves `attempts <= MaxAttempts`, already guaranteed by the variable domain and transition guards. This does not prove that the run stops when the bound is reached.

3. **BLOCKER — `check_formal.py` can be satisfied by fabricated formal evidence.**  
   `framework/tools/check_formal.py:128-203` trusts stored `result`, vacuity, and conformance-result strings unless rerun. Even with `--rerun`, it does not establish that the command invokes the declared tool or checks the listed sources/property. Its own passing fixture uses:
   - `tool: TLC`
   - `command: true`
   - a harmless dummy `.tla` source
   - `vacuity.command: false`
   - `conformance_check.command: true`  
   (`check_formal.py:228-232`). That is precisely fake proof evidence, and it passes the “clean” case. `check_tasks.py:150-156` invokes both evidence sensors without rerunning them, so this can mark an item Done. R3, R10, R11 and invariant 11 are not met.

4. **BLOCKER — `check_tasks.py` has a complete requirements/evidence bypass.**  
   `check_tasks.py:68-124` never verifies that the first `Signed:` target is `requirements.md` or even contains requirements. If the first signed file parses to zero Rn/Nn items:
   - missing-ID checks iterate over an empty set;
   - unknown IDs are accepted because the test is conditional on `req` being nonempty;
   - the Done evidence set is empty.  
   A TASKS file can therefore sign a different Markdown file first and bypass R2/R3 entirely. The Gate parser also accepts arbitrary text after a valid batch name rather than the required exact `— awaiting CEO` form.

5. **BLOCKER — the proposal’s own signed-gate state is invalid.**  
   - The CEO ruling preceded the item-level `Property` / `Formal` / `Conformance` additions (`proposals/0.9.7-autonomy-by-proof/requirements.md:270-286`). Under the new rule, the CEO signs the properties themselves; an agent cannot declare later edits non-semantic and reuse the earlier ruling. That is contract drift.
   - Scope is `feature`, a Phase-1 design exists, and R6 requires the Design batch to sign `design.md + standards.md` (`requirements.md:99`). No `standards.md` exists anywhere in the repository, while `TASKS.md:1-2` signs only `requirements.md` and claims the Ship gate is open.
   - At the final filesystem snapshot, `evidence/` contained only R1–R10 and no formal evidence directory, while `TASKS.md:14-21` marked R10–R15 and N2–N3 Done. R11–R15/N2/N3 therefore lack local evidence, and checked requirements R12/R13/R15 lack formal evidence. The evidence directory also changed during this review—R10 appeared after the initial inventory—so the filesystem was not a stable `HEAD` snapshot.

6. **HIGH — R9’s required schema is not implemented.**  
   R9 requires `Property`, `Formal`, and `Conformance` on every example item. `requirements.template.md:60-81` omits Formal and Conformance for R3, N1, and N3 when `Property: none`. `check_formal.py:128-131` immediately continues on `Property: none`, so it never detects those missing fields. R9 acceptance fails as written.

7. **HIGH — election trace validation is not step-by-step faithful.**  
   The core generation design is reasonable, and A1–A4 are plainly documented at `session-governance.md:286-289`. However:
   - `boot.py:189` omits generation `n` from scan traces.
   - `boot.py:193-197,238-242` silently ignores failed touch/release operations.
   - `Election.tla:109-135` models successful touch/release state changes.
   - `ElectionTrace.tla:23-32` cannot compare generation numbers or touch/release success.
   - `tools/check_models.py:196-207` serializes only the fields that `boot.py` supplied.  
   Consequently, a mutation that creates the wrong generation can still match, and a failed `utime` or release can be interpreted as the model’s successful action. Rejecting the one “refresh regardless of age” mutant does not establish general trace conformance required by R13.

8. **HIGH — the pin is outside the model on a false premise.**  
   `session-governance.md:293-295` says the pin “only ever makes sessions workers.” In fact, `boot.py:468-486` calls `elect(... may_take=False)`, but an existing holder can still be returned as orchestrator, written to its hint as orchestrator, and only receives advisory text telling it not to claim work. That is not “only workers” and relies on A3 rather than the modeled mechanism.

9. **HIGH — liveness vacuity claims are not wired into CI.**  
   `design.md:70-71` claims two deliberately false liveness properties were rejected, and `CHANGELOG.md:54` says every model has a seeded broken variant. But `tools/check_models.py:49-57` includes only safety failures:
   - ElectionV096 → `AtMostOneActing`
   - AidlcBroken → `NoPhasePastUnsignedBatch`  
   There is no retained broken liveness spec/configuration for `HooksEnd`, `ElectedAfterGone`, `NeverStuck`, `LoopTerminates`, or `TroubleReachesCEO`. R11 says every formal check must demonstrate non-vacuity.

10. **HIGH — the “exactly six interrupts” claim is internally inconsistent.**  
    `SKILL.md:780-822` says the run stops only for one of six interrupts, but `SKILL.md:768` separately says a token/time-budget overrun “STOPS and reports to the CEO.” It is neither a batch nor one of the six interrupts and has no row in the former-gate mapping. In addition, `cross-design` is only a prose architecture-delta review (`SKILL.md:812,878`); repository search found no executable sensor implementing it. This violates R7 and the reviewer’s deterministic rule that no removed stop may lack a replacement sensor.

11. **HIGH — mandatory gates have not run.**  
    CI has not run, QA evidence/verdict is absent, and N4 explicitly remains in progress awaiting the auditor (`TASKS.md:25`). The reviewer’s own file is changed, so `reviewer.md:91-94` and the proposal’s `requirements.md:289` require a second independent reviewer or adversarial council. This review can block the change but cannot be its sole approval.

12. **MEDIUM — the verdict schema still omits invariant 11.**  
    `framework/skills/aidlc/contracts/verdicts.template.md:101` still specifies `invariants_checked: [1..10]`, contradicting the updated reviewer prompt and R14.

## Assumption-retry assessment

The retry added in `tools/check_models.py:61,212-219` does **not** convert a TLC model mismatch into a pass; it retries only runs classified as outside A1/A2 and fails if all three attempts remain outside. That part is defensible for the accelerated 4s/2s harness.

It can, however, discard a trace before TLC sees it, and intermediate assumption violations are not reported. Record every discarded run and its reason in CI. This is secondary to the more fundamental trace omissions above.

## Acceptance summary

- **Appears satisfied in current prose:** R5, R8; invariants 2, 3, 5, 6, and the current text of the invariant-7 magnitude floor.
- **Failed or not established:** R2–R4, R6–R7, R9–R15, N1–N4.
- **R1:** template exists, but the broad “every ledger mention resolves to TASKS.md” acceptance was not independently established.
- **N2:** the prose says formal never replaces live, but the Done/evidence bypass means the mechanism does not enforce it reliably.
- **N3:** stdlib sources and a pinned TLC checksum are present, but neutrality and CI execution remain only author-reported.
- I could not perform the requested `git show 49d78dd:...` comparison because this reviewer has no shell and no plain-file snapshot of that commit was supplied. The current mapping already fails because of the unmapped budget stop. Diff-only checks—neutrality deny-list removals and historical magnitude-floor weakening—also require CI or a supplied base snapshot.

No self-merge path, role collapse, hardcoded product deployment topology, or obvious prompt-injection payload was found. The current role files still declare shared memory for all normal roles and none for reviewer.

```yaml
verdict: REJECT
model_used: gpt-5.6-sol
author_model_vendor: Anthropic
reviews_own_change: false
invariants_checked: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
concerns:
  - severity: blocker
    file: framework/formal/Aidlc.tla:24-43,73-83,146
    what: Build can start with the Intent batch unsigned when architecture and design are both skipped.
    why: The model proves a weakened prerequisite rather than R12(a).
  - severity: blocker
    file: framework/tools/check_tasks.py:177-185
    what: Exact Loop-A bounds 5/5 and stalled 3/3 pass.
    why: The interrupt fires only after an extra attempt, contrary to R4/R7 and invariant 11.
  - severity: blocker
    file: framework/tools/check_formal.py:128-203,228-232
    what: Trivial true/false commands and unrelated clean sources can satisfy formal, vacuity, and conformance evidence.
    why: The sensor does not prove that the signed property or declared source was checked.
  - severity: blocker
    file: framework/tools/check_tasks.py:68-156
    what: A non-requirements first Signed target can empty the requirement set and bypass IDs and Done evidence.
    why: R2/R3 can be defeated by file ordering.
  - severity: blocker
    file: proposals/0.9.7-autonomy-by-proof/requirements.md:270-289
    what: Formal property fields were added after the cited CEO ruling.
    why: The new protocol says the CEO signs the properties; post-signature edits are drift.
  - severity: blocker
    file: proposals/0.9.7-autonomy-by-proof/TASKS.md:1-25
    what: The ledger claims Ship-ready and marks unsupported items Done without a standards signature or complete live/formal evidence.
    why: The proposal fails its own gates.
  - severity: high
    file: framework/tools/boot.py:189-242
    what: Trace records omit generation and touch/release outcomes while filesystem errors are swallowed.
    why: ElectionTrace can accept executions that do not perform the state change modeled by Election.tla.
  - severity: high
    file: tools/check_models.py:49-57
    what: No seeded broken liveness checks are retained.
    why: The design and changelog claim every model/check demonstrates non-vacuity.
  - severity: high
    file: framework/skills/aidlc/SKILL.md:768,780-822
    what: Budget exhaustion is an extra CEO stop, and cross-design has no executable sensor.
    why: The claimed exact six-interrupt replacement is incomplete.
  - severity: high
    file: framework/skills/aidlc/contracts/requirements.template.md:60-81
    what: Property-none examples omit required Formal and Conformance fields.
    why: R9 requires all three fields on every example requirement.
  - severity: high
    file: framework/agents/reviewer.md:25-31,91-94
    what: CI has not run and this change edits reviewer.md.
    why: Author-local output cannot replace CI, and a second independent reviewer is mandatory.
  - severity: medium
    file: framework/skills/aidlc/contracts/verdicts.template.md:101
    what: The central verdict schema still lists only invariants 1-10.
    why: It can produce a structurally valid verdict that omits invariant 11.
```
