# TASKS.md — the run's only ledger

> Copy the block below to `TASKS.md` at the project root (for a framework
> change: `proposals/<slug>/TASKS.md`). It holds the **current state and
> nothing more** — git keeps the history, so nothing here is a record.
> Written by the orchestrator alone; every other role reports to it.
> `check_tasks.py` checks it at every step (its docstring is the full spec).

```markdown
Signed: requirements.md sha256:3f2a9c0b1d4e · standards.md sha256:77ab01c9e2f0
Gate: 🔴 design — awaiting CEO

## Done
- [x] R1 the user can log in

## In progress
- [~] R3 export CSV — verifying · backend · 2/5 · next: QA re-runs check_live
- [~] R4 import — blocked on the CRM key (CEO) · backend · 1/5 stalled 1/3 · next: ask

## Todo
- [ ] R5 audit log
- [ ] D1 split the 900-line handler (audit, medium)
```

## The header — only these two lines
- **`Signed:`** — each signed contract and the first 12 hex of its sha256,
  joined by ` · `; paths are relative to TASKS.md and the first one is the
  requirements. `check_tasks.py --sign requirements.md standards.md` prints
  the line; write it when the CEO signs a batch (intent adds
  `requirements.md`, design adds `standards.md`). A file that no longer
  matches its hash is the `drift` interrupt.
- **`Gate:`** — only while a batch is open: `Gate: 🔴 <intent|design|ship> —
  awaiting CEO`. Remove it when the CEO answers.

## The three sections — exactly these, in this order
| Section | Line form | Rule |
|---|---|---|
| `## Done` | `- [x] <ID> <title>` | one line, no status, no record. Only with fresh live (`check_live.py`) AND formal (`check_formal.py`) evidence |
| `## In progress` | `- [~] <ID> <title> — <status> · <owner> · <n>/<max> · next: <step>` | status is `building`, `verifying`, `fixing` or `blocked on <what>`. `<n>/<max>` is Loop A's attempt count, max at most 5; add `stalled <k>/3` once an attempt did not lower the failure count |
| `## Todo` | `- [ ] <ID> <title>` | not started. Also the home of `Dn` tech debt (the Phase-4 audit's medium/low findings) |

Every `Rn`/`Nn` of the signed requirements appears exactly once; no other ID
appears except `Dn`. Reaching `5/5` or `stalled 3/3` is the `loop-bound`
interrupt — stop and tell the CEO, do not raise the bound.
