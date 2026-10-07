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
     │     file copies. No daemon, no MCP.      │     retro → signed proposal →
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
│   who dispatches ▶ hooks + a link(2) CAS claim. NOT a prompt rule: two│
│                    windows both believing they are the orchestrator   │
│                    is the default here (§ Multi-session governance)   │
│   🔴 CEO gate    ▶ ask, then END THE TURN. The CEO is already in the  │
│                    conversation, so this is the most reliable gate    │
│                    of the three hosts.                                │
│   council        ▶ delegate to 2+ subagents on DIFFERENT models       │
│   shared memory  ▶ ⚠ no mount exists. Realised as a CLAUDE.md RULE:   │
│                    every devcrew agent reads/appends framework/memory/│
│                    ✘ EXCEPT reviewer — excluded explicitly (inv. 4)   │
│   ledger         ▶ TASKS.md at the project root — current state only, │
│                    written by the orchestrator, checked by            │
│                    .aidlc/tools/check_tasks.py                        │
│   scheduler      ▶ ⚠ none. The Phase-∞ meta-review runs on request.   │
│   question       ▶ AskUserQuestion (structured options)               │
│   resource check ▶ ⚠ none. Serialize heavy steps on a small machine.  │
│   preview        ▶ a headless-browser screenshot (e.g. Playwright)    │
└───────────────────────────────────────────────────────────────────────┘
     │ reads / writes                            ▲ the CEO is simply talking
     ▼                                           │ to the session
┌─ L1 · Claude Code runtime ────────────────────────────────────────────┐
│                                                                       │
│  ANY NUMBER of interactive sessions, each able to act as dispatcher.  │
│  There is no daemon, so nothing runs while you are not in a           │
│  conversation — and nothing coordinates two sessions unless you       │
│  install L2's governance wiring (see § Multi-session governance).     │
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
- **The ledger is a file, because nothing else survives a `/clear`.** On every
  host the ledger is `TASKS.md` at the project root (aidlc skill § *TASKS.md*):
  Done · In progress · Todo, the `Signed:` hashes and the open batch, nothing
  more — git keeps the history. Only the orchestrator writes it, and
  `.aidlc/tools/check_tasks.py` checks it (format, IDs, Loop A's `n/5` and
  `stalled k/3`, the drift halt on the `Signed:` hashes, and live + formal
  evidence for every Done item). That is what makes the bounds survive a
  compaction here.
- **No scheduler.** The Phase-∞ meta-review has no `cron` equivalent; it runs when
  the CEO asks for it. Say so rather than implying a periodic review happens.
- **Nothing stops a second session from also being the orchestrator.** The CEO can
  open five windows on one repo, and each one boots believing it is the dispatcher.
  The 🔴 gate is this host's strongest primitive precisely because the CEO is in
  the conversation — and that is also why they open more windows. Fixable, not
  inherent: install § *Multi-session governance* below, which is mandatory on this
  host and not merely recommended.

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
   `impeccable` (designer) is third-party, so install it rather than fold
   it at a pinned version (4.1.0 when this was written; pin the version you
   install and name it in the report):
   `npx impeccable@4.1.0 install --providers=claude --scope=project`. If the
   CLI's bundle download times out, `git clone` the repo at the matching tag
   and copy its `.claude/skills/impeccable/` instead. Its edit hook goes into
   `.claude/settings.local.json`, not the governance `settings.json`. That hook
   runs third-party code on every edit, so show the user the hook entry and get
   a yes before you keep it. Afterwards check that all five governance hooks are
   still present. Verify the install by running
   `npx impeccable@4.1.0 detect <file>`: exit 0 means clean, 2 means findings,
   and 1 means the scan failed. If it cannot be installed, say so; the designer
   then follows its *When impeccable cannot be installed* path.
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
7. **Install the multi-session governance layer** — `framework/tools/boot.py` →
   `.aidlc/tools/boot.py` and its adapter `.aidlc/tools/boot_host.py`, plus the
   five hooks in `.claude/settings.json`. Full
   instructions in § *Multi-session governance* below; the concept it implements
   is `framework/session-governance.md`. Do not treat this as optional on this
   host: without it, "the orchestrator" is whatever each open window believes.
   If you skip it deliberately (single-window user, no `python3`), say so to the
   user in those words rather than leaving them to assume they are covered.
8. **Install the sensors** — `framework/tools/check_live.py`,
   `check_formal.py` and `check_tasks.py` → `.aidlc/tools/`, side by side (the
   last two import `check_live.py` from their own directory). `check_live` is
   the only deterministic check that the delivered work runs on real services
   rather than on fakes (aidlc skill § *No fake data*); `check_formal` that each
   requirement's signed `Property:` was machine-checked, at its level, without
   an escape hatch and with a vacuity run; `check_tasks` that `TASKS.md` is true.
   Implementers run them at Phase 3, `qa` at Phase 4, `devops` at Phase 5, the
   orchestrator at every step. Skipping any of them is a thing to say out loud.
   `tools/check_models.py` (TLC on the framework's own protocol models, and
   trace validation of `boot.py`) is CI for devcrew itself — it is **not**
   installed into projects.

## Multi-session governance

**Install this whenever the repo belongs to a human who opens more than one
window.** It is the only part of this adapter that cannot be a prose rule: the
neutral spec is `framework/session-governance.md`, and the paragraphs below are
only the Claude Code wiring for it. Read the spec for the decision tree, the
lease semantics and the escape hatch; read this for which files to create.

Why wiring and not a `CLAUDE.md` rule: `CLAUDE.md` is loaded into the model's
context, so obeying it depends on the model choosing to run two commands at the
top of every session. Hooks are executed by the harness. One project shipped the
rule version first — "check who the orchestrator is before you start", in the
always-loaded instructions — and still produced two sessions signing
requirements for one intent. The second attempt was a boot prompt for the human
to paste into each window; the CEO's verdict on it was "I am not going to type
this every time, your approach is terrible". Both failure modes are the same
failure: a mechanism whose execution is somebody's responsibility to remember.

### (1) The script

Copy `framework/tools/boot.py` → `.aidlc/tools/boot.py`, and
`hosts/claude-code.boot_host.py` → `.aidlc/tools/boot_host.py`. Both are
stdlib-only. `boot.py` is host-neutral and prints a plain
`{message, context, quiet}` result. The adapter beside it reshapes that result
into Claude Code's hook JSON (`systemMessage`, `suppressOutput`,
`hookSpecificOutput.additionalContext`). Without the adapter the hooks still
run, but Claude Code ignores the output, so the role is never injected.

### (2) The wiring — `.claude/settings.json`

```
             the human opens a window, or types, or closes it
                                  │
┌─ .claude/settings.json ─────────▼───────────────────────────────────┐
│  SessionStart       ─▶ boot.py start  elect, then inject the role   │
│  UserPromptSubmit   ─▶ boot.py beat   refresh the lease…            │
│  PostToolUse (async)─▶ boot.py beat   …after every tool call (A2)…  │
│  Stop  (async)      ─▶ boot.py beat   …and at both ends of a turn   │
│  SessionEnd         ─▶ boot.py end    release it, if this session   │
│                                       is the holder                 │
└───────────────────────┬─────────────────────────────────────────────┘
                        │ stdin: {"session_id": …, "cwd": …}
                        ▼         ← the only identity key that works
              .aidlc/claims/ORCHESTRATOR.<n>.claim   (link CAS + mtime)
                        │
                        ▼ stdout: hookSpecificOutput.additionalContext
              "you are the orchestrator" + board, or "you are a worker"
```

```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [ { "type": "command",
          "command": "python3 \"${CLAUDE_PROJECT_DIR}/.aidlc/tools/boot.py\" start",
          "timeout": 25,
          "statusMessage": "Electing the orchestrator…" } ] }
    ],
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command",
          "command": "python3 \"${CLAUDE_PROJECT_DIR}/.aidlc/tools/boot.py\" beat",
          "timeout": 10 } ] }
    ],
    "PostToolUse": [
      { "matcher": "*",
        "hooks": [ { "type": "command",
          "command": "python3 \"${CLAUDE_PROJECT_DIR}/.aidlc/tools/boot.py\" beat",
          "timeout": 10, "async": true } ] }
    ],
    "Stop": [
      { "hooks": [ { "type": "command",
          "command": "python3 \"${CLAUDE_PROJECT_DIR}/.aidlc/tools/boot.py\" beat",
          "timeout": 10, "async": true } ] }
    ],
    "SessionEnd": [
      { "hooks": [ { "type": "command",
          "command": "python3 \"${CLAUDE_PROJECT_DIR}/.aidlc/tools/boot.py\" end",
          "timeout": 10 } ] }
    ]
  }
}
```

Five details in that JSON are load-bearing:

- **`session_id` from hook stdin is the identity.** It is stable for the
  session's whole life and differs between concurrent sessions. Do not
  substitute a pid: on this host the per-session socket files in
  `/tmp/cc-socks/` are *named after pids* (`lsof -U` shows pid 5819 listening
  on `5819.sock`), and a pid identifies a process, not a session.
- **Both `UserPromptSubmit` and `Stop` beat.** Together they bracket the turn, so
  the lease tracks "this session is in use" rather than "the human typed
  recently".
- **`PostToolUse` beats too — this one is assumption A2, not a nicety.** The
  election is proved (`framework/formal/Election.tla`) only while an acting
  orchestrator beats more often than `STALE − MARGIN` (40 min by default).
  Without a beat inside the turn, one autonomous turn longer than that lets the
  lease expire while the holder is still acting, and a second window takes
  over: two orchestrators, which is exactly what more autonomy produces. With
  it, the bound is one *tool call* longer than 40 min. The same beat is how a
  demoted session hears "stop acting as orchestrator" mid-turn. Omitting it is
  a thing to say out loud.
- **`Stop` and `PostToolUse` are `async`.** A heartbeat must not add latency
  to finishing a turn or to the next tool call.
- **`SessionStart` also fires on resume, `/clear` and after compaction.** That is
  a feature: the election is idempotent for the same `session_id`, so the role
  text gets re-injected into a context that just lost it. Compaction is how an
  orchestrator forgets it was mid-gate.

### (3) `.gitignore`

```
.aidlc/claims/*.claim
.aidlc/claims/*.released
.aidlc/claims/.new.*
```

Keep `.aidlc/claims/README.md` committed so the directory exists in a fresh
clone. Without the directory, the claim's `link` fails for the wrong reason and
every claim rule looks obeyed while doing nothing.

### (4) Verify — by racing it, not by reading it

A mechanism claiming kernel-level mutual exclusion should be made to prove it.
Both checks run against a throwaway tree, so they touch nothing real:

```bash
T=$(mktemp -d); mkdir -p "$T/.aidlc/claims"; export DEVCREW_PROJECT_DIR="$T"
B=.aidlc/tools/boot.py

# 32 sessions start at once → exactly 1 orchestrator, 31 workers
for i in $(seq 32); do
  echo "{\"session_id\":\"s-$i\"}" | python3 "$B" start > "$T/o.$i" &
done; wait
grep -l 'only orchestrator' "$T"/o.* | wc -l     # must print 1

# 20 sessions take over one expired claim at once → exactly 1 winner
touch -t 202001010000 "$T/.aidlc/claims/ORCHESTRATOR.1.claim"
for i in $(seq 20); do
  echo "{\"session_id\":\"t-$i\"}" | python3 "$B" start > "$T/t.$i" &
done; wait
grep -l 'Took over' "$T"/t.* | wc -l             # must print 1

echo '' | python3 "$B" start >/dev/null; echo "empty stdin exit=$?"   # must be 0
```

The race shows the compare-and-swap works; it cannot show that no interleaving
breaks it — that is what the model check and the trace validation in devcrew's
own CI are for (`framework/session-governance.md` § 8).

Then confirm it is live in the real session: open a second window and check that
it announces itself as a worker naming the first window's id. If the settings
file was created during this session the watcher may not have picked it up — the
user can open `/hooks` once, or restart. You cannot do that for them.

### (5) The `CLAUDE.md` half — and its limit

Add the short rule below. It is not the mechanism; it tells the model what the
two roles are *allowed* to do, which no hook can enforce:

```markdown
### Orchestrator or worker
Your role is elected by a hook at session start and injected into your context —
do not re-derive it, do not negotiate it with another session, and never
hand-edit anything in .aidlc/claims/. If a hook tells you that you are no longer
the orchestrator, stop acting as one at once. A worker may not do exactly two
things: claim or open a card slug, and write or sign requirements.md. Everything
else is open: a worker may do work, it may not define what the work is. A worker
never commits. Liveness comes from the host's session list only — a socket or pid
file is never evidence that a session is alive or dead. Both roles open every
report with the SITREP block; a worker's report to the orchestrator is digested
there, not relayed to the human.
```

⚠️ **Keep this text and the injected text in agreement.** They are edited at
different times by different people, and the injected copy wins every argument
because it arrives later in the context. When they disagree, the model gets two
truths and the human gets neither — so a change to the election belongs in the
same commit as the change to `CLAUDE.md`.

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
no team memory so its self-evolution review stays unbiased. A self-change to agents/skills
starts with a CEO-signed proposals/<slug>/requirements.md, then lands only through
a PR, CI, qa against that proposal, the reviewer, and the CEO's merge.
No fake data: every requirement is verified live against the real, deployed
service (Verify: live by default; no level accepts a fake), production code
ships no mock/stub/seed data, and nothing is Closes'd, passed or reported done
while `python3 .aidlc/tools/check_live.py --rerun` is red. A missing service or
credential is a question for the CEO, never a reason to build on a fake. If the
project has a runtime, Phase 5 runs; no note in this file can skip it.
Every requirement carries a signed `Property:`, machine-checked at its formal
level (`.aidlc/tools/check_formal.py`). The ledger is TASKS.md (Done · In
progress · Todo, current state only), written by the orchestrator and checked by
`.aidlc/tools/check_tasks.py`; an item is Done only with live AND formal
evidence. The CEO signs in three batches — intent, design, ship — and between
them the run does not stop except on one of the six interrupts a sensor raises
(drift, crossing the signed design, Loop A's bound, a missing service or
credential, an action not pre-authorized, a failed model check).
Every report — to the CEO or to the orchestrator — opens with the SITREP block
(SITUATION / ACTION / STATUS / NEXT) from
.claude/skills/aidlc/contracts/sitrep.template.md; NEXT always has a `CEO：` line.
```

## Verify

Confirm each `.claude/agents/*.md` frontmatter is valid, the skill copied,
`CLAUDE.md` has the devcrew section, and
`python3 .aidlc/tools/check_live.py --self-test`,
`python3 .aidlc/tools/check_formal.py --self-test` and
`python3 .aidlc/tools/check_tasks.py --self-test` each print `self-test ok` (and
`shasum -a 256` of each installed copy equals that of its `framework/tools/`
source, all 64 hex), and `.claude/settings.json` carries all five governance
hooks. Tell the user they can now ask the main
agent to "act as devcrew" or delegate to a specific role.
