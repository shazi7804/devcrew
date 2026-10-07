#!/usr/bin/env python3
"""Fail when host-neutral files name a host's tools or one machine's facts.

    tools/check_neutral.py              scan the neutral paths, exit 1 on a hit
    tools/check_neutral.py PATH...      scan these files/dirs instead
    tools/check_neutral.py --self-test  prove the check fails on a known leak

`framework/`, `ARCHITECTURE.md` and `docs/` are the host-neutral source
(invariant 9). A host's tool names belong only in `hosts/<host>.md`, which maps
the neutral terms (`spawn`, the ledger, the gate primitive, a resource check)
onto them. A specific machine's facts (instance size, cloud service, region,
home directory) belong nowhere in the repo.

Why a script and not a review rule: leaks like "the 128GB EC2 gateway" sat in
the neutral source for five releases. `reviewer` reads diffs, and a line that
already exists is never in a diff, so it was never reviewed. A grep over the
whole tree has no such blind spot.

Naming a host PRODUCT (KiroCrew, Mission Control, Claude Code) is allowed,
because listing the supported hosts is not a dependency on one of them.
"""
import pathlib
import re
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
NEUTRAL = ["framework", "ARCHITECTURE.md", "docs"]
SKIP = {"framework/memory"}  # append-only history; it records what happened
SUFFIXES = {".md", ".py", ".json", ".yml", ".yaml", ".sh", ".js", ".ts",
            ".html", ".toml", ".txt"}

HOST_TOOLS = [
    # KiroCrew
    "spawn_run", "spawn_sub_agents", "session_ledger", "learn_add",
    "cron_add", "cron_trigger", "ask_question", "register_hook",
    "resource_status", "fs_read", "fs_write", "execute_bash", "kiro-cli",
    "Browser panel", "browser-recording", "@kirocrew-",
    "skill://",
    # Claude Code
    "AskUserQuestion", "the Task tool", "settings.local.json", "settings.json",
    "CLAUDE.md", ".claude/", "~/.claude", "hookSpecificOutput",
    "additionalContext", "systemMessage", "suppressOutput", "mcp__",
    # Mission Control
    "decisions.json", "missions.json", "agents.json", "skills-library.json",
    "daemon-config.json", "activity-log.json",
]
MACHINE_FACTS = [
    (r"\bEC2\b", "a cloud instance type"),
    (r"\bSSM\b", "one deployment's ingress"),
    (r"\b\d+ ?(GB|GiB|TB|TiB)\b", "one machine's size"),
    (r"\b(us|eu|ap|sa|ca|me|af)-(north|south|east|west|central|northeast|"
     r"southeast|northwest|southwest)-\d\b", "a cloud region"),
    (r"\b(us|europe|asia|australia|southamerica|northamerica|me|africa)-"
     r"(north|south|east|west|central|northeast|southeast|northwest|"
     r"southwest)\d\b", "a cloud region"),
    (r"\b(eastus|westus|centralus|northeurope|westeurope|southeastasia|"
     r"eastasia|japaneast|uksouth)\d?\b", "a cloud region"),
    (r"/Users/\w|/home/\w|[A-Z]:\\Users\\", "a home directory"),
    (r"~/\.kiro\b", "a host install path"),
    (r"\blocal Mac\b", "one user's workstation"),
]
PATTERNS = [(re.compile(re.escape(t)), f"host tool `{t}`") for t in HOST_TOOLS]
PATTERNS += [(re.compile(p), why) for p, why in MACHINE_FACTS]


def files(paths):
    for p in paths:
        p = pathlib.Path(p)
        if not p.is_absolute():
            p = ROOT / p
        found = sorted(p.rglob("*")) if p.is_dir() else [p]
        for f in found:
            rel = f.relative_to(ROOT).as_posix() if f.is_relative_to(ROOT) else str(f)
            skipped = any(rel == s or rel.startswith(s + "/") for s in SKIP)
            if f.is_file() and f.suffix in SUFFIXES and not skipped \
                    and "__pycache__" not in f.parts:
                yield f, rel


def scan(paths):
    hits = []
    for f, rel in files(paths):
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for rx, why in PATTERNS:
                if rx.search(line):
                    hits.append(f"{rel}:{n}: {why}: {line.strip()[:100]}")
    return hits


def self_test():
    with tempfile.TemporaryDirectory() as d:
        for text in ['Dispatch with spawn_run(agents=["qa"]).',
                     "The gateway runs on the 128GB EC2.",
                     "Add the rule to CLAUDE.md.",
                     "It needs 8GB and runs in asia-east1."]:
            f = pathlib.Path(d, "leak.md")
            f.write_text(text, encoding="utf-8")
            if not scan([f]):
                print(f"self-test FAILED: no hit on {text!r}")
                return 1
        pathlib.Path(d, "leak.md").write_text("Dispatch with `spawn`.\n", encoding="utf-8")
        if scan([pathlib.Path(d, "leak.md")]):
            print("self-test FAILED: a neutral line was flagged")
            return 1
    print("self-test ok")
    return 0


def main(argv):
    if argv[:1] == ["--self-test"]:
        return self_test()
    hits = scan(argv or NEUTRAL)
    for h in hits:
        print(h)
    if hits:
        print(f"\n{len(hits)} host/machine leak(s). Move host names to "
              "hosts/<host>.md and use the neutral term here (invariant 9).")
        return 1
    print("neutral: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
