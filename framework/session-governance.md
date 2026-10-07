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

1. **At most one orchestrator holds the role at any instant** — and that is
   guaranteed by the kernel, not by everyone remembering to look first.
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
│  SESSION START ─┐                                                 │
│  EVERY TURN   ──┤  the HOST runs these, not the model. A rule the │
│  SESSION END  ──┘  model must remember to run is not a mechanism. │
└────────┬──────────────────────────────────────────────────────────┘
         │ passes in: a session identity stable for the whole session
         ▼
┌─ boot.py ── one script, three modes, always exit 0 ───────────────┐
│  start  elect, then inject the role + the board into the context  │
│  beat   refresh the lease; detect "I was demoted"                 │
│  end    release the lease if it is mine                           │
└──┬──────────────────────────────┬─────────────────────────────────┘
   │ O_EXCL create / utime        │ read only
   ▼                              ▼
┌─ <state>/claims/ ──────────┐  ┌─ <state>/ORCHESTRATOR.pin ──────┐
│  ORCHESTRATOR.claim        │  │  the ESCAPE HATCH.              │
│    mutual exclusion: the   │  │  Absent = normal.               │
│      kernel (O_EXCL)       │  │  Present = a human pinned the   │
│    lease: its own mtime    │  │    role ⇒ election is suspended │
│    takeover: only after    │  │  A human can override the       │
│      STALE_S of silence    │  │  machine. Never the reverse.    │
└────────────┬───────────────┘  └─────────────────────────────────┘
             │ orchestrator only
             ▼
┌─ board command (optional, host-supplied) ─────────────────────────┐
│  JOINs the card store + <state>/claims/ + a liveness list into    │
│  one page. GENERATED, never stored: a hand-written board is state │
│  in a governed file, and governed state goes stale by design.     │
└────────────┬──────────────────────────────────────────────────────┘
             ▼ injected into the model's context at session start
   "you are the orchestrator" + board + read-discipline
   "you are a worker" + the two prohibitions + live claims
```

## 4. Election — the decision tree

Run on session start. `me` = this session's identity.

```
START
│
├─ <state>/ORCHESTRATOR.pin exists?
│  └─ YES ─────────────────────────────────────▶ WORKER (human pinned)
├─ NO
│
├─ ORCHESTRATOR.claim exists?
│  │
│  ├─ NO → create with O_EXCL
│  │   ├─ created ───────────────────────────── ▶ ORCHESTRATOR (first come)
│  │   └─ EEXIST (lost the race by microseconds)
│  │        → re-read → holder == me?
│  │             ├─ YES ───────────────────────▶ ORCHESTRATOR
│  │             └─ NO ────────────────────────▶ WORKER
│  │
│  ├─ holder == me → touch mtime ──────────────▶ ORCHESTRATOR
│  │                    (same session resumed, or context compacted
│  │                     and the injection has to be replayed)
│  │
│  └─ holder == someone else → age = now - mtime
│       ├─ age ≤ STALE_S ─────────────────────▶ WORKER (lease is live)
│       └─ age > STALE_S
│            → rename(claim → evidence)   ← only one process can win
│               ├─ renamed AND re-created ────▶ ORCHESTRATOR (took over)
│               │     ⚠ log who took what, in the ledger
│               │     ⚠ the predecessor's in-process subagents do NOT
│               │       transfer: re-dispatch those cards, do not
│               │       "continue" them
│               └─ either step failed ────────▶ WORKER (someone else won)
│
└─ ANY exception ─────────────────────────────▶ exit 0, block nothing
```

Every leaf is one of two words. There is no "ask a human" leaf — that is
invariant 2, and it is the difference between a mechanism and a convention.

## 5. The lease — why a heartbeat and not a liveness guess

The lock file's **mtime is the lease**. The holder refreshes it on every turn;
nobody else may touch it.

```
 t ──────────────────────────────────────────────────────────────────▶
 A  start ─beat─beat─beat────────── window closed (END: released)
    ▲                                        │
    └ created the claim                      └ next session takes it
                                               instantly — no wait

 A  start ─beat─beat─ ✗ crash (no END ran)
                      ├──────── STALE_S ──────┤
 B                  start                   start
                    WORKER                  ORCHESTRATOR (takeover,
                    (lease still live —      evidence file kept)
                     do NOT take over)
```

Two properties matter more than the threshold's value:

- **A clean exit costs nothing.** `END` releases the lease, so the normal case
  never waits `STALE_S`. The threshold only covers crashes.
- **`STALE_S` trades one wrong answer for the other.** Too short: you take over
  a session that was merely slow, and overwrite live work. Too long: the repo
  has no orchestrator for that long. Start at 45 min and tune with evidence, not
  taste — the cost is asymmetric, so err long.

**Do not substitute anything for the heartbeat.** The tempting signals are all
wrong, and both directions have been measured on a real host:

| Signal | Why it lies |
|---|---|
| A socket/pid file exists | Measured: the file was there, the process was alive, and it was an orphan — detached from any terminal, absent from the host's session list, unreachable. You wait forever for a reply. |
| The socket/pid file is gone | Those names are *process* identity, not *session* identity. A process can be replaced while the session lives on. |
| Name in the lock == name in the session list | Measured false positive: the lock said `brand-lockup`, the list said `session-5b` — the same live session under two names. |

⇒ **Liveness comes from the heartbeat, or from the host's own session list.**
A socket may identify *who is who*; it is never evidence of life or death.

## 6. Takeover must `rename`, never `rm` + create

```
      rm + create  (BROKEN)              rename  (CORRECT)
 A  rm claim              ✓          A  rename(claim → ev-A)   ✓
 B  rm claim              ✓          B  rename(claim → ev-B)   ✗ ENOENT
 A  create claim          ✓                └ the source is already gone;
 B  create claim          ✓                  exactly one process can win
 ⇒ TWO orchestrators                 ⇒ ONE orchestrator, and the old
                                       claim survives as evidence
```

`rename(2)` is atomic on the same filesystem, so the *unlink* and the *claim to
have unlinked it* are the same operation. Two `rm`s both succeed, which is how a
takeover race produces two winners.

Keep the evidence file. Never delete it. One caveat to write down where the
reader will hit it: if `rename` succeeds but the re-create then fails, the
evidence file is named after a session that did **not** end up in charge — so
the evidence is only readable together with the ledger line, never alone.

## 7. The escape hatch — and why the default is the other way round

`<state>/ORCHESTRATOR.pin` suspends the election: while it exists, every new
session becomes a worker, whatever the lock says. Creating it requires no code
change and no disabling of the host wiring.

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

- **Creating the pin requires a ledger line saying why.** An unexplained pin is
  indistinguishable from a bug.
- **Warn the lock holder.** If the pin appears *after* someone took the lock,
  that holder still believes it is in charge while every new session is told
  otherwise. The `beat` mode checks for this and says so. Without that check,
  the escape hatch manufactures the exact failure this layer exists to prevent.

## 8. What this layer does NOT solve

State these at install time. A governance layer believed to cover more than it
does is worse than a smaller one whose edges are known.

- **It is not a distributed lock.** `O_EXCL` and `rename` are atomic on a local
  filesystem (APFS, ext4, NTFS). On NFS/SMB or a sync folder (Dropbox, iCloud,
  OneDrive) they degrade to advisory. Re-evaluate whenever the repo moves; if it
  must live there, move to a real lock service.
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
- [ ] Three lifecycle events wired: **start**, **every turn** (or every stop),
      and **end**. Missing `end` is survivable — it costs one `STALE_S` wait per
      crash. Missing *start* means the layer does not exist.
- [ ] `<state>/claims/` exists **in version control** (via a README), so a fresh
      clone has the directory. Without it `O_EXCL` fails for the wrong reason and
      the rule looks obeyed while doing nothing.
- [ ] The lock artifacts are **git-ignored**: `ORCHESTRATOR.claim`,
      `ORCHESTRATOR.stale.*`, `ORCHESTRATOR.released.claim`.
- [ ] The injected text tells the orchestrator its **read discipline**. The role
      is a context-scarce one: it reads the board and the contracts, and delegates
      reading code. An orchestrator that reads source is an orchestrator that
      compacts, and compaction is how it forgets it was mid-gate.
- [ ] The script **exits 0 on every path**, including malformed input.
- [ ] Verified by an actual race, not by reading: N concurrent starts ⇒ exactly
      one orchestrator; M concurrent takeovers of one stale lock ⇒ exactly one
      winner. Both are one shell loop; a mechanism claiming kernel-level mutual
      exclusion should be made to demonstrate it.

Reference implementation: `framework/tools/boot.py` (host-neutral, stdlib only).
It prints a neutral `{message, context, quiet}` result. A host that needs
another output shape supplies a `boot_host.py` adapter beside it, and its
`hosts/<host>.md` says where that adapter comes from.
Wiring: `hosts/claude-code.md` § *Multi-session governance*.
