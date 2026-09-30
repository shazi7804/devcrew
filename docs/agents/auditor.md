# auditor — Code Quality & Efficiency Auditor

> The waste gate. It asks the one question QA and Security don't: was this the
> amount of code it takes, and does it cost what it should to run?

[← The team](../../README.md#the-team) · Source prompt:
[`framework/agents/auditor.md`](../../framework/agents/auditor.md)

## At a glance

| | |
|---|---|
| **Phase** | 4, in parallel with `qa` and `security` |
| **Runs when** | The **magnitude floor** fires: more than 1000 changed lines or more than 20 changed files. A project can add its own triggers in `standards.md` |
| **Reads** | The diff · `requirements.md` · `standards.md` § *Code quality & efficiency budget* |
| **Produces** | Findings with measured evidence and a concrete fix each, and the efficiency-audit verdict YAML |
| **Gate** | A blocker or high finding fails the gate and loops back to Phase 3. Medium and low findings go to the ledger as tech debt |
| **Tools** | read · search · shell · web. **No write or edit tool, by design** |
| **Skills** | aidlc |
| **Memory** | Shared team memory |

## The six things it audits

1. **Redundancy and dead code**
2. **Duplication and missed reuse**: the most common source of AI bloat
3. **Over-abstraction**: one-implementation interfaces, forward-only wrappers,
   knobs nothing sets
4. **Runtime efficiency**: N+1 queries, O(n²) on a hot path, re-render storms
5. **Running cost**: instance size, chatty calls, log volume, bundle size,
   tokens per action
6. **Dependency weight**: a heavy library pulled in for one function

## Rules it keeps

- **Measure, don't assert.** A claim with no measurement is capped at medium.
  A blocker or high must show counts, a benchmark, a size delta or bill
  arithmetic.
- **Every finding carries a fix**, and where possible the saving: lines of code,
  ms, KB, or $/month.
- **Budgets come from `standards.md`.** It does not invent thresholds the CEO
  never signed.

## What it will not do

- Rewrite code. An auditor that fixes its own findings is auditing itself.
- Report style nits (that is lint's job), intent (QA's), vulnerabilities
  (Security's) or architecture (the architect's; it escalates these once
  instead).
- Inflate a medium to get it fixed, or deflate a blocker to keep things moving.

## Where it sits

```
diff > 1000 lines or > 20 files ──▶ qa ∥ security ∥ auditor ──▶ gate
```
