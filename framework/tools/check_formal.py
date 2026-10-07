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
     "conformance": "trace", "tool": "TLC 2.19", "command": "<runs the check>",
     "sources": ["spec/Cart.tla"], "bounds": "3 users, 4 items",
     "observed": "<excerpt>", "result": "pass", "sha": "<40-hex>", "at": "<ISO>",
     "vacuity": {"command": "<a run that must fail>", "observed": "...", "result": "fail"},
     "conformance_check": {"command": "...", "observed": "...", "result": "pass"}}
    Red when: no evidence; incomplete or not JSON; another id; the property is
    not the signed text (an edited property proves something else); level or
    conformance below the signed one; `checked` with no bounds; result not
    pass; no vacuity run, or one that passed (a check that cannot fail proves
    nothing); conformance claimed with no passing conformance_check; a source
    missing, or holding an escape hatch -- a proof that is not a proof
    (`sorry`, `admit`, `Admitted`, `axiom`, `assume`, `{:axiom}`, `OMITTED`,
    `assume(false)` ...); the sha not a full commit in HEAD's history, or the
    shipped tree changed since it (stale, same rule as check_live).
    With --rerun the check and the conformance check must exit 0 and the
    vacuity run must exit non-zero, now.

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
          "observed", "result", "sha", "at", "vacuity")

# Escape hatches, by file type: a proof that is not a proof. Comments count:
# "-- sorry, fix later" is exactly the confession this looks for.
ANY = [r"\bassume\s*\(\s*(false|False)\s*\)"]
HATCHES = {
    ".lean": [r"\bsorry\b", r"\badmit\b", r"^\s*axiom\b", r"\bnative_decide\b"],
    ".v": [r"\bAdmitted\b", r"\badmit\b", r"^\s*Axiom\b"],
    ".dfy": [r"\bassume\b", r"\{:axiom\}", r"\{:verify\s+false\}"],
    ".rs": [r"\bassume\s*\(", r"\badmit\s*\(", r"verifier::external_body",
            r"verifier\(external_body\)"],
    ".tla": [r"\bOMITTED\b"],
    ".thy": [r"\bsorry\b", r"\boops\b"],
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
        out[rid] = (None if re.match(r"none\b", prop) else prop, level, conf,
                    prop[4:].strip(" -—–:") if re.match(r"none\b", prop) else "")
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
    try:
        r = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, timeout=1800)
        return r.returncode
    except subprocess.TimeoutExpired:
        return None


def check(root, reqfile, evidence=None, only=None, rerun=False):
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
        for src in e["sources"] if isinstance(e["sources"], list) else [e["sources"]]:
            p = root / src
            if not p.is_file():
                hits.append(f"{tag}: source {src} does not exist")
                continue
            for h in hatches(p):
                hits.append(f"{tag}: escape hatch in {h} -- a proof that is not a proof")
        why = check_live.drifted(root, str(e["sha"]).lower(), evidence,
                                 reqfile.parent / "evidence")
        if why:
            hits.append(f"{tag}: sha {str(e['sha'])[:12]} " + {
                "bad": "is not a full commit id",
                "orphan": "is not in HEAD's history",
                "stale": "is stale -- the code changed since; re-run the check"}[why])
        if rerun:
            rc = run_cmd(e["command"], root)
            if rc != 0:
                hits.append(f"{tag}: re-run of the check exited {rc}")
            if v.get("command") and run_cmd(v["command"], root) in (0, None):
                hits.append(f"{tag}: re-run of the vacuity run did not fail")
            if isinstance(c, dict) and c.get("command") and run_cmd(c["command"], root) != 0:
                hits.append(f"{tag}: re-run of the conformance check failed")
    return hits


def self_test():
    quiet = ["-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
             "-c", "core.hooksPath=/dev/null"]
    git = check_live.git
    prop = "always at most one leader"
    req = (f"# r\n- **R1** — x\n  - *Property*: {prop}\n  - *Formal*: checked\n"
           "  - *Conformance*: trace\n- **R2** — y\n  - *Property*: none — copy text\n")

    def tree(d, extra=None, req_text=req):
        files = {"req/requirements.md": req_text, "spec/M.tla": "---- MODULE M ----\n====\n",
                 "src/app.py": "print(1)\n", **(extra or {})}
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
             "tool": "TLC", "command": "true", "sources": ["spec/M.tla"],
             "bounds": "3 nodes", "observed": "No error has been found", "result": "pass",
             "sha": head, "at": "2026-10-08T00:00:00Z",
             "vacuity": {"command": "false", "observed": "violated", "result": "fail"},
             "conformance_check": {"command": "true", "observed": "accepted", "result": "pass"}}
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
        ("a vacuity run that passed", {"vacuity": {"command": "true", "result": "pass"}}, {},
         "no vacuity run that failed", False),
        ("conformance with no check", {"conformance_check": None}, {}, "no passing conformance_check", False),
        ("a missing source", {"sources": ["spec/Nope.tla"]}, {}, "does not exist", False),
        ("a short sha", {"sha": "abc123"}, {}, "not a full commit id", False),
        ("a re-run that fails", {"command": "false"}, {}, "re-run of the check exited 1", True),
        ("a vacuity re-run that passes", {"vacuity": {"command": "true", "result": "fail"}}, {},
         "vacuity run did not fail", True),
        ("a clean re-run", {}, {}, None, True),
    ]
    for ext, line in [(".lean", "theorem t : p := by sorry"), (".lean", "axiom magic : False"),
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
    print(f"self-test ok ({len(cases) + len(more)} cases)")
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
