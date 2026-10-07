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
| `framework/formal/Aidlc.tla` | checked · set sync | 2 items, Loop A 5/3, every scope | `NoPhasePastUnsignedBatch`, `DoneHasEvidence`, `LoopBounded`, `AsksOnlyForBatchOrInterrupt`, `StopsOnlyForCEO`, `NeverStuck`, `LoopTerminates`, `TroubleReachesCEO` |
| `Aidlc.tla` + `AidlcBroken.cfg` | the seeded broken variant | 1 item | must violate `NoPhasePastUnsignedBatch` |

Time is modelled as age classes of the claim's mtime (fresh ≤ STALE−MARGIN <
margin ≤ STALE < stale), and the timing assumptions are constraints on when
it may age (A1–A4, `framework/session-governance.md` § 8). The orchestrator is
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
