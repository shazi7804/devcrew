# Host adapter — KiroCrew

How to install the neutral `framework/` source into KiroCrew. Follow this when
`AGENTS.md` Step 1 resolved to KiroCrew.

## The three layers — where every wire lives

Same reading as the Mission Control adapter: **L3 never names an L1 path.** Every
arrow crossing a gap is either an install artifact or a host primitive.

```
┌─ L3 · devcrew — the AIDLC flow ─────────── source: <repo>/framework ───┐
│  P0 ─🔴▶ P0.5 ─🔴▶ P1 ─▶ P2 ─🔴▶ ┌ frontend ┐▶┌ qa       ┐▶ P5 ─▶ P6   │
│  intent  market     arch  design └ backend  ┘ ├ security ┤  deploy     │
│                                               └ auditor* ┘  release 🔴 │
│  12 roles   framework/agents/<role>.md        (*big diffs only)        │
│  protocol   framework/skills/aidlc/SKILL.md   phases · gates · harness │
│  memory     framework/memory/{lessons,adr,retro}.md                    │
│  Host-neutral: knows nothing about ~/.kiro, JSON files, or MCP.        │
└────────────────────────────────────────────────────────────────────────┘
     │                                          ▲
     │ (A) INSTALL-TIME TRANSFORM — once,       │ (C) Phase ∞ writes back:
     │     by you, following THIS file          │     retro/lessons → framework/
     ▼                                          │     PR, never self-merged
┌─ L2 · adapter ────────────── this is the layer this file defines ──────┐
│                                                                        │
│ (A) install transform — which file becomes which                       │
│   framework/agents/<role>.md ──────▶ ~/.kiro/agents/<role>.json        │
│     frontmatter.tools  ──map──▶ .tools · .allowedTools · .permissions  │
│     the body           ──────▶ .prompt  (file:// repo or extracted)    │
│     frontmatter.skills ──map──▶ .resources[]  skill://…/SKILL.md       │
│     memory: shared     ──────▶ .resources[]  file://…/framework/       │
│                                              memory/**/*.md            │
│     model: best-available ───▶ "auto"                                  │
│       EXCEPT reviewer ───────▶ a PINNED other-vendor id, resolved at   │
│                                install time from the model catalog     │
│       EXCEPT reviewer ───────▶ NO memory glob (memory: none)           │
│       EXCEPT auditor  ───────▶ no write capability + an explicit DENY  │
│                                                                        │
│ (B) harness ──▶ host primitive                                         │
│   dispatch      ▶ spawn_run(agents=[…]) · spawn_sub_agents             │
│   durable ledger▶ session_ledger_record          @kirocrew-core        │
│   lessons       ▶ learn_add                      @kirocrew-core        │
│   meta-loop     ▶ cron_add · cron_trigger        @kirocrew-cron        │
│   council       ▶ the llm-council skill                                │
│   🔴 CEO gate   ▶ ask_question, then END THE TURN — the turn itself IS │
│                   the suspension; this host has no decision QUEUE      │
│   budgets       ▶ resource_status before each heavy step               │
│   contracts     ▶ real files in the product repo                       │
└────────────────────────────────────────────────────────────────────────┘
     │ reads / writes                            ▲ CEO answers in the dashboard
     ▼                                           │
┌─ L1 · KiroCrew runtime ────────────────────────────────────────────────┐
│                                                                        │
│  local Mac = CONTROL CONSOLE ONLY — no model turn ever runs here       │
│        │                                                               │
│        │  SSM — the ONLY ingress (no public port, no ssh)              │
│        ▼                                                               │
│  the 128 GB EC2 gateway                                                │
│    ~/.kiro/agents/*.json  auto-loaded ──▶ dashboard agent switcher     │
│    @kirocrew-core ── spawn_run ──▶ role agent processes (the fan-out)  │
│    @kirocrew-cron ── schedules the meta-review digest                  │
│    kiro-cli  = the model backend that actually runs a role's turns     │
│        │                                                               │
│        ▼  fan-out cap: resource_status FIRST; serialize when tight     │
│    the gateway bills hourly ──▶ pause a long-idle run, do not spin     │
└────────────────────────────────────────────────────────────────────────┘
```

## Known degradation on this host

State these to the user at install time rather than letting them be discovered
mid-run. This is the strongest of the three hosts — the list is short.

- **A 🔴 gate is a suspended *turn*, not a durable row.** Mission Control has
  `decisions.json`; here the turn ending *is* the suspension, so nothing outside
  the ledger records that a gate is open. `session_ledger_record` the pending gate
  **before** ending the turn, or a restart cannot tell "waiting on the CEO" from
  "never ran" — and the second guess is the dangerous one.
- **The gateway bills hourly.** An idle suspended run costs money while it waits,
  so a long 🔴 gate should pause the gateway rather than hold it.

## What KiroCrew expects

- Agents: one JSON per agent at `~/.kiro/agents/<name>.json` (auto-loaded, shows
  in the dashboard switcher, dispatchable via `spawn_run(agents=[...])`).
- Skills: referenced from an agent's `resources` as
  `skill://<abs-path>/SKILL.md`.
- Shared memory: any `file://<glob>` in `resources` is mounted read-only into
  the agent's context. Use this to mount `framework/memory/`.
- MCP: agents reach spawn / ledger / cron / council via the `kirocrew-core` and
  `kirocrew-cron` MCP servers.

## Neutral → KiroCrew tool mapping

| Neutral tool | KiroCrew tools |
|---|---|
| read | `fs_read`, `grep`, `glob` |
| write / edit | `fs_write` |
| shell | `execute_bash` |
| search | `grep`, `glob`, `code` |
| web | `web_fetch`, `web_search` |
| spawn | `@kirocrew-core` (spawn_run/spawn_sub_agents), `@kirocrew-cron` |
| memory | `@kirocrew-core` (session_ledger, learn_add), `introspect` |

`model: best-available` → `"auto"` (KiroCrew resolves the model), unless the user
pinned a specific one.

## Per-agent JSON to generate

For each `framework/agents/<name>.md`:

1. Parse the frontmatter (`name`, `tools`, `skills`, `memory`) and the body.
2. Write the body to a prompt file the JSON can reference (either point `prompt`
   at an extracted `.md` under the repo, or at `framework/agents/<name>.md`
   itself — KiroCrew reads the whole file as the prompt; the frontmatter is
   harmless preamble, but extracting a clean body is tidier).
3. Emit `~/.kiro/agents/<name>.json`:

```json
{
  "name": "<name>",
  "description": "<from frontmatter>",
  "model": "auto",
  "tools": ["<mapped tools>", "@kirocrew-core", "@kirocrew-cron"],
  "allowedTools": ["fs_read","grep","glob","web_fetch","web_search","@kirocrew-core"],
  "resources": [
    "file://<repo>/framework/memory/**/*.md",
    "skill://<repo>/framework/skills/aidlc/SKILL.md",
    "skill://<mapped host skill for each entry in frontmatter `skills`>"
  ],
  "includeMcpJson": false,
  "prompt": "file://<repo-or-extracted-prompt-path>",
  "mcpServers": {
    "kirocrew-core": {"command":"<kirocrew bin>","args":["mcp-core"]},
    "kirocrew-cron": {"command":"<kirocrew bin>","args":["mcp-cron"]}
  },
  "permissions": {"rules":[
    {"capability":"mcp","match":["kirocrew-core/*","kirocrew-cron/cron_add","kirocrew-cron/cron_list","kirocrew-cron/cron_trigger"],"effect":"allow"},
    {"capability":"web_fetch","effect":"allow"},
    {"capability":"web_search","effect":"allow"}
  ]}
}
```

- The orchestrator `orchestrator` gets the full tool set + cron (it schedules the
  monthly tech-refresh scan and dispatches roles). Role agents get the `build`
  set + `kirocrew-core`.
- **`auditor` is read-only by design** (its frontmatter has no `write`/`edit`): give
  it the read/search/shell/web set only, and add a deny rule for the write
  capability rather than relying on `allowedTools` alone. Verify at install that
  `auditor.json` grants nothing that can edit files — an auditor that can fix its
  own findings is auditing itself. Where the catalog allows it, ALSO pin its
  `model` to a different vendor than the implementers' (same mechanism as the
  reviewer pin below); unlike the reviewer's, this is a strengthening, not a
  requirement, so fall back to `auto` and say so.
- Map each neutral skill name in frontmatter `skills` to a KiroCrew skill path:
  `aidlc` → this repo's `framework/skills/aidlc/SKILL.md`; the others
  (`frontend-design-workflow`, `llm-council`, `goal-conductor`, `web-preview`,
  `web-verify`, `deploy-web`, `artifact-deploy`) → the installed
  `~/.kiro/crew/skills/<name>/SKILL.md`. If one is absent, note it to the user
  rather than inventing a path.
- Find the kirocrew binary from the running host (it is the command backing the
  core MCP server); do not hardcode a version-specific path from memory.

## Verify

Parse every generated JSON, confirm each `prompt`, `skill://`, and `file://`
memory path resolves, and confirm `orchestrator` is listed by the host's agent
listing. Then tell the user to pick **orchestrator** in the dashboard agent switcher.

## Reviewer model pin

`reviewer` must run on a DIFFERENT vendor than the dev team. The dev
team runs Anthropic (`auto` resolves to Claude), so pin the reviewer JSON's
`model` to the strongest OpenAI model available rather than `auto`. Resolve
this at INSTALL time: query the host's model catalog (e.g.
`kiro-cli chat --list-models --format json`), pick the strongest OpenAI id
currently offered, and WRITE THAT CONCRETE VERSION into the generated
`reviewer.json`. The reviewer's JSON must NOT include the shared
framework/memory glob in its resources (memory: none) — an unbiased self-evolution
review requires no team memory; verify this at install. The pinned version lives only in the install artifact,
never in the framework source — so a future clone re-resolves to whatever is
strongest then.
