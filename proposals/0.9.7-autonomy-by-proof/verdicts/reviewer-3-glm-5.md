I'll conduct an independent review of this framework change. Let me start by reading the signed requirements and the diff.
Now let me read the AIDLC skill to understand the phase structure, batch mappings, and interrupt definitions:
Now let me read the formal models and the tools that implement the sensors:
Now let me read the formal models to check what they actually prove:
Now let me check the former gates table in SKILL.md and trace what became of each:
Now let me check whether the design.md and verdicts from the other review are available to compare afterward:
Now I have enough context to form my review. Let me construct my findings systematically:
## Independent Review Findings
### Invariant 11: Autonomy earned by proof
**Finding 1 (HIGH)**: The claim "between batches the run proceeds only on bounds a machine checks" is **not fully established** for one interrupt.
**File**: `framework/skills/aidlc/SKILL.md` (lines around the interrupts table)
**What**: The `cross-design` interrupt has **two** triggers:
1. `check_tasks.py` detects when a file signed in the design batch (`design.md`, an ADR) has changed
2. The architect's "architecture-delta check" for code that departs from the design without editing it
**Why this matters**: The second trigger is **a judgment, not a sensor**. The SKILL.md explicitly states: "plus the architect's architecture-delta check, a judgment, for code that departs from the design without editing it."
R7 states: "Between batches the run SHALL NOT stop for the CEO, except on an interrupt, and the interrupts SHALL be exactly these..."
The architect's judgment is not a bound a machine checks. It is a semantic determination made by an LLM. This contradicts invariant 11's requirement that "between them the run proceeds on its own only on bounds a machine checks."
The CHANGELOG claims: "Between batches the run stops only on six interrupts, each raised by a sensor." This is **not true** for the architecture-delta branch of `cross-design`.
### Invariant 8: No gate weakened
**Finding 2 (HIGH)**: The batch grouping **does not preserve all former gates**.
**File**: `framework/skills/aidlc/SKILL.md` (Batches and interrupts section)
**What**: The "former 🔴 gate" table maps old gates to batches, but one transition is misleading:
- **Former gate**: "an architecture change crossing a signed boundary"
- **Now**: "interrupt `cross-design`"
This is a **weakening**. A CEO gate (🔴) requires explicit human approval. An interrupt only requires the CEO's attention if a sensor raises it. The architect's judgment that a change "crosses a signed boundary" is now an interrupt, not a gate.
The table should distinguish:
- Former gates that became **part of a batch** (still require CEO sign-off)
- Former gates that became **interrupts** (no longer require sign-off, only attention when raised)
R6 requires: "no item that the CEO signs today SHALL be dropped from them." An architecture-crossing-boundary gate where the CEO used to sign off is now an interrupt. The CEO no longer signs off on these—they are raised as interrupts, and the run continues after resolution.
This may be defensible (the CHANGELOG discusses it), but N1's claim that "every item the CEO signs today is still signed" needs a clearer mapping of what was a **sign-off gate** vs. a **suspend gate**.
### Invariant 10: Formal never replaces live
**Finding 3 (MEDIUM - but actually a strength)**: The implementation correctly enforces this.
**File**: `framework/tools/check_tasks.py` (lines 65-70)
**What**: The sensor correctly requires **both** live and formal evidence for Done items:
```python
if evidence and done and reqfile.is_file():
    ev = reqfile.parent / "evidence"
    live = check_live.check_evidence(root, reqfile, ev / env if env else ev, done,
                                     (), rerun, False, False)
    hits += [f"Done but not live: {h}" for h in live]
    hits += [f"Done but not formal: {h}"
             for h in check_formal.check(root, reqfile, only=done, rerun=rerun)]
```
This is correct. Done requires both.
### The Election Model and boot.py
**Finding 4 (HIGH)**: The model-checker found a real bug in 0.9.6, and the fix is sound—but the claim about trace validation is **stronger than the mechanism**.
**File**: `framework/tools/boot.py` vs `framework/formal/Election.tla`
**What**: The CHANGELOG claims: "`boot.py` is trace-validated: real concurrent runs log every step, and TLC must accept each trace as a behaviour of the model."
**Why this matters**: The trace validation (`check_models.py`) runs **scripted scenarios** (the `scripted` function) and **randomized crowds**. These scenarios are **finite and bounded**. They test that the code follows the model for specific sequences of actions.
But the model proves **temporal properties**: "at most one acting orchestrator" for **all possible interleavings**, not just the tested ones. The trace validation cannot prove the model holds—it can only catch deviations from the model in the tested traces.
The claim "trace-validated" implies a stronger conformance than exists. The correct statement is: "traces of real runs are checked against the model, and deviations are caught." This is **sampling**, not exhaustive validation.
Moreover, assumption A2 ("a beat after every tool call") is **load-bearing**: if violated, a long autonomous turn could let the lease expire while the holder is still acting. The CHANGELOG acknowledges this, but the mechanism (hook after every tool call) depends on the host correctly wiring it. The adapter guide documents it, but there is no **sensor** that detects if a host miswires it.
### Formal verification of the AIDLC model
**Finding 5 (MEDIUM)**: The Aidlc.tla model proves important properties, but its conformance is "none."
**File**: `framework/formal/Aidlc.tla` + requirements R12
**What**: R12 specifies:
- *Formal*: checked
- *Conformance*: trace
But the requirements themselves state for R12: "Conformance: none". And `check_models.py` does not trace-validate the orchestrator against Aidlc.tla because "the orchestrator is a model, not a program."
This is honest, but the distinction between:
- Aidlc.tla (checked, conformance none)
- Election.tla (checked, conformance trace)
should be explicit in the invariant 11 claim. The AIDLC protocol itself is not trace-validated—only the election mechanism is.
### The check_formal.py sensor
**Finding 6 (LOW - correct implementation)**: The sensor correctly checks for escape hatches, vacuity runs, and stale evidence.
The self-test demonstrates it catches:
- No vacuity run (a check that cannot fail proves nothing)
- An escape hatch (`sorry`, `admit`, `axiom`, etc.)
- Stale sha (code changed since the check)
- Level below signed
This is sound.
### The check_tasks.py sensor
**Finding 7 (MEDIUM)**: The bound enforcement is correct, but one case is subtle.
**File**: `framework/tools/check_tasks.py` (progress function)
**What**: The sensor correctly fails when attempts reach the bound AND the status is not "blocked on loop-bound." But the wording in SKILL.md says: "an item at `5/5` or `stalled 3/3`; or the run's token/time budget is spent."
The token/time budget check is not in `check_tasks.py`. It is described in the SKILL.md Budgets section but has no corresponding sensor. The interrupt is `loop-bound`, but the check for a spent token budget is not machine-checked—unless I missed it.
**Why this matters**: Invariant 11 requires "bounds a machine checks." A token/time budget that is "spent" but not machine-checked weakens this.
### The six interrupts
**Finding 8 (MEDIUM)**: One interrupt is not sensor-driven.
**File**: `framework/skills/aidlc/SKILL.md` (Batches and interrupts table)
The interrupts table shows:
- `drift` → `check_tasks.py`
- `cross-design` → `check_tasks.py` + architect's judgment
- `loop-bound` → `check_tasks.py` (but token budget unclear)
- `missing-service` → `check_live.py` / implementer's BLOCKED
- `unauthorized` → pre-authorized list
- `model-fail` → protocol model check
The `cross-design` interrupt has a **judgment component**. The `unauthorized` interrupt depends on code that checks the pre-authorized list—but where is that check? It is described in SKILL.md Phase 5, but is there a sensor?
Reading Phase 5: "High-risk, production, or infra-mutating actions come only from the pre-authorized list... An action not on it is the `unauthorized` interrupt: stop, state what it does..."
This is a **prompt rule**, not a sensor. The devops role is instructed to check. But invariant 11 requires "bounds a machine checks." A prompt rule the model must remember to follow is not a bound a machine checks.
---
Now let me read the other review to compare:
Now I have the other review. Let me now formulate my own verdict based on my independent findings:
## Self-Evolution Verdict
```yaml
verdict: REQUEST-CHANGES
model_used: glm-5
author_model_vendor: Anthropic
reviews_own_change: false
invariants_checked: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
concerns:
  - severity: high
    file: framework/skills/aidlc/SKILL.md:810-812
    what: The cross-design interrupt has a judgment component (architect's architecture-delta check) that is not machine-checked.
    why: Invariant 11 requires that between batches the run proceeds "only on bounds a machine checks." An LLM's judgment is not a machine-checked bound. The CHANGELOG claims all six interrupts are "raised by a sensor" — this is false for the architecture-delta branch of cross-design.
  - severity: high
    file: framework/skills/aidlc/SKILL.md:768
    what: Token/time budget overrun is described as an interrupt (loop-bound) but has no sensor.
    why: SKILL.md § Budgets says a spent token/time budget "raises the loop-bound interrupt." But check_tasks.py only checks the Loop-A attempt count. There is no sensor that checks whether the run's token/time budget is spent. Invariant 11 requires "bounds a machine checks."
  - severity: high
    file: framework/skills/aidlc/SKILL.md:625-628
    what: The unauthorized interrupt depends on the devops role checking the pre-authorized list, not on a sensor.
    why: SKILL.md Phase 5 instructs devops to check the pre-authorized list, but there is no sensor that enforces this. A prompt rule the model must remember to follow is not "a bound a machine checks" (invariant 11).
  - severity: high
    file: framework/skills/aidlc/SKILL.md:780-822
    what: The former-gate mapping shows "an architecture change crossing a signed boundary" became an interrupt, not a batch item.
    why: Invariant 8 says "no gate is weakened to make something pass." A CEO sign-off gate (🔴) became an interrupt that only requires attention when raised. The CEO no longer signs off on these. R6/N1 claim no item the CEO signed is dropped, but this gate's sign-off was dropped.
  - severity: medium
    file: tools/check_models.py (trace validation)
    what: Trace validation tests specific scenarios, not all possible interleavings.
    why: The CHANGELOG claims "boot.py is trace-validated." Trace validation can catch deviations in tested traces, but cannot prove the model holds for all interleavings. The claim is stronger than the mechanism. Correct phrasing: "traces of real runs are checked against the model."
  - severity: medium
    file: framework/formal/Aidlc.tla + requirements R12
    what: The AIDLC model has conformance "none" while Election has conformance "trace."
    why: Invariant 11's claim that "the protocol models in framework/formal/ are checked in CI" should distinguish between the election mechanism (trace-validated) and the AIDLC protocol itself (checked, but not trace-validated because the orchestrator is a model, not a program). This is honest but should be explicit.
  - severity: low
    file: framework/tools/check_tasks.py:65-70
    what: Correctly requires both live and formal evidence for Done items.
    why: This is correct and enforces invariant 10. No concern — noted as a strength.
  - severity: low
    file: framework/tools/check_formal.py (self-test)
    what: The sensor correctly checks for escape hatches, vacuity runs, and stale evidence.
    why: This is correct. The self-test demonstrates the sensor catches the required failure modes. No concern — noted as a strength.
```
## Summary
My independent review finds **three substantive concerns** that require changes:
1. **The cross-design interrupt is not fully machine-checked.** The architect's judgment is a semantic determination, not a sensor. This contradicts invariant 11 and the CHANGELOG's claim that all six interrupts are "raised by a sensor."
2. **The token/time budget has no sensor.** The Budgets section describes this as raising the `loop-bound` interrupt, but `check_tasks.py` only checks the attempt count. Invariant 11 is not satisfied.
3. **The unauthorized interrupt relies on a prompt rule, not a sensor.** The devops role is instructed to check the pre-authorized list, but there is no machine-checked enforcement.
The other reviewer (GPT-5.6) found additional blocking issues related to the formal model semantics (build before intent, loop-bound at equality) and evidence bypass. I did not independently verify those because my role is to check the invariants and the mechanisms, not to re-run the models or read CI logs. The reviewer should read CI results, but I am operating without shell access and without CI logs provided.
My verdict is **REQUEST-CHANGES** rather than REJECT because the core mechanism (generations for election, TASKS.md for ledger, batch sign-offs) is sound. The gaps are in the interrupt sensors and the claims about what is machine-checked vs. what is model-judged.
The author should:
1. Either make the architecture-delta check a deterministic sensor, or acknowledge it as a judgment (not a machine-checked bound) and adjust invariant 11's claim accordingly.
2. Either implement a token/time budget sensor, or remove the claim that budget overrun is an interrupt.
3. Either implement a pre-authorized-action sensor, or acknowledge it as a prompt rule (not a machine-checked bound).
4. Clarify the former-gate mapping to show which gates became batch items vs. interrupts.
