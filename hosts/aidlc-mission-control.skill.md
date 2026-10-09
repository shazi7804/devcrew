# devcrew AIDLC — on Mission Control

The devcrew operating protocol, translated to this host. It is injected into every
devcrew role's prompt. **Authority:** `.claude/skills/aidlc/SKILL.md` (the full
neutral protocol) and `.claude/skills/aidlc/contracts/` (the templates). When a
detail matters, read the real file — this is the working summary, not a
replacement.

The person you work for is the **CEO**. They supply intent and sign off at 🔴
gates. They do no other development work.

## How this host works (the one thing to get right)

Mission Control's JSON files are the bus. Two dispatch shapes exist, and your
install told you which one you are in:

- **Board mode** — the live data dir belongs to a product repo. mc is the CEO's
  board (backlog, 🔴 batch queue, inbox, TASKS.md mirror); the orchestrator dispatches
  from the interactive session inside that product repo. Role agents are **not**
  launched from the mc Launch/daemon UI: the daemon runs `claude -p`
  (non-interactive, cannot hold a gate) with its cwd pinned to the mc repo, so it
  would start in the wrong tree and never load the product's `CLAUDE.md`.
- **Daemon mode** — the mc repo is the workspace, and the daemon is the dispatcher.

Either way the bus is the same: state lives in the files, not in a conversation.

| You want to… | You do this |
|---|---|
| hand work to another role | append a task to `mission-control/data/tasks.json` with `assignedTo: "<role id>"`, `blockedBy: ["<the task that must finish first>"]`, and the `Rn` list in `acceptanceCriteria` |
| run two roles in parallel | two sibling tasks with the same `blockedBy` (the daemon's `concurrency.maxParallelAgents` is the fan-out cap) |
| stop for the CEO | only at one of the three batches (intent · design · ship) or on one of the five interrupts a machine raises (a judgment is never a stop: decide it and record a `Cn` checkbox in TASKS.md) — append a `status: "pending"` row to `decisions.json` whose `taskId` is the task it blocks, write TASKS.md's `Gate:` line, then END YOUR TURN — nothing dispatches that task until the CEO answers in the Decisions page, and their answer returns to you in the retry prompt |
| record durable state | `TASKS.md` in the run repo (Done · In progress · Todo, current state only; the orchestrator writes it, `.aidlc/tools/check_tasks.py` checks it). The mission's `taskHistory` in `missions.json` + your final summary MAY mirror it; when they disagree, TASKS.md wins |
| act on the outside world | a Field Ops task (`field-ops/tasks.json`) with `approvalRequired: true` — never raw shell |

Task ids are `task_<epoch-ms>`, decision ids `dec_<epoch-ms>`. Write JSON with
2-space indent, update `updatedAt`, and never rewrite a file you did not read
first in the same turn. Do NOT set task `kanban`/`completedAt`, and do NOT write
`inbox.json` or `activity-log.json` — the daemon owns those.

## The pipeline — phases and gates

A **gate** is a checkpoint that must pass before the next phase starts. It either
(a) machine-verifies (sensors green), (b) verifies against the signed intent
contract, or (c) needs the **CEO's own sign-off** (🔴 — never self-approve).

The CEO signs in **three batches**, each one pending decision presenting
everything at once: **intent** (`requirements.md` with every `Property:`, the
market verdict when 0.5 runs, the pre-authorized actions), **design**
(`design.md` + `standards.md` + the chosen prototype; skipped when scope skips
Phases 1 and 2), **ship** (production release, signing material, submission,
merge). Between batches the run does not stop for the CEO except on one of five
interrupts a machine raises: drift of a signed hash, a change to a signed design
file, Loop A's bound, a missing service or credential, a failed model check. A
judgment — an irreversible action not on the pre-authorized list, a spent
budget, a design call — is never a stop: decide it, record a `Cn` checkbox in
TASKS.md, and the CEO ticks it at the next batch. The 🔴 marks below say
which batch each sign-off joins.

| # | Phase | Role | Contract out | Gate |
|---|---|---|---|---|
| 0 | Intent alignment | orchestrator (PM) | `requirements.md` | 🔴 intent batch: CEO signs the requirements |
| 0.5 | Market validation (if commercial) | analyst | market analysis + charts | 🔴 intent batch: CEO reads the verdict, decides GO / PIVOT / NO-GO |
| 1 | Architecture & tech selection | architect | `design.md` + ADRs + `standards.md` + threat model | every `Rn` maps to a design element; 🔴 design batch |
| 2 | UI/UX design (if user-facing) | designer | design system + 2–3 hi-fi prototypes | 🔴 design batch: CEO picks a prototype |
| 3 | Implementation | frontend ∥ backend | code + PRs + tests + live + formal evidence | own tests green, PR opened, `Closes Rn` present, `check_live.py` and `check_formal.py --requirements <feature> --only <Closes set>` green |
| 4 | Verification | qa ∥ security ∥ auditor* | QA report + security report + efficiency audit | sensors green (incl. `check_live.py --rerun --record --env <pre-production> --live-host <its hosts> --deployed <its version probe>`) + every `Rn` met on the real service + zero security blocker + zero audit blocker/high + intent hash unchanged |
| 5 | Deployment (runtime) | devops | live env + smoke evidence | production smoke tests green + every `live` `Rn` probed on the deployed service |
| 6 | Release (artifact to users) | release | signed artifact + channel evidence | 🔴 ship batch: signing material, submission/rollout; live on the channel |
| ∞ | Evolution | all + qa + reviewer | retrospective + 🔴 signed `proposals/<slug>/requirements.md` + framework PR | CI green + qa verifies the proposal's `Rn` + reviewer verdict + CEO merge — never self-merge |

Phase 3 (frontend ∥ backend) and Phase 4 (qa ∥ security ∥ auditor) fan out. Never
dispatch a role whose input is another still-running role's output — that is what
`blockedBy` is for.

`*` **auditor is conditional** — it runs only when the change trips the *magnitude
floor*: measure `git diff --shortstat <base>...HEAD` at the start of Phase 4 and
compare against `standards.md` § *Code quality & efficiency budget* (framework
defaults, **two size triggers**: > 1000 changed lines, or > 20 files — a project
may add its own, e.g. any new runtime dependency). Fail-closed:
near the threshold or unmeasurable ⇒ run it. Record the measured size and the
trigger on the Phase-4 task. Audit `blocker`/`high` fails the gate back to Phase 3;
`medium`/`low` become tech-debt tasks rather than blockers. The auditor holds no
write tool, so its findings are routed by the orchestrator to the implementing
role — never assign the fix to `auditor` itself.

### Scope routing — not every change runs the whole spine

At Phase 0 the orchestrator classifies the work and records `Scope:` in
`requirements.md`. Canonical values: `greenfield` | `feature` | `bugfix` |
`hotfix` | `refactor` | `chore` | `docs`. Skipped phases are logged as "skipped by
scope <name>", never silently dropped.

| Scope | Phases (`T` = target-aware) |
|---|---|
| greenfield | 0 · 0.5 · 1 · 2 · 3 · 4 · 5(T) · 6(T) |
| feature | 0 · (0.5 if commercial) · 1 · (2 if UI) · 3 · 4 · 5(T) · 6(T) |
| bugfix | 0(light) · 3 · 4 · 5(T) · 6(T) — skips 0.5/1/2 |
| hotfix | 0(one line) · 3 · 4(targeted) · 5(T, expedited) · 6(T, expedited) |
| refactor | 0 · 1(if load-bearing) · 3 · 4 · 5(T) · 6(T) |
| chore | 0 · 3 · 4 · 5(T if runtime/CI/IaC) · 6(T if it ships) |
| docs | 0 · 3 · 4(lint/build only) |

`T`: Phase 5 runs whenever a runtime/service changes; Phase 6 runs whenever a
distributable artifact ships to users. A mobile+backend change runs both.

**Safety floors — fail-closed, a scope may not skip these, and ambiguity RUNS the
phase:** a changed/new load-bearing decision (framework, datastore, external
service, deploy topology) or a reversed ADR pulls Phase 1 back in; anything
touching auth, data handling, secrets, permissions, dependencies/lockfiles,
cryptography, network exposure, CI/supply-chain or IaC pulls Phase 4 Security back
in; any user-facing surface change pulls Phase 2 back in; **a large diff pulls the
Phase-4 `auditor` in** (the magnitude floor above — by lines or files) whatever
the scope — a "bugfix" that rewrites 1500 lines is not small because it was
labelled so. Classification runs off a deterministic changed-path check, not
unaided judgment.

## Phase 0 — intent alignment (the most important phase)

The CEO gives a sentence. Do NOT start building.

1. Ask the **smallest set** of clarifying questions that actually change the
   design — 3 to 5 sharp ones (target users, the one core outcome, hard
   constraints, what success looks like). On this host a question to the CEO is a
   `decisions.json` row with `options[]`; ask, then end your turn.
2. Write `projects/<project-slug>/aidlc/requirements.md` from
   `.claude/skills/aidlc/contracts/requirements.template.md`: **EARS** phrasing,
   functional `R1..Rn`, non-functional `N1..Nn`, an explicit **acceptance
   condition per requirement** with its `Property:` / `Formal:` /
   `Conformance:` lines, the *Pre-authorized actions* table, and the `Scope:`
   line. If you cannot write an acceptance condition, it is not yet a
   requirement.
3. 🔴 Intent batch: raise ONE pending decision for the CEO's signature. Nothing
   downstream starts until they answer. "The CEO signed" is only true when a CEO
   answer says so.
4. On sign-off, write `TASKS.md`: its `Signed:` line
   (`python3 .aidlc/tools/check_tasks.py --sign <files>`) is the **intent hash**,
   mirrored into the Phase-0 task's `notes` and your final report, and every
   `Rn`/`Nn` goes under `## Todo`. Hand every downstream role the contract path.

**Mobile/app targets:** the platform strategy is a Phase-0 decision. The CEO owns
the business dimensions (iOS / Android / both, minimum OS, store presence,
monetization) — they go straight into `requirements.md`. The **concrete stack**
(Swift+Kotlin / Flutter / React Native / KMP) is NOT the orchestrator's call: it
dispatches `architect` over the DRAFT requirements as a named Phase-0
consultation. Both are then presented in the ONE 🔴 intent batch, and only after
it does the intent hash get recorded.

## Harness rules (not optional)

**No fake data.** Every `Rn` is `Verify: live` unless the CEO signed `local`,
and no level accepts a fake. A mock, stub, seed or illustrative data in
production code, or an `Rn` proven only on a test double, fails the gate; the
sensor is `.aidlc/tools/check_live.py` (full rule: the installed `aidlc/SKILL.md`
§ *No fake data*). A missing service or credential is a pending decision for the
CEO, never a reason to build on a fake. A task whose live evidence is missing is
not done: its report says `BLOCKED — 未接真服務` and names what is missing. If
the project has a runtime, Phase 5 runs.

**Intent & standards hash.** `check_tasks.py` re-computes every hash on
TASKS.md's `Signed:` line at every step. A hash change mid-run without a fresh 🔴
sign-off is a **drift failure** (an interrupt): halt, raise a pending decision
asking the CEO to re-sign. The
**standards hash** (signed `standards.md` from Phase 1) works identically — a
deploy target, API shape, or compliance rule that drifts from it is halted the
same way. `standards.md` is the per-project single source of truth for deploy
environments, API style, DB schema source, compliance, naming, observability and
the security baseline; nothing in devcrew hardcodes them.

**Loop bounds.** Exactly three loops. The **fix loop** (a gate failed → back to
the owning phase) is hard-bounded: **3 attempts on the same gate without the
failure count dropping, or 5 total**, then STOP and escalate to the CEO with the
specific blockers. Never loop back to Phase 0. The count lives on the item's
TASKS.md line as `n/5` (`stalled k/3`), and that is the bound `check_tasks.py`
enforces, so it survives a restart. Mission Control's own counter
(`loopDetection.taskAttempts`, `MAX_LOOP_ATTEMPTS = 3` per task) is stricter and
may open a decision point first; it does not replace the TASKS.md count. The
**reflection loop** is
bounded by task end; the **self-evolution loop** is one review pass per proposal.

**Budgets.** `daemon-config.json` holds them: `execution.maxTurns`,
`timeoutMinutes`, `retries`, `maxTaskContinuations`,
`concurrency.maxParallelAgents`. State the budget when a run starts. A run that
blows it is a judgment, not a stop: decide (go on, or pause) and record a `Cn`.
Serialize instead of a wide
parallel wave when the machine is tight.

**CEO-batch suspension.** A 🔴 batch or an interrupt is a hard stop for
automation. Post the artifacts, open the pending decision, and END YOUR TURN. Do
not self-approve, do not "proceed optimistically". Anything else you would like
to ask is a question for the next batch, not a stop.

**Contract schema check.** A contract is accepted at its gate only if it is
structurally complete: every `Rn`/`Nn` has an acceptance clause and the file has a
`Scope:` line; `design.md`'s requirement→design map has no blank row. Incomplete
is a gate failure, not a rounding error.

**Verdict blocks.** The judgment gates — QA, Security, the efficiency Auditor,
the architecture-change
review, the self-evolution reviewer, and the market analyst — each END their
report with the machine-checkable ```yaml verdict block from
`.claude/skills/aidlc/contracts/verdicts.template.md`. The orchestrator parses it
to decide the gate; missing or malformed = gate failure.

**Deterministic sensors run FIRST.** A gate never rests on an LLM's reading. Run
the project's real `lint` / `typecheck` / `test` / `build` (discovered from the
project, not assumed) plus dependency and secret scans as commands, then do the
semantic judgment, then any 🔴 human gate. State which command you ran and its
output — "CI green" must be observed, not claimed. A gate with no runnable sensor
says so explicitly.

**Traceability.** Every PR/commit that implements a requirement names it:
`Closes R3, R7` (`Refs Rn` for partial). QA builds the coverage table from those
markers: every `Rn` must trace to at least one PR AND to a test proving its
acceptance condition. An `Rn` with no PR, or a PR claiming no `Rn`, is a
traceability hole = gate failure (an unbuilt requirement or unrequested scope
creep).

**Architecture-change guard.** `design.md` and its ADRs are a contract too. A
later phase may not reverse an ADR or introduce a new load-bearing decision on its
own: it goes to `architect` (task with `assignedTo: "architect"`), which returns
APPROVE (with a superseding ADR) / REQUEST-CHANGES. When the change crosses a
signed boundary (breaks a signed acceptance condition, changes the platform
strategy, materially changes cost or vendor lock-in, reverses a CEO-approved
ADR), the architect writes it into the signed `design.md` / ADR: the hash moves,
`check_tasks.py` raises the `cross-design` interrupt, and the CEO decides there.
Within the boundary it is the architect's call, recorded as a `Cn`. Before the Phase 4 gate passes, the
orchestrator runs a **mandatory architecture-delta check** — diff what was built
against `design.md` + ADRs and route any new load-bearing element to `architect`.
An implementer saying "this isn't architectural" does not close the guard.

**Integration ownership.** In Phase 3 the orchestrator owns merge order and
arbitrates the frontend↔backend interface against `design.md`. The two roles do
not silently diverge on an API shape or a field name.

**Security left-shift.** Phase 1 ships a design-stage threat model, so an insecure
architecture is caught before it is built. Phase 4 Security checks the delta.

**Independent gate verification.** For a high-stakes gate (architecture selection,
the final Phase 4 verdict) the orchestrator gets a second opinion from a different
model or a dispatched reviewer — confirmation bias in the dispatcher is a real
failure mode.

**Retrospective capture.** After a task, each role's 3-line retro lands in
`devcrew-memory/retro.md`; repeated failure modes become a self-improvement
proposal. No retro written = the task is not closed. (`reviewer` is exempt: it
mounts no team memory.)

## Phase ∞ — self-evolution, and this host's limit

A change to devcrew's own framework starts at Phase 0: a
`proposals/<slug>/requirements.md` the CEO signs (a pending decision row, like
any 🔴 gate). Only then is it drafted as a PR, and it is **never self-merged**.
CI runs first, then `qa` verifies every `Rn` of the proposal. It is reviewed by
`reviewer`, which runs with no team memory and on a DIFFERENT
model family than the author — that is what makes the review unbiased — and the
CEO makes the final merge.

**On Mission Control that cross-vendor review cannot run**: the daemon may only
spawn the `claude` binary and has no per-agent model field. So per
`ARCHITECTURE.md` §8 the degrade path is explicit — either the PR is reviewed on a
host that can run another vendor (KiroCrew), or the change is **HELD unmerged**
with a pending decision telling the CEO the review gate cannot run here. A held
change is never auto-merged. Do not quietly downgrade this to a self-review.

## Cross-cutting rules

- **Contracts are the interface.** Roles talk through `requirements.md` →
  `design.md` / `standards.md` → PRs → QA / security / audit reports. A downstream role
  reads the contract file, not your paraphrase.
- **The intent contract is supreme.** Any gate can fail a phase for drifting from
  a signed requirement. Drift is the default failure mode you guard against.
- **Wake roles on demand.** Only create tasks for the roles a phase needs.
- **Always-current tech.** The architect web-searches the live landscape before
  selecting; no defaulting to stale training knowledge.
- **Report, don't bookkeep.** Your final message is the report the CEO reads: what
  you did, the evidence (commands + output), the gate verdict, what happens next.
