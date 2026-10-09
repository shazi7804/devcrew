#!/usr/bin/env python3
"""Fail the gate when a requirement's formal property is not machine-checked.

    check_formal.py --requirements F [--only R1,R3]
                                       check the formal evidence of one feature
    check_formal.py --requirements F --rerun
                                       ...and re-run every check and its vacuity run
    check_formal.py --self-test        prove every rule fails on a known bad case
    options: --root DIR  --evidence DIR (default: <dir of F>/formal)

Reference implementation of the formal-verification rule in the aidlc skill.
Host-neutral, stdlib only; installed beside check_live.py (it imports it), as
`<state>/tools/check_formal.py`. Implementers run it at Phase 3, QA at Phase 4.

THE REQUIREMENT SIDE (requirements.md, per Rn/Nn)
    - *Property*: <the formal statement of the acceptance>   or   none -- <reason>
    - *Formal*: tested | checked | proved           weakest first
      tested   generated-input or stateful property testing -- sampling, not a
               formal method, and named so
      checked  model checking of a design model, at stated bounds
      proved   a machine-checked proof, unbounded
    - *Conformance*: none | trace | refinement      how the code is tied to it
    A missing Property is a hit; `none` needs a reason the CEO signed.

THE EVIDENCE SIDE (<dir>/formal/<ID>.json, written after the code is committed)
    {"id": "R3", "property": "<exactly the signed text>", "level": "checked",
     "conformance": "trace", "tool": "TLC 2.19",
     "command": "<runs the check; names one of the sources>",
     "sources": ["spec/Cart.tla", "tools/check_cart.sh"], "bounds": "3 users, 4 items",
     "expect": "No error has been found", "observed": "<excerpt>", "result": "pass",
     "sha": "<40-hex>", "at": "<ISO>",
     "vacuity": {"command": "<a run that must fail>", "expect": "is violated",
                 "observed": "...", "result": "fail"},
     "conformance_check": {"command": "...", "expect": "...", "observed": "...",
                           "result": "pass"}}
    Red when: no evidence; incomplete or not JSON; another id; the property is
    not the signed text (an edited property proves something else); level or
    conformance below the signed one; `checked` with no bounds; result not
    pass; no vacuity run, or one that passed (a check that cannot fail proves
    nothing); conformance claimed with no passing conformance_check; a check
    whose command names none of its sources, or is a no-op (`true`, `:`,
    `echo`, `exit 0`), or a vacuity run that is a bare `false` / `exit 1` or
    the check itself; an `expect` missing, matching anything, or not matched by
    its observed output; a `tool` that neither the command nor a source names;
    a Property naming a TLA+ definition (a CamelCase identifier, when a source
    is a .tla) that no source defines -- the checked property drifted from
    the signed one; a source missing, or holding an escape hatch -- a proof that is not a proof
    (`sorry`, `admit`, `Admitted`, `axiom`, `assume`, `{:axiom}`, `OMITTED`,
    `assume(false)` ...); the sha not a full commit in HEAD's history, or the
    shipped tree changed since it (stale, same rule as check_live).
    With --rerun the check and the conformance check must exit 0 and the
    vacuity run must exit non-zero, now, each printing what its `expect` says
    -- run in a throwaway checkout of HEAD, as check_live's re-runs are.

WHAT THIS CANNOT DO
    Stored evidence is its writer's claim: an agent that can write the file
    can write a plausible one. The rules above make a lazy fake fail; only a
    re-run is proof. So QA runs `--rerun`, and so does `check_tasks.py --rerun`
    before the Ship batch -- never sign on stored evidence alone. And a re-run
    proves only that the command still says what it said: whether the command
    is a faithful checker of the property is read by a person or a reviewer in
    the diff, where the command and its sources are. No sensor can decide it.

Formal evidence adds to live evidence; it never replaces it (check_tasks.py
requires both before an item is Done).
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import check_live  # noqa: E402

LEVELS = ("tested", "checked", "proved")
CONFORMANCE = ("none", "trace", "refinement")
FIELDS = ("id", "property", "level", "conformance", "tool", "command", "sources",
          "expect", "observed", "result", "sha", "at", "vacuity")
NOOP = re.compile(r"\s*(true|:|exit\s+0|echo\b.*|printf\b.*)\s*$")
FALSE = re.compile(r"\s*(false|exit\s+[1-9]\d*|!\s*true)\s*$")

# Escape hatches, by file type: a proof that is not a proof. Comments count:
# "-- sorry, fix later" is exactly the confession this looks for.
ANY = [r"\bassume\s*\(\s*(false|False)\s*\)"]
HATCHES = {
    ".lean": [r"\bsorry\b", r"\badmit\b",
              r"^\s*(@\[[^\]]*\]\s*)?((private|protected|noncomputable)\s+)*axiom\b",
              r"\bnative_decide\b"],
    ".v": [r"\bAdmitted\b", r"\badmit\b", r"^\s*(Local\s+|Global\s+)?(Axiom|Axioms|Parameter|Parameters|Hypothesis|Hypotheses|Conjecture)\b"],
    ".dfy": [r"\bassume\b", r"\{:axiom\}", r"\{:verify\s+false\}"],
    ".rs": [r"\bassume\s*\(", r"\badmit\s*\(", r"verifier::external_body",
            r"verifier\(external_body\)"],
    ".tla": [r"\bOMITTED\b"],
    ".thy": [r"\bsorry\b", r"\boops\b", r"\baxiomatization\b"],
    ".fst": [r"\badmit\b", r"\bassume\b"],
    ".fsti": [r"\badmit\b", r"\bassume\b"],
}


def norm(text):
    return " ".join(str(text).split()).strip("` ")


def signed(reqfile):
    """{id: (property, level, conformance)}; property None when it is `none`."""
    out = {}
    for rid, f in check_live.fields(reqfile).items():
        prop = norm(f.get("property", ""))
        level = norm(f.get("formal", "")).lower().split(" ")[0] if f.get("formal") else ""
        conf = norm(f.get("conformance", "none")).lower().split(" ")[0]
        none = re.match(r"none\s*(?:[—–:-]|$)", prop)
        out[rid] = (None if none else prop, level, conf,
                    prop[none.end():].strip(" -—–:") if none else "")
    return out


def hatches(path):
    rules = ANY + HATCHES.get(path.suffix, [])
    hits = []
    for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace")
                             .splitlines(), 1):
        for rx in rules:
            if re.search(rx, line):
                hits.append(f"{path.name}:{n} `{line.strip()[:60]}`")
                break
    return hits


def run_cmd(cmd, root):
    """(exit code or None on timeout, output)"""
    try:
        r = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, timeout=3600)
        return r.returncode, (r.stdout + r.stderr).decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return None, ""


def pattern(tag, what, block, hits):
    """The compiled `expect` of a check, or None (and a hit) if it proves nothing."""
    try:
        rx = re.compile(str(block.get("expect", "")))
    except re.error as err:
        hits.append(f"{tag}: {what} expect is not a regex ({err})")
        return None
    if not block.get("expect") or rx.search(""):
        hits.append(f"{tag}: {what} has no expect, or one that matches anything")
        return None
    if not rx.search(str(block.get("observed", ""))):
        hits.append(f"{tag}: {what} observed output does not match its expect")
    return rx


def check(root, reqfile, evidence=None, only=None, rerun=False):
    tree = check_live.HeadTree(root)
    try:
        return _check(root, reqfile, evidence, only, rerun, tree)
    finally:
        tree.close()


def _check(root, reqfile, evidence, only, rerun, tree):
    req = signed(reqfile)
    if not req:
        return [f"{reqfile}: no Rn/Nn items -- nothing is verified"]
    if only:
        unknown = sorted(set(only) - set(req))
        if unknown:
            return [f"{reqfile}: --only names {', '.join(unknown)}, not in the requirements"]
        req = {k: v for k, v in req.items() if k in only}
    evidence = evidence or reqfile.parent / "formal"
    hits = []
    for rid, (prop, level, conf, reason) in req.items():
        tag = f"{reqfile.name} {rid}"
        if prop is None:
            if not reason:
                hits.append(f"{tag}: `Property: none` needs a reason the CEO signs")
            continue
        if not prop:
            hits.append(f"{tag}: no `Property:` -- state the acceptance formally, "
                        "or `none -- <reason>`")
            continue
        if level not in LEVELS:
            hits.append(f"{tag}: Formal `{level or '(missing)'}` is not a level "
                        f"({' | '.join(LEVELS)})")
            continue
        if conf not in CONFORMANCE:
            hits.append(f"{tag}: Conformance `{conf}` is not one of {' | '.join(CONFORMANCE)}")
            continue
        f = evidence / f"{rid}.json"
        if not f.is_file():
            hits.append(f"{tag}: no formal evidence ({f.name}) -- unchecked")
            continue
        try:
            e = json.loads(f.read_text(encoding="utf-8"))
            assert isinstance(e, dict)
        except (ValueError, AssertionError):
            hits.append(f"{tag}: formal evidence is not a JSON object")
            continue
        missing = [k for k in FIELDS if not e.get(k)]
        if missing:
            hits.append(f"{tag}: formal evidence lacks {', '.join(missing)}")
            continue
        if e["id"] != rid:
            hits.append(f"{tag}: evidence file says id {e['id']!r}")
        if norm(e["property"]) != prop:
            hits.append(f"{tag}: the checked property is not the signed one -- "
                        "it proves something else")
        if e["level"] not in LEVELS or LEVELS.index(e["level"]) < LEVELS.index(level):
            hits.append(f"{tag}: level {e['level']!r} is below the signed {level!r}")
        got_conf = e.get("conformance", "none")
        if got_conf not in CONFORMANCE or CONFORMANCE.index(got_conf) < CONFORMANCE.index(conf):
            hits.append(f"{tag}: conformance {got_conf!r} is below the signed {conf!r}")
        if e["level"] == "checked" and not str(e.get("bounds", "")).strip():
            hits.append(f"{tag}: `checked` without bounds -- a model check holds only "
                        "at the bounds it ran")
        if e["result"] != "pass":
            hits.append(f"{tag}: check result is {e['result']!r}")
        v = e["vacuity"] if isinstance(e["vacuity"], dict) else {}
        if not v.get("command") or v.get("result") != "fail":
            hits.append(f"{tag}: no vacuity run that failed -- a check that cannot "
                        "fail proves nothing")
        c = e.get("conformance_check")
        if got_conf != "none" and not (isinstance(c, dict) and c.get("command")
                                       and c.get("result") == "pass"):
            hits.append(f"{tag}: conformance {got_conf!r} claimed with no passing "
                        "conformance_check")
        sources = e["sources"] if isinstance(e["sources"], list) else [e["sources"]]
        cmd = check_live.code(str(e["command"]))
        if NOOP.match(cmd) or not any(str(x) in cmd for x in sources):
            hits.append(f"{tag}: the check command names none of its sources, or does "
                        "nothing -- it cannot have checked them")
        vcmd = check_live.code(str(v.get("command", "")))
        if v.get("command") and (FALSE.match(vcmd) or vcmd.strip() == cmd.strip()):
            hits.append(f"{tag}: the vacuity run is a bare failure or the check itself "
                        "-- it shows nothing about the check")
        ex = pattern(tag, "the check", e, hits)
        vx = pattern(tag, "the vacuity run", v, hits) if v.get("command") else None
        cx = pattern(tag, "the conformance check", c, hits) if isinstance(c, dict) and \
            c.get("command") else None
        texts = {}
        for src in sources:
            try:
                texts[src] = (root / src).read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
        word = str(e["tool"]).split()[0].lower() if str(e["tool"]).split() else ""
        code = [ln for t in texts.values() for ln in t.lower().splitlines()
                if not re.match(r"\s*(#|//|--|\(\*|\*|\\\*)", ln)]
        if word and word not in cmd.lower() and not any(word in ln for ln in code):
            hits.append(f"{tag}: tool {e['tool']!r} is named by neither the command nor a "
                        "source -- nothing shows it ran")
        tla = "\n".join(t for s_, t in texts.items() if str(s_).endswith(".tla"))
        if tla:
            for ident in sorted(set(re.findall(r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b", prop))):
                if not re.search(rf"^\s*{ident}\s*(\(.*\))?\s*==", tla, re.M):
                    hits.append(f"{tag}: the signed Property names {ident}, which no .tla "
                                "source defines -- the checked property is not the signed one")
        for src in sources:
            p = root / src
            if not p.is_file():
                hits.append(f"{tag}: source {src} does not exist")
                continue
            for h in hatches(p):
                hits.append(f"{tag}: escape hatch in {h} -- a proof that is not a proof")
        why = check_live.drifted(root, str(e["sha"]).lower(), evidence,
                                 check_live.contract(root, reqfile))
        if why:
            hits.append(f"{tag}: sha {str(e['sha'])[:12]} " + {
                "bad": "is not a full commit id",
                "orphan": "is not in HEAD's history",
                "stale": "is stale -- the code changed since; re-run the check"}[why])
        if rerun:
            rc, text = run_cmd(e["command"], tree.get())
            if rc != 0:
                hits.append(f"{tag}: re-run of the check exited {rc}")
            elif ex and not ex.search(text):
                hits.append(f"{tag}: re-run of the check does not print its expect")
            if v.get("command"):
                rc, text = run_cmd(v["command"], tree.get())
                if rc in (0, None):
                    hits.append(f"{tag}: re-run of the vacuity run did not fail")
                elif vx and not vx.search(text):
                    hits.append(f"{tag}: re-run of the vacuity run failed for another "
                                "reason than its expect")
            if cx:
                rc, text = run_cmd(c["command"], tree.get())
                if rc != 0 or not cx.search(text):
                    hits.append(f"{tag}: re-run of the conformance check failed")
    return hits


# The self-test's stand-in model checker: a real program, so a re-run means it.
CHECKER = """# a stand-in model checker for the self-test
import sys
TOOL = "TLC"
a = sys.argv[1:]
if "--broken" in a or "--fail" in a:
    print("Invariant is violated")
    sys.exit(1)
if "--crash" in a:
    print("Traceback: boom")
    sys.exit(2)
print("trace accepted" if "--trace" in a else "done" if "--quiet" in a
      else "No error has been found")
"""


def self_test():
    quiet = ["-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
             "-c", "core.hooksPath=/dev/null"]
    git = check_live.git
    prop = "always at most one leader"
    req = (f"# r\n- **R1** — x\n  - *Property*: {prop}\n  - *Formal*: checked\n"
           "  - *Conformance*: trace\n- **R2** — y\n  - *Property*: none — copy text\n")

    def tree(d, extra=None, req_text=req):
        files = {"req/requirements.md": req_text, "spec/M.tla": "---- MODULE M ----\n====\n",
                 "spec/check.py": CHECKER, "src/app.py": "print(1)\n", **(extra or {})}
        for rel, text in files.items():
            p = pathlib.Path(d, rel)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        git(d, "init", "-q")
        git(d, "add", "-A")
        git(d, *quiet, "commit", "-qm", "x")
        return check_live.out(git(d, "rev-parse", "HEAD")).strip()

    def ev(d, head, **kw):
        e = {"id": "R1", "property": prop, "level": "checked", "conformance": "trace",
             "tool": "TLC", "command": "python3 spec/check.py spec/M.tla",
             "sources": ["spec/M.tla", "spec/check.py"], "bounds": "3 nodes",
             "expect": "No error has been found", "observed": "No error has been found",
             "result": "pass", "sha": head, "at": "2026-10-08T00:00:00Z",
             "vacuity": {"command": "python3 spec/check.py spec/M.tla --broken",
                         "expect": "is violated", "observed": "Invariant is violated",
                         "result": "fail"},
             "conformance_check": {"command": "python3 spec/check.py --trace", "expect": "accepted",
                                   "observed": "trace accepted", "result": "pass"}}
        e.update(kw)
        e = {k: v for k, v in e.items() if v is not None}
        p = pathlib.Path(d, "req/formal/R1.json")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(e), encoding="utf-8")

    cases = [
        ("a clean set", {}, {}, None, False),
        ("no evidence", None, {}, "no formal evidence", False),
        ("an edited property", {"property": "at most two leaders"}, {}, "not the signed one", False),
        ("a level below the signed one", {"level": "tested"}, {}, "below the signed 'checked'", False),
        ("conformance below the signed one", {"conformance": "none"}, {}, "below the signed 'trace'", False),
        ("checked without bounds", {"bounds": None}, {}, "without bounds", False),
        ("a failed check", {"result": "fail"}, {}, "check result is 'fail'", False),
        ("no vacuity run", {"vacuity": None}, {}, "lacks vacuity", False),
        ("a vacuity run that passed", {"vacuity": {"command": "python3 spec/check.py x",
                                                    "expect": "violated", "observed": "violated",
                                                    "result": "pass"}}, {},
         "no vacuity run that failed", False),
        ("a no-op check", {"command": "true"}, {}, "names none of its sources", False),
        ("a tool nothing names", {"tool": "Apalache"}, {}, "named by neither", False),
        ("a tool named only in a comment", {"tool": "Quint"},
         {"spec/check.py": CHECKER.replace("# a stand-in", "# Quint: a stand-in")},
         "named by neither", False),
        ("a check naming no source", {"command": "python3 elsewhere.py"}, {},
         "names none of its sources", False),
        ("a bare-false vacuity run", {"vacuity": {"command": "false", "expect": "x",
                                                  "observed": "x", "result": "fail"}}, {},
         "bare failure or the check itself", False),
        ("a vacuity run that is the check", {"vacuity": {
            "command": "python3 spec/check.py spec/M.tla", "expect": "error",
            "observed": "error", "result": "fail"}}, {}, "bare failure or the check itself", False),
        ("no expect", {"expect": None}, {}, "lacks expect", False),
        ("an expect that matches anything", {"expect": ".*"}, {}, "matches anything", False),
        ("observed not matching expect", {"observed": "something else"}, {},
         "does not match its expect", False),
        ("a re-run that prints something else", {"command": "python3 spec/check.py spec/M.tla --quiet"},
         {}, "does not print its expect", True),
        ("a vacuity re-run failing for another reason", {"vacuity": {
            "command": "python3 spec/check.py spec/M.tla --crash", "expect": "is violated",
            "observed": "is violated", "result": "fail"}}, {}, "another reason", True),
        ("conformance with no check", {"conformance_check": None}, {}, "no passing conformance_check", False),
        ("a missing source", {"sources": ["spec/Nope.tla"]}, {}, "does not exist", False),
        ("a short sha", {"sha": "abc123"}, {}, "not a full commit id", False),
        ("a re-run that fails", {"command": "python3 spec/check.py spec/M.tla --fail"}, {},
         "re-run of the check exited 1", True),
        ("a vacuity re-run that passes", {"vacuity": {
            "command": "python3 spec/check.py spec/M.tla --pass", "expect": "is violated",
            "observed": "is violated", "result": "fail"}}, {}, "vacuity run did not fail", True),
        ("a clean re-run", {}, {}, None, True),
    ]
    for ext, line in [(".lean", "theorem t : p := by sorry"), (".lean", "axiom magic : False"),
                      (".lean", "private axiom magic : False"), (".v", "Parameter magic : False."),
                      (".v", "Hypothesis h : False."), (".thy", "axiomatization where ax: False"),
                      (".v", "Admitted."), (".dfy", "assume x > 0;"), (".dfy", "lemma {:axiom} L()"),
                      (".rs", "assume(n > 0);"), (".rs", "#[verifier::external_body]"),
                      (".tla", "THEOREM T == Spec => Inv PROOF OMITTED"), (".thy", "  sorry"),
                      (".py", "assume(False)")]:
        cases.append((f"escape hatch {line!r}", {"sources": [f"spec/P{ext}"]},
                      {f"spec/P{ext}": line + "\n"}, "escape hatch", False))
    for label, kw, extra, want, rerun in cases:
        with tempfile.TemporaryDirectory() as d:
            head = tree(d, extra)
            if kw is not None:
                ev(d, head, **kw)
            got = check(pathlib.Path(d), pathlib.Path(d, "req/requirements.md"),
                        only=["R1"], rerun=rerun)
            if not ((not got) if want is None else any(want in h for h in got)):
                print(f"self-test FAILED: {label}: expected {want or 'clean'}, got {got or 'clean'}")
                return 1
    with tempfile.TemporaryDirectory() as d:
        tree(d, req_text="# r\n- **R1** — x\n  - *Property*: none of the orders is lost\n")
        got = check(pathlib.Path(d), pathlib.Path(d, "req/requirements.md"))
        if not any("Formal" in h for h in got):
            print(f"self-test FAILED: a property starting with 'none of': got {got or 'clean'}")
            return 1
    more = [
        ("stale evidence", "stale"),
        ("Property: none without a reason", "needs a reason"),
        ("no Property line", "no `Property:`"),
    ]
    with tempfile.TemporaryDirectory() as d:
        head = tree(d)
        ev(d, head)
        pathlib.Path(d, "src/app.py").write_text("print(2)\n")
        git(d, "add", "-A")
        git(d, *quiet, "commit", "-qm", "y")
        got = check(pathlib.Path(d), pathlib.Path(d, "req/requirements.md"), only=["R1"])
        if not any("stale" in h for h in got):
            print(f"self-test FAILED: {more[0][0]}: got {got or 'clean'}")
            return 1
    for label, text, want in [(more[1][0], "# r\n- **R1** — x\n  - *Property*: none\n", more[1][1]),
                              (more[2][0], "# r\n- **R1** — x\n  - *Verify*: local\n", more[2][1])]:
        with tempfile.TemporaryDirectory() as d:
            tree(d, req_text=text)
            got = check(pathlib.Path(d), pathlib.Path(d, "req/requirements.md"))
            if not any(want in h for h in got):
                print(f"self-test FAILED: {label}: got {got or 'clean'}")
                return 1
    print(f"self-test ok ({len(cases) + len(more) + 1} cases)")
    return 0


def main(argv):
    if "--self-test" in argv:
        return self_test()
    ap = argparse.ArgumentParser(description="formal evidence for every requirement")
    ap.add_argument("--root", default=".")
    ap.add_argument("--requirements", required=True)
    ap.add_argument("--evidence")
    ap.add_argument("--only", type=lambda s: [x.strip() for x in s.split(",") if x.strip()])
    ap.add_argument("--rerun", action="store_true")
    a = ap.parse_args(argv)
    root = pathlib.Path(a.root).resolve()
    hits = check(root, root / a.requirements, root / a.evidence if a.evidence else None,
                 a.only, a.rerun)
    for h in hits:
        print(h)
    if hits:
        print(f"\n{len(hits)} hit(s). A property nobody checked is a wish.")
        return 1
    print("formal: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
