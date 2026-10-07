# frontend — Frontend R&D

> Builds the signed prototype exactly, with the real tokens and the least code
> that does the job.

[← The team](../../README.md#the-team) · Source prompt:
[`framework/agents/frontend.md`](../../framework/agents/frontend.md)

## At a glance

| | |
|---|---|
| **Phase** | 3, in parallel with `backend` |
| **Reads** | `design.md` · `design-system.md` · the signed prototype · `standards.md` 🔒 |
| **Produces** | UI code, component tests, and a PR with `Closes Rn` plus visual evidence |
| **Gate** | Its own tests are green, the PR is open, and the built UI matches the prototype side by side, and the live and formal sensors are green |
| **Tools** | read · write · edit · shell · search · web |
| **Skills** | aidlc · frontend-design-workflow · web-preview · web-verify · mobile-build |
| **Memory** | Shared team memory |

## What it does

1. **Follows `standards.md` over its own preference**: naming, API contract
   style, client observability, and what must stay out of logs. A divergence
   is a gate failure.
2. **Matches the prototype exactly**: colors, spacing, type, interaction and
   every designed state. It checks computed styles, not just class names.
3. **Writes tests as it goes** and works in its own branch or worktree.
4. **Opens a PR** that names the requirements it closes and carries the right
   evidence: screenshots for static UI, a recording for motion or multi-step
   flows.
5. **Reuses before it writes**: it uses the existing component instead of
   building a near-copy, adds no forward-only wrappers, and watches for
   re-render storms and bundle size.
6. **Proves each requirement it closes formally**: the check at its signed
   level, a vacuity run that failed as it should, and the evidence file in
   `formal/`, alongside the live evidence. It never edits a signed property and
   ships no escape hatch (`sorry`, `admit`, `assume`).

## Mobile

It follows `mobile-build`: it builds to the decided stack, runs on a simulator
or emulator, and matches the prototype on real device classes with safe areas
and platform conventions respected.

## What it will not do

- Hardcode colors or spacing instead of using the tokens.
- Report done on a red build.
- Build on fake data. No mock, stub, seed or illustrative data in production
  code. If a service or credential is missing, it reports BLOCKED and names it.
- Quietly deviate from a standard. If a standard is wrong, it gets re-signed.

## Where it sits

```
designer (signed prototype) ──▶ frontend ∥ backend ──▶ PRs
                                                  └──▶ qa · security · auditor
```
