# Host adapter — KiroCrew

How to install the neutral `framework/` source into KiroCrew. Follow this when
`AGENTS.md` Step 1 resolved to KiroCrew.

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

- The orchestrator `devcrew` gets the full tool set + cron (it schedules the
  monthly tech-refresh scan and dispatches roles). Role agents get the `build`
  set + `kirocrew-core`.
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
memory path resolves, and confirm `devcrew` is listed by the host's agent
listing. Then tell the user to pick **devcrew** in the dashboard agent switcher.

## Reviewer model pin

`devcrew-reviewer` must run on a DIFFERENT vendor than the dev team. The dev
team runs Anthropic (`auto` resolves to Claude), so pin the reviewer JSON's
`model` to the strongest OpenAI model available rather than `auto`. Resolve
this at INSTALL time: query the host's model catalog (e.g.
`kiro-cli chat --list-models --format json`), pick the strongest OpenAI id
currently offered, and WRITE THAT CONCRETE VERSION into the generated
`devcrew-reviewer.json`. The pinned version lives only in the install artifact,
never in the framework source — so a future clone re-resolves to whatever is
strongest then.
