# qa — QA

> The intent gate: proves that every signed requirement is met. "Tests pass" is
> not enough.

[← The team](../../README.md#the-team) · Source prompt:
[`framework/agents/qa.md`](../../framework/agents/qa.md)

## At a glance

| | |
|---|---|
| **Phase** | 4, in parallel with `security` and, on a large diff, `auditor` |
| **Reads** | `requirements.md` 🔒 · `standards.md` 🔒 · the implementation PRs |
| **Produces** | A requirement → evidence → verdict table, and the QA verdict YAML |
| **Gate** | CI and the live sensor are green, every Rn/Nn is met on the real service, and no QA blocker is open |
| **Tools** | read · write · edit · shell · search · web |
| **Skills** | aidlc · web-verify · mobile-verify |
| **Memory** | Shared team memory |

## How it runs the gate

1. **Sensors first**: lint, typecheck, test and build, using the project's
   real commands, plus `check_live.py --rerun`, which re-runs every probe
   against the real service and scans production code for fakes. A red sensor
   fails the gate before intent is judged.
2. **Traceability**: every `Rn` must trace to a PR (`Closes Rn`) and to a test.
   Every `Nn` must trace to its proof: a benchmark, an audit or a scan. A
   requirement with no evidence fails, and so does one proven only on a fake
   (a stubbed upstream, a fake DOM, seed data), and so does a PR that claims no
   requirement.
3. **Standards conformance**: it re-computes the `standards.md` hash, then
   checks the delivered work against the file.
4. **Exercises the flows like a real user**, including edge cases, empty states
   and error paths.
5. **Returns a verdict block** that the orchestrator parses. A missing or
   malformed block fails the gate.

It verifies framework changes the same way. Every `Rn` in the proposal's
signed `proposals/<slug>/requirements.md` needs evidence, and it also looks for
behavior regressions in the roles the change touches.

On a mobile app it verifies on a device/OS matrix, including permissions (and
the deny path), deep links, offline use, the app lifecycle and interruptions.

## What it will not do

- Judge whether code is lean. That is the auditor's job, and QA notes any waste
  for the auditor instead.
- Judge vulnerabilities. That is Security's job.
- Pass a requirement because the code is tidy, or fail one because it isn't.

## Where it sits

```
frontend · backend PRs ──▶ qa ∥ security ∥ auditor ──▶ gate ──FAIL──▶ back to P3
                                                    └─PASS──▶ devops / release
```
