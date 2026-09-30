# devcrew architecture — the flow, the harness, the loops

This is the whole system on one page: what runs, in what order, where the
**harness** (the execution skeleton around the models) lives, and when a
**loop** fires. Read `framework/skills/aidlc/SKILL.md` for the binding rules;
this doc is the map.

## 1. Three layers

```
┌───────────────────────────────────────────────────────────────┐
│ LAYER 3 — ROLES (the "who")                                   │
│   orchestrator (PM) + 11 role agents.                         │
│   Each = its own prompt, tools, model, memory mount.          │
├───────────────────────────────────────────────────────────────┤
│ LAYER 2 — HARNESS (the "how it stays reliable")               │
│   Everything wrapped around the model calls:                  │
│   • intent contract + version lock                            │
│   • per-gate verification                                     │
│   • loop bounds + budgets (stop conditions)                   │
│   • CEO-gate suspension mechanism                             │
│   • durable ledger (survives compaction/restart)              │
│   • retrospective capture hook                                │
│   • orchestrator election (hosts that run N sessions) — §9    │
├───────────────────────────────────────────────────────────────┤
│ LAYER 1 — RUNTIME (the "where")                               │
│   The host that runs the roles: KiroCrew, Mission Control or  │
│   Claude Code. Each hosts/<host>.md maps the harness onto     │
│   that host's primitives. The framework names none of them.   │
└───────────────────────────────────────────────────────────────┘
```

**The harness (Layer 2) is the point of this project.** The models are
interchangeable; the harness is what makes "idea → production" repeatable and
safe. Every rule in the AIDLC skill is a harness rule.

## 2. The flow (linear spine + where each control sits)

```
CEO idea
  │
  ▼
┌─ PHASE 0 · Intent (orchestrator/PM) ─────────────────────────────────────┐
│  writes requirements.md (EARS + acceptance per Rn)                       │
│  APP/MOBILE: also resolves the PLATFORM STRATEGY here                    │
│    (iOS/Android/both, min OS, native vs cross-platform) —                │
│    a 🔴 CEO gate; the concrete stack lives in the project.               │
│  HARNESS: schema check (every Rn has an acceptance clause)               │
│  🔴 CEO GATE — orchestrator SUSPENDS here (the host's gate               │
│     primitive) until the CEO signs. Never self-approves.                 │
│  LOCK: on sign, record requirements.md content hash =                    │
│         "intent hash". Every later gate re-checks this hash.             │
└──────────────────────────────────────────────────────────────────────────┘
  │  (signed intent hash)
  ▼
┌─ PHASE 0.5 · Market validation (Market Analyst) — if commercial ─────────┐
│  live market research (web-search) + charts                              │
│  verdict: GO / PIVOT / NO-GO                                             │
│  🔴 CEO GATE — reads analysis, decides. NO-GO = stop (saved cost).       │
│  PIVOT loops back to Phase 0. Internal-only tools skip this phase.       │
└──────────────────────────────────────────────────────────────────────────┘
  │  (GO)
  ▼
┌─ PHASE 1 · Architecture (Architect) ─────────────────────────────────────┐
│  llm-council picks the stack (web-search current first)                  │
│  writes design.md + ADRs + requirement→design map                        │
│  + a design-stage THREAT MODEL (security left-shift)                     │
│  GATE: every Rn maps to a design element (machine-checkable              │
│        map table); orchestrator verifies against intent hash.            │
└──────────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─ PHASE 2 · Design/UX (Design) — only if user-facing ─────────────────────┐
│  Decision "is there a UI?" is the ORCHESTRATOR's, recorded.              │
│  design system (tokens) + IA + 2-3 hi-fi prototypes                      │
│  🔴 CEO GATE — suspends until CEO picks a prototype.                     │
└──────────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─ PHASE 3 · Implementation (Frontend ∥ Backend, parallel) ────────────────┐
│  each builds to the signed prototype/design, writes tests,               │
│  opens a PR on its own branch/worktree.                                  │
│  INTEGRATION: orchestrator owns merge order + interface                  │
│    arbitration between Frontend and Backend (named owner, no race).      │
│  GATE: role tests green + PR opened.                                     │
└──────────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─ PHASE 4 · Verification (QA ∥ Security ∥ Auditor, parallel) ─────────────┐
│  QA: every Rn/Nn acceptance vs built system (pass/fail table)            │
│  Security: threat-model delta + dep + secret + authz scan                │
│  Auditor (CONDITIONAL — magnitude floor: >1000 changed lines or          │
│    >20 files; thresholds from standards.md):                             │
│    redundancy · duplication · over-abstraction · hot-path ·              │
│    running cost · dependency weight. Measured, with fixes.               │
│    Reports only — holds no write tool by design.                         │
│  GATE: CI green AND every Rn met AND zero security blocker               │
│        AND zero audit blocker/high AND intent hash unchanged.            │
│        (audit medium/low → tech debt in the ledger, no block)            │
│  ── FAIL ──▶ LOOP BACK to Phase 3 (see loop bounds below)                │
└──────────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─ PHASE 5 · Deploy runtime (DevOps) — service targets ────────────────────┐
│  Deploy to the envs in standards.md. CI/CD, observability.               │
│  🔴 high-risk/infra-mutating actions need CEO confirm.                   │
│  GATE: production smoke tests green with evidence.                       │
│  (thin for a mobile app — no runtime to deploy)                          │
└──────────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─ PHASE 6 · Release (Release Manager) — ship to users ────────────────────┐
│  version + changelog, SIGN the artifact, pick channel                    │
│  (TestFlight / Play track / prod), staged rollout, rollback.             │
│  🔴 signing material (Apple certs / Android keystore) = CEO.             │
│  🔴 store submission / rollout promotion = CEO.                          │
│  GATE: signed + on the channel; store app = approved & live              │
│        ("submitted" ≠ "released"; review can reject).                    │
└──────────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─ PHASE ∞ · Evolution (all + qa + reviewer) — see loops below ────────────┐
│  retro → signed proposal 🔴 → PR → CI → qa ∥ cross-vendor reviewer       │
│  → 🔴 CEO merge                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## 3. When does a LOOP fire? (there are exactly three)

The harness runs **three distinct loops**, each with an explicit bound so none
can run forever. Where they attach to the spine:

```
  P0 ──▶ P0.5 ──▶ P1 ──▶ P2 ──▶ P3 ──▶ P4 ──▶ P5 ──▶ P6 ──▶ P∞
   ▲      ╷                      ▲      ╷      ╷      ╷       ╷
   │      │ PIVOT                │      │ FAIL │ FAIL │ reject│
   └──────┘                      └──────┴──────┴──────┘       │
   re-sign: a PIVOT produces        (A) FIX LOOP — back to the │
   a NEW intent hash, so it is      phase that OWNS the fix.   │
   a fresh P0, not a fix loop       NEVER back to P0.          │
                                                              │
                             (B) REFLECTION ◀──── task end ───┤
                             every role writes 3 lines →       │
                             framework/memory/retro.md         │
                                     │                         │
                                     │ a retro yields a        │
                                     ▼ framework change        │
                             (C) SELF-EVOLUTION ◀─────────────┘
                             proposal requirements 🔴 ▶ PR ▶
                             CI ▶ qa ∥ reviewer ▶ 🔴 CEO merge
                             (detail: SKILL.md § Phase ∞)
```

Only **A** can spin: it is the one that re-runs work. **B** is bounded by the
task ending, **C** by one review pass per proposal. So A is the only one carrying
a counter:

```
 (A) BOUND — tracked in the ledger, so it survives a compaction
     attempt 1 ──▶ 2 ──▶ 3 ──▶ is the failure count DROPPING?
                              ├─ yes ──▶ keep going, ceiling 5 total
                              └─ no  ──▶ STOP · escalate 🔴 CEO
                                         with the specific blockers
     "3 on the same gate" means 3 stalled attempts, not 3 attempts.
     Progress buys more tries; spinning in place does not.
```

| Loop | Fires when | What it does | Bound |
|---|---|---|---|
| **A. Fix loop** | a gate FAILS (QA / Security / Auditor / build) | re-runs the phase that owns the fix | the 3/5 counter above — the only loop that needs one |
| **B. Reflection** | end of every task, and on the meta-review | each role writes a retro; repeated failure modes become a self-improvement proposal | the task ending. The meta-review is a scheduled `cron`, not an open loop |
| **C. Self-evolution** | a retro yields a framework change | 🔴 signed `proposals/<slug>/requirements.md` → PR → CI → qa ∥ cross-vendor reviewer → 🔴 CEO merge | one pass per proposal; the verdict is terminal for that round |

## 4. Budgets (the other stop condition)

Every run carries ceilings, checked by the orchestrator before each heavy step
(a host resource check first on a memory-tight host):

- **Step/attempt budget**: Loop A's 3/5 rule above.
- **Fan-out cap**: never more parallel role agents than the host can hold
  (serialize on a tight host; a wide wave only when resources are ample).
- **Token/time budget**: a run that blows its budget STOPS and reports to the
  CEO rather than pressing on. State the budget when a run starts.
- **Cost awareness**: on a host that bills for compute, a long-idle run should be
  paused, not left spinning.

## 5. The contracts — who produces what, who reads it

Roles never hand each other a paraphrase; they hand over a **file path**. This is
the artifact graph, and it is the only interface between roles. 🔒 marks the two
files that are hash-locked:

```
 PRODUCED AT      THE CONTRACT                        READ BY
 ───────────      ────────────                        ───────
 P0 🔴  ────────▶ requirements.md            🔒 intent  every later role
                  R1..Rn · N1..Nn · an acceptance      (handed the path AND
                  clause each · Scope:                  the expected hash)
                        │
 P1 🔴  ──────┬───┴───▶ design.md                      frontend · backend · qa
              │         ADRs · Rn→design map ·
              │         design-stage threat model
              │
              └──────▶ standards.md          🔒 standards  devops · release ·
                        deploy envs · API style · DB ·      auditor · qa ·
                        compliance · efficiency budget      frontend · backend
 P2 🔴  ────────▶ design-system.md + the CHOSEN prototype   frontend
                  tokens · IA · a11y   (the prototype IS the visual spec)
 P3     ────────▶ one PR per role, naming `Closes Rn`    qa · security · auditor
 P4     ────────▶ verdict YAML (QA · Security · Auditor) orchestrator → the gate
 P5     ────────▶ production smoke evidence                release
 P6 🔴  ────────▶ signed artifact + channel/review evidence the CEO
```

Note the fan-in at P4: all three verifiers read the **same** delivered diff and
none reads another's output — that is what lets them run in parallel, and why
their verdicts are independent.

### How drift is actually caught

"The intent contract is supreme" is enforced mechanically, not by vibes. Both
hashes are recorded at their 🔴 sign-off and re-checked at every gate downstream:

```
  P0 ─── P0.5 ── P1 ─── P2 ─── P3 ─── P4 ─── P5 ─── P6
  │              │
  │ CEO signs 🔴 │ CEO signs 🔴
  ▼              ▼
 record         record              the ledger holds both hashes, so the
 INTENT hash    STANDARDS hash      check still works after a compaction
  │              │
  ╞══════════════╪═ re-read the file, re-compute, compare ═══════════▶
                 │      ✓       ✓      ✓      ✓      ✓
                 │
                 └─▶ mismatch, and no fresh 🔴 sign-off?
                     = DRIFT FAILURE → halt and ask the CEO to re-sign.
                       Not a warning. The run does not build on a moved target.
```

A deploy target, API shape or compliance rule that wandered from the signed
`standards.md` is the same class of failure as a changed requirement — both halt.

## 6. Three kinds of state (do not confuse them)

The system writes to three stores with different lifetimes, owners and readers.
Most confusion about "where does that live?" is these three being conflated:

```
┌─ CONTRACTS · per project, the INTERFACE ─────────────────────────┐
│  requirements.md · design.md · standards.md · design-system.md   │
│  written by  the role that owns the phase, at its gate           │
│  read by     downstream roles (by PATH, never paraphrased)       │
│  lifetime    the project. Versioned in the product repo.         │
│  authority   SUPREME — a gate fails if output drifts from these  │
└──────────────────────────────────────────────────────────────────┘
┌─ LEDGER · per run, the PROGRESS ─────────────────────────────────┐
│  goal · phase · gate status · next step · intent+standards hash  │
│  · Loop-A attempt counts · requirement→PR→test map · tech debt   │
│  written by  the orchestrator ONLY (roles do not bookkeep)       │
│  read by     the orchestrator after a compaction or restart      │
│  lifetime    the run. Stored by the host's ledger (hosts/)       │
│  authority   the resume point — without it, bounds reset to 0    │
└──────────────────────────────────────────────────────────────────┘
┌─ MEMORY · across runs, the EXPERIENCE ───────────────────────────┐
│  framework/memory/{lessons,adr,retro}.md                         │
│  written by  the orchestrator (retros and lessons)               │
│  read by     11 of the 12 roles, mounted read-only               │
│  lifetime    forever, across projects. Append-only.              │
│  authority   advisory — it informs judgment, it does not gate    │
└──────────────────────────────────────────────────────────────────┘
```

A compaction wipes the context, not these. That is the whole point of writing
them down: the ledger restores *where we were*, the contracts restore *what we
agreed*, memory restores *what we learned last time*.

### Who mounts memory — and the two deliberate holes

```
  framework/memory/  ──mounted read-only──▶  orchestrator · analyst
  lessons · adr · retro                      architect · designer · frontend
        ▲                                    backend · qa · security · auditor
        │ appends                            devops · release      (11 roles)
        │
  orchestrator ◀── 3-line retro per role that ran
        after EVERY task. No retro written = the task is NOT closed.

  ✘ reviewer  — memory: none, ON PURPOSE (invariant 4). A self-evolution
                review is only unbiased if it does not share the team's
                memory. Verified at install on every host.
  ✘ auditor   — mounts memory, but holds NO write/edit tool (invariant 7).
                An auditor that can fix its own findings audits itself.
```

Both holes are capabilities the install step must *withhold*, so each host
adapter verifies them rather than assuming the frontmatter was honoured.

## 7. Where the harness lives in the code

| Harness concern | Where it is written |
|---|---|
| Contract schema + templates | `framework/skills/aidlc/contracts/` |
| Standards single-source-of-truth (deploy/API/DB/compliance/…) | `contracts/standards.template.md` → per-project `standards.md` (standards hash) |
| Gate rules, loop bounds, budgets | `framework/skills/aidlc/SKILL.md` |
| Scope routing (which phases run) | `framework/skills/aidlc/SKILL.md` + `requirements.md` `Scope:` |
| Structured verdict schemas | `framework/skills/aidlc/contracts/verdicts.template.md` |
| Deterministic sensors (per gate) | `framework/skills/aidlc/SKILL.md` + each gate role |
| Traceability (requirement→PR→test) | `Closes Rn` markers + orchestrator ledger |
| Architecture-change guard (re-review + human escalation) | `framework/skills/aidlc/SKILL.md` + `architect` |
| Platform strategy gate (app/mobile) | `framework/skills/aidlc/SKILL.md` Phase 0 |
| Role behavior (the "who") | `framework/agents/*.md` |
| Shared experience (feeds reflection loop) | `framework/memory/` |
| Durable state (survives restart) | the host's ledger primitive, mapped per host in `hosts/<host>.md` |
| Self-evolution gate | `proposals/<slug>/requirements.md` + CI (`tools/check_neutral.py`, `tools/check_repo.py`, `.github/workflows/`) + `qa` + `reviewer` + CEO merge |
| Cross-host install | `AGENTS.md` + `hosts/` |

## 8. Reviewer availability fallback

The self-evolution reviewer needs a cross-vendor model (dev=Anthropic →
reviewer=strongest OpenAI). If no other-vendor model is available on the host at
review time, the harness does **not** silently skip the gate: it either (a)
falls back to an adversarial `llm-council` pass across whatever distinct models
ARE available, or (b) if none, HOLDS the change unmerged and tells the CEO the
review gate cannot run — a held change is never auto-merged.

## 9. When the host runs more than one session

Everything above draws **one** orchestrator on the spine. That is true of the
flow and false of the runtime on any host where the human can open a second
window — and the human will, because one session is slow and its context window
is small. Two windows then produce two Phase-0 contracts for one intent, or two
sessions working the same card, or one session deciding another is dead and
overwriting live work. All three have happened in a real repo that had the rule
written down.

The layer that repairs it is `framework/session-governance.md`: the role is taken
by an `O_EXCL` lock, the lock's mtime is a lease refreshed every turn, takeover
after a stale lease goes through `rename` (two processes can both `rm`; exactly
one can `rename`), and a human can pin the role to suspend the election — never
the other way round. Its defining constraint is that **no human input may be
required per session**, which is why it is wired to host lifecycle events rather
than written as a rule in the prompt: a rule the model must remember to run is
not a mechanism.

| | Where |
|---|---|
| The concept, the decision tree, the non-goals | `framework/session-governance.md` |
| Reference implementation (stdlib, host-neutral) | `framework/tools/boot.py` |
| Claude Code wiring (4 lifecycle hooks + the output adapter) | `hosts/claude-code.md` § *Multi-session governance* |

It does **not** decide what to work on, and it does not reach a dispatcher that
lives outside the repo. It decides who may decide.
