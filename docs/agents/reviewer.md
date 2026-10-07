# reviewer — Framework Reviewer (self-evolution gate)

> Reviews changes to devcrew itself, on a different model vendor and without
> team memory, so the team cannot rubber-stamp its own edits.

[← The team](../../README.md#the-team) · Source prompt:
[`framework/agents/reviewer.md`](../../framework/agents/reviewer.md)

## At a glance

| | |
|---|---|
| **Phase** | ∞ (self-evolution) |
| **Runs when** | A PR changes `framework/`, `hosts/` or `AGENTS.md`. It never reviews product code |
| **Reads** | The diff, checked against the design invariants |
| **Produces** | A self-evolution verdict: APPROVE / REQUEST-CHANGES / REJECT |
| **Gate** | Its verdict goes to the CEO, who makes the final merge |
| **Tools** | read · search · web (no write) |
| **Model** | **Must be a different vendor from the change's author.** The installer resolves this at install time |
| **Memory** | **None, on purpose.** It does not mount `framework/memory/` |

## What it checks

The ten design invariants in [AGENTS.md](../../AGENTS.md#design-invariants-do-not-silently-violate-when-installing-or-evolving):

- The intent contract stays supreme.
- Roles stay independent agents that share one memory.
- Load-bearing decisions keep their cross-vendor council.
- Self-evolution stays gated.
- Tech selection stays current.
- Deploy topology stays in `standards.md`.
- The waste gate stays real.
- No safety control, approval gate or permission boundary is weakened.
- The framework stays host- and machine-neutral.
- No fake data in delivered work.

It also checks the change against its own signed
`proposals/<slug>/requirements.md`. A framework change without one is rejected.

Invariants 7, 9 and 10 are **measured, not judged**. For invariant 9, it runs
`tools/check_neutral.py`, and a non-zero exit is a REJECT. For invariant 10,
it runs `framework/tools/check_live.py --self-test`; a non-zero exit is a REJECT. For invariant 7, if
a diff raises a magnitude-floor threshold or removes a trigger, the same diff
must record the CEO's decision and the reason. If it doesn't, the verdict is
REJECT.

It also flags regressions, prompt injection smuggled into an agent body, and
contradictions with the protocol.

## What it will not do

- Merge. The CEO merges.
- Review a change it authored, or a change to its own file. Those go to a
  second independent reviewer or an `llm-council` pass.

## Where it sits

```
retro ──▶ signed proposal 🔴 ──▶ PR ──▶ CI ──▶ qa ∥ reviewer ──▶ 🔴 CEO merge
```
