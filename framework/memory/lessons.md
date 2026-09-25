# Team Lessons — shared across all devcrew roles

> This is the team's shared experience. Every role mounts this directory.
> Append durable corrections here (what to do / what not to do). Keep entries
> one-liners with a date. Do NOT record one-off, project-specific facts — those
> live in the project's own SDD docs, not here.

## Format
- `YYYY-MM-DD [role] rule — NOT: the mistake it prevents`

## Before appending, run the wording through this filter
A lesson earns a place here only if it survives being stripped of the stack it was
learned on. Check each candidate:

1. **Is any noun in it specific to one technology?** (a CSS concept, a framework's
   lifecycle, a particular file layout) → rewrite in terms of the underlying
   mechanism, or it belongs in the project's own lessons file, not here.
2. **Would a backend, infra, or CLI role recognize this problem?** If not, either
   find its general form or leave it downstream.
3. **Is it a rule, or is it one project's fact?** Facts go in that project's docs.

This filter exists because the first batch promoted from field use arrived with
front-end assumptions baked into the wording, and review had to send it back.

## Lessons
- 2026-09-19 [team] The intent contract (requirements.md) is supreme; verify every gate against it — NOT: accepting a phase output that drifted from a signed requirement.
- 2026-09-19 [architect] Web-search the current tech landscape before selecting a stack — NOT: defaulting to a familiar or training-cutoff stack without checking what is current.
- 2026-09-19 [team] Self-changes to any agent/skill land only through a PR + the QA gate — NOT: rewriting an agent's own operating instructions in place.

## Promoted from field use (first real project, 2026-09)

> These generalize. Project-specific findings stayed in that project's own files.

- 2026-09-25 [qa] Prove every new assertion can go red by breaking the implementation on purpose — NOT: reporting a green suite as evidence (first real mutation run scored 0/6, and both causes were in the tests).
- 2026-09-25 [qa] A mutation whose anchor does not occur exactly once is a FAILURE — NOT: logging that the patch did not apply and counting the round as passed.
- 2026-09-25 [qa] When a mutation stays green, first check the code is reachable — NOT: assuming a weak assertion and rewriting it, when the target was dead code shadowed by a later definition.
- 2026-09-25 [qa] Assert which items must be present — NOT: asserting how many there are (a "≥12" check on 14 items passes after deleting two).
- 2026-09-25 [qa] Before asserting a value was reset, set it to something else and assert that worked — NOT: asserting a reset that was already true on entry, which passes regardless of the implementation.
- 2026-09-25 [qa] Derive expected values from the loaded state — NOT: reading them off the source data file, when other modules push fixtures at load time.
- 2026-09-25 [qa] Decide per assertion whether a failing old one is spec or fossil — NOT: reverting correct new behavior, or editing correct source, to keep a suite green.
- 2026-09-25 [team] Degrading a gate requires substituting, labelling `DEGRADED:` in the verdict, and never claiming the pass — NOT: reporting green gates on a host that could not run them.
- 2026-09-25 [team] Before accepting a substitute, name the property the gate's power comes from and check the substitute has it; if not, HOLD instead — NOT: writing "degrade to <same-thing-minus-the-point>" into the protocol, which every later session reads as permission.
- 2026-09-25 [team] Map the host's real capabilities before Phase 0 — NOT: discovering mid-run that a gate's tool does not exist here, and quietly skipping it.
- 2026-09-25 [team] State plainly when a claim comes from training knowledge rather than a live check — NOT: presenting unverified recall as something that was looked up.
- 2026-09-25 [team] On a tree where another session may be writing, every git restore command is banned — NOT: using `git checkout <file>` to undo a test mutation and destroying a peer session's work.
- 2026-09-25 [fe+be] Extend a foundational artifact by non-breaking addition (defensive initialization, versioned migration, late-bound accessor, override applied later in composition order) — NOT: editing the frozen base in place to satisfy one feature.
- 2026-09-25 [fe+be] Compute derived values on demand — NOT: snapshotting them at load from mutable state, which cannot see the state change and presents as two views of the same data disagreeing.
- 2026-09-25 [fe+be] Prefer the platform primitive over a hand-rolled equivalent — NOT: reimplementing it, which forces you to invent a granularity or precision the platform already settled, silently lossy on data that does not fit it, and forfeits the behavior you would have got for free.
- 2026-09-25 [design] One action gets one entry point, and its name describes what it does now — NOT: three implementations of one behavior, or a name left over from what it used to do.
- 2026-09-25 [team] At a 🔴 gate write prose, drop requirement codes, ask exactly one question, then stop — NOT: a status dump with three questions, which gets answered on the easiest one.
- 2026-09-25 [team] Resume by reading the ledger, then team memory, then the working tree — NOT: starting a session by writing code, which redoes or undoes something.
- 2026-09-25 [qa] When a defect cannot be reproduced, write several independent defenses and label the reasoning as inference — NOT: recording a guessed root cause as fact.
