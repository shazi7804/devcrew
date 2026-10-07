# Multi-session governance — election, lease, and the escape hatch

`ARCHITECTURE.md` draws one spine with one orchestrator on it. That is true of
the *flow*, and it is false of the *runtime* the moment a human opens a second
window. This file defines the layer that makes the spine survive that, and it is
**host-neutral**: it names no hook, no tool and no filename outside `<state>/`.
Each host adapter wires it to its own lifecycle events (`hosts/claude-code.md`
does it with hooks).

Install it whenever the host can run more than one interactive session against
one repo. On such a host, skipping it does not mean "no governance" — it means
the governance is whatever the sessions each decided to believe.

## 1. The assumption that breaks

AIDLC's dispatch model is *one orchestrator, N in-process subagents*. Those
subagents share a context, so two of them cannot silently disagree about who
owns a card. Independent sessions have no shared context at all:

```
      AIDLC assumes                    what actually happens
┌──────────────────────────┐      ┌──────────────────────────┐
│      orchestrator        │      │ session A │ session B    │
│      ╱     │     ╲       │      │  "I am    │  "I am the   │
│  sub-1   sub-2   sub-3   │      │   the     │   orchestra- │
│                          │      │   orch."  │   tor too"   │
│  one context ⇒ they      │      │                          │
│  cannot disagree         │      │  no shared context ⇒     │
└──────────────────────────┘      │  both sign requirements  │
                                  └──────────────────────────┘
```

Three failures follow, and they are *not* fixed by telling the sessions to be
careful — every one of them happened in a real repo with the rule written down:

| Failure | What it costs |
|---|---|
| Two sessions claim the orchestrator role | Two Phase-0 contracts for one intent |
| Two sessions run the same card | Double spend, then a merge conflict |
| A session guesses another is dead and takes over | It overwrites a live session's work |

## 2. Four invariants

1. **At most one session acts as orchestrator at any instant** — guaranteed
   by a compare-and-swap the kernel performs, not by everyone remembering to
   look first, and *model-checked* under the assumptions of §8
   (`framework/formal/Election.tla`).
2. **Nobody has to designate anybody.** A mechanism that needs a human to answer
   "who is in charge?" on every session start is a mechanism that will not run.
   *This is the whole reason the layer exists* — see §7.
3. **Liveness is never inferred.** A session is alive because it *says so*
   (heartbeat) or because the host's session list shows it — never because a
   socket, pid or lock file happens to exist.
4. **Failure is closed, except the governance script itself, which fails open.**
   Cannot tell whether the holder is alive ⇒ do not take over. But a broken
   governance script must never stop a session from starting: a mechanism that
   locks people out of their own repo is worse than the disorder it prevents.

## 3. The mechanism

```
                    the human — zero input per session
                              │
                              ▼ (opens a window / types anything)
┌─ host lifecycle events ───────────────────────────────────────────┐
│  SESSION START   ─┐                                               │
│  EVERY TURN (both ends)  the HOST runs these, not the model. A    │
│  AFTER EVERY TOOL CALL   rule the model must remember to run is   │
│  SESSION END     ─┘      not a mechanism.                         │
└────────┬──────────────────────────────────────────────────────────┘
         │ passes in: a session identity stable for the whole session
         ▼
┌─ boot.py ── one script, three modes, always exit 0 ───────────────┐
│  start  elect, then inject the role + the board into the context  │
│  beat   the same election: refresh, renew, take a free claim, or  │
│         learn "I was demoted" — and say so, mid-turn included     │
│  end    mark the claim released if it is mine                     │
└──┬──────────────────────────────┬─────────────────────────────────┘
   │ link (CAS) / utime / marker  │ read only
   ▼                              ▼
┌─ <state>/claims/ ──────────┐  ┌─ <state>/ORCHESTRATOR.pin ──────┐
│  ORCHESTRATOR.<n>.claim    │  │  the ESCAPE HATCH.              │
│    the highest n holds     │  │  Absent = normal.               │
│    made by link(2): the    │  │  Present = a human pinned the   │
│      kernel refuses a name │  │    role ⇒ election is suspended │
│      that exists           │  │  A human can override the       │
│    lease: its own mtime    │  │  machine. Never the reverse.    │
│  ORCHESTRATOR.<n>.released │  │                                 │
│    marker: n was let go    │  │                                 │
└────────────┬───────────────┘  └─────────────────────────────────┘
             │ orchestrator only
             ▼
┌─ board command (optional, host-supplied) ─────────────────────────┐
│  JOINs TASKS.md + <state>/claims/ + a liveness list into one      │
│  page. GENERATED, never stored: a hand-written board is state in  │
│  a governed file, and governed state goes stale by design.        │
└────────────┬──────────────────────────────────────────────────────┘
             ▼ injected into the model's context
   "you are the orchestrator" + board + read-discipline
   "you are a worker" + the two prohibitions + live claims
```

**The claim is a generation.** `<state>/claims/ORCHESTRATOR.<n>.claim`; the
highest `n` present is the claim. A session takes the role by creating
generation `n+1`: it writes the whole file under a temporary name
(`.new.<pid>.<id>`) and `link`s it into place. `link` refuses a name that
already exists, and a name is never reused, so this is a **compare-and-swap**:
it succeeds only if nobody made `n+1` since this session read `n`. No reader
ever sees a half-written claim. Releasing creates the marker
`ORCHESTRATOR.<n>.released`; nothing is renamed and nothing is deleted, so
every generation stays as evidence of who held the role and when.

## 4. Election — the decision tree

Run at session start **and at every beat**. `me` = this session's identity;
`top` = the highest generation, read once; `age` = now − its mtime.

```
START or BEAT
│
├─ <state>/ORCHESTRATOR.pin exists?
│  └─ YES ─▶ START: WORKER (human pinned) · BEAT: take nothing; if I
│            still hold the claim, WARN me the pin now outranks me
├─ NO
│
├─ top is mine (not released) and age ≤ STALE − MARGIN?
│  └─ YES → touch its mtime → is it still the top?
│            ├─ YES ───────────────────────────────▶ ORCHESTRATOR (kept)
│            └─ NO ────────────────────────────────▶ WORKER (superseded)
│
├─ top is mine but older than that     ─┐
├─ top released, or there is none      ─┼─▶ link generation n+1
├─ top is someone else's, age > STALE  ─┘     ├─ linked, still the top
│                                             │    ▶ ORCHESTRATOR
│                                             │      (renewed / first /
│                                             │       took over ⚠)
│                                             └─ name existed ─▶ WORKER
│                                                  (someone else won n+1)
│
├─ top is someone else's, age ≤ STALE ─────────────▶ WORKER (lease live)
│
└─ ANY exception ──────────────────────────────────▶ exit 0, block nothing

 ⚠ took over: write in TASKS.md who took what. The predecessor's in-process
   subagents do NOT transfer: re-dispatch those cards, do not "continue" them.
```

Every leaf is one of two words. There is no "ask a human" leaf — that is
invariant 2, and it is the difference between a mechanism and a convention.

Two consequences of running the same tree at every beat:

- **A crashed orchestrator is replaced without anyone opening a window.** The
  next beat of any worker that finds the claim released or stale takes `n+1`.
- **A demotion is noticed at the next tool call**, not at the next turn. The
  injected text tells the session to stop acting as orchestrator at once
  (assumption A3).

## 5. The lease — why a heartbeat and not a liveness guess

The claim's **mtime is the lease**. The holder refreshes it at both ends of
every turn and after every tool call; nobody else touches it.

```
 t ─────────────────────────────────────────────────────────────────▶
 A  start ─beat─beat─beat────────── window closed (END: released)
    ▲                                        │
    └ linked generation 1                    └ the next start or beat
                                               takes generation 2 —
                                               no wait

 A  start ─beat─beat─ ✗ crash (no END ran)
                      ├──────── STALE ────────┤
 B                  start                   beat
                    WORKER                  ORCHESTRATOR (took over:
                    (lease still live —      generation 2; generation
                     do NOT take over)       1 stays as evidence)
```

The holder's own clock has a margin. A holder whose lease is older than
`STALE − MARGIN` does **not** just refresh it: by then a newcomer may already
have read it as stale and be on its way to `link` the next generation. So the
holder competes for `n+1` like anyone else, and the CAS lets exactly one win.
`MARGIN` (default 5 min, `DEVCREW_MARGIN_SECONDS`) is the longest pause a
process may take between two of its steps — assumption A1.

Two properties matter more than the threshold's value:

- **A clean exit costs nothing.** `END` releases the lease, so the normal case
  never waits `STALE`. The threshold only covers crashes.
- **`STALE` trades one wrong answer for the other.** Too short: you take over a
  session that was merely slow, and overwrite live work. Too long: the repo has
  no orchestrator for that long. Start at 45 min (`DEVCREW_STALE_SECONDS`) and
  tune with evidence, not taste — the cost is asymmetric, so err long.

**Do not substitute anything for the heartbeat.** The tempting signals are all
wrong, and both directions have been measured on a real host:

| Signal | Why it lies |
|---|---|
| A socket/pid file exists | Measured: the file was there, the process was alive, and it was an orphan — detached from any terminal, absent from the host's session list, unreachable. You wait forever for a reply. |
| The socket/pid file is gone | Those names are *process* identity, not *session* identity. A process can be replaced while the session lives on. |
| Name in the lock == name in the session list | Measured false positive: the lock said `brand-lockup`, the list said `session-5b` — the same live session under two names. |

⇒ **Liveness comes from the heartbeat, or from the host's own session list.**
A socket may identify *who is who*; it is never evidence of life or death.

## 6. Why a generation, and not one path renamed on takeover

Up to 0.9.6 the claim was ONE path, `ORCHESTRATOR.claim`, taken over by
`rename` once stale. A model checker found two orchestrators in 14 steps
(`framework/formal/ElectionV096.tla`, kept as the seeded broken variant):

```
 A holds the claim; A goes idle past STALE
 A  resumes a turn: reads its own (stale) lock ── about to utime it
 B  starts: reads the lock as stale ───────────── about to rename it
 A  utime(LOCK) ✓  ⇒ A ACTS as orchestrator
 B  rename(LOCK → evidence) ✓   ← moves A's now-fresh lock away
 B  create(LOCK) ✓              ⇒ B ACTS as orchestrator too
```

The flaw is in the code, not in the environment — it happens under the same
assumptions the current design needs. `rename` and `utime` act on **whatever
file is at the path now**, not on the file that was read. A 20-way concurrent
takeover race passes every time and never shows it, because the window needs
a process that pauses between its read and its write while the holder
resumes. Removing an `rm` + create race (two `rm`s both succeed) by `rename`
was right; it was not enough.

The generation fixes the cause instead of the symptom: a takeover writes a
*new* name derived from what was read (`n+1`), so a decision made on a stale
read cannot touch anybody's live claim — at worst it loses the CAS.

## 7. The escape hatch — and why the default is the other way round

`<state>/ORCHESTRATOR.pin` suspends the election: while it exists, every new
session becomes a worker and no beat takes a claim. Creating it requires no
code change and no disabling of the host wiring.

```
    human decision ─────────────▶ pin present ─────▶ machine yields
    machine election ────────X──▶ pin removed  ─────▶ machine decides
                             └ never: a mechanism must not be able to
                               overrule a decision a human just made
```

This asymmetry is the design, not a convenience: automatic election is *correct*
far more often than a human pin, and it is still the thing that has to yield.
A mechanism that can overrule its owner is unaccountable regardless of its hit
rate.

Two rules keep the hatch honest:

- **Creating the pin requires a TASKS.md line saying why.** An unexplained pin
  is indistinguishable from a bug.
- **Warn the claim holder.** If the pin appears *after* someone took the claim,
  that holder still believes it is in charge while every new session is told
  otherwise. The `beat` mode checks for this and says so. Without that check,
  the escape hatch manufactures the exact failure this layer exists to prevent.

## 8. What is proved, under which assumptions — and what is not

`framework/formal/Election.tla` models `boot.py` one atomic file-system step
per action and TLC checks, at its stated bounds (safety at 3 concurrent
sessions, liveness at 2), that **at most one session acts as orchestrator**,
that only the holder of the top claim acts, that every hook run ends, and that
once the holder is gone a session that opens is elected. `tools/check_models.py`
runs it in CI, together with the seeded broken variant (0.9.6) that must yield
a counterexample.

**Trace validation ties the code to the model.** With `DEVCREW_TRACE=<file>`,
`boot.py` logs every step that touches a claim — under an exclusive lock, so
the log's order is the order the steps happened in — with what it saw.
`check_models.py` runs real concurrent elections, takeovers, renewals and
releases this way and has TLC accept each trace as a behaviour of the model
(`framework/formal/ElectionTrace.tla`); a mutant `boot.py` (0.9.6's "refresh
my lease whatever its age") must be rejected. A change to `boot.py` that the
model does not allow fails CI.

The model takes these as constants. **They are assumptions, not results**, and
an install that cannot meet one must say so:

| | Assumption | What breaks without it |
|---|---|---|
| A1 | A hook process pauses for less than `MARGIN` between two of its steps (it runs for milliseconds; the host kills it after its own timeout) | a holder that read its lease as fresh could refresh it after a newcomer read it as stale |
| A2 | An acting orchestrator beats more often than `STALE − MARGIN`: a beat at both ends of every turn **and after every tool call**, so no single tool call runs longer than that | a long autonomous turn lets the lease expire while the holder is still acting — the more autonomy, the likelier |
| A3 | A session told it is a worker stops acting as orchestrator at once | the claim moves, the behaviour does not |
| A4 | `<state>/claims/` is on a local file system, where `link` and `O_EXCL` are atomic (APFS, ext4, NTFS) — not NFS/SMB, not a sync folder (Dropbox, iCloud, OneDrive) | the CAS degrades to advisory and so does everything above it |

**Not modelled:**

- **The pin.** While it exists no session TAKES the role: a start elects
  nobody and a beat takes no free claim. But a session that already holds the
  claim keeps it -- its beats still refresh or renew it -- and is told, at
  every beat, that the human pinned the role elsewhere. Stopping is then A3,
  not the mechanism. The pin never adds an orchestrator; it is outside the
  model on purpose, because it is the human's override of the model.
- **The scan is not one atomic read.** `boot.py` lists the directory, then
  reads and stats the top claim. The model treats that as one step. The real
  scan can only see a claim fresher, or a release later, than at the listing —
  both lead to WORKER, the conservative side.

**Not solved by this layer at all:**

- **It is not a distributed lock** (A4). Re-evaluate whenever the repo moves;
  if it must live on a network or sync folder, move to a real lock service.
- **It does not reach processes outside the repo.** An external dispatcher that
  spawns agents against the same tree obeys none of this. That path is bounded
  by the human ("do not launch while the tree is being written").
- **It does not decide *what* to work on.** It decides *who may decide*. Two
  workers can still both start the same card if the claim namespace is loose
  enough that their filenames never collide — that is the *claim-key* problem,
  and it is a separate rule: constrain claim keys to a name derived from the
  work item (a card id, a contract slug) so that two sessions picking the same
  work produce the same filename and therefore collide.
- **It does not survive a host without lifecycle events.** If the host cannot
  run a script at session start, this layer can only be prose — and prose is the
  thing that already failed. Say so rather than installing a half version.

## 9. Install checklist

For a host adapter claiming to implement this file:

- [ ] A **session identity** that is stable for the session's whole lifetime and
      differs between concurrent sessions. Not a pid. Not a socket name. Not a
      user-chosen label.
- [ ] Four lifecycle events wired: **start**, **both ends of every turn**,
      **after every tool call** (A2) and **end**. Missing `end` is survivable —
      it costs one `STALE` wait per crash. Missing the after-tool-call event
      voids A2: say so out loud, it is not a detail. Missing *start* means the
      layer does not exist.
- [ ] `<state>/claims/` exists **in version control** (via a README), so a fresh
      clone has the directory. Without it the `link` fails for the wrong reason
      and the rule looks obeyed while doing nothing.
- [ ] The claim artifacts are **git-ignored**: `<state>/claims/*.claim`,
      `<state>/claims/*.released`, `<state>/claims/.new.*`,
      `<state>/claims/ORCHESTRATOR.top` (a lookup hint, never trusted).
- [ ] The injected text tells the orchestrator its **read discipline**. The role
      is a context-scarce one: it reads the board, `TASKS.md` and the contracts,
      and delegates reading code. An orchestrator that reads source is an
      orchestrator that compacts, and compaction is how it forgets it was
      mid-gate.
- [ ] The script **exits 0 on every path**, including malformed input.
- [ ] Verified by an actual race, not by reading: N concurrent starts ⇒ exactly
      one orchestrator; M concurrent takeovers of one stale claim ⇒ exactly one
      winner. Both are one shell loop. The race shows the CAS works; only the
      model shows there is no interleaving left in which it does not.

Reference implementation: `framework/tools/boot.py` (host-neutral, stdlib only).
It prints a neutral `{message, context, quiet}` result. A host that needs
another output shape supplies a `boot_host.py` adapter beside it, and its
`hosts/<host>.md` says where that adapter comes from.
Wiring: `hosts/claude-code.md` § *Multi-session governance*.
