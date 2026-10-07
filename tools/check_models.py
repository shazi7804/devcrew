#!/usr/bin/env python3
"""Model-check the framework's own protocols, and check the code against them.

    check_models.py                    every model, then trace validation
    check_models.py --models           only the model checks
    check_models.py --trace            only trace validation of boot.py
    check_models.py --holds SPEC:CFG   exit 0 iff that one model holds
    check_models.py --accepts real|mutant|skip-gen
                                       exit 0 iff the scripted trace of boot.py
                                       (or of the mutant) matches the model
                                       -- single checks for formal evidence;
                                       exit 0 accepted, 1 rejected, 2 the run
                                       broke an assumption (no verdict)
    options: --jar PATH (or $TLA2TOOLS_JAR)  --java PATH (or $JAVA, else java)

WHAT RUNS
    1. TLC on each model in framework/formal/ at the bounds in its .cfg. A
       model that must hold must hold; a SEEDED BROKEN VARIANT must yield a
       counterexample naming the expected property -- a check that cannot
       fail proves nothing.
    2. Trace validation of framework/tools/boot.py: real concurrent runs with
       DEVCREW_TRACE set, every logged step checked against Election.tla by
       TLC (ElectionTrace.tla). Then the same scenario on a mutant boot.py
       (0.9.6's "refresh my lease whatever its age") must be REJECTED.

The checker is TLC from tla2tools.jar, pinned by sha256 below; it needs a
Java runtime. Nothing here is a framework sensor installed into projects --
it is CI for devcrew itself.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
import pathlib
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
FORMAL = ROOT / "framework" / "formal"
BOOT = ROOT / "framework" / "tools" / "boot.py"
TLA_VERSION = "1.7.4"
TLA_SHA256 = "936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88"

# (spec, config, expectation): "holds", or the property that must be violated
# "temporal" = a liveness property violated. Every model has a seeded broken
# variant for safety AND for liveness: a check that cannot fail proves nothing.
MODELS = [
    ("Election", "Election", "holds"),
    ("Election", "ElectionLive", "holds"),
    ("ElectionV096", "ElectionV096", "AtMostOneActing"),
    ("Election", "ElectionLiveBroken", "temporal"),
    ("Aidlc", "Aidlc", "holds"),
    ("Aidlc", "AidlcLive", "holds"),
    ("Aidlc", "AidlcBroken", "NoPhasePastUnsignedBatch"),
    ("Aidlc", "AidlcLiveBroken", "temporal"),
]

STALE, MARGIN = 4, 2          # seconds, for the trace runs: fresh <= 2 < margin <= 4 < stale
RETRIES = 3                   # a run that broke an assumption is re-run, not judged
# Mutants of boot.py the trace check must reject, each a different way to be
# wrong: 0.9.6's "refresh my lease whatever its age", and skipping a generation.
MUTANTS = {
    "mutant": ('if mine and top["age"] == "fresh":', "if mine:"),
    "skip-gen": ("if create(sid, n + 1, cwd) and verify(sid, n + 1):",
                 "if create(sid, n + 2, cwd) and verify(sid, n + 2):"),
    "touch-old": ("if touch(sid, n) and verify(sid, n):",
                  "if touch(sid, n - 1) and verify(sid, n):"),
}


def tlc(java, jar, spec, cfg, cwd, timeout=1800):
    meta = tempfile.mkdtemp(prefix="tlc-")
    try:
        r = subprocess.run([java, "-XX:+UseParallelGC", "-cp", jar, "tlc2.TLC",
                            "-workers", "auto", "-metadir", meta, "-config", f"{cfg}.cfg",
                            f"{spec}.tla"], cwd=cwd, capture_output=True, text=True,
                           timeout=timeout)
        return r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return f"TIMEOUT after {timeout}s -- no verdict"
    finally:
        shutil.rmtree(meta, ignore_errors=True)


def outcome(text):
    """'holds', the name of a violated property, or 'error: ...'."""
    if "Model checking completed. No error has been found." in text:
        return "holds"
    m = re.search(r"(?:Invariant|Action property) (\w+) is violated", text)
    if m:
        return m.group(1)
    if "Temporal properties were violated" in text:
        return "temporal"
    tail = " / ".join(ln for ln in text.strip().splitlines()[-4:])
    return f"error: {tail[:300]}"


def states(text):
    m = re.findall(r"([\d,]+) distinct states found", text)
    return m[-1] if m else "?"


def check_models(java, jar):
    hits = []
    for spec, cfg, want in MODELS:
        t0 = time.time()
        text = tlc(java, jar, spec, cfg, FORMAL)
        got = outcome(text)
        ok = got == want
        print(f"  {'ok ' if ok else 'BAD'} {spec}/{cfg}: {got} (expected {want}; "
              f"{states(text)} states, {time.time() - t0:.0f}s)")
        if not ok:
            hits.append(f"{spec}/{cfg}: expected {want}, got {got}")
    return hits


# ---- trace validation ---------------------------------------------------------

def boot(script, project, trace, sid, mode):
    env = {**os.environ, "DEVCREW_PROJECT_DIR": str(project), "DEVCREW_TRACE": str(trace),
           "DEVCREW_STALE_SECONDS": str(STALE), "DEVCREW_MARGIN_SECONDS": str(MARGIN),
           "TMPDIR": str(project)}
    subprocess.run([sys.executable, str(script), mode], input=json.dumps({"session_id": sid}),
                   env=env, capture_output=True, text=True, timeout=30, check=True)


GAPS = []                     # (sid, seconds) between two beats of one turn


def turn(script, project, trace, sid, mids=0):
    last = time.time()
    for _ in range(mids + 2):                                  # start, tool calls, end
        boot(script, project, trace, sid, "beat")
        GAPS.append((sid, time.time() - last))
        last = time.time()


def assumptions(events):
    """What this run broke of the model's assumptions, from the timestamps:
    A1, a hook run (fire .. its last step) shorter than MARGIN; A2, two beats
    of one turn closer than STALE - MARGIN. A run that broke one is outside
    what the model claims anything about -- neither a pass nor a failure."""
    broke, start = [], {}
    for e in events:
        if e["op"] == "fire":
            start[e["s"]] = e["t"]
        elif e["t"] - start.get(e["s"], e["t"]) >= MARGIN:
            broke.append(f"A1: a hook run of {e['s']} took {e['t'] - start[e['s']]:.1f}s")
    broke += [f"A2: {sid} beat {gap:.1f}s apart inside a turn" for sid, gap in GAPS
              if gap >= STALE - MARGIN]
    return broke


def scripted(script, project, trace):
    """Every branch of the election, in order: first, kept, renewed, took over,
    held/demoted, released, first again."""
    b = lambda sid, mode: boot(script, project, trace, sid, mode)
    b("a1", "start")
    turn(script, project, trace, "a1", mids=1)                 # kept
    time.sleep(STALE - MARGIN + 0.4)                           # a1's lease: margin
    turn(script, project, trace, "a1")                         # renewed
    time.sleep(STALE + 0.4)                                    # a1's lease: stale
    b("a2", "start")                                           # took over
    turn(script, project, trace, "a1")                         # held -> demoted
    turn(script, project, trace, "a2")
    b("a2", "end")                                             # released
    b("a3", "start")                                           # first again
    b("a3", "end")
    b("a1", "end")


def crowd(script, project, trace, n=6, seed=0):
    """n sessions at once: they race the first claim, take turns with tool
    calls, sometimes go idle past STALE, sometimes vanish without an end hook.
    A sleep only ever falls between turns (assumption A2)."""
    def life(k):
        rng, sid = random.Random(seed * 100 + k), f"c{k}"
        boot(script, project, trace, sid, "start")
        for _ in range(rng.randint(1, 4)):
            turn(script, project, trace, sid, mids=rng.randint(0, 2))
            time.sleep(rng.choice([0, 0, 0.1, STALE - MARGIN + 0.3, STALE + 0.3]))
        if rng.random() < 0.7:
            boot(script, project, trace, sid, "end")
    with concurrent.futures.ThreadPoolExecutor(n) as pool:
        list(pool.map(life, range(n)))


def stampede(script, project, trace, n=8):
    """n sessions released by one barrier onto an empty claim directory, then
    -- once that claim has gone stale -- n more onto it: the CAS under load."""
    import threading                                              # noqa: PLC0415
    def wave(prefix):
        gate = threading.Barrier(n)
        def one(k):
            gate.wait()
            boot(script, project, trace, f"{prefix}{k}", "start")
        with concurrent.futures.ThreadPoolExecutor(n) as pool:
            list(pool.map(one, range(n)))
    wave("w")
    time.sleep(STALE + 0.4)
    wave("x")


def trace_module(events, path):
    def rec(e):
        f = [f's |-> "{e["s"]}"', f'op |-> "{e["op"]}"']
        if "mode" in e:
            f.append(f'mode |-> "{e["mode"]}"')
        if "ok" in e:
            f.append(f'ok |-> {"TRUE" if e["ok"] else "FALSE"}')
        if "n" in e:
            f.append(f'n |-> {int(e["n"])}')
        if "top" in e:
            t = e["top"]
            f.append(f'top |-> [sid |-> "{t["sid"] or "none"}", age |-> "{t["age"]}", '
                     f'rel |-> {"TRUE" if t["rel"] else "FALSE"}]')
        return "[" + ", ".join(f) + "]"
    body = ",\n  ".join(rec(e) for e in events)
    path.write_text(f"---- MODULE TraceData ----\nTrace == <<\n  {body}\n>>\n====\n")


def validate(java, jar, script, scenario):
    """(matched, steps, outcome). A run that broke an assumption is re-run;
    after RETRIES it is reported as outside the assumptions, never as a pass."""
    for _ in range(RETRIES):
        ok, n, got = attempt(java, jar, script, scenario)
        if not got.startswith("outside"):
            break
    return ok, n, got


def attempt(java, jar, script, scenario):
    work = pathlib.Path(tempfile.mkdtemp(prefix="trace-"))
    try:
        project, trace = work / "project", work / "trace.jsonl"
        (project / ".aidlc" / "claims").mkdir(parents=True)
        GAPS.clear()
        scenario(script, project, trace)
        events = [json.loads(ln) for ln in trace.read_text().splitlines()]
        broke = assumptions(events)
        if broke:
            return False, len(events), f"outside the assumptions ({'; '.join(broke[:2])})"
        sids = sorted({e["s"] for e in events})
        for f in ("Election.tla", "ElectionTrace.tla"):
            shutil.copy(FORMAL / f, work / f)
        trace_module(events, work / "TraceData.tla")
        (work / "ElectionTrace.cfg").write_text(
            "CONSTANTS\n  Sessions = {" + ", ".join(f'"{s}"' for s in sids) + "}\n"
            "  None = None\n  TakeOnBeat = TRUE\nSPECIFICATION TSpec\nINVARIANT Unmatched\nCHECK_DEADLOCK FALSE\n")
        got = outcome(tlc(java, jar, "ElectionTrace", "ElectionTrace", work))
        return got == "Unmatched", len(events), got
    finally:
        shutil.rmtree(work, ignore_errors=True)


def check_trace(java, jar):
    hits = []
    runs = [("scripted", scripted), ("stampede", stampede)] + [
        (f"concurrent seed {k}", lambda s, p, t, k=k: crowd(s, p, t, seed=k))
        for k in range(3)]
    for name, scenario in runs:
        ok, n, got = validate(java, jar, BOOT, scenario)
        print(f"  {'ok ' if ok else 'BAD'} boot.py {name}: {n} steps "
              f"{'accepted by the model' if ok else 'REJECTED (' + got + ')'}")
        if not ok:
            hits.append(f"boot.py trace ({name}): " + (
                f"could not be run inside the model's assumptions -- {got}"
                if got.startswith("outside") else "not a behaviour of Election.tla"))
    src = BOOT.read_text()
    for name, (site, change) in MUTANTS.items():
        if site not in src:
            hits.append(f"mutation site {site!r} not found in boot.py")
            continue
        with tempfile.TemporaryDirectory() as d:
            mutant = pathlib.Path(d) / "boot.py"
            mutant.write_text(src.replace(site, change))
            ok, n, got = validate(java, jar, mutant, scripted)
        valid = not got.startswith("outside")
        print(f"  {'ok ' if valid and not ok else 'BAD'} boot.py {name} ({change!r}): "
              f"{n} steps {'rejected' if valid and not ok else got if not valid else 'ACCEPTED'}")
        if ok or not valid:
            hits.append(f"trace validation did not reject {name} inside the "
                        "assumptions -- it has not shown it can fail")
    return hits


def jar_path(arg):
    jar = arg or os.environ.get("TLA2TOOLS_JAR")
    if not jar or not pathlib.Path(jar).is_file():
        sys.exit(f"check_models: tla2tools.jar {TLA_VERSION} not found -- pass --jar "
                 "or set TLA2TOOLS_JAR")
    digest = hashlib.sha256(pathlib.Path(jar).read_bytes()).hexdigest()
    if digest != TLA_SHA256:
        sys.exit(f"check_models: {jar} is not tla2tools {TLA_VERSION} "
                 f"(sha256 {digest[:12]}, pinned {TLA_SHA256[:12]})")
    return jar


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--jar")
    ap.add_argument("--java", default=os.environ.get("JAVA", "java"))
    ap.add_argument("--models", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--holds", metavar="SPEC:CFG")
    ap.add_argument("--accepts", choices=("real", *MUTANTS))
    a = ap.parse_args(argv)
    jar = jar_path(a.jar)
    if a.holds:
        spec, _, cfg = a.holds.partition(":")
        got = outcome(tlc(a.java, jar, spec, cfg or spec, FORMAL))
        print(f"{spec}/{cfg or spec}: {got}")
        return 0 if got == "holds" else 1
    if a.accepts:
        with tempfile.TemporaryDirectory() as d:
            script = BOOT
            if a.accepts != "real":
                script = pathlib.Path(d) / "boot.py"
                script.write_text(BOOT.read_text().replace(*MUTANTS[a.accepts]))
            ok, n, got = validate(a.java, jar, script, scripted)
        print(f"boot.py ({a.accepts}) scripted trace, {n} steps: "
              f"{'accepted' if ok else got if got.startswith('outside') else 'rejected'}")
        return 0 if ok else 2 if got.startswith("outside") else 1
    both = not (a.models or a.trace)
    hits = []
    if a.models or both:
        print("models:")
        hits += check_models(a.java, jar)
    if a.trace or both:
        print("trace validation:")
        hits += check_trace(a.java, jar)
    for h in hits:
        print(f"FAIL {h}")
    print("models: ok" if not hits else f"models: {len(hits)} failure(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
