#!/usr/bin/env python3
"""Fail the gate when TASKS.md -- the run's only ledger -- is wrong.

    check_tasks.py [--tasks TASKS.md]  check the format, the IDs, the signatures,
                                       the loop bounds, and every Done item's
                                       live + formal evidence
    check_tasks.py --sign              print the `Signed:` line for the files it
                                       names (the orchestrator writes it at a batch)
    check_tasks.py --rerun             ...and re-run every Done item's live probes
                                       and formal checks: stored evidence is the
                                       writer's claim, a re-run is proof (QA, and
                                       the Ship batch, run this)
    check_tasks.py --self-test         prove every rule fails on a known bad file
    options: --root DIR  --env NAME (whose live evidence proves Done)
             --src PATH...  --test GLOB...  --allow FILE (check_live's code
             scan, from standards.md: a Done item is `check_live --only <ID>`
             green, and that includes its code scan)
             --no-evidence (format, IDs and signatures only)

Reference implementation of the TASKS.md rule in the aidlc skill. Host-neutral,
stdlib only; installed beside check_live.py and check_formal.py, which it runs.

THE FILE -- the current state, nothing more (git keeps the history)
    Signed: requirements.md sha256:3f2a9c0b1d4e · standards.md sha256:77ab01c9e2f0
    Gate: 🔴 design — awaiting CEO                  (only while a batch is open)

    ## Done
    - [x] R1 the user can log in
    ## In progress
    - [~] R3 export CSV — verifying · backend · 2/5 stalled 1/3 · next: QA re-runs
    - [~] R4 import — blocked on the CRM key (CEO) · backend · 1/5 stalled 0/3 · next: ask
    ## Todo
    - [ ] R5 audit log
    - [ ] C1 deployed to production without a pre-authorization — every sensor green, rollback tested
    - [ ] D1 split the 900-line handler (audit, medium)

    `Cn` is a decision a role made on its own judgment -- it did not stop the
    run to ask. Open (`[ ]`) in Todo until the CEO ticks it at the next batch,
    then `[x]` in Done.

    Paths in `Signed:` are relative to TASKS.md. The first is the requirements;
    the design batch adds standards.md, design.md and the ADRs.

RED WHEN
    the three sections are missing, out of order, or joined by another; a line
    is not its section's form; a status is not building | verifying | fixing |
    blocked on <what>; the attempts field is not `<n>/5 stalled <k>/3` (both
    counters, always); a count is AT its bound without `blocked on loop-bound` -- the bound stops the run,
    it is not one more try; a requirement ID is missing, listed twice, or
    unknown -- `Dn` tech debt is allowed, in Todo only, and `Cn` (a decision
    for the CEO to tick) in Todo or Done, never In progress; a Done line carries a
    status (a status word, `blocked on`, an attempt count or `next:`, after
    any joint); a Done item's live (check_live) or formal (check_formal) evidence is
    not fresh; the first `Signed:` file is not named requirements.md, or has no
    items; a
    `Signed:` hash does not match the file now -- the run stops until the CEO
    re-signs: `drift` for requirements.md / standards.md, `cross-design` for
    any other signed file (design.md, an ADR); the Gate is not exactly
    `🔴 <intent|design|ship> — awaiting CEO`.
"""
import argparse
import hashlib
import os
import json
import pathlib
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.dont_write_bytecode = True     # no __pycache__ in the user's tree
import check_formal  # noqa: E402
import check_live  # noqa: E402

SECTIONS = ("Done", "In progress", "Todo")
MARK = {"Done": "x", "In progress": "~", "Todo": " "}
BATCHES = ("intent", "design", "ship")
MAX_ATTEMPTS, MAX_STALLED = 5, 3
FORM = (f"— <status> · <owner> · <n>/{MAX_ATTEMPTS} stalled <k>/{MAX_STALLED} · "
        "next: <step>")
STATUS = re.compile(r"(building|verifying|fixing|blocked on \S.*)$")
LEAD = r"(?:--|(?<!\w)-|[—–·:,(\[|])"   # what may join a status onto a title
TAIL = r"(?:$|--|[-—–·:,)\].|])"
DONE_STATUS = re.compile(rf"(?i){LEAD}\s*(?:(?:building|verifying|fixing|blocked)\s*{TAIL}|"
                         rf"blocked on\b|(?:attempts?\s+)?\d+/\d+\b)|\bstalled\s+\d+/\d+|"
                         rf"\bnext:")
GATE = re.compile(r"🔴 (intent|design|ship) — awaiting CEO")
DRIFT = ("requirements.md", "standards.md")      # anything else signed: cross-design
ITEM = re.compile(r"- \[(.)\] ([RNDC]\d+) (\S.*)$")
DASH = re.compile(r"\s+[—–]\s+")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def sign(tasks, files):
    return "Signed: " + " · ".join(f"{f} sha256:{digest(tasks.parent / f)}" for f in files)


def parse(text):
    """(signed [(path, hash)], gate, {section: [(lineno, mark, id, rest)]}, hits)"""
    signed, gate, sections, cur, hits = [], None, {}, None, []
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        if line.startswith("## "):
            cur = line[3:].strip()
            if cur not in SECTIONS:
                hits.append(f"TASKS.md:{n}: section `{cur}` -- only {', '.join(SECTIONS)}")
            elif cur in sections:
                hits.append(f"TASKS.md:{n}: section `{cur}` twice")
            sections.setdefault(cur, [])
            continue
        if cur is None:
            if line.startswith("Signed:"):
                for part in line[7:].split("·"):
                    m = re.fullmatch(r"\s*(\S+)\s+sha256:([0-9a-f]{12})\s*", part)
                    if not m:
                        hits.append(f"TASKS.md:{n}: `{part.strip()}` is not `<path> sha256:<12 hex>`")
                    else:
                        signed.append((m.group(1), m.group(2)))
            elif line.startswith("Gate:"):
                gate = line[5:].strip()
            elif not line.startswith("#"):
                hits.append(f"TASKS.md:{n}: before the sections only `Signed:` and `Gate:`")
            continue
        m = ITEM.match(line.strip())
        if not m:
            hits.append(f"TASKS.md:{n}: `{line.strip()[:60]}` is not `- [ ] <ID> <title>`")
            continue
        sections[cur].append((n, m.group(1), m.group(2), m.group(3)))
    order = [s for s in sections if s in SECTIONS]
    if order != list(SECTIONS):
        hits.append(f"TASKS.md: sections must be exactly {' / '.join(SECTIONS)} in that "
                    f"order (found {' / '.join(order) or 'none'})")
    return signed, gate, sections, hits


def check(root, tasks, evidence=True, env=None, rerun=False, src=None, tests=(),
          allow=None):
    if rerun and (why := check_live.unclean(root)):
        return [why]
    if not tasks.is_file():
        return [f"no TASKS.md at {tasks} -- the run has no ledger"]
    signed, gate, sections, hits = parse(tasks.read_text(encoding="utf-8"))
    if not signed:
        return hits + ["TASKS.md: no `Signed:` line -- nothing is signed, nothing may run"]
    if rerun and (why := check_live.at_head(root, tasks, *[tasks.parent / p for p, _ in signed
                                                            if (tasks.parent / p).is_file()])):
        return [why]
    for path, want in signed:
        f = tasks.parent / path
        if not f.is_file():
            hits.append(f"TASKS.md: signed file {path} does not exist")
        elif digest(f) != want:
            kind = "drift" if pathlib.Path(path).name in DRIFT else "cross-design"
            hits.append(f"TASKS.md: {kind.upper()} -- {path} is sha256:{digest(f)}, "
                        f"signed sha256:{want}. Interrupt `{kind}`: the run stops "
                        "until the CEO re-signs it.")
    if gate is not None and not GATE.fullmatch(gate):
        hits.append(f"TASKS.md: Gate `{gate}` is not `🔴 <{'|'.join(BATCHES)}> — awaiting CEO`")
    reqfile = tasks.parent / signed[0][0]
    req = check_live.fields(reqfile) if reqfile.is_file() else {}
    if signed[0][0] != "requirements.md" or not req:
        return hits + [f"TASKS.md: the first `Signed:` file, {signed[0][0]}, is not named "
                       "requirements.md, or has no Rn/Nn items -- nothing can be checked"]
    seen = {}
    for sec, lines in sections.items():
        for n, mark, rid, rest in lines:
            tag = f"TASKS.md:{n} {rid}"
            if sec in MARK and mark != MARK[sec]:
                hits.append(f"{tag}: `[{mark}]` in {sec} -- it takes `[{MARK[sec]}]`")
            seen.setdefault(rid, []).append(sec)
            if rid.startswith("D"):
                if sec != "Todo":
                    hits.append(f"{tag}: tech debt lives in Todo")
                continue
            if rid.startswith("C"):
                if sec == "In progress":
                    hits.append(f"{tag}: a decision for the CEO is open (Todo) or "
                                "ticked (Done), never in progress")
                continue
            parts = DASH.split(rest, maxsplit=1)
            # a status, however it is joined (a dash, `--`, `·`, `:` or `,`): a
            # status word that ends there or at the next joint, `blocked on`,
            # an attempt count, or `next:` -- not a title such as
            # `Property · Formal · Conformance` or `build - fixing the parser`
            if sec == "Done" and (len(parts) > 1 or DONE_STATUS.search(rest)):
                hits.append(f"{tag}: a Done line carries no status")
            if sec == "In progress":
                hits += progress(tag, parts)
    for rid in req:
        if rid not in seen:
            hits.append(f"TASKS.md: {rid} is in the requirements but not in TASKS.md")
    for rid, secs in seen.items():
        if len(secs) > 1:
            hits.append(f"TASKS.md: {rid} is listed {len(secs)} times ({', '.join(secs)})")
        if rid[0] not in "DC" and rid not in req:
            hits.append(f"TASKS.md: {rid} is not a requirement of {signed[0][0]}")
    done = [rid for _, _, rid, _ in sections.get("Done", []) if rid in req]
    if evidence and done and reqfile.is_file():
        ev = reqfile.parent / "evidence"
        # one HEAD for both re-runs, reading up front what the checks will read
        tree = check_live.HeadTree(root, check_formal.sources(reqfile, only=done) +
                                   ([check_live.rel_to(root, allow)] if allow else []))
        if rerun:
            tree.want_dir(ev / env if env else ev)
            tree.want_dir(reqfile.parent / "formal")
        try:
            live = check_live.check_evidence(root, reqfile, ev / env if env else ev, done,
                                             (), rerun, False, False, tree)
            hits += [f"Done but not live: {h}" for h in live]
            # check_live --only <ID> also runs the code scan over what ships
            hits += [f"Done but not live: {h}"
                     for h in check_live.scan(root, tree, rerun, src, tests, allow)]
            hits += [f"Done but not formal: {h}" for h in
                     check_formal.check(root, reqfile, only=done, rerun=rerun, tree=tree)]
        finally:
            tree.close()
    return hits


def progress(tag, parts):
    if len(parts) < 2:
        return [f"{tag}: in progress needs `{FORM}`"]
    f = [x.strip() for x in parts[1].split("·")]
    if len(f) != 4 or not f[3].startswith("next:") or not f[3][5:].strip():
        return [f"{tag}: in progress needs `{FORM}`"]
    hits = []
    if not STATUS.match(f[0]):
        hits.append(f"{tag}: status `{f[0]}` -- building | verifying | fixing | "
                    "blocked on <what>")
    if not f[1]:
        hits.append(f"{tag}: no owner")
    m = re.fullmatch(r"(\d+)/(\d+)\s+stalled\s+(\d+)/(\d+)", f[2])
    if not m:
        hits.append(f"{tag}: attempts `{f[2]}` is not `<n>/{MAX_ATTEMPTS} stalled "
                    f"<k>/{MAX_STALLED}` -- both counters, always")
    else:
        n, cap, k, kcap = (int(x) for x in m.groups())
        raised = f[0].startswith("blocked on loop-bound")
        if cap != MAX_ATTEMPTS or kcap != MAX_STALLED:
            hits.append(f"{tag}: the bounds are Loop A's {MAX_ATTEMPTS} total / "
                        f"{MAX_STALLED} stalled, written as such -- changing them is a "
                        "CEO decision")
        elif n > cap or k > kcap:
            hits.append(f"{tag}: {f[2]} -- past Loop A's bound: the run should have "
                        "stopped at it")
        elif (n == cap or k == kcap) and not raised:
            hits.append(f"{tag}: {f[2]} -- Loop A's bound is reached: the status must be "
                        "`blocked on loop-bound`, and the CEO decides")
    return hits


def self_test():
    req = ("# r\n- **R1** — a\n  - *Verify*: local\n  - *Property*: none — text\n"
           "- **R2** — b\n- **N1** — c\n")
    good = ("{signed}\n\n## Done\n\n## In progress\n"
            "- [~] R1 a — verifying · qa · 2/5 stalled 0/3 · next: rerun\n"
            "- [~] R2 b — blocked on the CRM key · backend · 1/5 stalled 1/3 · next: ask\n"
            "## Todo\n- [ ] N1 c\n- [ ] D1 split the handler\n")
    cases = [
        ("a clean file", lambda t: t, None),
        ("no Signed line", lambda t: t.split("\n", 1)[1], "no `Signed:` line"),
        ("a missing section", lambda t: t.replace("## Done\n", ""), "sections must be exactly"),
        ("sections out of order", lambda t: t.replace("## Done\n\n## In progress\n",
                                                      "## In progress\n## Done\n"), "in that order"),
        ("an extra section", lambda t: t + "## Later\n", "only Done"),
        ("a bad status", lambda t: t.replace("verifying ·", "almost ·"), "status `almost`"),
        ("blocked with no reason", lambda t: t.replace("blocked on the CRM key", "blocked"),
         "status `blocked`"),
        ("a missing ID", lambda t: t.replace("- [ ] N1 c\n", ""), "N1 is in the requirements"),
        ("a duplicated ID", lambda t: t + "- [ ] R2 b again\n", "listed 2 times"),
        ("an unknown ID", lambda t: t + "- [ ] R9 ghost\n", "R9 is not a requirement"),
        ("an open decision for the CEO", lambda t: t + "- [ ] C1 shipped without the key — the CEO ticks it\n", None),
        ("a ticked decision", lambda t: t.replace("## In progress", "- [x] C1 shipped — ticked\n## In progress"),
         "!C1"),
        ("a decision in progress", lambda t: t.replace(
            "## Todo", "- [~] C1 deciding — fixing · be · 1/5 stalled 0/3 · next: x\n## Todo"),
         "never in progress"),
        ("tech debt in progress", lambda t: t.replace(
            "- [ ] D1 split the handler\n", "").replace(
            "## Todo", "- [~] D1 split — fixing · be · 1/5 · next: x\n## Todo"), "tech debt lives in Todo"),
        ("a wrong mark", lambda t: t.replace("- [ ] N1", "- [x] N1"), "takes `[ ]`"),
        ("6/5 attempts", lambda t: t.replace("2/5", "6/5"), "past Loop A's bound"),
        ("5/5 attempts, still trying", lambda t: t.replace("2/5", "5/5"), "bound is reached"),
        ("5/5 attempts, raised", lambda t: t.replace("verifying · qa · 2/5",
                                                     "blocked on loop-bound (CEO) · qa · 5/5"), None),
        ("no stalled counter", lambda t: t.replace("2/5 stalled 0/3", "2/5"), "both counters"),
        ("a stalled count past its bound", lambda t: t.replace("stalled 1/3", "stalled 4/3"),
         "past Loop A's bound"),
        ("a decoy requirements file signed first", lambda t: t.replace(
            "Signed: requirements.md", "Signed: fake-requirements.md"), "not named requirements.md"),
        ("stalled 3/3, still trying", lambda t: t.replace("stalled 1/3", "stalled 3/3").replace(
            "blocked on the CRM key", "fixing"), "bound is reached"),
        ("a raised bound", lambda t: t.replace("2/5", "2/9"), "changing them is a CEO decision"),
        ("a lowered bound", lambda t: t.replace("stalled 0/3", "stalled 0/2"),
         "changing them is a CEO decision"),
        ("a nested decoy requirements file", lambda t: t.replace(
            "Signed: requirements.md", "Signed: nested/requirements.md"), "not named requirements.md"),
        ("4/3 stalled", lambda t: t.replace("stalled 1/3", "stalled 4/3"), "past Loop A's bound"),
        ("a bad in-progress line", lambda t: t.replace(" · next: rerun", ""), "in progress needs"),
        ("a Gate naming no batch", lambda t: t.replace("\n\n## Done", "\nGate: 🔴 later\n\n## Done"),
         "is not `🔴"),
        ("a Gate with trailing text", lambda t: t.replace(
            "\n\n## Done", "\nGate: 🔴 design — awaiting CEO, or not\n\n## Done"), "is not `🔴"),
        ("the first Signed file is not the requirements",
         lambda t: re.sub(r"^Signed: (requirements\.md \S+) · (standards\.md \S+)",
                          r"Signed: \2 · \1", t), "is not named requirements.md"),
        ("a Gate naming a batch", lambda t: t.replace("\n\n## Done",
                                                      "\nGate: 🔴 design — awaiting CEO\n\n## Done"), None),
        ("a Done line with a status", lambda t: t.replace(
            "## Done\n", "## Done\n- [x] N1 c — verifying · qa · 1/5 · next: x\n").replace(
            "- [ ] N1 c\n", ""), "carries no status"),
        ("a Done line with a status after a hyphen", lambda t: t.replace(
            "## Done\n", "## Done\n- [x] N1 c - verifying · qa · 1/5 stalled 0/3 · next: x\n").replace(
            "- [ ] N1 c\n", ""), "carries no status"),
        ("a Done title with a middle dot", lambda t: t.replace("- [ ] N1 c\n", "").replace(
            "## Done\n", "## Done\n- [x] N1 Property · Formal · Conformance\n"), "!carries no status"),
        ("a Done line with a status after `--`", lambda t: t.replace("- [ ] N1 c\n", "").replace(
            "## Done\n", "## Done\n- [x] N1 c -- verifying\n"), "carries no status"),
        ("a Done line with a status after a middle dot", lambda t: t.replace("- [ ] N1 c\n", "").replace(
            "## Done\n", "## Done\n- [x] N1 c · verifying · qa\n"), "carries no status"),
        ("a Done line with an attempt count", lambda t: t.replace("- [ ] N1 c\n", "").replace(
            "## Done\n", "## Done\n- [x] N1 c · qa · 2/5\n"), "carries no status"),
        ("a Done line ending in a bare blocked", lambda t: t.replace("- [ ] N1 c\n", "").replace(
            "## Done\n", "## Done\n- [x] N1 c · blocked\n"), "carries no status"),
        ("a Done line with a bracketed status", lambda t: t.replace("- [ ] N1 c\n", "").replace(
            "## Done\n", "## Done\n- [x] N1 c (verifying)\n"), "carries no status"),
        ("a Done line with a capitalised status", lambda t: t.replace("- [ ] N1 c\n", "").replace(
            "## Done\n", "## Done\n- [x] N1 c · Verifying · qa\n"), "carries no status"),
        ("a Done line with a stalled count", lambda t: t.replace("- [ ] N1 c\n", "").replace(
            "## Done\n", "## Done\n- [x] N1 c · stalled 1/3\n"), "carries no status"),
        ("a Done line with an attempt count", lambda t: t.replace("- [ ] N1 c\n", "").replace(
            "## Done\n", "## Done\n- [x] N1 c · attempt 2/5\n"), "carries no status"),
        ("a Done title with a hyphenated word", lambda t: t.replace("- [ ] N1 c\n", "").replace(
            "## Done\n", "## Done\n- [x] N1 support re-verifying\n"), "!carries no status"),
        ("a Done title with a status word in prose", lambda t: t.replace("- [ ] N1 c\n", "").replace(
            "## Done\n", "## Done\n- [x] N1 build - fixing the parser\n"), "!carries no status"),
        ("Done without evidence", lambda t: t.replace(
            "## Done\n", "## Done\n- [x] N1 c\n").replace("- [ ] N1 c\n", ""), "Done but not live"),
    ]
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "req").mkdir()
        (root / "req/requirements.md").write_text(req, encoding="utf-8")
        (root / "req/standards.md").write_text("# s\n", encoding="utf-8")
        (root / "req/design.md").write_text("# d\n", encoding="utf-8")
        (root / "req/fake-requirements.md").write_text(req, encoding="utf-8")
        (root / "req/nested").mkdir()
        (root / "req/nested/requirements.md").write_text(req, encoding="utf-8")
        q = ["-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
        subprocess.run(["git", "-C", d, "init", "-q"], check=True)
        subprocess.run(["git", "-C", d, "add", "-A"], check=True)
        subprocess.run(["git", "-C", d, *q, "commit", "-qm", "x"], check=True)
        tasks = root / "req/TASKS.md"
        signed = sign(tasks, ["requirements.md", "standards.md", "design.md"])
        for label, edit, want in cases:
            tasks.write_text(edit(good.format(signed=signed)), encoding="utf-8")
            got = check(root, tasks)
            ok = (not got) if want is None else \
                not any(want[1:] in h for h in got) if want.startswith("!") else \
                any(want in h for h in got)          # "!x": no hit says x
            if not ok:
                print(f"self-test FAILED: {label}: expected {want or 'clean'}, got {got or 'clean'}")
                return 1
        drift = [("requirements.md drifted", "requirements.md", "DRIFT -- requirements.md"),
                 ("standards.md drifted", "standards.md", "DRIFT -- standards.md"),
                 ("design.md drifted", "design.md", "CROSS-DESIGN -- design.md")]
        for label, f, want in drift:
            tasks.write_text(good.format(signed=signed), encoding="utf-8")
            p = root / "req" / f
            before = p.read_text(encoding="utf-8")
            p.write_text(before + "\nedited after signing\n", encoding="utf-8")
            got = check(root, tasks)
            p.write_text(before, encoding="utf-8")
            if not any(want in h for h in got):
                print(f"self-test FAILED: {label}: got {got or 'clean'}")
                return 1
    # A Done item is `check_live --only <ID>` green, and that runs the code scan:
    # a mock shipped in the code fails it, unless the allow file names it.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        files = {"req/requirements.md": "# r\n- **R1** — a\n  - *Verify*: local\n"
                                        "  - *Property*: none — text\n",
                 "src/app.js": "export const t = mockTemp();\n",
                 "allow.txt": "src/app.js mockTemp -- the self-test's seeded hit\n"}
        for rel, text in files.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text, encoding="utf-8")
        q = ["-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
        subprocess.run(["git", "-C", d, "init", "-q"], check=True)
        subprocess.run(["git", "-C", d, "add", "-A"], check=True)
        subprocess.run(["git", "-C", d, *q, "commit", "-qm", "x"], check=True)
        sha = check_live.out(check_live.git(root, "rev-parse", "HEAD")).strip()
        (root / "req/evidence").mkdir()
        (root / "req/evidence/R1.json").write_text(json.dumps(
            {"id": "R1", "verify": "local", "target": "this checkout", "command": "echo ok",
             "expect": "ok", "observed": "ok", "result": "pass", "sha": sha,
             "at": "2026-10-09T00:00:00Z"}), encoding="utf-8")
        subprocess.run(["git", "-C", d, "add", "-A"], check=True)     # HEAD's record
        subprocess.run(["git", "-C", d, *q, "commit", "-qm", "ev"], check=True)
        tasks = root / "req/TASKS.md"
        tasks.write_text(sign(tasks, ["requirements.md"]) + "\n\n## Done\n- [x] R1 a\n"
                         "\n## In progress\n\n## Todo\n", encoding="utf-8")
        subprocess.run(["git", "-C", d, "add", "-A"], check=True)     # a re-run needs HEAD
        subprocess.run(["git", "-C", d, *q, "commit", "-qm", "tasks"], check=True)
        for label, kw, want in (("a Done item with a mock in the code", {}, True),
                                ("...on a re-run", {"rerun": True}, True),
                                ("...that the allow file names", {"allow": root / "allow.txt"},
                                 False)):
            got = check(root, tasks, **kw)
            if any("src/app.js:1" in h for h in got) != want:
                print(f"self-test FAILED: {label}: got {got or 'clean'}")
                return 1
        (root / "untracked.txt").write_text("x\n", encoding="utf-8")
        if not any("commit or stash" in h for h in check(root, tasks, rerun=True)):
            print("self-test FAILED: a re-run beside an untracked file is not refused")
            return 1
        (root / "untracked.txt").unlink()
        subprocess.run(["git", "-C", d, "update-index", "--skip-worktree", "req/TASKS.md"],
                       check=True)
        tasks.write_text(tasks.read_text(encoding="utf-8").replace("## Done\n- [x] R1 a\n",
                         "## Done\n"), encoding="utf-8")
        if not any("commit or stash" in h for h in check(root, tasks, rerun=True)):
            print("self-test FAILED: a re-run beside an edit hidden by --skip-worktree")
            return 1
        subprocess.run(["git", "-C", d, "update-index", "--no-skip-worktree", "req/TASKS.md"],
                       check=True)
        subprocess.run(["git", "-C", d, "rm", "-q", "--cached", "req/TASKS.md"], check=True)
        (root / ".gitignore").write_text("req/TASKS.md\n", encoding="utf-8")
        subprocess.run(["git", "-C", d, "add", ".gitignore"], check=True)
        subprocess.run(["git", "-C", d, *q, "commit", "-qm", "ignore the ledger"], check=True)
        if not any("not HEAD's" in h for h in check(root, tasks, rerun=True)):
            print("self-test FAILED: a re-run of a ledger HEAD does not have")
            return 1
    print(f"self-test ok ({len(cases) + len(drift) + 6} cases)")
    return 0


def main(argv):
    if "--self-test" in argv:
        return self_test()
    ap = argparse.ArgumentParser(description="TASKS.md: the run's only ledger")
    ap.add_argument("--root", default=".")
    ap.add_argument("--tasks", default="TASKS.md")
    ap.add_argument("--sign", nargs="+", metavar="FILE",
                    help="print the Signed: line for these files (relative to TASKS.md)")
    ap.add_argument("--env")
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--no-evidence", action="store_true")
    ap.add_argument("--src", nargs="+")
    ap.add_argument("--test", nargs="+", default=[])
    ap.add_argument("--allow")
    a = ap.parse_args(argv)
    root = pathlib.Path(a.root).resolve()
    tasks = root / a.tasks
    if a.sign:
        print(sign(tasks, a.sign))
        return 0
    hits = check(root, tasks, evidence=not a.no_evidence, env=a.env, rerun=a.rerun,
                 src=a.src, tests=a.test, allow=root / a.allow if a.allow else None)
    for h in hits:
        print(h)
    if hits:
        print(f"\n{len(hits)} hit(s). TASKS.md is what the run believes; make it true.")
        return 1
    print("tasks: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
