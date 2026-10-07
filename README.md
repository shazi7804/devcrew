# devcrew

**English** · [繁體中文](README.zh-TW.md)

**A whole AI software team behind one agent.** You are the CEO: you bring an
idea and sign off at a few gates. The `orchestrator` runs everything else. It
turns your idea into a signed contract, hands each phase to a specialist agent,
and checks every result against what you signed. The result goes to production.

It installs into **KiroCrew**, **Mission Control** or **Claude Code** from the
same source. Clone this repo on a new machine and your agent rebuilds the team.

## Setup

You do not run an installer. Your coding agent reads `AGENTS.md` and installs
the team into itself.

**1. Clone the repo**

```bash
git clone https://github.com/shazi7804/devcrew
cd devcrew
```

**2. Open your coding agent in that folder** (Claude Code, KiroCrew or Mission
Control) and paste this:

> Read `AGENTS.md` in this repo and install devcrew into whichever coding-agent
> host you are running in. Detect the host, translate the neutral `framework/`
> source with the matching guide in `hosts/`, generate the agent + skill files,
> verify them, and tell me how to switch to the `orchestrator` agent.

**3. Check what it reports back.** The agent reports four things:

- which host it detected,
- which agent files and skills it generated,
- which external skills it installed or could not find (see
  [Native skills](#native-skills)),
- how to switch to `orchestrator`.

On Claude Code it also installs the multi-session governance hooks and races
them, to prove that exactly one session becomes the orchestrator.

| Host | What gets generated | How you switch to it |
|---|---|---|
| Claude Code | `.claude/agents/*.md`, `.claude/skills/`, a `CLAUDE.md` section, hooks in `.claude/settings.json` | nothing to switch: the first session is elected orchestrator, and later windows become workers |
| KiroCrew | `~/.kiro/agents/<role>.json` | pick **orchestrator** in the dashboard agent switcher |
| Mission Control | roles in `<DATA_DIR>/agents.json` + `skills-library.json` | create a task with `assignedTo: "orchestrator"` |

On a new machine, clone again and repeat step 2. The repo is the source of
truth. Installed files are generated artifacts, so never hand-edit them.

## After setup, just talk to your `orchestrator` agent naturally

There are no commands to learn. You are the CEO: say what you want, the way you
would say it to a person.

> I want a landing page for our coffee subscription, with a signup flow and a
> Stripe checkout.

> Customers say the export button is slow on big reports. Fix it.

> 做一個記帳 App，iOS 和 Android 都要，可以拍收據自動辨識金額。

The orchestrator asks the few questions that change the design, writes down
what you meant, and has you sign it. From then on it only comes back to you at
a 🔴 gate. Every message it sends is a four-line **SITREP**, and the `CEO：`
line tells you whether anything is waiting on you.

## Architecture

```
                        ┌──────────┐
                        │   CEO    │  idea in · 🔴 sign-offs · final merge
                        └────┬─────┘
                             │ talks only to
                             ▼
┌───────────────────────────────────────────────────────────────────────┐
│ orchestrator (PM): dispatches roles, verifies gates, keeps TASKS.md   │
└──┬────────────────────────────────────────────────────────────────────┘
   │ hands each role a FILE PATH (a contract), never a paraphrase
   ▼
 PHASE       ROLE(S)                   PRODUCES                  GATE
 ─────       ───────                   ────────                  ────
 0   Intent  orchestrator              requirements.md 🔒        🔴 CEO
 0.5 Market  analyst (commercial)      GO / PIVOT / NO-GO        🔴 CEO
 1   Arch.   architect                 design.md + ADRs
                                       standards.md 🔒           🔴 CEO
 2   Design  designer (if UI)          design system + prototype
                                       (award-grade loop)        🔴 CEO
 3   Build   frontend ∥ backend        code + PRs + tests        tests green
 4   Verify  qa ∥ security ∥ auditor*  three verdicts            all pass
 5   Deploy  devops (if service)       running system + smoke    smoke green
 6   Release release (if shipped)      signed artifact → users   🔴 CEO
 ∞   Evolve  proposal → qa ∥ reviewer  signed proposal + PR      🔴 CEO merge

 🔒 = hash-locked. Every later gate re-checks the hash. A change without a new
      signature is drift, and drift halts the run.
 *  = auditor runs only on a large diff (> 1000 changed lines or > 20 files).
 ∥  = dispatched in parallel. Each role has its own context and none reads
      another's verdict.

 LOOPS
   A  fix       a gate fails ──▶ back to the phase that owns the fix (never P0)
                3 attempts, up to 5 while failures keep dropping, then 🔴 CEO
   B  reflect   every task ends with a 3-line retro ──▶ framework/memory/
   C  evolve    a retro suggests a framework change ──▶ signed proposal
                requirements 🔴 ──▶ PR ──▶ CI ──▶ qa ∥ reviewer (another
                model vendor, no team memory) ──▶ 🔴 CEO merge

 ONE SOURCE, THREE HOSTS
   framework/ ──▶ hosts/kirocrew.md        ~/.kiro/agents/*.json
              ──▶ hosts/mission-control.md agents.json + skills-library.json
              ──▶ hosts/claude-code.md     .claude/agents/*.md + hooks
```

For the full picture, read [ARCHITECTURE.md](ARCHITECTURE.md): the harness
layers, the loop bounds, the contract graph, the three kinds of state, and
multi-session governance. The binding rules are in
[framework/skills/aidlc/SKILL.md](framework/skills/aidlc/SKILL.md).

## The team

Each role has its own page: what it does, what it takes in and hands on, the
gate it must pass, and what it refuses to do.

| Agent | Role | Phase | In one line |
|---|---|---|---|
| [orchestrator](docs/agents/orchestrator.md) | Orchestrator + PM | all | Aligns intent, dispatches roles, decides every gate |
| [analyst](docs/agents/analyst.md) | Market Analyst | 0.5 | Decides whether the idea is worth building: GO / PIVOT / NO-GO |
| [architect](docs/agents/architect.md) | Architect | 1 | Picks the stack through a cross-vendor council; writes the ADRs and `standards.md` |
| [designer](docs/agents/designer.md) | Design (UI/UX) | 2 | Design system + 2–3 prototypes, iterated until they reach award grade |
| [frontend](docs/agents/frontend.md) | Frontend R&D | 3 | Builds the signed prototype exactly, using the tokens |
| [backend](docs/agents/backend.md) | Backend R&D | 3 | Services, APIs and data layer, secure by default |
| [qa](docs/agents/qa.md) | QA | 4 | Checks that every signed requirement is met, with evidence |
| [security](docs/agents/security.md) | Security | 4 | Threat model, dependency and secret scans, authn/authz review |
| [auditor](docs/agents/auditor.md) | Efficiency Auditor | 4* | Flags redundancy, reuse misses and running cost; read-only |
| [devops](docs/agents/devops.md) | DevOps / SRE | 5 | Deploys to the environments in `standards.md` and runs smoke tests |
| [release](docs/agents/release.md) | Release Manager | 6 | Version, signing, channel, staged rollout, rollback |
| [reviewer](docs/agents/reviewer.md) | Framework Reviewer | ∞ | Reviews changes to devcrew itself; a different vendor, no memory |

## Native skills

Skills are procedures a role loads on demand. Some ship in this repo; the rest
come from the host or from a third party, and `AGENTS.md` installs or maps
them. If one is missing, the installer tells you instead of inventing it.

| Skill | Used by | Source |
|---|---|---|
| `aidlc` | every role | this repo: [framework/skills/aidlc](framework/skills/aidlc/SKILL.md) (the protocol and contract templates) |
| `mobile-build` | frontend | this repo: [framework/skills/mobile-build](framework/skills/mobile-build/SKILL.md) |
| `mobile-verify` | qa, security | this repo: [framework/skills/mobile-verify](framework/skills/mobile-verify/SKILL.md) |
| `mobile-release` | release | this repo: [framework/skills/mobile-release](framework/skills/mobile-release/SKILL.md) |
| `impeccable` | designer | [impeccable.style](https://impeccable.style/) · [pbakaus/impeccable](https://github.com/pbakaus/impeccable) (Apache-2.0): design critique, audit, anti-"AI slop" detector |
| `llm-council` | orchestrator, architect | host skill: an adversarial cross-vendor model council |
| `frontend-design-workflow` | orchestrator, designer, frontend | host skill: the prototype-first UI workflow |
| `web-preview` · `web-verify` | designer, frontend, qa, devops, release | host skills: show and verify a page in the browser |
| `deploy-web` · `artifact-deploy` | orchestrator, devops, release | host skills: static and artifact deploys |
| `goal-conductor` | orchestrator | host skill: long-running goal tracking |
| `image-authoring` · `widgets` | analyst | host skills: charts for the market analysis |

The SITREP report format is adapted from
[joshuaboys/SITREP](https://github.com/joshuaboys/SITREP) (MIT).

## See it work

### What a run looks like

1. **You say what you want.** For example: *"I want a landing page for our
   coffee subscription."*
2. **The orchestrator asks only what would change the design**, then writes
   `requirements.md` and asks you to sign it (🔴 gate).
3. **It dispatches the roles your scope needs**, one gate at a time: architect,
   then designer if there is a UI, then frontend ∥ backend, then qa ∥ security
   (plus auditor on a large diff), then devops and release if the work ships.
4. **It comes back to you only at a 🔴 gate or when it is done.** Every report
   uses the same four-line block, so the one line you act on is always in the
   same place:

```
SITUATION  <one line: where things stand>
ACTION     <what was done this turn, max 3 lines>
STATUS     DONE | IN PROGRESS | BLOCKED | FAIL — <one clause>
NEXT       CEO：<numbered asks you answer by number>  | 無
           我：<what it does next, with no input from you>
```

Reply with the number (`1 ①`). Filled-in examples of the block are in
[contracts/sitrep.template.md](framework/skills/aidlc/contracts/sitrep.template.md).
Each gate leaves a file behind (`requirements.md`, `design.md`,
`design-scorecard.md`, the verdict YAML), so you can open any of them and
check the evidence yourself.

### Check the machinery yourself

These are real commands run on this repo, with the output they printed
(trimmed only where noted). You can run them too.

**The team's source names no host's tools and no machine's facts**
(invariant 9):

```console
$ python3 tools/check_neutral.py --self-test
self-test ok
$ python3 tools/check_neutral.py
neutral: ok
```

**Open 32 Claude Code windows at once, and exactly one becomes the
orchestrator.** Below is the output of the race script in
[hosts/claude-code.md](hosts/claude-code.md) § *Multi-session governance* (4),
run against a throwaway directory with `B=framework/tools/boot.py`:

```console
       1
       1
empty stdin exit=0
```

The first `1` counts the orchestrators among 32 sessions started at the same
moment. The second counts the winners among 20 sessions taking over one expired
lock at the same moment. The last line shows that a malformed hook input does
not block a session.

**The designer's anti-"AI slop" check.** This is `impeccable detect` run on a
deliberately generic hero section (Inter, a purple gradient, gray text). The
designer loops until this reports nothing:

```console
$ npx impeccable detect index.html
  [gray-on-color] text #999999 on bg gradient(#6366f1, #a855f7)
  [low-contrast] 1.4:1 (need 4.5:1) — text #999999 on #a855f7
  [overused-font] Primary font: inter
  [ai-color-palette] Purple/violet accent colors detected

4 anti-patterns found.
$ echo $?
2
```

(Trimmed: the first line, which is the scanned file's path, and each
finding's one-line fix hint.)

## Docs

| Read this | For |
|---|---|
| [docs/agents/](#the-team) | One page per role: what it does, its gate, what it refuses to do |
| [ARCHITECTURE.md](ARCHITECTURE.md) | The whole system on one page: layers, flow, loops, contracts, state |
| [framework/skills/aidlc/SKILL.md](framework/skills/aidlc/SKILL.md) | The binding protocol: phases, gates, scope routing, magnitude floor |
| [framework/skills/aidlc/contracts/](framework/skills/aidlc/contracts/) | Templates: requirements, design, standards, verdicts, SITREP |
| [framework/session-governance.md](framework/session-governance.md) | How one orchestrator is chosen when several sessions are open |
| [hosts/](hosts/) | Install guides: KiroCrew, Mission Control, Claude Code |
| [AGENTS.md](AGENTS.md) | The AI bootstrap and the ten design invariants |
| [CHANGELOG.md](CHANGELOG.md) | What changed in each version, and why |

## Repository layout

| Path | What it is |
|---|---|
| `AGENTS.md` | The bootstrap an AI reads on a fresh clone to install itself |
| `framework/agents/` | The 12 role prompts: the source of truth for each agent |
| `framework/skills/aidlc/` | The AIDLC protocol, plus contract templates (requirements, design, standards, verdicts, SITREP) |
| `framework/skills/mobile-*` | Mobile build / verify / release procedures |
| `framework/memory/` | Shared team memory: lessons, ADRs, retrospectives |
| `framework/session-governance.md` + `framework/tools/boot.py` | Decides which session is the orchestrator when several windows are open |
| `hosts/` | One adapter guide per host |
| `docs/agents/` | Human-readable guide to each role (this README links to them) |
| `proposals/` | The signed requirements for each change to devcrew itself |
| `tools/` + `.github/workflows/` | The CI checks: neutrality, links and role files, diagram alignment |

## Principles

1. **The signed intent is supreme.** Every gate checks against it.
2. **Roles are independent agents that share one memory.** Separate contexts
   make adversarial review real, and the shared memory carries experience across
   the team.
3. **Load-bearing decisions go through a cross-vendor council**, not a single
   model's say-so.
4. **Self-evolution is gated.** A change to the framework starts with its own
   signed requirements, like any product change. It lands only as a PR that
   passes CI, QA against those requirements, and a reviewer from a different
   model vendor, and the CEO merges it. No agent merges its own change.
5. **Tech selection is always current.** The Architect searches the live
   landscape before choosing.
6. **Deploy topology is per project.** It is defined with the CEO in
   `standards.md`; the framework never assumes a cloud.
7. **Waste fails the gate.** Passing tests do not prove the code was worth its
   size. On a large diff, the Auditor checks it against the budget in
   `standards.md`.
8. **No gate is weakened to make something pass.** Loosening an approval gate,
   a safety control, a permission boundary or a trigger takes a CEO decision,
   recorded with its reason.
9. **The framework is host- and machine-neutral.** `framework/` names no host's
   tools and no machine's facts. `tools/check_neutral.py` checks the whole tree
   in CI.
10. **A mechanism decides who is in charge, not a rule.** When several sessions
    are open, a kernel-level lock with a heartbeat lease picks the orchestrator,
    and no session needs input from the human.

## License

[MIT](LICENSE)
