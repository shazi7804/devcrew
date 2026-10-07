#!/usr/bin/env python3
"""Fail on a broken relative link or a malformed role file.

    tools/check_repo.py        check every Markdown file and every role file

LINKS — every relative Markdown link must point at a file that exists, and a
`#anchor` into a Markdown file must match one of its headings (GitHub's slug
rules). External URLs are not fetched: CI must not fail because a third-party
site is down.

ROLE FILES — each `framework/agents/<name>.md` is what every host adapter
translates, so a typo here becomes a broken agent on three hosts at once. Its
frontmatter must carry name, role, description, tools, model, skills and
memory; `name` must match the file name; `tools` must use the neutral
vocabulary the adapters map; `memory` must be `shared` or `none`. Two
capabilities are withheld by design and checked here, not assumed: `reviewer`
mounts no memory (invariant 4) and `auditor` holds no write tool (invariant 7).

PROTOCOL SETS — the stages, batches and interrupts that SKILL.md names (in its
protocol-sets block, and in the batch and interrupt tables) must be the ones
framework/formal/Aidlc.tla model-checks. The orchestrator is a model,
not a program, so this is the conformance there is: a phase, batch or interrupt
added to the prose and not to the model is one nobody proved anything about.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "node_modules", ".claude", ".aidlc"}

REQUIRED = ["name", "role", "description", "tools", "model", "skills", "memory"]
NEUTRAL_TOOLS = {"read", "write", "edit", "shell", "search", "web", "spawn", "memory"}
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def markdown_files():
    for f in sorted(ROOT.rglob("*.md")):
        if not SKIP_DIRS.intersection(f.relative_to(ROOT).parts):
            yield f


def prose_lines(text, keep_code=False):
    """Lines outside code fences; inline code is removed unless kept."""
    infence = False
    for n, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            infence = not infence
            continue
        if not infence:
            yield n, line if keep_code else re.sub(r"`[^`]*`", "", line)


def slug(heading):
    s = heading.strip().lower()
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")


def anchors(path):
    text = path.read_text(encoding="utf-8")
    return {slug(line.lstrip("#")) for _, line in prose_lines(text, keep_code=True)
            if re.match(r"#{1,6} ", line)}


def check_links():
    problems = []
    for f in markdown_files():
        rel = f.relative_to(ROOT).as_posix()
        for n, line in prose_lines(f.read_text(encoding="utf-8")):
            for target in LINK.findall(line):
                if re.match(r"[a-z]+:", target):
                    continue
                path, _, anchor = target.partition("#")
                dest = (f.parent / path).resolve() if path else f
                if not dest.exists():
                    problems.append(f"{rel}:{n}: broken link {target}")
                elif anchor and dest.suffix == ".md" and anchor not in anchors(dest):
                    problems.append(f"{rel}:{n}: no heading for #{anchor} in {path or rel}")
    return problems


def frontmatter(text):
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    fm = {}
    for line in text[4:end].splitlines():
        m = re.match(r"([a-z_]+):\s*(.*?)\s*(#.*)?$", line)
        if m:
            fm[m.group(1)] = m.group(2)
    return fm


def check_roles():
    problems = []
    for f in sorted((ROOT / "framework" / "agents").glob("*.md")):
        rel = f.relative_to(ROOT).as_posix()
        fm = frontmatter(f.read_text(encoding="utf-8"))
        if fm is None:
            problems.append(f"{rel}: no YAML frontmatter")
            continue
        for key in REQUIRED:
            if not fm.get(key):
                problems.append(f"{rel}: frontmatter is missing `{key}`")
        if fm.get("name") and fm["name"] != f.stem:
            problems.append(f"{rel}: name `{fm['name']}` does not match the file name")
        tools = {t.strip() for t in fm.get("tools", "").split(",") if t.strip()}
        for t in sorted(tools - NEUTRAL_TOOLS):
            problems.append(f"{rel}: tool `{t}` is not neutral vocabulary")
        if fm.get("memory") not in (None, "", "shared", "none"):
            problems.append(f"{rel}: memory must be `shared` or `none`")
        if f.stem == "reviewer" and fm.get("memory") != "none":
            problems.append(f"{rel}: reviewer must mount no memory (invariant 4)")
        if f.stem == "auditor" and tools & {"write", "edit"}:
            problems.append(f"{rel}: auditor must hold no write tool (invariant 7)")
    return problems


def tla_set(text, name):
    m = re.search(rf"^{name}\s*==\s*(?:<<|\{{)(.*?)(?:>>|\}})", text, re.M | re.S)
    return set(re.findall(r'"([^"]+)"', m.group(1))) if m else None


def table_ids(skill, header, bold):
    """The first-column ids of the table whose header row starts `header`."""
    lines, ids, on = skill.splitlines(), set(), False
    for ln in lines:
        if ln.startswith(header):
            on = True
            continue
        if on:
            if not ln.startswith("|"):
                break
            m = re.match(r"\|\s*\*\*(\w[\w-]*)\*\*" if bold else r"\|\s*`([\w-]+)`", ln)
            if m:
                ids.add(m.group(1))
    return ids


def check_protocol_sets():
    model = (ROOT / "framework/formal/Aidlc.tla").read_text(encoding="utf-8")
    skill = (ROOT / "framework/skills/aidlc/SKILL.md").read_text(encoding="utf-8")
    problems = []
    for name, header, bold in (("batches", "| Batch |", True), ("interrupts", "| Interrupt |", False)):
        tla, rows = tla_set(model, name.capitalize()), table_ids(skill, header, bold)
        if tla is not None and rows != tla:
            problems.append(f"{name}: SKILL.md's `{header}` table and Aidlc.tla differ -- "
                            f"table {sorted(rows)}, model {sorted(tla)}")
    for name in ("stages", "batches", "interrupts"):
        m = re.search(rf"^{name}:\s*(.+)$", skill, re.M)
        prose = set(m.group(1).split()) if m else None
        tla = tla_set(model, name.capitalize())
        if prose is None:
            problems.append(f"SKILL.md: no `{name}:` line in the protocol-sets block")
        elif tla is None:
            problems.append(f"Aidlc.tla: no `{name.capitalize()} ==` definition")
        elif prose != tla:
            problems.append(f"{name}: SKILL.md and Aidlc.tla differ -- only in SKILL.md: "
                            f"{sorted(prose - tla) or '-'}; only in the model: "
                            f"{sorted(tla - prose) or '-'}")
    return problems


def main():
    problems = check_links() + check_roles() + check_protocol_sets()
    for p in problems:
        print(p)
    if problems:
        print(f"\n{len(problems)} problem(s).")
        return 1
    print("repo: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
