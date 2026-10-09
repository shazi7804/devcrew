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
- [~] R3 export CSV — verifying · backend · 2/5 stalled 0/3 · next: QA re-runs check_live
- [~] R4 import — blocked on the CRM key (CEO) · backend · 1/5 stalled 1/3 · next: ask

## Todo
- [ ] R5 audit log
- [ ] C1 deployed the import worker to production, not on the pre-authorized list — every sensor green; undo: `make rollback`
- [ ] D1 split the 900-line handler (audit, medium)
```

## The header — only these two lines
- **`Signed:`** — each signed contract and the first 12 hex of its sha256,
  joined by ` · `; paths are relative to TASKS.md and the first one is the
  requirements. `check_tasks.py --sign requirements.md design.md standards.md`
  prints the line; write it when the CEO signs a batch (intent adds
  `requirements.md`; design adds `design.md`, `standards.md` and any ADR). A
  changed `requirements.md` / `standards.md` is the `drift` interrupt, any
  other signed file `cross-design`; a `design.md` that exists unsigned after
  the design batch fails `check_tasks.py`.
- **`Gate:`** — only while a batch is open: `Gate: 🔴 <intent|design|ship> —
  awaiting CEO`. Remove it when the CEO answers.

## The three sections — exactly these, in this order
| Section | Line form | Rule |
|---|---|---|
| `## Done` | `- [x] <ID> <title>` | one line, no status, no record. Only with fresh live (`check_live.py`) AND formal (`check_formal.py`) evidence |
| `## In progress` | `- [~] <ID> <title> — <status> · <owner> · <n>/5 stalled <k>/3 · next: <step>` | status is `building`, `verifying`, `fixing` or `blocked on <what>`. `<n>/5` is Loop A's attempt count, `stalled <k>/3` the attempts that did not lower the failure count — both, always |
| `## Todo` | `- [ ] <ID> <title>` | not started. Also the home of `Dn` tech debt (the Phase-4 audit's medium/low findings) and of open `Cn` decisions |

Every `Rn`/`Nn` of the signed requirements appears exactly once; no other ID
appears except `Dn` and `Cn`. Reaching `5/5` or `stalled 3/3` is the
`loop-bound` interrupt — the status becomes `blocked on loop-bound`; do not
raise the bound.

## `Cn` — a decision for the CEO to tick, never a stop
A judgment does not stop the run. The role decides it, writes
`- [ ] C<n> <what was decided> — <why, and how to undo it>` in Todo, and goes
on: an irreversible action not on the pre-authorized list, code that departs
from an unchanged design, a spent token/time budget, an implementer's doubt.
The next batch's SITREP lists every open `Cn` as a checklist; when the CEO
ticks one it moves to Done as `[x]`. Never in progress.
