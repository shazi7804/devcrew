# orchestrator — Orchestrator + PM

> The only agent the CEO talks to. It owns the loop and does none of the
> roles' work itself.

[← The team](../../README.md#the-team) · Source prompt:
[`framework/agents/orchestrator.md`](../../framework/agents/orchestrator.md)

## At a glance

| | |
|---|---|
| **Phase** | All of them. It runs Phase 0 itself and dispatches every other phase |
| **Reads** | The CEO's idea, every role's verdict block, the ledger |
| **Produces** | `requirements.md` (Phase 0), the ledger, a SITREP to the CEO every turn |
| **Gate** | Phase 0: the CEO signs `requirements.md`, and its hash becomes the intent hash |
| **Tools** | read · write · edit · shell · search · web · spawn · memory |
| **Skills** | aidlc · frontend-design-workflow · llm-council · goal-conductor · web-preview · web-verify · deploy-web · artifact-deploy |
| **Memory** | Shared team memory; it is also the one role that appends the retros |

## What it does

1. **Aligns intent before anything is built.** It asks only the questions that
   would change the design, writes `requirements.md` (EARS requirements, each
   with an acceptance condition), and waits for the CEO to sign.
2. **Classifies the scope** (greenfield / feature / bugfix / hotfix / refactor /
   chore / docs) and runs only the phases that scope needs. Safety floors still
   pull a phase back in: an auth change pulls Security, a UI change pulls
   Design, and a large diff pulls the Auditor.
3. **Dispatches roles one gate at a time.** Each role gets contract file paths,
   not a paraphrase. Independent roles run as one parallel batch: frontend ∥
   backend, and qa ∥ security ∥ auditor.
4. **Decides each gate from the structured verdict YAML**, never from prose. It
   runs the gate in a fixed order: deterministic sensors, then semantic
   judgment, then a 🔴 CEO gate if there is one.
5. **Catches drift.** It re-hashes `requirements.md` and `standards.md` at every
   gate. A changed hash without a fresh signature halts the run.
6. **Measures the magnitude floor** (`git diff --shortstat`) at the start of
   Phase 4, and dispatches `auditor` when the diff is over 1000 lines or 20
   files.
7. **Keeps a durable ledger**: phase, gate status, hashes, fix-loop counters,
   and the requirement→PR→test map. A restart resumes where it left off.
8. **Runs the retrospective and self-evolution loop.** A framework change starts
   with its own signed `proposals/<slug>/requirements.md`. It then goes out as
   a PR through CI, `qa` and `reviewer`, and the CEO merges it.

## What it will not do

- Write architecture, code or design in its own turns. That is the roles' work.
- Approve its own 🔴 gates, or run a high-risk production action without the
  CEO's confirmation.
- Relay a role's report to the CEO verbatim. It condenses each report into a
  SITREP.

## Where it sits

```
CEO ⇄ orchestrator ──▶ analyst · architect · designer · frontend · backend
                       qa · security · auditor · devops · release · reviewer
```
