# Retrospectives — the self-evolution log

> After every task, each role that ran appends 3 lines here: what worked, what
> failed, what to change next time. The orchestrator folds these in; the
> periodic meta-review scans this file for repeated failure modes and opens a
> gated self-improvement proposal to the CEO.

## Format
```
### YYYY-MM-DD — <project> — <phase/role>
- worked: ...
- failed: ...
- change: ...   (-> lesson / skill-edit PR / new skill / none)
```

## Entries

### 2026-10-01 — devcrew 0.9.5 — P4/qa
- worked: re-running every output the README shows proved all three were real, not invented.
- failed: attempt 1 FAIL — R8's literal-string grep missed four stale descriptions of the self-evolution path; an unsourced example was called "real".
- change: -> lesson (search requirements by concept, not string)
