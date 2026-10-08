# Host adapter — Mission Control

How to install the neutral `framework/` source into **Mission Control** (mc, the
Next.js agent command center: `github.com/MeisnerDan/mission-control`). Follow
this when `AGENTS.md` Step 1 resolved to Mission Control.

Mission Control is a different KIND of host from KiroCrew and Claude Code. There,
an agent dispatches. Here, **JSON files are the bus** and a background daemon
spawns `claude -p` per task. So the neutral `spawn` tool and the 🔴 CEO gate are
realized as *data*, not as tool calls.

**Read Step 0 before writing anything.** The most expensive mistake on this host
is installing into the wrong directory: it looks like it worked and changes
nothing the running app can see.

## Step 0 — resolve the live data directory

`mission-control/data/` in the repo is **seed/demo data**. The live directory is
resolved by `mission-control/src/lib/paths.ts`, in this order:

1. `MC_DATA_DIR` env var;
2. a `.mc-data-dir` file in the app root (`mission-control/`) holding the path;
3. `<app root>/data` — only if neither of the above exists.

Resolve it and use the answer everywhere:

```bash
cd <mc repo>/mission-control && npx tsx -e "import {DATA_DIR} from './src/lib/paths'; console.log(DATA_DIR)"
```

A pointer file means the workspace is **not** the mc repo — it is whatever product
repo owns that data dir (e.g. `~/Github/triptag/.mc`). That single fact decides
which of the two modes below you are installing.

## Step 0.5 — pick the mode (they are not interchangeable)

| | **Board mode** | **Daemon mode** |
|---|---|---|
| When | the live data dir lives inside another product repo (`.mc-data-dir` points out of the mc repo) | the mc repo IS the workspace (default `data/`) |
| Who dispatches | the interactive session (KiroCrew `spawn_run` / Claude Code `Task`) inside the **product** repo | the mc daemon (`mission-control/scripts/daemon/`) |
| What mc is | the CEO's board: backlog, 🔴 gate queue, inbox, ledger mirror, Field Ops | the whole runtime |
| Install devcrew into | the **product repo**, per `hosts/kirocrew.md` or `hosts/claude-code.md`, **plus** the mc registry mirror below | the mc repo, per the artifact list below |

Why board mode exists, and why you must not "improve" it into daemon mode for an
external product repo — three hard facts in mc's own code:

- `mission-control/scripts/daemon/runner.ts` spawns `claude -p … --output-format
  json`. That is
  **non-interactive**: a role cannot suspend mid-run and wait for the CEO, so a 🔴
  gate cannot be held *inside* a run (only *between* tasks — see the gate row in
  the mapping table).
- `runner.ts` / `run-task.ts` set `cwd` to `WORKSPACE_ROOT =
  path.resolve(__dirname, "../../..")` — **the mc repo root, always**. There is no
  per-project cwd. A daemon-spawned agent therefore never loads the product
  repo's `CLAUDE.md` (its rules, its freeze list) and starts in the wrong tree.
- `prompt-builder.ts` reads `.claude/commands/<id>/user.md` from the mc repo root
  too, not from the product repo.

So for an external product repo the daemon can run *bookkeeping* work, but it must
not run the devcrew roles. Register the roles anyway (the UI, `assignedTo`, the
decisions queue and the reports all key off the registry) and say so in the
`instructions` — see "Registry mirror" below.

## The three layers — and where every wire actually lives

Mission Control is the **runtime** (it owns dispatch, prompts, durable state, the
CEO's UI). devcrew is the **flow** that runs on top of it (phases, roles, gates,
contracts). Between them is a thin **adapter layer that is not a process**: half of
it is a one-time install transform (file → file), the other half is a data
convention that mc's own functions then enforce for free.

```text
┌─ L3 · devcrew — the AIDLC flow ───────────────────── source: ~/Github/devcrew┐
│                                                                              │
│  P0 ─🔴→ P0.5 ─🔴→ P1 ─→ P2 ─🔴→ ┌ frontend ┐→┌ qa       ┐→ P5 ─→ P6 ─🔴→ P∞ │
│  intent  market    arch  design  └ backend  ┘ ├ security ┤  deploy  release  │
│                                               └ auditor* ┘  (*big diffs only)│
│                                                                              │
│  12 roles   framework/agents/<role>.md          the role's system prompt     │
│  protocol   framework/skills/aidlc/SKILL.md     phases · gates · harness     │
│  contracts  framework/skills/aidlc/contracts/*.template.md                   │
│  memory     framework/memory/{lessons,adr,retro}.md                          │
│                                                                              │
│  Host-neutral: knows nothing about JSON files, daemons, tasks or decisions.  │
└──────────────────────────────────────────────────────────────────────────────┘
        │                                             ▲
        │ (A) INSTALL-TIME TRANSFORM — run once,      │ (C) Phase ∞ writes back:
        │     by you, following THIS file             │     retro → proposal 🔴
        ▼                                             │     → PR, no self-merge
┌─ L2 · adapter · "middleware" ─────────── this is the layer this file defines ┐
│                                                                              │
│ (A) install transform — which file becomes which                             │
│   framework/agents/<role>.md   ──body──▶ <DATA_DIR>/agents.json .instructions│
│                                ──head──▶ .claude/agents/<role>.md  (run repo)│
│   hosts/aidlc-mission-control.skill.md ▶ <DATA_DIR>/skills-library.json      │
│                                          skill_devcrew_aidlc .content        │
│   framework/skills/aidlc/**    ────────▶ <run repo>/.claude/skills/aidlc/**  │
│   framework/memory/*.md        ────────▶ <run repo>/devcrew-memory/*.md      │
│   (optional mirror, NOT the prompt path: sync-commands.ts →                  │
│    .claude/commands/<role>/user.md, skills/<skill-id>/SKILL.md)              │
│                                                                              │
│ (B) run-time convention — the harness encoded as JSON fields                 │
│   phase order   ▶ tasks.json .blockedBy        enforced by isTaskUnblocked() │
│   dispatch      ▶ tasks.json .assignedTo       → the registry id             │
│   🔴 CEO batch  ▶ decisions.json {status:pending, taskId} — an open batch    │
│                   (intent·design·ship) or one of the five interrupts         │
│                                              enforced by hasPendingDecision()│
│   gate answer   ▶ decisions.json {status:answered, answer} → the next prompt,│
│                                              via buildRetryContext()         │
│   definition-of-done ▶ tasks.json .acceptanceCriteria[]  ← each Rn           │
│   intent/std hash ▶ tasks.json .notes   (sha256 of the signed contract)      │
│   ledger       ▶ TASKS.md in the run repo; missions.json .taskHistory MAY    │
│                  mirror it (buildRestartContext) — TASKS.md wins             │
│   loop bound   ▶ TASKS.md n/5 (stalled k/3), enforced by check_tasks.py      │
│   budgets       ▶ daemon-config.json .execution / .concurrency               │
│   outward act   ▶ field-ops/tasks.json {approvalRequired:true}               │
│   contracts    ▶ real files in the run repo (.aidlc/…); the path is in .notes│
│                                                                              │
│  Nothing here runs. (A) is done once at install; (B) is just the shape of the│
│  rows you write — mc's functions do the enforcing.                           │
└──────────────────────────────────────────────────────────────────────────────┘
        │ reads / writes                              ▲ CEO answers, reads it
        ▼                                             │
┌─ L1 · Mission Control — the runtime ───── repo: ~/Github/mission-control ────┐
│                                                                              │
│  src/lib/paths.ts → DATA_DIR = MC_DATA_DIR ⇢ .mc-data-dir ⇢ <app root>/data  │
│      └── THE JSON BUS: tasks · decisions · missions · inbox · activity-log · │
│          agents · skills-library · daemon-config · field-ops/                │
│                                                                              │
│  Next.js UI ─ Board · Decisions(🔴 queue) · Inbox(reports) · Field Ops ─▶ CEO│
│                                                                              │
│  daemon  mission-control/scripts/daemon/                                     │
│   scheduler.ts ─▶ dispatcher.ts ──┬ isTaskUnblocked()     ─ blocked? skip    │
│                                   └ hasPendingDecision()  ─ 🔴 open? skip    │
│        │ passes both                                                         │
│        ▼                                                                     │
│   prompt-builder.ts  buildTaskPrompt(agentId, task, missionId)               │
│     ① persona   = agents.json .instructions + every linked skill .content    │
│                   (link resolves BOTH ways: agent.skillIds ∥ skill.agentIds) │
│     ② fieldOps  = only if linked to skill_field_ops                          │
│     ③ restart   = buildRestartContext(missionId)  ← missions.json taskHistory│
│     ④ retry     = buildRetryContext(taskId)       ← the CEO's decision answer│
│     ⑤ task      = title · description · subtasks · acceptanceCriteria · notes│
│                   (so .notes IS read by the role — that is why the contract  │
│                    path and the intent/standards hash belong there)          │
│     ⑥ SOP       = "do NOT do your own bookkeeping"                           │
│        │  one string, ≤100 KB                                                │
│        ▼                                                                     │
│   security.ts   ALLOWED_BINARIES = claude* · MAX_PROMPT_LENGTH · stripped env│
│        ▼                                                                     │
│   runner.ts     spawn: claude -p <prompt> --output-format json --max-turns N │
│                 cwd = WORKSPACE_ROOT = the mc repo root, ALWAYS              │
│        ▼ stdout                                                              │
│   run-task.ts   writes task status · inbox report · activity event ·         │
│                 missions.taskHistory · a decision point at 3 failed attempts │
└──────────────────────────────────────────────────────────────────────────────┘
```

Read the diagram as: **L3 never names an L1 file.** Every arrow that crosses the
gap is either an install artifact or a JSON field — that is the whole integration.
The per-concern detail behind (B) is the dispatch-contract table below.

### Where the picture changes in board mode

In **daemon mode** the drawing above is the whole system. In **board mode** the
live `DATA_DIR` belongs to a product repo, so the L1 dispatch column is deliberately
**cut** — because `cwd` is pinned to the mc repo and `claude -p` cannot hold a 🔴
gate:

```text
   L3 devcrew flow ── installed into ──▶ the PRODUCT repo
                                         .claude/agents/ · .claude/skills/aidlc/
                                         .aidlc/ (contracts · memory) · TASKS.md
                                              │
        the interactive session in that repo dispatches the roles
        (Claude Code `Task` / KiroCrew `spawn_run`)
                                              │
                            reads + writes the same JSON bus
                                              ▼
   L1 Mission Control ── DATA_DIR = <product repo>/.mc ─── mc = the CEO's BOARD
        UI: Board · Decisions(🔴) · Inbox · Field Ops                  ✔ used
        daemon: scheduler → dispatcher → runner → claude -p           ✘ MUST NOT
                                                                      run roles
```

Same bus, same JSON conventions, same 🔴 gate rows — only the *dispatcher* moves
from the daemon to the interactive session. The durable authority is the same
in both modes: the product repo's `TASKS.md` (mc mirrors it).

## Known degradation on this host

State these in the install report; a degraded gate must say "degraded, because X"
in every report, not quietly pass.

- **Cross-vendor reviewer is impossible.** `security.ts` allows only the `claude`
  binary and there is no per-agent model field, so invariant 4's "review on a
  different model family" cannot run from mc. Per `ARCHITECTURE.md` §8: review the
  self-evolution PR on a host that can (KiroCrew), or **HOLD it unmerged** with a
  pending decision telling the CEO the gate cannot run. A held change is never
  auto-merged. The `reviewer` still mounts **no** team memory.
- **No interactive 🔴 gate inside a run** (daemon mode) — gates only exist between
  tasks, via the pending-decision mechanism above. A phase whose gate must be held
  mid-run belongs in board mode.
- **No per-project cwd** — see Step 0.5. Board mode is the answer, not a workaround.
- **The `auditor`'s read-only guarantee is instruction-only in daemon mode.**
  `agents.json` has no per-agent tool allowlist, so nothing mechanically stops the
  auditor from editing code the way the Claude Code artifact's `tools:` line does.
  Compensate: state the prohibition at the TOP of its `instructions`, keep the
  `.claude/agents/auditor.md` form tool-restricted (that is what a manually
  launched run uses), and assign the fix task to the implementing role — never to
  `auditor`. Say "degraded, because mc has no per-agent tool allowlist" in the
  install report.

## What Mission Control expects

- **Agent registry**: `<DATA_DIR>/agents.json` — `{ agents: [{ id, name, icon,
  description, instructions, capabilities, skillIds, status, createdAt,
  updatedAt }] }`. `instructions` IS the prompt the daemon injects (max 20 000
  chars). `id` must match `^[a-z0-9-]+$` (≤ 50). `icon` must be one of the Lucide
  names registered in `mission-control/src/lib/agent-icons.ts` — `User, Search,
  Code, Megaphone, BarChart3, Bot, Brain, Palette, Shield, Database, Globe,
  Wrench, BookOpen, HeartPulse, Scale, Briefcase`. An unregistered name is not an
  error — `getAgentIcon()` silently falls back to `Bot`, so every role you gave a
  made-up icon looks identical on the board. Give each role a distinct registered
  name.
- **Skill library**: `<DATA_DIR>/skills-library.json` — `{ skills: [{ id, name,
  description, content, agentIds, tags }] }`. `content` (max 50 000) is injected
  **verbatim** into every linked agent's prompt; `agentIds` holds ≤ 20 entries.
  The link is resolved from **both** directions (`prompt-builder.ts`:
  `agent.skillIds.includes(skill.id) || skill.agentIds.includes(agent.id)`), so a
  role listed on only one side is still linked — do not "fix" the other side.
- **Generated command files**: `.claude/commands/<agent-id>/user.md` +
  `skills/<skill-id>/SKILL.md`, produced from the registry by
  `mission-control/src/lib/sync-commands.ts`. **They are NOT how a role gets its
  prompt.** `buildTaskPrompt()` assembles the prompt from `agents.json` +
  `skills-library.json` directly; `COMMANDS_DIR` is read only by
  `buildScheduledPrompt(command)` (the scheduled `daily-plan` / `standup` runs) and
  by a human typing `/<agent-id>` in Claude Code. So they are a convenience mirror:
  nice to have, never the authority. If you generate them, use mc's own generator —
  `syncAgentCommand(agent)` per devcrew role and `syncSkillFile(skill)` for the
  devcrew skill only. Never `syncAllSkillFiles()`: it fans every pre-existing demo
  skill out into new untracked `skills/<skill_id>/` directories.
- **Execution** (daemon mode): `scheduler` → `dispatcher` → `runner` spawns
  `claude -p <prompt> --output-format json --max-turns N`. `security.ts` hard-limits
  the binary to `claude*` (`ALLOWED_BINARIES`) and the prompt to 100 KB, and strips
  the environment down to PATH/HOME/temp + `CLAUDE_CODE_OAUTH_TOKEN`.
- **No per-agent model.** `agents.json` has no model field and the daemon can only
  spawn `claude`. Do not invent a `model` key — it is silently ignored.
- **Data is the only bus**: `tasks.json`, `decisions.json`, `inbox.json`,
  `missions.json`, `activity-log.json`, `field-ops/`. Roles are told NOT to do
  their own bookkeeping: the daemon writes task status, the inbox report and the
  activity event from the agent's final summary.

## Neutral → Mission Control mapping

| Neutral tool | Mission Control realization |
|---|---|
| read | `Read`, `Grep`, `Glob` (`daemon-config.json` → `execution.allowedTools`) |
| write / edit | `Write`, `Edit` |
| shell | `Bash` |
| search | `Grep`, `Glob` |
| web | `WebSearch`, `WebFetch` |
| **spawn** | **not a tool.** Daemon mode: append a task with `assignedTo` + `blockedBy` and the daemon spawns it. Board mode: the interactive session's own subagent tool, with mc holding the plan. `Task` is off in a daemon run unless `execution.agentTeams` is true. |
| **memory** | `Read`/`Write` of the memory files in the workspace (mc has no memory mount): `devcrew-memory/*.md` in daemon mode, the product repo's existing memory dir in board mode |
| structured question | a `decisions.json` pending row with `options` (daemon mode); the interactive session's own question tool (board mode) |
| browser preview | a headless-browser screenshot, as on Claude Code; mc has no preview panel |
| host resource check | none as a tool: `concurrency.maxParallelAgents` in `daemon-config.json` is the fan-out cap |

`model: best-available` → whatever the `claude` CLI is configured to use; record the
intent in `description` if the CEO needs to know. `reviewer`'s
`model: cross-vendor-from-author` **cannot be honored on this host** — see the
degradation section.

## Artifacts to generate

For each `framework/agents/<name>.md`:

1. **Registry entry** appended to `<DATA_DIR>/agents.json`:
   - `id` = the neutral `name` (prefix it, e.g. `devcrew-<name>`, only if the data
     dir already holds unrelated agents whose ids would collide — and then keep the
     prefix consistent across `tasks.json` `assignedTo`, `inbox` `to`/`from` and
     `decisions` `requestedBy`, or you orphan existing rows);
   - `name` = neutral `role`; `description` = neutral `description`; `icon` = a
     registered Lucide name; `status` = `"active"`;
   - `instructions` = the dispatch contract (below) + the neutral body, or — in
     board mode — a short pointer block naming the **absolute path** of the role
     file in the product repo as the authority (cwd is not that repo);
   - `capabilities` = short phrases from the body;
   - `skillIds` = the devcrew AIDLC skill, plus `skill_field_ops` for the roles
     that legitimately act on the outside world (`devops`, `release`).
2. **`.claude/agents/<name>.md`** — the Claude Code form (`hosts/claude-code.md`),
   in the repo the roles actually run in: the product repo in board mode, the mc
   repo in daemon mode.
3. **`.claude/commands/<name>/user.md`** — mc's generator, per above (daemon mode;
   optional in board mode, where nothing reads them).
4. **Skill entry `skill_devcrew_aidlc`** in `<DATA_DIR>/skills-library.json`, whose
   `content` is `hosts/aidlc-mission-control.skill.md` (the AIDLC protocol
   translated to mc's bus), linked to every devcrew role id. It stays under the
   50 000-char cap and points at the installed `aidlc/SKILL.md` for the full text,
   because it is injected into every role prompt.
5. **`.claude/skills/aidlc/`** (+ the `mobile-*` skills if the product ships an
   app) — copy `framework/skills/…` into the repo the roles run in, so the full
   protocol and `contracts/` templates are readable in-workspace.
   `impeccable` (designer) is third-party: install it into the same repo the
   Claude Code way (`hosts/claude-code.md` § *Per-agent file to generate*,
   step 4, pinned version and hook review included), and verify it with
   `npx impeccable@4.1.0 detect <file>` (exit 0 clean,
   2 findings, 1 failed).
6. **Shared memory** — `framework/memory/*.md` into the workspace
   (`devcrew-memory/` if the repo has no memory dir yet).
7. **`CLAUDE.md`** of that repo — the devcrew section (roles, AIDLC flow, memory
   rule, the reviewer exception, the no-fake-data rule).
8. **The sensors** — `framework/tools/check_live.py`, `check_formal.py` and
   `check_tasks.py` → `.aidlc/tools/` in that repo, side by side (the last two
   import `check_live.py` from their own directory): no fake data, formal
   evidence per signed `Property:`, and a true `TASKS.md` (aidlc skill).

## The AIDLC dispatch contract on Mission Control

This is what makes the harness real here. Every generated `instructions` block
carries it, and the skill entry states it.

| Harness concern | Mission Control realization |
|---|---|
| Phase ordering | one task per phase in `tasks.json`; later phases carry `blockedBy: [<earlier task ids>]`. `isTaskUnblocked()` enforces the spine. |
| Dispatch | `assignedTo: "<role id>"` (daemon mode: the daemon picks it up in Eisenhower order; board mode: the interactive orchestrator reads the board and dispatches). |
| Parallel phases (P3 FE ∥ BE, P4 QA ∥ Security ∥ Auditor) | sibling tasks with the same `blockedBy`; `concurrency.maxParallelAgents` is the fan-out cap. |
| 🔴 CEO batch or interrupt | the CEO signs in three batches — intent, design, ship — and is otherwise stopped only by one of the five interrupts a machine raises; a judgment is a `Cn` checkbox in TASKS.md, never a pending row. Either is a `decisions.json` row `{ requestedBy, taskId: <the task the gate blocks>, question, options, context, status: "pending" }`. `hasPendingDecision()` refuses to dispatch that task until the CEO answers in the Decisions page, and `buildRetryContext()` feeds the answer back into the next prompt. **A role writes the pending row and ENDS ITS TURN — it never assumes a gate passed.** In a non-interactive daemon run this is the only suspension mechanism available. |
| Contracts | `requirements.md` / `design.md` / `standards.md` / verdict blocks as files in the product repo (e.g. `.aidlc/` or `projects/<slug>/aidlc/`); the task's `notes` names the path. Templates from the installed `aidlc/contracts/`. |
| Intent hash / standards hash | the `Signed:` line of `TASKS.md` (12 hex of `sha256` per signed file; also mirrored into the phase task's `notes`); `check_tasks.py` re-computes and compares at every step. Drift without a fresh sign-off → halt and raise a pending decision (interrupt `drift`). |
| Acceptance criteria | mirror each `Rn` into the task's `acceptanceCriteria[]`, so the prompt builder hands the gate its own definition of done. |
| Ledger (durable state) | `TASKS.md` in the run repo — Done · In progress · Todo, current state only, written by the orchestrator, checked by `check_tasks.py`. `missions.json` (`taskHistory`, `loopDetection.taskAttempts`) + `activity-log.json` + `inbox.json` MAY mirror it, and `buildRestartContext()` replays the mirror into the next prompt; when they disagree, TASKS.md wins. |
| Loop A bound | devcrew's bound is 3 stalled / 5 in total, written as `n/5` (`stalled k/3`) on the item's TASKS.md line — that is the bound `check_tasks.py` enforces. mc's own `MAX_LOOP_ATTEMPTS = 3` (`run-task.ts`) is a different, stricter per-task counter: it may stop a task first and open a decision point; it does not replace the TASKS.md count. |
| Budgets | `daemon-config.json`: `execution.maxTurns`, `timeoutMinutes`, `retries`, `maxTaskContinuations`, `concurrency.maxParallelAgents`. State them when a run starts instead of inventing ceilings. |
| Reporting | the agent's final stdout IS the inbox report. Do not write `inbox.json` / `activity-log.json` / task status — the daemon does, and double-writing corrupts the feed. |
| P5/P6 outward actions | Field Ops tasks (`field-ops/tasks.json`) with `approvalRequired: true`; the mission `autonomyLevel` + spend limits are the CEO's throttle. Posting, paying, publishing never go through raw `Bash`. |

## Verify

1. You wrote to the **resolved** `DATA_DIR` (re-run the Step 0 command and diff),
   and the pre-existing agents/skills in it are untouched.
2. `agents.json` and `skills-library.json` parse; every devcrew id is
   `^[a-z0-9-]+$`, `status: "active"`, `instructions` ≤ 20 000 chars, icons are
   registered names, the skill's `agentIds` ≤ 20.
3. Every id referenced by `tasks.json` `assignedTo`, `inbox` `to`/`from` and
   `decisions` `requestedBy` exists in the registry (no orphans after a rename).
4. The role files + `aidlc` skill + `contracts/` + memory exist in the repo the
   roles actually run in, and its `CLAUDE.md` has the devcrew section.
5. The reviewer artifact mounts no shared memory (grep it for the memory path),
   and the `auditor` artifact grants no write/edit tool (grep `.claude/agents/auditor.md`
   for `Write`/`Edit`).
6. `--self-test` of `.aidlc/tools/check_live.py`, `check_formal.py` and
   `check_tasks.py` each prints `self-test ok` in the repo the roles run in, and
   `shasum -a 256` of each installed copy equals the framework's (all 64 hex).
7. Regenerate the context snapshot (`pnpm gen:context`) so the dashboard and every
   prompt see the new roster.
8. Tell the CEO which mode is installed, that 🔴 gates appear in the **Decisions**
   page, and — in board mode — that role agents must not be launched from the mc
   Launch/daemon UI.
