# devcrew

A full AI software team you switch to as one agent. It takes an idea from a
CEO all the way to production — an orchestrator that wears the PM hat and
dispatches independent role agents (Architect, Design, Frontend, Backend, QA,
Security, Auditor, DevOps, Release) across an AI-Driven Development Life Cycle
(AIDLC), aligning intent as a signed contract, verifying every gate against it,
and improving itself through a gated self-evolution loop.

Host-neutral: the same repo installs into **KiroCrew**, **Mission Control**, or
**Claude Code**. Clone it on any machine and your agent restores the whole team.

## Install (paste this to your AI agent — it does the rest)

> Read `AGENTS.md` in this repo and install devcrew into whichever coding-agent
> host you are running in. Detect the host, translate the neutral `framework/`
> source with the matching guide in `hosts/`, generate the agent + skill files,
> verify them, and tell me how to switch to the `orchestrator` agent.

You do not run an installer. The AI reads `AGENTS.md` and self-installs.

## How it works

The user is the **CEO**: supplies intent, signs off at gates, does no other dev
work. Everything else is an agent.

```
idea → [PM] requirements.md + scope (🔴 CEO signs)
     → [Architect] design.md + ADRs (adversarial tech selection)
     → [Design] design system + clickable prototype (🔴 CEO signs)
     → [Frontend + Backend] code + PRs + tests
     → [QA + Security + Auditor] verify every requirement + scan + (on a big
       diff) audit for redundancy / inefficiency / running cost
     → [DevOps] Phase 5 deploy runtime (to envs in standards.md) + smoke tests
     → [Release] Phase 6 ship artifact (sign, TestFlight/Play/store, rollout) 🔴
     → [all] retrospective → gated self-improvement
```

Phases 5/6 are target-aware: a service change runs Deploy, a user-shipped
artifact (mobile app / release) runs Release, a mobile+backend change runs both.

The protocol lives in `framework/skills/aidlc/SKILL.md`.

## Layout

- `AGENTS.md` — AI bootstrap (read by the agent on a fresh clone)
- `framework/agents/` — the 12 neutral role agents (source of truth)
- `framework/skills/aidlc/` — the AIDLC collaboration protocol + contract templates
- `framework/memory/` — shared team memory (lessons, ADRs, retros)
- `hosts/` — per-host adapter guides (KiroCrew, Mission Control, Claude Code)

## Principles

1. The signed intent contract is supreme — gates verify against it.
2. Roles are independent agents (real adversarial review) that share one memory
   (shared experience).
3. Load-bearing decisions go through an adversarial cross-vendor council.
4. Self-evolution is gated — changes land only through a PR + the QA gate.
5. Tech selection is always current — the Architect checks the live landscape.
6. Deploy topology is defined per-project in `standards.md` (with the CEO), not hardcoded — the framework stores the rule, not the cloud.
7. Waste is a gate failure — on a large change (>1000 lines or >20 files) the
   Auditor audits the diff for redundancy, duplication, hot-path inefficiency and
   running cost, against the budget in `standards.md`. Green tests do not prove
   the code was worth its size.
