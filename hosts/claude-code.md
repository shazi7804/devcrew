# Host adapter — Claude Code

How to install the neutral `framework/` source into Claude Code. Follow this when
`AGENTS.md` Step 1 resolved to Claude Code.

## The three layers — where every wire lives

This is the thinnest of the three hosts: the install is a set of file copies and
the dispatcher is the session you are already in. That buys the strongest 🔴 gate
and the weakest durability — both visible below.

```
┌─ L3 · devcrew — the AIDLC flow ─────────── source: <repo>/framework ──┐
│  identical to every other host — it names no Claude Code path.        │
│  12 roles · the AIDLC protocol · the contracts · the shared memory    │
└───────────────────────────────────────────────────────────────────────┘
     │                                          ▲
     │ (A) INSTALL-TIME TRANSFORM — plain       │ (C) Phase ∞ writes back:
     │     file copies. No daemon, no MCP.      │     retro/lessons → framework/
     ▼                                          │     PR, never self-merged
┌─ L2 · adapter ────────────── this is the layer this file defines ─────┐
│                                                                       │
│ (A) install transform — which file becomes which                      │
│   framework/agents/<role>.md ──────▶ .claude/agents/<role>.md         │
│     the body           ──────▶ kept AS-IS (already a valid prompt)    │
│     the frontmatter    ──────▶ rewritten: name·description·tools·model│
│       description ── the MAIN agent routes on this, so write it as    │
│                      "when to delegate here". Vague = never picked.   │
│     ✘ auditor  ──────▶ tools: Read,Grep,Glob,Bash,WebFetch,WebSearch  │
│                        NEVER omit `tools` for it — omitting means     │
│                        inherit ALL, which hands it Write (invariant 7)│
│   framework/skills/aidlc/ ─────────▶ .claude/skills/aidlc/            │
│   the other skills ────────────────▶ install an equivalent, OR fold   │
│                        the procedure into the agent body — and TELL   │
│                        the user which of the two you did              │
│                                                                       │
│ (B) harness ──▶ host primitive                                        │
│   dispatch       ▶ the Task tool — the main session delegates         │
│   🔴 CEO gate    ▶ ask, then END THE TURN. The CEO is already in the  │
│                    conversation, so this is the most reliable gate    │
│                    of the three hosts.                                │
│   council        ▶ delegate to 2+ subagents on DIFFERENT models       │
│   shared memory  ▶ ⚠ no mount exists. Realised as a CLAUDE.md RULE:   │
│                    every devcrew agent reads/appends framework/memory/│
│                    ✘ EXCEPT reviewer — excluded explicitly (inv. 4)   │
│   durable ledger ▶ ⚠ NOT DEFINED by this adapter — see below          │
│   scheduler      ▶ ⚠ none. The Phase-∞ meta-review runs on request.   │
└───────────────────────────────────────────────────────────────────────┘
     │ reads / writes                            ▲ the CEO is simply talking
     ▼                                           │ to the session
┌─ L1 · Claude Code runtime ────────────────────────────────────────────┐
│                                                                       │
│  ONE interactive session = the dispatcher. There is no daemon, so     │
│  nothing runs while you are not in the conversation.                  │
│     .claude/agents/*.md   loaded as subagents (Task targets)          │
│     .claude/skills/**     loaded as skills                            │
│     CLAUDE.md             project routing + the shared-memory RULE    │
│                                                                       │
│  Consequence: every harness rule that depends on a BACKGROUND process │
│  (a queue, a cron, a restart replay) has to become a file in the repo │
│  or it does not exist on this host.                                   │
└───────────────────────────────────────────────────────────────────────┘
```

## Known degradation on this host

State these to the user at install time rather than letting them be discovered
mid-run:

- **Shared memory is a convention, not a mount.** `memory: shared` is enforced by
  prose in `CLAUDE.md`; a subagent that ignores it loses team experience silently.
  Verify the rule is present, and if a role keeps missing it, restate the rule in
  that role's own body.
- **No durable ledger primitive.** Nothing survives a `/clear` on its own, so
  Loop A's attempt bound, the intent/standards hashes and the requirement→PR→test
  map all reset unless they are written to a file. The Mission Control adapter
  already establishes the convention for a product repo — `.aidlc/` holding
  contracts · ledger · memory — so use that same layout here and keep the ledger
  as a file the orchestrator appends to.
- **No scheduler.** The Phase-∞ meta-review has no `cron` equivalent; it runs when
  the CEO asks for it. Say so rather than implying a periodic review happens.

## What Claude Code expects

- Subagents: one Markdown file per agent at `.claude/agents/<name>.md` (project
  scope) or `~/.claude/agents/<name>.md` (user scope). YAML frontmatter
  (`name`, `description`, `tools`, `model`) + a Markdown body that is the
  agent's system prompt. The main session delegates to them via the Task tool.
- Skills: directories under `.claude/skills/<name>/SKILL.md`.
- Project memory / routing: `CLAUDE.md` at the repo root.

## Neutral → Claude Code tool mapping

| Neutral tool | Claude Code tools |
|---|---|
| read | `Read`, `Grep`, `Glob` |
| write / edit | `Write`, `Edit` |
| shell | `Bash` |
| search | `Grep`, `Glob` |
| web | `WebFetch`, `WebSearch` |
| spawn | `Task` (subagent delegation) |
| memory | `Read`/`Write` of `framework/memory/**` + CLAUDE.md |

`model: best-available` → the strongest model alias Claude Code currently
exposes (check what is available at install time; do not hardcode a dated id).
Omit `tools` entirely to inherit all tools if a role needs the full set.

## Per-agent file to generate

For each `framework/agents/<name>.md`:

1. Keep the Markdown body as-is (it is already a valid system prompt).
2. Rewrite the frontmatter to Claude Code's shape:

```markdown
---
name: <name>
description: <from neutral frontmatter — write it so the main agent knows WHEN to delegate here>
tools: <mapped tool list, or omit to inherit all>
model: <current best alias>
---

<the neutral body, unchanged>
```

3. Write it to `.claude/agents/<name>.md`.
4. Copy `framework/skills/aidlc/` to `.claude/skills/aidlc/`. For the other
   skills a role references (`frontend-design-workflow`, `llm-council`, etc.),
   either install equivalents into `.claude/skills/` or fold their essential
   procedure into the agent body — note to the user which you did.
5. Because Claude Code has no cross-agent shared-memory mount, realize
   `memory: shared` by adding to `CLAUDE.md` a rule that every devcrew agent
   reads and appends to `framework/memory/` (lessons, ADRs, retros). That file
   IS the shared experience on this host. **EXCEPTION: `reviewer` has
   `memory: none` and MUST NOT read or append to `framework/memory/`** — its
   value is judging a self-evolution change unbiased by team memory (invariant
   4). Exclude it explicitly from the shared-memory rule, and verify at install
   that the reviewer artifact mounts no shared memory.
6. **`auditor` must be installed read-only.** Its neutral frontmatter lists no
   `write`/`edit` on purpose (an auditor that fixes its own findings audits
   itself), so map it to `tools: Read, Grep, Glob, Bash, WebFetch, WebSearch` and
   do NOT fall back to omitting `tools` for it. Verify after install that the
   generated `.claude/agents/auditor.md` grants no `Write`/`Edit`.

## CLAUDE.md section to add

```markdown
## devcrew
This repo carries the devcrew AI software team. Roles live in .claude/agents/:
orchestrator (PM), analyst, architect, designer, frontend,
backend, qa, security, auditor, devops, release, reviewer.
Follow the AIDLC protocol in .claude/skills/aidlc/SKILL.md: align intent into a
signed requirements.md, then Architect -> Design -> Frontend+Backend -> QA+Security
(+auditor when the magnitude floor fires: >1000 changed lines or >20 files) ->
DevOps (runtime) -> Release (ship artifact), verifying every gate against the
signed intent. Load-bearing decisions
go through an adversarial cross-vendor review. All roles read and append to
framework/memory/ (the shared team experience) — EXCEPT reviewer, which mounts
no team memory so its self-evolution review stays unbiased. Self-changes to agents/skills
land only through a PR + the QA gate.
```

## Verify

Confirm each `.claude/agents/*.md` frontmatter is valid, the skill copied, and
`CLAUDE.md` has the devcrew section. Tell the user they can now ask the main
agent to "act as devcrew" or delegate to a specific role.
