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
   IS the shared experience on this host.

## CLAUDE.md section to add

```markdown
## devcrew
This repo carries the devcrew AI software team. Roles live in .claude/agents/:
devcrew (orchestrator/PM), devcrew-architect, devcrew-design, devcrew-fe,
devcrew-be, devcrew-qa, devcrew-security, devcrew-devops.
Follow the AIDLC protocol in .claude/skills/aidlc/SKILL.md: align intent into a
signed requirements.md, then Architect -> Design -> FE+BE -> QA+Security ->
DevOps, verifying every gate against the signed intent. Load-bearing decisions
go through an adversarial cross-vendor review. All roles read and append to
framework/memory/ (the shared team experience). Self-changes to agents/skills
land only through a PR + the QA gate.
```

## Verify

Confirm each `.claude/agents/*.md` frontmatter is valid, the skill copied, and
`CLAUDE.md` has the devcrew section. Tell the user they can now ask the main
agent to "act as devcrew" or delegate to a specific role.

---

# Field notes from a real install

Everything below comes from running this framework on a real project (Triptag) for
several weeks. Two confidence levels are marked, and the difference matters:

- **[verified]** — observed directly in a live Claude Code session.
- **[unverified]** — from training knowledge, not checked against current docs.
  Confirm with `claude --help`, `/hooks`, `/agents`, `/config` before relying on it.

## The capability table for this host

Fill this into the install (it is the `Host capability contract` the skill asks
for). Values observed on Claude Code:

| Capability | Claude Code reality |
|---|---|
| spawn | **[verified]** Project agents in `.claude/agents/*.md` are loaded and directly dispatchable by name. **Do not route through a generic agent and have it read the role file** — that wastes a Read of context and, worse, the role's `tools` allowlist never takes effect |
| durable ledger | No native tool. A plain-text file in the repo (`ledger.md`). Read it first on resume |
| ask-human | The question/options tool. Ask one thing, end the turn |
| cross-vendor model | **Not available in-host.** Requires an external call (e.g. Bedrock). Without credentials this gate degrades — see the skill's degradation protocol |
| web | Available unless the environment restricts egress. **A sandboxed/allowlisted environment silently breaks Phase 0.5 and the Architect's stack choice** — check before planning work that needs it |
| browser/screenshot | Not built in; needs a browser MCP server. Without one, UI verification is text-level only |
| resource check | No tool. **The scarce resource here is context, not memory.** Cap fan-out and scope each task to one screen/module |
| memory write | `Read`/`Write` on `framework/memory/*.md`. Host-level memory does not travel with the repo — anything that must survive a host switch goes in the repo |
| PR / branch | Real git. Use a branch per feature; the self-evolution gate becomes a real PR |

## Subagent frontmatter gotchas

- **[verified]** A `role:` key in the frontmatter is **not a Claude Code field and
  is ignored.** The neutral source uses it; the adapter must fold it into
  `description` or the body, or the role identity silently does not transfer.
- **[unverified]** Supported keys: `name`, `description`, `tools`, `model`, `color`.
  Omitting `tools` inherits everything; listing it makes it an allowlist. `model`
  accepts `inherit`.
- `description` is the routing signal — it decides whether the role ever gets
  dispatched. Write it as *when to delegate here*, not as a job title.

## Skills: install it, or inline it

`.claude/skills/<name>/SKILL.md` is the standard location. **[verified]** But a
project can also skip installing the skill and put the operating protocol directly
in `CLAUDE.md`, which is auto-loaded every session. Trade-off worth stating to the
user: `CLAUDE.md` always loads (reliable, costs context every session); a skill
loads on demand (cheaper, but only if it actually gets triggered). For a protocol
that must apply to *every* turn, `CLAUDE.md` is the safer placement.

## Hooks — make verification unforgettable

**[unverified]** in its field names; the design lesson is solid. Hooks go in
`.claude/settings.json`. Precedence: managed policy > CLI flags > `settings.local.json`
> `settings.json` > user settings. Do not define the same hook in both local and
shared settings.

**Use `Stop`, not `PostToolUse`, to run a full verification suite** — a round that
edits five files would otherwise build five times. The workable shape is a cheap
`PostToolUse` hook that only touches a dirty-flag file, and a `Stop` hook that runs
the suite when the flag is set.

What breaks installs:

- Event names are PascalCase: `PreToolUse`, `PostToolUse`, `UserPromptSubmit`,
  `Stop`, `SubagentStop`, `Notification`, `PreCompact`, `SessionStart`, `SessionEnd`.
- The structure is three levels: event → array of `{matcher, hooks}` → array of
  `{type, command, timeout}`. Collapsing a level is the most common mistake.
- **`matcher` matches tool names only, never file paths.** "Only when `src/`
  changed" must be decided inside the script, from the stdin JSON's
  `tool_input.file_path` (snake_case).
- **Exit codes carry meaning**: `0` succeeds and its stdout is *not* shown to the
  model; **`2` is a blocking error and its stderr is fed back to the model**; other
  non-zero codes are non-blocking. So "fail the build and make the agent fix it"
  means *write to stderr and exit 2*.
- **`Stop` takes no matcher, and its stdin carries `stop_hook_active`. Exiting 2
  without checking that flag is an infinite loop.**
- A build hook writes the default artifact path. On a repo where several sessions
  may run, make the hook emit a private output file, or the sessions fight over it.

## Slash commands — pin the rituals

**[unverified]** `.claude/commands/<name>.md`; subdirectories namespace the command
(`commands/aidlc/gate.md` → `/aidlc:gate`). Frontmatter keys are kebab-case:
`description`, `argument-hint`, `allowed-tools`, `model`, `disable-model-invocation`.
`$ARGUMENTS` is everything, `$1`/`$2` are positional; `` !`cmd` `` injects shell
output at run time (**requires Bash in `allowed-tools`**); `@path` inlines a file.

The four worth creating, because each one encodes a step that otherwise gets
skipped: **resume** (read ledger + memory before acting), **verify** (run the whole
suite, never a subset), **mutate** (the mutation-testing pass), **gate** (recompute
the intent hash, check drift, then present to the human in prose and stop).

## Plan mode and headless

- **[unverified]** Plan mode (`--permission-mode plan`) fits Phases 0 and 1
  exactly: the agent reads and proposes but cannot edit. A planning phase that
  *cannot* write is structurally better than one that is merely asked not to.
- **[unverified]** Headless (`claude -p "..." --output-format json`) runs a
  verification pass in a separate context and returns a result — noticeably cheaper
  than running it in the main conversation, which matters because context is the
  binding constraint on this host. Do not reach for
  `--dangerously-skip-permissions` anywhere with write access.

## Splitting work across two hosts

If the CEO also uses a conversational Claude client, the split that worked: the
**CLI** does implementation, verification, mutation testing, and git; the
**conversational client** handles the CEO dialogue and 🔴 gates, because a
non-engineer approves things more naturally in a conversation than in a terminal.

**The boundary between them must be files in the repo.** Anything either side
learns has to land in the ledger, the lessons file, or the standing-decisions file.
Host-level memory does not cross the boundary, and whatever does not get written
down is gone the moment the CEO switches windows.
