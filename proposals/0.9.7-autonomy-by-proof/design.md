# Design — devcrew 0.9.7: autonomy earned by proof

> The Phase-1 record for this change: what was chosen, against what, and what
> the model checker found once it ran. Requirements: `requirements.md`.

## 1. The formal tool for the framework's own protocols

Landscape checked on 2026-10-08 (release pages, not memory — invariant 5):

| Candidate | State | For this job |
|---|---|---|
| TLA+ / **TLC 2.19** (tla2tools **1.7.4**, stable) | 1.8.0 exists only as a rolling pre-release (2026-10-06) | exhaustive explicit-state checking at bounds; safety and liveness under WF/SF fairness; one jar, a JVM |
| Apalache 0.62.3 (2026-10-01) | active | symbolic, bounded; needs type annotations; stronger at large parameters, weaker for liveness |
| Quint | active | a front end that runs on the TLC/Apalache back ends; adds a TypeScript toolchain |
| Alloy 6 | active | relational; temporal properties exist but fairness-based liveness is not its home |
| P | active | systematic testing of state machines — sampling, i.e. `tested`, not `checked` |
| TLAPS · Lean 4 · Verus · Dafny | active | `proved` (unbounded); costly per property; Verus is Rust-only |

**Chosen: TLA+ with TLC 1.7.4**, pinned by sha256 in `tools/check_models.py`.
The protocols here are small concurrent state machines whose load-bearing
claims are one safety property (one orchestrator) and three liveness
properties (no deadlock, Loop A terminates, a dead holder is replaced). TLC
checks both kinds exhaustively at stated bounds, and the same checker does
trace validation, so model and code are tied without a second tool. The JVM
is needed only in CI for devcrew itself; nothing is installed into projects.

Not chosen, and why: a proof (`proved`) is not needed for the claims made —
the bounds are stated (3 sessions for safety, 2 for liveness), and nothing in
the arguments depends on a fourth session. That is a recorded limit, not a
proof of the general case.

## 2. The models

| Model | Level · conformance | Bounds | Properties |
|---|---|---|---|
| `framework/formal/Election.tla` | checked · trace | 3 sessions (safety), 2 (liveness) | `AtMostOneActing`, `ActingHoldsTop`, `HooksEnd`, `ElectedAfterGone` |
| `framework/formal/ElectionV096.tla` | the seeded broken variant | 3 sessions | must violate `AtMostOneActing` |
| `framework/formal/Aidlc.tla` | checked · set sync | 2 items, Loop A 5/3, every scope | `NoPhasePastUnsignedBatch`, `DoneHasEvidence`, `AtBoundNoProgress`, `AsksOnlyForBatchOrInterrupt`, `StopsOnlyForCEO`, `NeverStuck`, `LoopTerminates`, `BoundInterrupts`, `TroubleReachesCEO` |
| `Aidlc.tla` + `AidlcBroken.cfg` | the seeded broken variant | 1 item | must violate `NoPhasePastUnsignedBatch` |

Time is modelled as age classes of the claim's mtime (fresh ≤ STALE−MARGIN <
margin ≤ STALE < stale), and the timing assumptions are constraints on when
it may age (A1–A5, `framework/session-governance.md` § 8). The orchestrator is
an LLM, so `Aidlc.tla` has no trace to validate; its conformance is that its
stages, batches and interrupts are the ones SKILL.md names
(`tools/check_repo.py`).

## 3. What the checker found

1. **0.9.6's election admits two orchestrators** — TLC, 14 steps, 2 seconds.
   A holder resuming after its lease went stale refreshed it with `utime`
   while a newcomer that had read it as stale renamed it away; both acted.
   Root cause: `rename` and `utime` act on whatever file is at the path now,
   not on the file that was read. The repo's race test (20 concurrent
   takeovers → exactly one winner) passed all along: it never paused a
   process between its read and its write, and never resumed the holder.
2. **Fix:** generations. `ORCHESTRATOR.<n>.claim` is written in full and
   published with `os.link`, which refuses an existing name; names are never
   reused, so "create n+1" is a compare-and-swap. The holder trusts its own
   lease only below STALE−MARGIN and must re-win n+1 above it; every step that
   touched a claim is followed by a verify. Any beat may take a free claim, so
   a crashed orchestrator is replaced without a new window (liveness g).
3. **More autonomy breaks the lease unless the heartbeat is per tool call.**
   With beats only at the ends of a turn, a turn longer than STALE lets a
   second session take over while the first is still acting (assumption A2).
   The host adapters add a beat after every tool call.
4. Two bugs were in the *model*, not the code, and were caught by the
   counterexamples: A1 first bounded only the touch step (it bounds the whole
   hook run), and closing a session did not end it (which let fairness be
   dodged). Liveness was checked for vacuity: two deliberately false
   properties (`running ~> finished`, an item in progress always closes) are
   rejected.

## 4. Trace validation

`boot.py` with `DEVCREW_TRACE=<file>` logs each step that touches a claim
under an exclusive lock, so the log's order is the real order. `tools/check_models.py` runs
five scenarios — scripted (every branch), a stampede (8 sessions released by
one barrier, twice), three seeded crowds — turns each log into `TraceData.tla`,
and asks TLC whether some behaviour of `Election.tla` matches every step. A
mutant `boot.py` (0.9.6's "refresh my lease whatever its age") must be
rejected, and is.

Honest limit: interpreter start-up spreads concurrent hook runs out, so the
crowds exercise little true contention (one failed create per run, typically).
Exhaustive interleavings are the model's job; trace validation's job is that
each real step means what the model says it means.

## 5. Sensors

`check_tasks.py` (TASKS.md) and `check_formal.py` (formal evidence) are stdlib
Python beside `check_live.py`, which they import — its requirement-field
parser and its freshness rule (`drifted`) are shared, not copied.

## 6. What the independent reviews found, and what changed

The cross-vendor reviewer (`gpt-5.6-sol`, no team memory, read-only) returned
**REJECT** on the first implementation; the auditor returned PASS-WITH-DEBT.
The reviewer's findings, and what was done:

| # | Finding | Done |
|---|---|---|
| 1 | `Aidlc.tla` let build start with the intent batch unsigned when a scope skipped arch and design — the property checked only the design batch | `Required(s)` is cumulative; the property checks every batch before a stage |
| 2 | Loop A at exactly `5/5` / `stalled 3/3` passed; in the model, prove/close stayed enabled at the bound, so fairness did not force the interrupt | `check_tasks.py` requires `blocked on loop-bound` at the bound; the model disables prove/close there; new `AtBoundNoProgress`, `BoundInterrupts` |
| 3 | `check_formal.py` accepted `command: true`, a dummy source, `vacuity: false` | the command must name a source and not be a no-op; every check carries an `expect` its output must match, on record and on re-run; a bare `false` vacuity run is refused; `check_tasks.py --rerun`; the limit (stored evidence is a claim) is written into the sensor |
| 4 | a TASKS.md whose first `Signed:` file was not the requirements emptied every check; the Gate parser was loose | both refused |
| 5 | this proposal's Property lines were added after the ruling; `design.md` was never signed in a design batch | **open — the CEO's** (see TASKS.md) |
| 6 | `Property: none` examples lacked Formal / Conformance lines | added |
| 7 | traces omitted the generation number and the outcome of touch / release; failed file operations were swallowed | logged; ghost variables in `ElectionTrace.tla` tie generation numbers; a failed `utime` now gives up the role (modelled as `TouchFail`); a second mutant (skipping a generation) must be rejected |
| 8 | the pin was said to "only make workers" | corrected: a holder keeps its claim and is warned at every beat |
| 9 | no seeded broken liveness variant | `ElectionLiveBroken.cfg` (0.9.6's start-only takeover → `ElectedAfterGone` fails), `AidlcLiveBroken.cfg` (no raise → `TroubleReachesCEO` fails) |
| 10 | a budget overrun was a seventh stop; `cross-design` had no executable sensor | the budget stop is `loop-bound`; `check_tasks.py` raises `cross-design` when a design-batch file changes — the rest of cross-design stays the architect's judgment, and says so |
| 11 | CI not run, QA not run, a second reviewer required (this edits `reviewer.md`) | QA and a second reviewer run on the fixed tree; CI needs the branch pushed — **the CEO's** |
| 12 | the verdict schema listed invariants 1–10 | 1–11 |

From the auditor: a beat listed the claims directory twice and the directory
grows by one entry per election — `verify` is now one stat and `top_gen`
probes upward from a hint (generations are contiguous); `orchestrator.md`'s
copy of the interrupt list became a pointer; the models job has its own
workflow with a path filter and a cached checker. Kept as debt: the 945-byte
gate map stays in SKILL.md because R6 requires it there; `ElectionV096.tla`
keeps its own copy of the lifecycle layer, since it is a frozen record of the
old code.

Also found while fixing: the 3-session safety check grew past a 15-minute
timeout once the failure branches were modelled; sessions are symmetric, so it
now runs under `SYMMETRY Permutations(Sessions)` (safety only — symmetry is
unsound for liveness, which runs at 2 sessions without it).

## 7. Round 2: the re-review, a second reviewer, and QA

`gpt-5.6-sol` re-reviewed the fixes (REJECT; 5 of 12 resolved), `glm-5` —
a third vendor, required because this change edits `reviewer.md` — reviewed
independently (REQUEST-CHANGES), and QA re-ran every piece of evidence
(FAIL). They converged; each finding was real:

| Finding (who) | Done |
|---|---|
| R12's signed Property still named `LoopBounded`, which the model no longer defines (reviewer, QA) | Property corrected; `check_formal.py` now fails a Property that names a TLA+ definition no source defines. A signed-text change: TASKS.md is at `drift` until the CEO re-signs |
| `fake-requirements.md` passed as the requirements (reviewer) | the name must be exactly `requirements.md` |
| the stalled counter was optional; `stalled 2/1` passed (reviewer) | `n/5 stalled k/3`, always, each against its own bound |
| the evidence's `tool` was bound to nothing (reviewer) | the command or a source must name it; that a command is a *faithful* checker is a reviewer's reading, and the sensor says so |
| touch / verify / release carried no generation in the trace (reviewer) | logged and bound to what the session read or made; a third mutant (touch an old generation) must be rejected |
| a failed create with a still-valid read was not in the model (QA) | `CreateFail`; liveness then needed **A5** — a file operation does not fail forever — which TLC demonstrated by electing nobody on a disk full forever |
| a Done line's status after a plain hyphen passed (QA) | any status-shaped tail is refused |
| `private axiom`, Coq `Parameter`/`Hypothesis`, Isabelle `axiomatization`; a Property starting "none of …" read as none (QA) | caught |
| every Done item went stale when a non-`.md` verdict was committed; the R12/R13/R15 live probes lost the checker's environment; a `local` item could never re-run fresh (QA) | the verdict is `.md`; the probes name `$JAVA` / `$TLA2TOOLS_JAR`; a local probe re-run on a clean checkout of HEAD is HEAD's proof |
| `check_repo` compared only the sets block (QA) | the batch and interrupt tables too |
| `unauthorized`, part of `cross-design` and the budget part of `loop-bound` are role judgments, not machine checks (both reviewers) | named per interrupt in SKILL.md (machine · judgment), fail-closed, and in invariant 11; mechanising them needs the host and is debt D6–D8 — **whether that is acceptable for merge is the CEO's call** |
| an interrupt looked like a dropped sign-off (glm-5) | SKILL.md: an interrupt is still a hard stop the CEO decides |
| "trace-validated" over-claimed (glm-5) | "sampled real runs checked against the model"; exhaustiveness is the model's |
