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
    The claim is a generation: `claims/ORCHESTRATOR.<n>.claim`, highest n wins.
    A session takes the role by creating generation n+1 with os.link -- the
    kernel refuses a name that exists, and a name is never reused, so it is a
    compare-and-swap: it succeeds only if nobody made n+1 since we read n. The
    file is written in full first and linked into place, so no reader ever sees
    a half-written claim.

    0.9.6 used ONE path, renamed on takeover. A model checker found two
    orchestrators in 14 steps (framework/formal/ElectionV096.tla): rename and
    utime act on whatever file is at the path NOW, not on the file that was
    read. A holder resuming a stale lease refreshed it while a newcomer, who
    had read it as stale, renamed it away -- both acted. This version is the
    one framework/formal/Election.tla proves, and DEVCREW_TRACE checks the
    real script against it (tools/check_models.py).

    The holder trusts its own lease only while it is younger than
    STALE_S - MARGIN_S; past that it must win n+1 like anyone else. That
    margin is what a paused process may not exceed (assumption A1 in
    framework/session-governance.md section 8).

PORTABILITY
    os.link is atomic on a local filesystem. On NFS/SMB or inside a
    sync folder (Dropbox, iCloud, OneDrive) it degrades to advisory and this
    layer degrades with it. Do not rely on it there -- see
    framework/session-governance.md section 8.
"""

import contextlib
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
PIN = STATE / "ORCHESTRATOR.pin"          # the escape hatch; normally absent
GEN = re.compile(r"^ORCHESTRATOR\.(\d+)\.claim$")
TOP_HINT = CLAIMS / "ORCHESTRATOR.top"     # a hint for top_gen(), never trusted

# How long the lock may go without a heartbeat before another session may take
# it. The cost is asymmetric: too short and you overwrite a live session's work,
# too long and the repo has no orchestrator. Err long.
STALE_S = int(os.environ.get("DEVCREW_STALE_SECONDS", 45 * 60))
# The holder's own lease is trusted only while younger than STALE_S - MARGIN_S.
MARGIN_S = int(os.environ.get("DEVCREW_MARGIN_SECONDS", 5 * 60))

# With a path set, every step that touches a claim is logged (and serialised)
# so the run can be checked against the model. Off in normal use.
TRACE = os.environ.get("DEVCREW_TRACE")

# Optional one-page board. Discovered, not required: no board is a smaller loss
# than a hardcoded path to a card store this project does not have.
BOARD = STATE / "tools" / "board.py"
BOARD_TIMEOUT_S = 12

# Per-session note of "what I was last time", kept OUTSIDE the repo so it never
# shows up in a diff. Only powers the demotion warning; the real exclusion is
# the claim.
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
# The claim -- one function per atomic step of framework/formal/Election.tla
# ---------------------------------------------------------------------------

def claim(n):
    return CLAIMS / f"ORCHESTRATOR.{n}.claim"


def released(n):
    return CLAIMS / f"ORCHESTRATOR.{n}.released"


def top_gen():
    """The highest generation. Generations are contiguous (n+1 is only ever
    made by someone who read n), so probe upward from the last top seen; list
    the directory only when that hint is missing or wrong. The directory keeps
    every generation as evidence, so it grows; a beat must not grow with it."""
    try:
        n = int(TOP_HINT.read_text())
        if n < 1 or not claim(n).exists():
            raise ValueError
    except (OSError, ValueError):
        gens = (GEN.match(p.name) for p in CLAIMS.glob("ORCHESTRATOR.*.claim"))
        n = max((int(m.group(1)) for m in gens if m), default=0)
    while claim(n + 1).exists():
        n += 1
    return n


def fired(sid, mode):
    """Traced, mark where a hook run begins: the model's start of a run."""
    if TRACE:
        with step(sid, "fire") as seen:
            seen["mode"] = mode


@contextlib.contextmanager
def step(sid, op):
    """One atomic step. Traced, it holds an exclusive lock on the trace file so
    the log's order is the order the steps happened in."""
    if not TRACE:
        yield {}
        return
    import fcntl                                                  # noqa: PLC0415
    with open(TRACE, "a", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        seen = {}
        yield seen
        f.write(json.dumps({"s": sid, "op": op, "t": round(time.time(), 4), "pid": os.getpid(),
                            **seen}) + "\n")


def scan(sid):
    """The highest generation: {n, sid, age, rel, age_s}. n == 0: there is none.
    age is fresh / margin / stale against STALE_S - MARGIN_S and STALE_S."""
    with step(sid, "scan") as seen:
        top = {"n": top_gen(), "sid": None, "age": "stale", "rel": True, "age_s": 0}
        if top["n"]:
            try:
                f = claim(top["n"])
                m = re.search(r"^session_id:\s*(.*)$", f.read_text(errors="replace"), re.M)
                age = time.time() - f.stat().st_mtime
                top.update(sid=m.group(1).strip() if m else None, age_s=age,
                           rel=released(top["n"]).exists(),
                           age="fresh" if age <= STALE_S - MARGIN_S else
                               "margin" if age <= STALE_S else "stale")
            except OSError:
                # unreadable is not free: held by someone unknown, so nobody
                # takes it on this read (Election.tla ScanFail; A5 says a read
                # does not fail forever)
                top.update(sid="?", age="fresh", rel=False, age_s=0)
                seen["ok"] = False
        seen.setdefault("ok", True)
        seen["n"] = top["n"]
        seen["top"] = {k: top[k] for k in ("sid", "age", "rel")}
    return top


def touch(sid, n):
    """Refresh the lease. False if it could not be: then it was NOT refreshed,
    and the caller must not go on as if it had been."""
    with step(sid, "touch") as seen:
        seen["n"] = n
        try:
            os.utime(claim(n), None)
            seen["ok"] = True
        except OSError:
            seen["ok"] = False
    return seen["ok"]


def create(sid, n, cwd):
    """Generation n, in full, in one step: os.link refuses a name that exists."""
    body = (
        "role: orchestrator\n"
        f"session_id: {sid}\n"
        f"since: {now()}\n"
        f"cwd: {cwd}\n"
        "note: this file's mtime IS the heartbeat, refreshed by `boot.py beat`.\n"
        "      Do not hand-edit it. To change orchestrator, close that session\n"
        "      (its end hook releases the claim) or use the escape hatch.\n"
    )
    tmp = CLAIMS / f".new.{os.getpid()}.{re.sub(r'[^A-Za-z0-9]', '', sid)[:16]}"
    try:
        CLAIMS.mkdir(parents=True, exist_ok=True)
        tmp.write_text(body)
        staged = True
    except OSError:
        staged = False              # still one create step, and it failed
    with step(sid, "create") as seen:
        seen["n"] = n
        try:
            if not staged:
                raise OSError("could not stage the claim")
            os.link(tmp, claim(n))
            seen["ok"] = True
        except OSError:
            seen["ok"] = False
    try:
        tmp.unlink()
    except OSError:
        pass
    return seen["ok"]


def verify(sid, n):
    """Is the generation I touched or made still the highest? Contiguous
    generations make that one stat: nobody has made n+1."""
    with step(sid, "verify") as seen:
        seen["n"] = n
        seen["ok"] = claim(n).exists() and not claim(n + 1).exists()
    if seen["ok"]:
        try:
            TOP_HINT.write_text(str(n))
        except OSError:
            pass
    return seen["ok"]


def release(sid, n):
    with step(sid, "release") as seen:
        seen["n"] = n
        try:
            released(n).touch()
            seen["ok"] = True
        except OSError:
            seen["ok"] = False


def pinned():
    """First non-comment line of the escape hatch, or None if it is absent.

    Absent is the normal state, so this returns None almost always. It exists so
    that a human can suspend the election -- automation went wrong, or the role
    needs freezing for a moment -- without editing code and without unwiring the
    host. Semantics are deliberately one-directional: a human decision overrides
    the machine, never the reverse. Creating this file should come with a line in
    TASKS.md saying who opened it and why; an unexplained pin is
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

def elect(sid, cwd, may_take=True):
    """Return (role, how, top). role is 'orchestrator' or 'worker'; how is one
    of first, kept, renewed, took, raced, held, lost. Never asks.

    The same tree runs at start and at every beat: a worker whose beat finds
    nobody holding a live claim takes it, so a crashed orchestrator is replaced
    without anyone opening a window."""
    top = scan(sid)
    n, mine = top["n"], top["sid"] == sid and not top["rel"]
    if mine and top["age"] == "fresh":
        if touch(sid, n) and verify(sid, n):
            return "orchestrator", "kept", top
        return "worker", "lost", top
    free = top["rel"] or top["sid"] is None or top["age"] == "stale"
    if mine or (free and may_take):
        if create(sid, n + 1, cwd) and verify(sid, n + 1):
            how = "renewed" if mine else "took" if n and not top["rel"] else "first"
            return "orchestrator", how, top
        return "worker", "raced", top
    return "worker", "lost" if mine else "held", top


def elect_note(how, top):
    who, mins = (top["sid"] or "?")[:8], int(top["age_s"] // 60)
    return {
        "first": "Took the role automatically (first come, an atomic `link`). "
                 "Nobody had to appoint you.",
        "kept": "You already held the role (same session resumed, or the context "
                "was compacted and this injection is being replayed).",
        "renewed": f"You held the role, but its heartbeat was {mins} min old -- "
                   "too old to trust -- so you re-won it as the next generation.",
        "took": f"**Took over**: the previous holder {who} stopped heartbeating "
                f"{mins} min ago (threshold {STALE_S // 60} min). Its generation "
                f"({top['n']}) stays in `{STATE_DIR}/claims/` as evidence; it is "
                "never deleted. Record in TASKS.md who took over what. Note that "
                "the predecessor's in-process subagents did NOT transfer: "
                "re-dispatch those cards, do not 'continue' them.",
        "raced": "Another session took the role in the instant between the check "
                 "and the create. This is the exclusion working, not a fault.",
        "held": f"The orchestrator is {who} (heartbeat {mins} min ago, so it is "
                "alive). Do not take over and do not open cards.",
        "lost": "The claim you held was superseded while you checked it.",
    }[how]


# ---------------------------------------------------------------------------
# Context injected at session start
# ---------------------------------------------------------------------------

def board_text():
    if not BOARD.exists():
        return ("(no board tool installed at "
                f"`{STATE_DIR}/tools/board.py` -- read TASKS.md instead)")
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

The role is decided mechanically, not by announcing it: the claim is the
highest `{state}/claims/ORCHESTRATOR.<n>.claim` (made by an atomic `link`), its
mtime is your heartbeat, it is refreshed at both ends of every turn and after
every tool call, and released when this session ends. Do not hand-edit it, and
do not negotiate the role with another session. If a beat ever tells you that
you are no longer the orchestrator, stop acting as one at once.

Your context discipline -- **the orchestrator reads thin, workers read thick**:
read the board, `TASKS.md` and the `{state}/features/<slug>/` contracts. Do NOT
read source trees, build output, or git history. To have code read, dispatch a
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

PINNED = (
    "The role is **pinned by a human** to `{who}` (`{state}/ORCHESTRATOR.pin` "
    "exists, which suspends the automatic election). You are a worker. If you "
    "ARE that session, ignore this. To return to automatic election, delete "
    "that file and record who opened it, who closed it, and why, in TASKS.md."
)

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

    pin = pinned()
    if pin:
        role, note = "worker", PINNED.format(who=pin.split()[0], state=STATE_DIR)
    else:
        fired(sid, "start")
        role, how, top = elect(sid, payload.get("cwd") or str(ROOT))
        note = elect_note(how, top)

    try:
        hint_path(sid).write_text(role)
    except OSError:
        pass
    return inject(payload, role, note)


def inject(payload, role, note):
    if role == "orchestrator":
        txt = ORCHESTRATOR_TXT.format(note=note, board=board_text(), state=STATE_DIR)
        msg = "🧭 this session is the orchestrator (elected, not appointed)"
    else:
        txt = WORKER_TXT.format(note=note, claims=claims_summary(), state=STATE_DIR)
        msg = "🔧 this session is a worker"
    return render(payload, msg, txt)


def do_beat(payload):
    """Refresh the lease -- at both ends of a turn and after every tool call
    (assumption A2) -- and catch every way the role can change hands."""
    sid = session_identity(payload)
    if sid is None:
        return QUIET

    pin = pinned()
    hint = hint_path(sid)
    was = hint.read_text().strip() if hint.exists() else ""
    fired(sid, "beat")
    role, how, top = elect(sid, payload.get("cwd") or str(ROOT), may_take=not pin)
    try:
        hint.write_text(role)
    except OSError:
        pass

    if role == "orchestrator" and pin:
        # The hatch opened *after* this session took the claim. Unsaid, this
        # session keeps acting as orchestrator while every new session is
        # told the role belongs to someone else -- which is precisely the
        # two-orchestrators failure the layer exists to prevent.
        return render(
            payload, "⚠️ the role was pinned out from under you",
            "⚠️ **You hold the orchestrator claim, but "
            f"`{STATE_DIR}/ORCHESTRATOR.pin` now exists** (a human pinned "
            f"the role to `{pin.split()[0]}`). **The human's pin wins** -- "
            "new sessions have already been told the role is not yours. "
            "Claim and open nothing until this is settled, and confirm the "
            "pin was intended (its creation should have a TASKS.md line).",
        )
    if role == "orchestrator" and was != "orchestrator":
        return inject(payload, role, elect_note(how, top))
    if role == "worker" and was == "orchestrator":
        who = (top["sid"] or "(nobody)")[:8] if how == "held" else "another session"
        return render(
            payload, "⚠️ this session is no longer the orchestrator",
            "⚠️ **You are no longer the orchestrator** -- the claim in "
            f"`{STATE_DIR}/claims/` now belongs to {who}. **Stop acting as "
            "orchestrator now, mid-turn included**: from here you are a worker. "
            "Do not claim or open card slugs, do not write or sign "
            "`requirements.md`. Finish the concrete work in your hands and "
            "report it to the current orchestrator.",
        )
    return QUIET


def do_end(payload):
    """Release, so the next session does not wait out STALE_S for nothing."""
    sid = session_identity(payload)
    if sid is None:
        return QUIET
    fired(sid, "end")
    top = scan(sid)
    if top["sid"] == sid and not top["rel"]:
        release(sid, top["n"])
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
