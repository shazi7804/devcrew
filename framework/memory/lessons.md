# Team Lessons — shared across all devcrew roles

> This is the team's shared experience. Every role mounts this directory.
> Append durable corrections here (what to do / what not to do). Keep entries
> one-liners with a date. Do NOT record one-off, project-specific facts — those
> live in the project's own SDD docs, not here.

## Format
- `YYYY-MM-DD [role] rule — NOT: the mistake it prevents`

## Lessons
- 2026-09-19 [team] The intent contract (requirements.md) is supreme; verify every gate against it — NOT: accepting a phase output that drifted from a signed requirement.
- 2026-09-19 [architect] Web-search the current tech landscape before selecting a stack — NOT: defaulting to a familiar or training-cutoff stack without checking what is current.
- 2026-09-19 [team] Self-changes to any agent/skill land only through a PR + the QA gate — NOT: rewriting an agent's own operating instructions in place.
- 2026-10-01 [team] A framework change starts at Phase 0: a CEO-signed proposals/<slug>/requirements.md, then PR → CI → qa (against that proposal) ∥ reviewer → CEO merge — NOT: going from a retro straight to a PR, which leaves QA nothing to verify and the reviewer no intent to judge against. Supersedes the 2026-09-19 "PR + the QA gate" line.
- 2026-10-01 [team] Neutral files name no host tool and no machine (invariant 9); run tools/check_neutral.py over the whole tree — NOT: trusting diff review, which never sees a leak that already exists (the "128GB EC2" line survived five releases that way).
- 2026-10-01 [qa] Verify a "no file still says X" requirement by searching for the concept (every place that describes the path), not the literal string — NOT: grepping one phrase; the literal "PR + QA gate" had one hit, while four stale descriptions of the same path used other words.
- 2026-10-06 [team] Nothing is done until it runs on the real service: every Rn is Verify: live by default, proven by a probe's evidence file, and check_live.py is a Phase-4 sensor — NOT: closing requirements on green tests against fake upstreams, a fake DOM and seed data while the backend was never deployed (a project reported two features done that way).
- 2026-10-06 [orchestrator] Turn a CEO ruling on how work is verified into a mechanism the same day (a sensor, a template field, a gate) — NOT: leaving "connect everything for real" as a sentence in a prompt; it was said twice and never ran.
- 2026-10-06 [devops] Decide whether Phase 5 runs from the repo as it is (a server/API/datastore = a runtime), never from a project note — NOT: trusting "no runtime, P5 downgraded" after a backend appeared, which skipped every deploy and smoke test.
