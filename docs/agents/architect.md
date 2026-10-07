# architect — Architect

> Turns the signed requirements into a stack it can justify, and guards every
> later change to that decision.

[← The team](../../README.md#the-team) · Source prompt:
[`framework/agents/architect.md`](../../framework/agents/architect.md)

## At a glance

| | |
|---|---|
| **Phase** | 1, plus two standing duties (below) |
| **Reads** | `requirements.md` |
| **Produces** | `design.md` (ADRs, requirement→design map, data model, interfaces, threat model) and `standards.md`, written with the CEO |
| **Gate** | Every Rn/Nn maps to a design element and every big choice has an ADR. 🔴 The CEO signs `standards.md`, which is then hash-locked |
| **Tools** | read · write · edit · shell · search · web |
| **Skills** | aidlc · llm-council |
| **Memory** | Shared team memory |

## What it does

1. **Extracts the constraints that drive the choice**: scale, latency, budget,
   team, deploy target and compliance.
2. **Searches the current landscape**, then puts 2–3 candidate stacks through a
   cross-vendor `llm-council` before deciding. It never defaults to a familiar
   stack.
3. **Writes `design.md`**: one ADR per load-bearing decision, and a
   requirement→design map with no blank rows.
4. **Writes `standards.md` with the CEO**: deploy environments, API style, DB
   schema source, compliance, observability and security baselines, and the
   code-efficiency budget. The CEO makes the business calls, such as which cloud.

## Standing duties

- **Architecture-change guard.** A mid-flight change to a signed ADR comes back
  to the architect, never lands on an implementer's say-so. It answers APPROVE,
  REQUEST-CHANGES or ESCALATE. It escalates to the CEO when the change breaks a
  requirement, changes the platform strategy, shifts cost or lock-in, or
  reverses an ADR the CEO approved.
- **Mobile consultation in Phase 0.** For an app, it recommends native or
  cross-platform (Flutter / React Native / KMP) over the draft requirements. The
  CEO signs that choice as the first ADR.

## What it will not do

- Hardcode a deploy target such as "AWS prod". The environment is decided with
  the CEO.
- Approve a load-bearing reversal on its own single reading.

## Where it sits

```
analyst / orchestrator ──▶ architect ──▶ design.md ──▶ designer · frontend
                                                      backend · qa
                                     └─▶ standards.md 🔒 ──▶ everyone downstream
```
