# devcrew architecture — the flow, the harness, the loops

This is the whole system on one page: what runs, in what order, where the
**harness** (the execution skeleton around the models) lives, and when a
**loop** fires. Read `framework/skills/aidlc/SKILL.md` for the binding rules;
this doc is the map.

## 1. Three layers

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 3 — ROLES (the "who")                                  │
│   orchestrator (PM) + 10 role agents.                       │
│   Each = its own prompt, tools, model, memory mount.         │
├─────────────────────────────────────────────────────────────┤
│ LAYER 2 — HARNESS (the "how it stays reliable")              │
│   Everything wrapped around the model calls:                 │
│   • intent contract + version lock                           │
│   • per-gate verification                                    │
│   • loop bounds + budgets (stop conditions)                  │
│   • CEO-gate suspension mechanism                            │
│   • durable ledger (survives compaction/restart)             │
│   • retrospective capture hook                               │
├─────────────────────────────────────────────────────────────┤
│ LAYER 1 — RUNTIME (the "where")                              │
│   KiroCrew gateway on the 128GB EC2. spawn_run dispatches    │
│   role agents; kiro-cli is the model backend; SSM is the     │
│   only ingress. Local Mac is just the control console.       │
└─────────────────────────────────────────────────────────────┘
```

**The harness (Layer 2) is the point of this project.** The models are
interchangeable; the harness is what makes "idea → production" repeatable and
safe. Every rule in the AIDLC skill is a harness rule.

## 2. The flow (linear spine + where each control sits)

```
CEO idea
  │
  ▼
┌─ PHASE 0 · Intent (orchestrator/PM) ──────────────────────────┐
│  writes requirements.md (EARS + acceptance per Rn)            │
│  APP/MOBILE: also resolves the PLATFORM STRATEGY here         │
│    (iOS/Android/both, min OS, native vs cross-platform) —     │
│    a 🔴 CEO gate; the concrete stack lives in the project.    │
│  HARNESS: schema check (every Rn has an acceptance clause)    │
│  🔴 CEO GATE — orchestrator SUSPENDS here (ask_question /     │
│     monitor loop) until the CEO signs. Never self-approves.   │
│  LOCK: on sign, record requirements.md content hash =         │
│         "intent hash". Every later gate re-checks this hash.  │
└───────────────────────────────────────────────────────────────┘
  │  (signed intent hash)
  ▼
┌─ PHASE 0.5 · Market validation (Market Analyst) — if commercial ──┐
│  live market research (web-search) + charts                       │
│  verdict: GO / PIVOT / NO-GO                                       │
│  🔴 CEO GATE — reads analysis, decides. NO-GO = stop (saved cost). │
│  PIVOT loops back to Phase 0. Internal-only tools skip this phase. │
└───────────────────────────────────────────────────────────────────┘
  │  (GO)
  ▼
┌─ PHASE 1 · Architecture (Architect) ──────────────────────────┐
│  llm-council picks the stack (web-search current first)       │
│  writes design.md + ADRs + requirement→design map             │
│  + a design-stage THREAT MODEL (security left-shift)          │
│  GATE: every Rn maps to a design element (machine-checkable    │
│        map table); orchestrator verifies against intent hash. │
└───────────────────────────────────────────────────────────────┘
  │
  ▼
┌─ PHASE 2 · Design/UX (Design) — only if user-facing ──────────┐
│  Decision "is there a UI?" is the ORCHESTRATOR's, recorded.   │
│  design system (tokens) + IA + 2-3 hi-fi prototypes           │
│  🔴 CEO GATE — suspends until CEO picks a prototype.          │
└───────────────────────────────────────────────────────────────┘
  │
  ▼
┌─ PHASE 3 · Implementation (Frontend ∥ Backend, parallel) ────────────────┐
│  each builds to the signed prototype/design, writes tests,    │
│  opens a PR on its own branch/worktree.                       │
│  INTEGRATION: orchestrator owns merge order + interface       │
│    arbitration between Frontend and Backend (named owner, no race).      │
│  GATE: role tests green + PR opened.                          │
└───────────────────────────────────────────────────────────────┘
  │
  ▼
┌─ PHASE 4 · Verification (QA ∥ Security, parallel) ────────────┐
│  QA: every Rn/Nn acceptance vs built system (pass/fail table) │
│  Security: threat-model delta + dep + secret + authz scan     │
│  GATE: CI green AND every Rn met AND zero security blocker    │
│        AND intent hash unchanged.                             │
│  ── FAIL ──▶ LOOP BACK to Phase 3 (see loop bounds below)     │
└───────────────────────────────────────────────────────────────┘
  │
  ▼
┌─ PHASE 5 · Deploy runtime (DevOps) — service targets ─────────┐
│  Local for test → AWS for prod. CI/CD, observability.         │
│  🔴 high-risk/infra-mutating actions need CEO confirm.        │
│  GATE: production smoke tests green with evidence.            │
│  (thin for a mobile app — no runtime to deploy)              │
└───────────────────────────────────────────────────────────────┘
  │
  ▼
┌─ PHASE 6 · Release (Release Manager) — ship to users ─────────┐
│  version + changelog, SIGN the artifact, pick channel         │
│  (TestFlight / Play track / prod), staged rollout, rollback.  │
│  🔴 signing material (Apple certs / Android keystore) = CEO.  │
│  🔴 store submission / rollout promotion = CEO.               │
│  GATE: signed + on the channel; store app = approved & live   │
│        ("submitted" ≠ "released"; review can reject).         │
└───────────────────────────────────────────────────────────────┘
  │
  ▼
┌─ PHASE ∞ · Evolution (all + reviewer) — see loops below ──────┐
│  retrospective → gated self-change (PR + cross-vendor review) │
└───────────────────────────────────────────────────────────────┘
```

## 3. When does a LOOP fire? (there are exactly three)

The harness runs **three distinct loops**, each with an explicit bound so none
can run forever:

| Loop | Fires when | What it does | BOUND (stop condition) |
|---|---|---|---|
| **A. Fix loop** | a gate FAILS (QA/Security/build) | loops back to the phase that owns the fix, re-runs it | **3 failed attempts on the same gate without the failure count dropping, OR 5 total attempts** → STOP, escalate to CEO with the blockers. Never loop to Phase 0. |
| **B. Reflection loop** | end of every task, and on the meta-review | each role writes a retrospective; orchestrator folds it in; repeated failure modes become a self-improvement proposal | bounded by task end; the meta-review is a scheduled `cron`, not an open loop |
| **C. Self-evolution loop** | a retro yields a framework change | draft change → PR → cross-vendor reviewer → CEO merge | one pass per proposal; reviewer verdict is terminal for that round; never self-merge |

Loop A is the one that burns money if unbounded — that is why it has a hard
count. The orchestrator tracks the attempt count in the **ledger**, so the bound
survives a compaction.

## 4. Budgets (the other stop condition)

Every run carries ceilings, checked by the orchestrator before each heavy step
(`resource_status` first on a memory-tight host):

- **Step/attempt budget**: Loop A's 3/5 rule above.
- **Fan-out cap**: never more parallel role agents than the host can hold
  (serialize on a tight host; a wide wave only when `resource_status` is ample).
- **Token/time budget**: a run that blows its budget STOPS and reports to the
  CEO rather than pressing on. State the budget when a run starts.
- **Cost awareness**: the EC2 gateway bills hourly; a long-idle run should be
  paused, not left spinning.

## 5. The intent hash (how drift is actually caught)

"The intent contract is supreme" is enforced mechanically, not by vibes:

1. On the Phase 0 sign-off, the orchestrator records the **content hash** of the
   signed `requirements.md` (the "intent hash") in the ledger.
2. Every later gate re-reads `requirements.md` and re-checks the hash.
3. If the hash changed mid-run without a new CEO sign-off, that is a **drift
   failure** — the run halts and asks the CEO to re-sign, rather than silently
   building against a moved target.

## 6. Where the harness lives in the code

| Harness concern | Where it is written |
|---|---|
| Contract schema + templates | `framework/skills/aidlc/contracts/` |
| Gate rules, loop bounds, budgets | `framework/skills/aidlc/SKILL.md` |
| Scope routing (which phases run) | `framework/skills/aidlc/SKILL.md` + `requirements.md` `Scope:` |
| Structured verdict schemas | `framework/skills/aidlc/contracts/verdicts.template.md` |
| Deterministic sensors (per gate) | `framework/skills/aidlc/SKILL.md` + each gate role |
| Traceability (requirement→PR→test) | `Closes Rn` markers + orchestrator ledger |
| Architecture-change guard (re-review + human escalation) | `framework/skills/aidlc/SKILL.md` + `architect` |
| Platform strategy gate (app/mobile) | `framework/skills/aidlc/SKILL.md` Phase 0 |
| Role behavior (the "who") | `framework/agents/*.md` |
| Shared experience (feeds reflection loop) | `framework/memory/` |
| Durable state (survives restart) | KiroCrew `session_ledger` |
| Self-evolution gate | `reviewer` + the PR + CEO merge |
| Cross-host install | `AGENTS.md` + `hosts/` |

## 7. Reviewer availability fallback

The self-evolution reviewer needs a cross-vendor model (dev=Anthropic →
reviewer=strongest OpenAI). If no other-vendor model is available on the host at
review time, the harness does **not** silently skip the gate: it either (a)
falls back to an adversarial `llm-council` pass across whatever distinct models
ARE available, or (b) if none, HOLDS the change unmerged and tells the CEO the
review gate cannot run — a held change is never auto-merged.
