#!/usr/bin/env python3
"""Orchestrator election for hosts that can run several sessions at once.

Reference implementation of `framework/session-governance.md`. Host-neutral and
stdlib only. Install it into the project as `<state>/tools/boot.py` and wire the
three modes to the host's lifecycle events (see `hosts/claude-code.md`).

WHY THIS IS A SCRIPT THE HOST RUNS, AND NOT A RULE IN THE PROMPT
    Because the rule version does not run. A project that had "check who the
    orchestrator is before you start" written in its always-loaded instructions
    still ended up with two sessions signing requirements for one intent: the
    rule depends on the model remembering to obey it, on every session, forever.
    The first attempt at a fix was a boot prompt for the human to paste into
    each new window. The CEO rejected it in one sentence -- "I am not going to
    type this every time, your approach is terrible" -- and was right. A
    mechanism that charges the human per session is a mechanism that will be
    skipped. The host runs this script whether or not anybody remembers it.

THE THREE MODES
    start   elect a role, then inject it (plus the board) into the context
    beat    refresh the lease; detect "I was the orchestrator and no longer am"
    end     release the lease if this session holds it

    modes = {'start': elect + inject, 'beat': heartbeat, 'end': release}

IT ALWAYS EXITS 0
    A governance script that can lock people out of their own repo is worse than
    the disorder it prevents. Every failure path here degrades to "say something
    and get out of the way".

WHAT MAKES THE MUTUAL EXCLUSION REAL
    os.open(..., O_CREAT | O_EXCL)  -- the same guarantee as `set -C` in shell.
    The kernel refuses the second creator. Nothing here relies on everyone
    remembering to look first.

    Takeover uses os.rename, never unlink+create. Two processes can both
    succeed at unlinking; exactly one can succeed at renaming the same source.
    That difference is the difference between one orchestrator and two.

PORTABILITY
    O_EXCL and rename are atomic on a local filesystem. On NFS/SMB or inside a
    sync folder (Dropbox, iCloud, OneDrive) they degrade to advisory and this
    layer degrades with them. Do not rely on it there -- see
    framework/session-governance.md section 8.
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Layout. Override with env vars if the project keeps its state elsewhere.
# ---------------------------------------------------------------------------

STATE_DIR = os.environ.get("DEVCREW_STATE_DIR", ".aidlc")
ROOT = Path(os.environ.get("DEVCREW_PROJECT_DIR") or Path(__file__).resolve().parents[2])
STATE = ROOT / STATE_DIR
CLAIMS = STATE / "claims"
LOCK = CLAIMS / "ORCHESTRATOR.claim"
PIN = STATE / "ORCHESTRATOR.pin"          # the escape hatch; normally absent
RELEASED = CLAIMS / "ORCHESTRATOR.released.claim"

# How long the lock may go without a heartbeat before another session may take
# it. The cost is asymmetric: too short and you overwrite a live session's work,
# too long and the repo has no orchestrator. Err long.
STALE_S = int(os.environ.get("DEVCREW_STALE_SECONDS", 45 * 60))

# Optional one-page board. Discovered, not required: no board is a smaller loss
# than a hardcoded path to a card store this project does not have.
BOARD = STATE / "tools" / "board.py"
BOARD_TIMEOUT_S = 12

# Per-session note of "what I was last time", kept OUTSIDE the repo so it never
# shows up in a diff. Only powers the demotion warning; the real exclusion is
# the lock.
HINT_DIR = Path(os.environ.get("TMPDIR", "/tmp"))


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def hint_path(sid):
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", sid)[:64]
    return HINT_DIR / f"devcrew-orchestrator-{safe}"


# ---------------------------------------------------------------------------
# Session identity
# ---------------------------------------------------------------------------

def session_identity(payload):
    """The only key this layer trusts. None means "the host did not give one".

    It must be stable for the whole session and differ between concurrent
    sessions. A pid is neither: on at least one host the per-session socket
    files are named after pids, and a pid identifies a process, not a session.

    When there is no identity, this script elects NOBODY. A wrong key is worse
    than no key -- it produces a lock whose holder cannot be recognised even by
    itself, so the lock can never be refreshed or released.
    """
    for k in ("session_id", "sessionId", "session-id"):
        v = payload.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    v = os.environ.get("DEVCREW_SESSION_ID", "").strip()
    return v or None


# ---------------------------------------------------------------------------
# The lock
# ---------------------------------------------------------------------------

def read_lock():
    """Return a dict (with `_age` in seconds) or None. Must survive garbage:
    a half-written lock still has to yield its session_id, because that is what
    decides whether we are allowed to touch it."""
    try:
        text = LOCK.read_text(errors="replace")
        age = time.time() - LOCK.stat().st_mtime
    except OSError:
        return None
    d = {k: v.strip() for k, v in re.findall(r"^(\w+):\s*(.*)$", text, re.M)}
    d["_age"] = age
    return d


def create_lock(sid, cwd):
    """O_EXCL: fails if the file exists. The kernel is the arbiter."""
    body = (
        "role: orchestrator\n"
        f"session_id: {sid}\n"
        f"since: {now()}\n"
        f"cwd: {cwd}\n"
        "note: this file's mtime IS the heartbeat, refreshed by `boot.py beat`.\n"
        "      Do not hand-edit it. To change orchestrator, close that session\n"
        "      (its end hook releases the lock) or use the escape hatch.\n"
    )
    try:
        CLAIMS.mkdir(parents=True, exist_ok=True)
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except (FileExistsError, OSError):
        return False
    try:
        with os.fdopen(fd, "w") as f:
            f.write(body)
    except OSError:
        return False
    return True


def pinned():
    """First non-comment line of the escape hatch, or None if it is absent.

    Absent is the normal state, so this returns None almost always. It exists so
    that a human can suspend the election -- automation went wrong, or the role
    needs freezing for a moment -- without editing code and without unwiring the
    host. Semantics are deliberately one-directional: a human decision overrides
    the machine, never the reverse. Creating this file should come with a line in
    the ledger saying who opened it and why; an unexplained pin is
    indistinguishable from a bug.
    """
    try:
        for ln in PIN.read_text(errors="replace").splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                return ln
    except OSError:
        pass
    return None


# ---------------------------------------------------------------------------
# Election -- the decision tree in session-governance.md section 4
# ---------------------------------------------------------------------------

def elect(sid, cwd):
    """Return (role, note). role is 'orchestrator' or 'worker'. Never asks."""
    pin = pinned()
    if pin:
        who = pin.split()[0]
        return "worker", (
            f"The role is **pinned by a human** to `{who}` "
            f"(`{STATE_DIR}/ORCHESTRATOR.pin` exists, which suspends the "
            "automatic election). You are a worker. If you ARE that session, "
            "ignore this. To return to automatic election, delete that file and "
            "record who opened it, who closed it, and why, in the ledger."
        )

    cur = read_lock()

    if cur is None:
        if create_lock(sid, cwd):
            return "orchestrator", (
                "Took the role automatically (first come, `O_EXCL`). "
                "Nobody had to appoint you."
            )
        cur = read_lock()          # somebody won it in the microseconds between
        if cur and cur.get("session_id") == sid:
            return "orchestrator", "Took the role automatically."
        return "worker", (
            "Another session took the role in the instant between the check and "
            "the create. This is the exclusion working, not a fault."
        )

    if cur.get("session_id") == sid:
        try:
            os.utime(LOCK, None)
        except OSError:
            pass
        return "orchestrator", (
            "You already held the role (same session resumed, or the context "
            "was compacted and this injection is being replayed)."
        )

    if cur["_age"] > STALE_S:
        # Rename first, create second. Only one process can rename one source.
        evidence = CLAIMS / f"ORCHESTRATOR.stale.{re.sub(r'[^A-Za-z0-9]', '', sid)[:8]}.claim"
        try:
            os.rename(LOCK, evidence)
            won = True
        except OSError:
            won = False
        if won and create_lock(sid, cwd):
            return "orchestrator", (
                f"**Took over**: the previous holder "
                f"{cur.get('session_id', '?')[:8]} stopped heartbeating "
                f"{int(cur['_age'] // 60)} min ago (threshold "
                f"{STALE_S // 60} min). Evidence kept as {evidence.name}; it is "
                "never deleted. Record in the ledger who took over what. Note "
                "that the predecessor's in-process subagents did NOT transfer: "
                "re-dispatch those cards, do not 'continue' them."
            )
        return "worker", (
            "The role was expired, but another session took it over first."
        )

    return "worker", (
        f"The orchestrator is {cur.get('session_id', '?')[:8]} "
        f"(heartbeat {int(cur['_age'] // 60)} min ago, so it is alive). "
        "Do not take over and do not open cards."
    )


# ---------------------------------------------------------------------------
# Context injected at session start
# ---------------------------------------------------------------------------

def board_text():
    if not BOARD.exists():
        return ("(no board tool installed at "
                f"`{STATE_DIR}/tools/board.py` -- read the ledger tail instead)")
    try:
        r = subprocess.run(
            [sys.executable, str(BOARD)],
            capture_output=True, text=True,
            timeout=BOARD_TIMEOUT_S, cwd=str(ROOT),
        )
        return (r.stdout or "").strip() or "(the board printed nothing)"
    except Exception as e:                                        # noqa: BLE001
        return f"(the board failed: {e!r} -- run it by hand to see why)"


def claims_summary():
    if not CLAIMS.is_dir():
        return (f"(`{STATE_DIR}/claims/` does not exist, so every `set -C` claim "
                "fails for the wrong reason and the rule looks obeyed while "
                "doing nothing. Create it with a committed README.)")
    out = []
    for p in sorted(CLAIMS.glob("*.claim")):
        if p.name.startswith("ORCHESTRATOR"):
            continue
        m = re.search(r"^session:\s*(\S+)", p.read_text(errors="replace"), re.M)
        out.append(f"    {p.name}  <- {m.group(1) if m else '?'}")
    return "\n".join(out) if out else "    (nobody is claiming anything)"


ORCHESTRATOR_TXT = """\
[multi-session governance -- injected by a host hook, not typed by the human]

**You are the only orchestrator in this repo right now.**
{note}

The role is decided mechanically, not by announcing it: the lock is
`{state}/claims/ORCHESTRATOR.claim` (`O_EXCL`), its mtime is your heartbeat, it
is refreshed every turn and released when this session ends. Do not hand-edit
it, and do not negotiate the role with another session.

Your context discipline -- **the orchestrator reads thin, workers read thick**:
read the board and the `{state}/features/<slug>/` contracts. Do NOT read source
trees, build output, or the whole ledger (tail it). To have code read, dispatch a
worker or a subagent and hand it the **contract path**, never your summary. An
orchestrator that reads code is an orchestrator that compacts, and compaction is
how it forgets it was mid-gate.

Every message you end a turn with opens with the SITREP block
(`SITUATION / ACTION / STATUS / NEXT`, `contracts/sitrep.template.md` in the
aidlc skill); `NEXT` always carries a `CEO：` line, `無` when nothing is needed.

{board}

Liveness is not established yet: list the live sessions with the host's own
session list before you clear any stale claim. Until then, claims are
fail-closed -- **nothing gets cleaned up**.
"""

WORKER_TXT = """\
[multi-session governance -- injected by a host hook, not typed by the human]

**You are a worker.** {note}

A worker may not do exactly two things: (1) claim or open a card slug,
(2) write or sign `requirements.md`. Everything else is open. In one line:
**a worker may do work; it may not define what the work is.**

Claim before you write, and stop if you lose the claim -- do not rename your way
around it:

    ( set -C; echo "session: $ID" > {state}/claims/<card-id>.claim ) || stop

Currently held:
{claims}

If the human gives you a **new large intent** in this window: do not open a slug.
Tell them which session is the orchestrator and register it there, quoting their
**own words**, not your summary. A clearly bounded task: just do it, then report
to the orchestrator with their original wording (it has to attach your output to
a requirement and get it signed on that same card, not retroactively).
**A worker never commits.**
Every report -- to the human or to the orchestrator -- opens with the SITREP
block (`contracts/sitrep.template.md` in the aidlc skill).
"""


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

NO_IDENTITY = (
    "[multi-session governance] ⚠️ **This layer is not running.** The host gave "
    "this session no stable identity, so `boot.py` elected nobody: a lock keyed "
    "on a guess can never be refreshed or released by its own holder. Until the "
    "wiring passes a session id, treat the orchestrator role as undefined and "
    "ask before claiming anything. See `framework/session-governance.md` § 9."
)


def do_start(payload):
    sid = session_identity(payload)
    if sid is None:
        return render(payload, "⚠️ session governance inactive", NO_IDENTITY)

    cwd = payload.get("cwd") or str(ROOT)
    role, note = elect(sid, cwd)

    try:
        hint_path(sid).write_text(role)
    except OSError:
        pass

    if role == "orchestrator":
        txt = ORCHESTRATOR_TXT.format(note=note, board=board_text(), state=STATE_DIR)
        msg = "🧭 this session is the orchestrator (elected, not appointed)"
    else:
        txt = WORKER_TXT.format(note=note, claims=claims_summary(), state=STATE_DIR)
        msg = "🔧 this session is a worker"
    return render(payload, msg, txt)


def do_beat(payload):
    """Refresh the lease, and catch the two ways a holder can be wrong about
    still being in charge."""
    sid = session_identity(payload)
    if sid is None:
        return QUIET

    cur = read_lock()
    mine = bool(cur) and cur.get("session_id") == sid
    hint = hint_path(sid)
    was = hint.read_text().strip() if hint.exists() else ""

    if mine:
        try:
            os.utime(LOCK, None)
        except OSError:
            pass
        pin = pinned()
        if pin:
            # The hatch opened *after* this session took the lock. Unsaid, this
            # session keeps acting as orchestrator while every new session is
            # told the role belongs to someone else -- which is precisely the
            # two-orchestrators failure the layer exists to prevent.
            return render(
                payload, "⚠️ the role was pinned out from under you",
                "⚠️ **You hold `ORCHESTRATOR.claim`, but "
                f"`{STATE_DIR}/ORCHESTRATOR.pin` now exists** (a human pinned "
                f"the role to `{pin.split()[0]}`). **The human's pin wins** -- "
                "new sessions have already been told the role is not yours. "
                "Claim and open nothing until this is settled, and confirm the "
                "pin was intended (its creation should have a ledger line).",
            )
        return QUIET

    if was == "orchestrator":
        try:
            hint.write_text("worker")
        except OSError:
            pass
        who = (cur or {}).get("session_id", "(nobody)")[:8]
        return render(
            payload, "⚠️ this session is no longer the orchestrator",
            "⚠️ **You are no longer the orchestrator** -- "
            f"`{STATE_DIR}/claims/ORCHESTRATOR.claim` now belongs to `{who}`. "
            "From here you are a worker: do not claim or open card slugs, do not "
            "write or sign `requirements.md`. Finish the concrete work in your "
            "hands and report it to the current orchestrator.",
        )
    return QUIET


def do_end(payload):
    """Release, so the next session does not wait out STALE_S for nothing."""
    sid = session_identity(payload)
    if sid is None:
        return QUIET
    cur = read_lock()
    if cur and cur.get("session_id") == sid:
        # Fixed filename: each release overwrites the last, so this leaves
        # exactly one "who held it previously" file rather than accumulating
        # litter. (Takeover evidence keeps a unique name -- that uniqueness is
        # what makes the rename exclusive, so it must not be collapsed.)
        try:
            os.rename(LOCK, RELEASED)
        except OSError:
            pass
    return QUIET


# ---------------------------------------------------------------------------
# Output — neutral here, shaped by the host's adapter
# ---------------------------------------------------------------------------

QUIET = {"quiet": True}


def render(payload, message, context):
    """The neutral result: `message` is for the human, `context` for the model.

    A host that needs another shape ships an adapter as `boot_host.py` beside
    this file, with `adapt(out, payload) -> dict`. Its hosts/<host>.md says so.
    This file stays host-neutral; the host's protocol lives in its adapter.
    """
    return {"message": message, "context": context, "quiet": True}


def adapt(out, payload):
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import boot_host                                          # noqa: PLC0415
    except ImportError:
        return out
    return boot_host.adapt(out, payload)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "start"
    try:
        raw = sys.stdin.read()
    except Exception:                                             # noqa: BLE001
        raw = ""
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    try:
        out = {"start": do_start, "beat": do_beat, "end": do_end}[mode](payload)
    except Exception as e:                                        # noqa: BLE001
        # Never let a broken governance script block a session.
        out = {"message": f"(governance hook boot.py {mode} failed, skipped: {e!r})"}

    try:
        out = adapt(out, payload)
    except Exception as e:                                        # noqa: BLE001
        out = {"message": f"(boot_host adapter failed, skipped: {e!r})", **out}
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
