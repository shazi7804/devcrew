# Host adapter — Claude Code

How to install the neutral `framework/` source into Claude Code. Follow this when
`AGENTS.md` Step 1 resolved to Claude Code.

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

## CLAUDE.md section to add

```markdown
## devcrew
This repo carries the devcrew AI software team. Roles live in .claude/agents/:
orchestrator (PM), analyst, architect, designer, frontend,
backend, qa, security, devops, release, reviewer.
Follow the AIDLC protocol in .claude/skills/aidlc/SKILL.md: align intent into a
signed requirements.md, then Architect -> Design -> Frontend+Backend -> QA+Security ->
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
