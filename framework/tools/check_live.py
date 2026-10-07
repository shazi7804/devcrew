#!/usr/bin/env python3
"""Fail the gate when delivered work is verified against fakes, or ships them.

    check_live.py                      both checks on the current repo
    check_live.py --requirements F --only R1,R3
                                       one feature, only these items (a PR's
                                       `Closes` set); the code scan still runs
    check_live.py --rerun [--deployed CMD [--record]]
                                       ...and re-run every probe now; --deployed
                                       proves the environment runs HEAD, and
                                       --record writes the fresh result back
    check_live.py --self-test          prove every rule fails on a known fake
    options: --root DIR  --requirements FILE...  --env NAME  --live-host GLOB...
             --src PATH...  --test GLOB...  --allow FILE  --deployed CMD
             (all of them come from standards.md § Real data & integrations)

Reference implementation of the "no fake data" rule in the aidlc skill.
Host-neutral, stdlib only. Install it into the project as
`<state>/tools/check_live.py`; implementers run it at Phase 3, QA at Phase 4,
devops at Phase 5. A red exit fails the gate before anyone reads for intent.
A gate confirms the project's copy is the framework's by hashing both files
itself (sha256, all 64 hex) -- a copy's own report of its hash proves nothing.

WHY THIS IS A SCRIPT AND NOT A RULE IN THE PROMPT
    A project's CEO said "connect everything for real", and that sentence sat
    in its instructions while every test ran on fakes and two features were
    reported done with nothing behind them. "Has a commit, has an assertion,
    the assertion is green" is true of a fake. A mandate that does not run is
    a wish.

CHECK 1 -- EVIDENCE (every Rn/Nn in each requirements file)
    Each requirement carries a `*Verify*:` line, `live` or `local`. A missing
    line means `live`; there is no level that accepts a fake.
      live   proven against the real, deployed service it depends on
      local  touches no external service or remote data -- proven on the real
             runtime (a device, a simulator, a browser) with real input
    Evidence lives next to its requirements file, one directory per
    environment: `<dir>/evidence/<env>/<ID>.json` (`<dir>/evidence/<ID>.json`
    without --env), written by a READ-ONLY probe after the code is committed:
      {"id": "R3", "verify": "live",
       "command": "curl -fsS -H \"Authorization: Bearer $WEATHER_KEY\" https://api.acme.io/v1/w",
       "target": "https://api.acme.io/v1/w",
       "expect": "\"temp\":\\s*-?\\d+",          a regex the real response matches
       "observed": "{\"temp\": 21, ...}",        an excerpt of that response
       "result": "pass", "sha": "<40-hex commit verified>", "at": "<ISO time>"}
    Red when: no requirement is found; the file is missing, incomplete, not
    JSON, or names another id; result is not pass; `expect` matches anything,
    or `observed` does not match it; a `live` target -- or any URL in its
    command -- has no host, or is loopback / private / link-local (in any
    notation) / a bare service name / a reserved, cluster-internal or
    loopback-DNS domain / a public mock or echo service / a file, or a label
    names a mock -- or, with --live-host, is not a host of the environment
    under test; a target names a mock at any level; the command (outside a
    shell comment) never names the target's host; the sha is not a full commit
    in HEAD's history; the working tree changed outside the evidence and docs
    since the sha (stale -- verify what ships); the evidence holds what looks
    like a secret (credentials come from the environment, never the file).
    With --rerun each probe runs again, with only PATH/HOME/LANG and the
    variables its command names, and must exit 0 and match `expect`; its host
    must resolve, and only to global addresses. A service that answers proves
    the build it runs, not HEAD: --deployed CMD is the environment's version
    probe (one per service; each must ask a live host), and its output must
    contain HEAD's sha. Only then is a passing
    re-run fresh proof -- a stale or rewritten-history sha is not a hit -- and
    only then may --record write it back (sha = HEAD), for an item with no
    other hit. A `local` probe runs on this checkout, not on a deployed
    service, so its re-run is HEAD's proof when the tracked tree is HEAD's
    (no uncommitted change) -- it needs no --deployed.

CHECK 2 -- NO FAKES IN PRODUCTION CODE
    Scans tracked files outside test paths and lockfiles for: an identifier
    word mock / fake / stub / dummy; "lorem ipsum" and the Chinese words for
    fake data and "illustrative only"; a TODO to wire something up; and
    production code that imports from a test path (the classic: "dev uses the
    stubs unless an env var is set"). Comments are scanned on purpose: "// fake
    until the API exists" is exactly the confession this looks for. An
    exemption goes in the allow file, one per line, as
    `<path-glob> <regex> -- <reason>`. A wildcard glob needs a specific regex
    (one that does not match a bare fake word); a broad regex is only accepted
    for one named file. That file is named in standards.md, so changing it
    means re-signing the standards.

IT EXITS NON-ZERO ON ANY HIT
    Unlike boot.py, this is a gate sensor: failing closed is the job.
"""
import argparse
import datetime
import fnmatch
import hashlib
import ipaddress
import json
import os
import pathlib
import re
import socket
import subprocess
import sys
import tempfile
import urllib.parse

STATE = ".aidlc"
FIELDS = ("id", "verify", "command", "target", "expect", "observed", "result",
          "sha", "at")
LEVELS = ("live", "local")
TEST_NAMES = ("test", "tests", "__tests__", "__mocks__", "mocks", "spec", "specs",
              "e2e", "fixtures", "testdata", "test-utils", "testing", "androidTest",
              "stubs", "fakes")
_names = "|".join(re.escape(n) for n in TEST_NAMES)
TEST_DIR = re.compile(rf"(^|/)({_names})(/|$)")
TEST_FILE = re.compile(r"(\.|_)(test|spec|stories)\.\w+$|(^|/)(test_\w+|conftest)\.py$"
                       r"|_test\.go$")
NOT_CODE = re.compile(rf"(^|/)(docs|proposals|{re.escape(STATE)})(/|$)|\.(md|txt|lock)$"
                      r"|-lock\.(json|yaml)$|(^|/)(go\.sum|npm-shrinkwrap\.json)$")
CODE = {".js", ".mjs", ".cjs", ".mts", ".cts", ".jsx", ".ts", ".tsx", ".vue",
        ".svelte", ".astro", ".py", ".rb", ".go", ".rs", ".java", ".kt", ".kts",
        ".scala", ".swift", ".m", ".mm", ".h", ".c", ".cc", ".cpp", ".dart", ".php",
        ".cs", ".ex", ".exs", ".lua", ".sh", ".sql", ".graphql", ".gql", ".html",
        ".xml", ".plist", ".gradle", ".json", ".yml", ".yaml", ".toml", ".ini",
        ".cfg", ".conf", ".properties", ".env"}
ROOTS = ("mock", "fake", "stub", "dummy")
FAKE_WORDS = {"mock", "mocks", "mocked", "mocking", "fake", "fakes", "faked",
              "faking", "stub", "stubs", "stubbed", "stubbing", "dummy", "dummies"}
FAKE_TEXT = [
    (re.compile(r"(?i)lorem ipsum"), "placeholder copy"),
    (re.compile(r"假資料|假数据|示意(?![圖图])"), "fake / illustrative-only data"),
    (re.compile(r"(?i)\b(todo|fixme|xxx)\b.*\b(wire|hook up|connect|real "
                r"(api|data|backend)|backend|api)\b|\bnot wired\b"),
     "a TODO to wire it up"),
    (re.compile(rf"(?i)(import|require|from)\b.*['\"`]([^'\"`]*/)?({_names})(/|['\"`])"),
     "production imports a test path"),
    (re.compile(rf"(?i)^\s*(from\s+\.*|import\s+)([\w]+\.)*({_names})(\.|\s|$)"
                rf"|^\s*from\s+\.+\s+import\s+.*\b({_names})\b"),
     "production imports a test path"),
]
# Reserved, internal, loopback-DNS and public mock/echo domains: never live.
NOT_LIVE_DOMAINS = (
    ".local", ".localhost", ".localdomain", ".internal", ".lan", ".home.arpa",
    ".svc", ".corp", ".intranet", ".test", ".example", ".invalid", ".example.com",
    ".example.org", ".example.net", ".nip.io", ".sslip.io", ".localtest.me",
    ".lvh.me", ".mocky.io", ".mockapi.io", ".beeceptor.com", ".webhook.site",
    ".jsonplaceholder.typicode.com", ".httpbin.org", ".reqres.in",
    ".postman-echo.com", ".requestcatcher.com")
SECRET = re.compile(r"(?i)(-----BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}|"
                    r"\bsk-[A-Za-z0-9_-]{20,}|\bgh[pousr]_[A-Za-z0-9]{30,}|"
                    r"\bxox[abprs]-[A-Za-z0-9-]{10,}|bearer\s+[A-Za-z0-9._~+/-]{20,}|"
                    r"(api[_-]?key|token|secret|password)[\"']?\s*[=:]\s*[\"']?"
                    r"(?!\$)[A-Za-z0-9._~+/-]{12,}|://[^/\s:@$]+:[^/\s@$]+@|"
                    r"\s-u\s*['\"]?[^\s$:'\"]+:[^\s$'\"]+)")
BROAD = ("", "x", "a b", "mock", "fake", "stub", "dummy", "lorem ipsum",
         "TODO wire the api", "假資料", "示意", "const mockTrips = [];", "fakeUser()",
         "stubbedApi", "x = 1;", "import a from 'b'")
URL = re.compile(r"(?i)\b[a-z][\w+.-]*://[^\s'\"`<>]+")


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True)


def out(proc):
    return proc.stdout.decode("utf-8", "replace")


def fields(path):
    """{id: {field: text}} for every Rn/Nn item (bullet, bold line, heading or
    table row) and its `- *Field*: text` lines; a field's text runs on over
    the indented lines below it."""
    found, cur, key = {}, None, None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"\s*(?:[-*+]\s+|#{2,6}\s+)?\*\*([RN]\d+)\b", line) or \
            re.match(r"#{2,6}\s+([RN]\d+)\b", line) or \
            re.match(r"\s*\|\s*\**([RN]\d+)\**\s*\|", line)
        f = re.match(r"(\s*)- \*(\w+)\*:\s*(.*)$", line)
        if m:
            cur, key = m.group(1), None
            found[cur] = {}
        elif line.startswith("#"):
            cur, key = None, None
        elif f and cur:
            key = f.group(2).lower()
            found[cur][key] = (f.group(3).strip(), len(f.group(1)))
        elif key and cur and line.strip() and \
                len(line) - len(line.lstrip()) > found[cur][key][1] and \
                not re.match(r"\s*[-*+]\s", line):
            text, indent = found[cur][key]
            found[cur][key] = (f"{text} {line.strip()}", indent)
        else:
            key = None
    return {i: {k: v[0] for k, v in f.items()} for i, f in found.items()}


def requirements(path):
    """{id: level} for every Rn/Nn item; no Verify line => live."""
    return {i: (re.match(r"`?([\w-]+)", f["verify"]).group(1).lower()
                if re.match(r"`?[\w-]+", f.get("verify", "")) else "live")
            for i, f in fields(path).items()}


def drifted(root, sha, *evidence):
    """Why evidence recorded at `sha` does not prove what ships now, or None:
    'bad' (not a full commit id), 'orphan' (not in HEAD's history), 'stale'
    (the tree changed outside the evidence dirs, the state and docs since)."""
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        return "bad"
    if git(root, "merge-base", "--is-ancestor", sha, "HEAD").returncode:
        return "orphan"
    if git(root, "diff", "--quiet", sha, "--", ".",
           *(f":!{os.path.relpath(e, root)}" for e in evidence), f":!{STATE}",
           ":!*.md").returncode or \
            git(root, "diff", "--quiet", sha, "--", f"{STATE}/tools").returncode:
        return "stale"
    return None


def hostname(target):
    t = target.strip()
    if not re.match(r"^[a-z][\w+.-]*://", t, re.I):
        t = "//" + t
    try:
        h = (urllib.parse.urlsplit(t).hostname or "").rstrip(".").lower()
    except ValueError:
        return ""
    return h if re.fullmatch(r"[a-z0-9._:-]+", h) else ""


FAKE_TOKEN = re.compile(r"(api|apis|server|srv|svc|data|db|backend|host|wire)?"
                        r"(mock|fake|stub|dumm)(s|ed|y|ies)?"
                        r"(api|apis|server|srv|svc|data|db|backend|host)?\d*")


def names_a_fake(text):
    """A word of `text` is a fake (mock, mock-api, wiremock) -- not stubhub."""
    return any(FAKE_TOKEN.fullmatch(w) for w in re.split(r"[^a-z0-9]+", text.lower()))


def address(h):
    """The IP a host literal denotes, in any notation curl accepts, or None."""
    try:
        return ipaddress.ip_address(h)
    except ValueError:
        pass
    if re.fullmatch(r"[0-9a-fx.]+", h) and h[0].isdigit():
        try:
            return ipaddress.ip_address(socket.inet_aton(h))
        except OSError:
            pass
    return None


def resolve(h):
    try:
        return {ipaddress.ip_address(a[4][0].split("%")[0])
                for a in socket.getaddrinfo(h, None)}
    except (OSError, ValueError):
        return set()


def off_net(h):
    """Why `h`, resolved now, is not a live host, or None."""
    addrs = resolve(h)
    if not addrs:
        return f"{h} does not resolve"
    bad = sorted(str(a) for a in addrs if not a.is_global)
    return f"{h} resolves to {', '.join(bad)}" if bad else None


def code(cmd):
    """A shell command without its comments -- a URL in a comment asks nothing."""
    return re.sub(r"(^|[\s;&|()])#.*$", r"\1", cmd, flags=re.M)


def not_live(target, live_hosts):
    """Why `target` is not a live service, or None."""
    if target.strip().lower().startswith("file:"):
        return "a file"
    h = hostname(target)
    if not h:
        return "names no host"
    ip = address(h)
    if ip is not None:
        if not ip.is_global:
            return "a loopback / private / reserved address"
    elif h == "localhost" or "." not in h:
        return "loopback or a bare service name"
    elif any(h == d[1:] or h.endswith(d) for d in NOT_LIVE_DOMAINS):
        return "a reserved, internal, loopback-DNS or public mock domain"
    if names_a_fake(h):
        return "a host that names a mock"
    if live_hosts and not any(fnmatch.fnmatch(h, g.lower()) for g in live_hosts):
        return f"not a host of the environment under test ({', '.join(live_hosts)})"
    return None


def probe(cmd, root):
    keep = {"PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "SYSTEMROOT"}
    keep |= set(re.findall(r"\$\{?([A-Za-z_]\w*)", cmd))
    env = {k: v for k, v in os.environ.items() if k in keep}
    r = subprocess.run(cmd, shell=True, cwd=root, timeout=300, capture_output=True,
                       env=env)
    return r.returncode, (r.stdout + r.stderr).decode("utf-8", "replace")


def check_evidence(root, reqfile, evidence, only, live_hosts, rerun, record, proven):
    req = requirements(reqfile)
    if not req:
        return [f"{reqfile}: no Rn/Nn items -- nothing is verified"]
    if only:
        unknown = sorted(set(only) - set(req))
        if unknown:
            return [f"{reqfile}: --only names {', '.join(unknown)}, not in the requirements"]
        req = {k: v for k, v in req.items() if k in only}
    head = out(git(root, "rev-parse", "HEAD")).strip()
    hits = []
    for rid, level in req.items():
        tag, n0 = f"{os.path.relpath(reqfile, root)} {rid}", len(hits)
        if level not in LEVELS:
            hits.append(f"{tag}: Verify `{level}` is not a level ({' | '.join(LEVELS)})")
            continue
        f = evidence / f"{rid}.json"
        if not f.is_file():
            hits.append(f"{tag}: no evidence ({os.path.relpath(f, root)}) -- unverified")
            continue
        raw = f.read_text(encoding="utf-8", errors="replace")
        try:
            e = json.loads(raw)
            assert isinstance(e, dict)
        except (ValueError, AssertionError):
            hits.append(f"{tag}: evidence is not a JSON object")
            continue
        missing = [k for k in FIELDS if e.get(k) is None or not str(e[k]).strip()]
        if missing:
            hits.append(f"{tag}: evidence lacks {', '.join(missing)}")
            continue
        e = {k: str(e[k]) for k in FIELDS}
        if SECRET.search(raw):
            hits.append(f"{tag}: evidence holds what looks like a secret -- take "
                        "credentials from the environment ($VAR), redact the excerpt")
        if e["id"] != rid:
            hits.append(f"{tag}: evidence file says id {e['id']!r}")
        if e["result"] != "pass":
            hits.append(f"{tag}: probe result is {e['result']!r}")
        if e["verify"] not in LEVELS:
            hits.append(f"{tag}: evidence level {e['verify']!r} is not a level")
        elif level == "live" and e["verify"] != "live":
            hits.append(f"{tag}: requires live, evidence is {e['verify']!r}")
        try:
            expect = re.compile(e["expect"])
        except re.error as err:
            hits.append(f"{tag}: expect is not a regex ({err})")
            expect = None
        if expect and expect.search(""):
            hits.append(f"{tag}: expect matches anything -- it proves nothing")
            expect = None
        if expect and not expect.search(e["observed"]):
            hits.append(f"{tag}: observed does not match expect")
        h = hostname(e["target"])
        cmd = code(e["command"])
        live = level == "live" or e["verify"] == "live"
        if live:
            for t in dict.fromkeys([e["target"]] + URL.findall(cmd)):
                why = not_live(t, live_hosts)
                if why:
                    hits.append(f"{tag}: {t!r} is not a live service: {why}")
        elif names_a_fake(e["target"]):
            hits.append(f"{tag}: target {e['target']!r} names a mock")
        if h and h not in cmd.lower():
            hits.append(f"{tag}: the probe command never names {h}")
        sha = e["sha"].lower()
        why = drifted(root, sha, evidence, reqfile.parent / "formal")
        if why == "bad":
            hits.append(f"{tag}: sha {sha!r} is not a full commit id")
        stale, orphan = why == "stale", why == "orphan"
        fresh, excerpt = False, None
        if rerun and expect:
            hosts = [h] + [hostname(t) for t in URL.findall(cmd)] if live else []
            bad = "; ".join(w for x in dict.fromkeys(hosts) if x and (w := off_net(x)))
            if bad:
                hits.append(f"{tag}: {bad} -- not live")
            try:
                rc, text = probe(e["command"], root)
                if rc:
                    hits.append(f"{tag}: re-run exited {rc}: {text.strip()[:120]}")
                elif not (m := expect.search(text)):
                    hits.append(f"{tag}: re-run output does not match expect")
                elif not bad:
                    # The service answered -- it is HEAD's proof only if the
                    # environment is proven to run HEAD (--deployed). A local
                    # probe ran on this checkout: proof if it is HEAD's tree.
                    fresh = proven or (not live and not git(
                        root, "diff", "--quiet", "HEAD", "--").returncode)
                    excerpt = text[max(0, m.start() - 80):m.end() + 80].strip()
            except subprocess.TimeoutExpired:
                hits.append(f"{tag}: re-run timed out after 300s")
        if (stale or orphan) and not fresh:
            why = (f"sha {sha[:12]} is not in HEAD's history" if orphan else
                   f"stale -- code changed since {sha[:12]}")
            hint = ("; the re-run passed, but nothing proves the environment runs HEAD "
                    "(--deployed)" if excerpt and not proven else "; re-run the probe")
            hits.append(f"{tag}: {why}{hint}")
        if record and fresh and len(hits) == n0 and not SECRET.search(excerpt):
            now = datetime.datetime.now(datetime.timezone.utc)
            f.write_text(json.dumps({**e, "observed": excerpt, "sha": head,
                                     "at": now.isoformat(timespec="seconds"),
                                     "result": "pass"}, indent=2,
                                    ensure_ascii=False) + "\n", encoding="utf-8")
    return hits


def allowed(allow):
    rules = []
    if not allow:
        return rules
    try:
        text = allow.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        raise SystemExit(f"--allow {allow}: {err}")
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"(\S+)\s+(.+?)\s+--\s+(\S.*)$", line)
        if not m:
            raise SystemExit(f"{allow}:{n}: want `<path-glob> <regex> -- <reason>`")
        glob = m.group(1)
        try:
            rx = re.compile(m.group(2))
        except re.error as err:
            raise SystemExit(f"{allow}:{n}: not a regex ({err})")
        wild = any(c in glob for c in "*?[")
        if rx.search("") or not glob.strip("*?[]/!") or \
                (wild and any(rx.search(t) for t in BROAD)):
            raise SystemExit(f"{allow}:{n}: an exemption names one path and one "
                             "pattern; it cannot exempt everything")
        rules.append((glob, rx))
    return rules


def check_code(root, src, tests, rules):
    ls = git(root, "ls-files", "-z", "--", *(src or ["."]))
    if ls.returncode:
        return [f"not a git repo: {root}"]
    hits = []
    for rel in out(ls).split("\0"):
        p = root / rel
        is_code = p.suffix in CODE or p.name.startswith(".env")
        if not rel or not is_code or TEST_DIR.search(rel) or TEST_FILE.search(rel) \
                or NOT_CODE.search(rel) or any(fnmatch.fnmatch(rel, g) for g in tests) \
                or not p.is_file():
            continue
        data = p.read_bytes()
        if b"\0" in data[:8192]:
            continue
        for n, line in enumerate(data.decode("utf-8", "replace").splitlines(), 1):
            toks = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", line)
            words = {t.lower() for t in toks}
            why = [f"`{w}`" for w in sorted(words & FAKE_WORDS)]
            why += [f"`{t}`" for t in toks if t.isupper() and len(t) > 4
                    and t.lower().startswith(ROOTS) and t.lower() not in FAKE_WORDS]
            why += [w for rx, w in FAKE_TEXT if rx.search(line)]
            if why and not any(fnmatch.fnmatch(rel, g) and rx.search(line)
                               for g, rx in rules):
                hits.append(f"{rel}:{n}: {', '.join(dict.fromkeys(why))}: {line.strip()[:90]}")
    return hits


def default_requirements(root):
    found = [root / STATE / "requirements.md"]
    found += sorted((root / STATE / "features").glob("*/requirements.md"))
    return [p for p in found if p.is_file()]


def run(root, reqfiles=None, evidence=None, only=None, env=None, live_hosts=(),
        src=None, tests=(), allow=None, rerun=False, record=False, deployed=None):
    reqfiles = reqfiles or default_requirements(root)
    if (only or evidence) and len(reqfiles) != 1:
        raise SystemExit("--only / --evidence apply to one feature: pass "
                         "--requirements <its requirements.md>")
    if record and not deployed:
        raise SystemExit("--record stamps HEAD: pass --deployed <the probe that prints "
                         "the build the environment runs>")
    hits = [] if reqfiles else [f"no requirements file under {root / STATE} -- nothing is verified"]
    proven = False
    if rerun and deployed:
        # One version probe per service; each must ask a live host and print HEAD.
        head, n0 = out(git(root, "rev-parse", "HEAD")).strip(), len(hits)
        for cmd in deployed:
            urls = list(dict.fromkeys(URL.findall(code(cmd))))
            if not urls:
                hits.append(f"--deployed {cmd!r} asks no service -- it proves nothing")
                continue
            why = [f"{t!r}: {w}" for t in urls if (w := not_live(t, live_hosts))]
            why += [w for t in urls if (h := hostname(t)) and (w := off_net(h))]
            if why:
                hits.append(f"--deployed {cmd!r} is not a live service: {'; '.join(why)}")
                continue
            try:
                rc, text = probe(cmd, root)
            except subprocess.TimeoutExpired:
                rc, text = 1, "timed out after 300s"
            if rc or head[:12] not in text.lower():
                hits.append(f"--deployed {cmd!r}: the environment does not run HEAD "
                            f"{head[:12]} ({text.strip()[:80]!r}) -- deploy it, then re-run")
        proven = len(hits) == n0
    for rf in reqfiles:
        if not rf.is_file():
            hits.append(f"no requirements file at {rf} -- nothing is verified")
            continue
        ev = evidence or rf.parent / "evidence"
        hits += check_evidence(root, rf, ev / env if env else ev, only, live_hosts,
                               rerun, record, proven)
    return hits + check_code(root, src, tests, allowed(allow))


def self_test():
    global resolve
    # The self-test runs offline: every host resolves to a public address but
    # the ones named "nowhere".
    resolve = lambda h: set() if "nowhere" in h else {ipaddress.ip_address("8.8.8.8")}  # noqa: E731
    quiet = ["-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
             "-c", "core.hooksPath=/dev/null"]

    def write(d, files):
        for rel, text in files.items():
            p = pathlib.Path(d, rel)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")

    def commit(d, files):
        write(d, files)
        git(d, "init", "-q")
        git(d, "add", "-A")
        git(d, *quiet, "commit", "-qm", "x")
        return out(git(d, "rev-parse", "HEAD")).strip()

    def ev(d, head, rid="R1", where=f"{STATE}/evidence", **kw):
        e = {"id": rid, "verify": "live", "target": "https://api.prod.acme.io/v1/weather",
             "command": "curl -fsS https://api.prod.acme.io/v1/weather",
             "expect": r'"temp":\s*-?\d+', "observed": '{"temp": 21}',
             "result": "pass", "sha": head, "at": "2026-10-06T00:00:00Z", **kw}
        write(d, {f"{where}/{rid}.json": json.dumps(e)})

    def check(label, got, want):
        if (not got) if want is None else any(want in h for h in got):
            return True
        print(f"self-test FAILED: {label}: expected "
              f"{'clean' if want is None else repr(want)}, got {got or 'clean'}")
        return False

    def attempt(root, **kw):
        try:
            return run(root, **kw)
        except SystemExit as err:
            return [str(err)]

    req = f"{STATE}/requirements.md"
    base = {req: "## Functional\n- **R1** — WHEN asked, SHALL show weather.\n"
                 "  - *Acceptance*: x\n",
            "src/app.js": "export const temp = await api.get('/v1/weather');\n",
            "tests/app.test.js": "const fakeApi = mockFetch();\n"}
    local_ok = {"verify": "local", "target": "iPhone 15 simulator, iOS 18",
                "command": "xcrun simctl launch booted com.acme.app"}
    T = "https://api.prod.acme.io/v1"

    def at(url):
        return {"target": url, "command": f"curl {url}"}

    def allow(line):
        return {"allow.txt": line + "\n"}
    # (case, extra files, evidence override | "skip", kwargs to run, expected reason)
    cases = [
        ("clean", {}, None, {}, None),
        ("clean local", {req: "- **R1** — x\n  - *Verify*: local\n"}, local_ok, {}, None),
        ("a bolded title", {req: "- **R1 — Weather.** SHALL show it.\n"}, None, {}, None),
        ("a heading item", {req: "## R1 —— weather\nSHALL show it.\n"}, None, {}, None),
        ("a table row", {req: "| ID | Need |\n|---|---|\n| **R1** | weather |\n"}, None,
         {}, None),
        ("no fake word in downsample", {"src/img.js": "downsample(url)\n"}, None, {}, None),
        ("an illustrative diagram", {"src/a.js": "alt = '架構示意圖'\n"}, None, {}, None),
        ("a host that contains a root mid-word", {}, at("https://api.stubhub.com/x"),
         {}, None),
        ("a host that ends in a root", {}, at("https://www.hammock.com/x"), {}, None),
        ("a lockfile", {"package-lock.json": '{"jest-mock": "29"}\n'}, None, {}, None),
        ("a story", {"src/Button.stories.tsx": "args: mockArgs\n"}, None, {}, None),
        ("allowed exemption", {"src/rpc.js": "new WeatherStub(channel)\n",
         **allow("src/*.js WeatherStub -- the gRPC client class")}, None,
         {"allow": "allow.txt"}, None),
        ("a whole named file", {"src/rpc.js": "new WeatherStub(channel)\n",
         **allow("src/rpc.js (?i)stub -- generated gRPC client")}, None,
         {"allow": "allow.txt"}, None),
        ("a Verify line under another heading", {req: base[req] +
         "## Notes\n- *Verify*: bogus\n"}, None, {}, None),
        ("a binary file", {}, None, {}, None),
        ("an exemption for everything", allow("* .* -- all of it"), None,
         {"allow": "allow.txt"}, "cannot exempt everything"),
        ("an exemption for any path", allow("?* . -- all of it"), None,
         {"allow": "allow.txt"}, "cannot exempt everything"),
        ("a broad exemption for a tree", allow("src/** (?i)stub -- all stubs"), None,
         {"allow": "allow.txt"}, "cannot exempt everything"),
        ("a compound-word exemption", allow(r"src/** (?i)stub\w+ -- stubs"), None,
         {"allow": "allow.txt"}, "cannot exempt everything"),
        ("a punctuation exemption", allow("src/** [=(;] -- code"), None,
         {"allow": "allow.txt"}, "cannot exempt everything"),
        ("an exemption that is not a regex", allow("src/a.js ([ -- x"), None,
         {"allow": "allow.txt"}, "not a regex"),
        ("go imports testdata", {"srv/main.go": 'import "acme.io/app/testdata/trips"\n'},
         None, {}, "imports a test path"),
        ("js imports a fixtures index", {"src/t.js": 'import trips from "../fixtures"\n'},
         None, {}, "imports a test path"),
        ("python relative import", {"app/s.py": "from .fixtures import trips\n"},
         None, {}, "imports a test path"),
        ("no requirements", {req: "# nothing here\n"}, None, {}, "nothing is verified"),
        ("no evidence", {}, "skip", {}, "no evidence"),
        ("loopback", {}, at("http://localhost:3000"), {}, "loopback"),
        ("no scheme, user@", {}, at("u@localhost/x"), {}, "loopback"),
        ("decimal loopback", {}, at("http://2130706433/"), {}, "loopback / private"),
        ("shorthand loopback", {}, at("http://127.1/"), {}, "loopback / private"),
        ("hex loopback", {}, at("http://0x7f.0.0.1/"), {}, "loopback / private"),
        ("mapped loopback", {}, at("http://[::ffff:127.0.0.1]/"), {}, "loopback / private"),
        ("link-local", {}, at("http://169.254.169.254/"), {}, "loopback / private"),
        ("bare service name", {}, at("http://api:8080/"), {}, "bare service name"),
        ("docker host", {}, at("http://host.docker.internal/"), {}, "reserved"),
        ("cluster name", {}, at("http://api.default.svc/"), {}, "reserved"),
        ("loopback DNS", {}, at("http://127.0.0.1.nip.io/"), {}, "loopback-DNS"),
        ("a public mock service", {}, at("https://run.mocky.io/v3/x"), {}, "public mock"),
        ("a label prefixed with a root", {}, at("https://wiremock.acme.io/x"), {},
         "names a mock"),
        ("query string", {}, at("http://localhost/?x=a.example.com"), {}, "loopback"),
        ("no host", {}, {"target": "the API"}, {}, "names no host"),
        ("mock target", {}, at("https://mock.acme.io"), {}, "names a mock"),
        ("a mock-api label", {}, at("https://mock-api.acme.io/x"), {}, "names a mock"),
        ("mock target at local", {req: "- **R1** — x\n  - *Verify*: local\n"},
         {**local_ok, "target": "fake device farm"}, {}, "names a mock"),
        ("not the env under test", {}, None, {"live_hosts": ["*.staging.acme.io"]},
         "environment under test"),
        ("command in a comment", {}, {"command": "echo ok # curl https://api.prod.acme.io"},
         {}, "never names"),
        ("command after ;#", {}, {"command": "echo ok;# curl https://api.prod.acme.io"},
         {}, "never names"),
        ("a probe that reaches another host", {}, {"command":
         "curl -H Host:api.prod.acme.io http://localhost:3000/v1/weather"}, {},
         "'http://localhost:3000/v1/weather' is not a live service"),
        ("probe failed", {}, {"result": "fail"}, {}, "probe result"),
        ("observed is not the expected", {}, {"observed": "<html>coming soon"}, {},
         "does not match expect"),
        ("expect matches anything", {}, {"expect": ".*"}, {}, "matches anything"),
        ("local where live is required", {}, {**local_ok}, {}, "requires live"),
        ("wrong id", {}, {"id": "R2"}, {}, "says id"),
        ("short sha", {}, {"sha": "HEAD"}, {}, "not a full commit"),
        ("a sha outside HEAD's history", {}, {"sha": "0" * 40}, {}, "not in HEAD's"),
        ("missing field", {}, {"expect": ""}, {}, "lacks expect"),
        ("a null field", {}, {"observed": None}, {}, "lacks observed"),
        ("a secret", {}, {"command": f"curl -H 'Authorization: Bearer {'a1' * 16}' {T}"},
         {}, "secret"),
        ("a password in the URL", {}, {"command":
         "curl https://u:hunter2pass@api.prod.acme.io/v1/weather"}, {}, "secret"),
        ("--only unknown", {}, None, {"only": ["R9"]}, "not in the requirements"),
        ("fake in production", {"src/data.js": "const mockTrips = [];\n"}, None, {}, "`mock`"),
        ("all-caps fake", {"src/k.js": "const FAKEAPI = 1;\n"}, None, {}, "`FAKEAPI`"),
        ("prod imports a stub", {"src/srv.js": "import('../tests/stubs.mjs')\n"}, None, {},
         "imports a test path"),
        ("python imports a fixture", {"app/srv.py": "from app.fixtures import trips\n"},
         None, {}, "imports a test path"),
        ("illustrative data", {"src/home.js": "label = '示意'\n"}, None, {}, "illustrative"),
        ("lorem", {"src/c.html": "<p>Lorem ipsum</p>\n"}, None, {}, "placeholder"),
        ("todo wire", {"src/w.ts": "// TODO wire to backend\n"}, None, {}, "wire it up"),
        ("a sql seed", {"db/seed.sql": "insert into t values ('dummy');\n"}, None, {},
         "`dummy`"),
        ("non-ascii path", {"src/首頁.js": "const fake = 1;\n"}, None, {}, "`fake`"),
        ("non-utf8 file", {}, None, {}, "`stub`"),
    ]
    for name, extra, override, kw, want in cases:
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "src").mkdir()
            if name == "non-utf8 file":
                (root / "src/l1.js").write_bytes("const stub = 'caf\xe9';\n".encode("latin-1"))
            if name == "a binary file":
                (root / "src/blob.json").write_bytes(b"\x00\x01 fake mock stub")
            sha = commit(d, {**base, **extra})
            if override != "skip":
                ev(d, sha, **(override or {}))
            if "allow" in kw:
                kw = {**kw, "allow": root / kw["allow"]}
            if not check(name, attempt(root, **kw), want):
                return 1
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        sha = commit(d, base)
        ev(d, sha)
        (root / "src/app.js").write_text("export const temp = 1;\n", encoding="utf-8")
        if not check("evidence older than the working tree", run(root), "stale"):
            return 1
        ev(d, sha, command="echo https://nowhere.acme.io/x https://api.prod.acme.io/v1/weather")
        if not check("a probe URL that does not resolve", run(root, rerun=True),
                     "nowhere.acme.io does not resolve"):
            return 1
        ev(d, sha, command="echo https://api.prod.acme.io/v1/weather")
        if not check("a re-run that never reached the service", run(root, rerun=True),
                     "re-run output does not match"):
            return 1
    # A local item: a re-run on a clean checkout of HEAD refreshes it; on a
    # dirty tree it does not (the probe ran on code nobody committed).
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        lreq = {req: "- **R1** — x\n  - *Verify*: local\n"}
        sha = commit(d, {**base, **lreq})
        ev(d, sha, verify="local", target="this checkout", command="echo 'temp: 21'",
           expect=r"temp: \d+", observed="temp: 21")
        write(d, {"src/app.js": "export const temp = 2;\n"})
        git(d, "add", "-A")
        git(d, *quiet, "commit", "-qm", "y")
        if not check("a local re-run on a clean HEAD", run(root, rerun=True), None):
            return 1
        write(d, {"src/app.js": "export const temp = 3;\n"})
        if not check("a local re-run on a dirty tree", run(root, rerun=True), "stale"):
            return 1
    # Two features: one PR's run, staleness after another feature lands, a
    # re-run that refreshes it, and environments that do not overwrite each other.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        fa, fb = f"{STATE}/features/a", f"{STATE}/features/b"
        offline = "echo https://api.prod.acme.io/v1/weather '\"temp\": 21'"
        # Stands in for `curl https://api.prod.acme.io/version`.
        on_head = {"deployed": ["echo https://api.prod.acme.io/version $(git rev-parse HEAD)"]}
        sha = commit(d, {f"{fa}/requirements.md": base[req], "src/a.js": "a()\n"})
        ev(d, sha, where=f"{fa}/evidence/pre", command=offline)
        write(d, {f"{fb}/requirements.md": base[req], "src/b.js": "b()\n"})
        git(d, "add", "-A")
        git(d, *quiet, "commit", "-qm", "b")
        sha2 = out(git(d, "rev-parse", "HEAD")).strip()
        ev(d, sha2, where=f"{fb}/evidence/pre", command=offline)
        steps = [
            ("one feature's PR", {"reqfiles": [root / fb / "requirements.md"],
                                  "only": ["R1"], "env": "pre"}, None),
            ("--only across features", {"only": ["R1"]}, "apply to one feature"),
            ("a feature stale after another lands", {"env": "pre"}, "stale"),
            ("a re-run without --deployed is no proof of HEAD",
             {"env": "pre", "rerun": True}, "nothing proves the environment runs HEAD"),
            ("an environment that does not run HEAD",
             {"env": "pre", "rerun": True,
              "deployed": ["echo https://api.prod.acme.io/version 0123456789ab"]},
             "does not run HEAD"),
            ("a version probe that asks no service",
             {"env": "pre", "rerun": True, "deployed": ["git rev-parse HEAD"]},
             "asks no service"),
            ("a version probe that names its URL in a comment", {"env": "pre", "rerun": True,
             "deployed": ["git rev-parse HEAD # https://api.prod.acme.io/version"]},
             "asks no service"),
            ("a version probe whose host does not resolve", {"env": "pre", "rerun": True,
             "deployed": ["echo https://nowhere.prod.acme.io/version $(git rev-parse HEAD)"]},
             "does not resolve"),
            ("a version probe on loopback", {"env": "pre", "rerun": True, "deployed":
             ["echo http://localhost/version $(git rev-parse HEAD)"]}, "not a live service"),
            ("one service of two not on HEAD", {"env": "pre", "rerun": True, "deployed":
             on_head["deployed"] + ["echo https://web.prod.acme.io/version 0123456789ab"]},
             "nothing proves the environment runs HEAD"),
            ("--record without --deployed", {"env": "pre", "rerun": True, "record": True},
             "--record stamps HEAD"),
            ("a re-run on HEAD is fresh proof", {"env": "pre", "rerun": True, **on_head},
             None),
            ("--record refreshes the sha",
             {"env": "pre", "rerun": True, "record": True, **on_head}, None),
            ("recorded evidence is current", {"env": "pre"}, None),
            ("production keeps its own evidence", {"env": "prod"}, "no evidence"),
        ]
        for label, kw, want in steps:
            if not check(label, attempt(root, **kw), want):
                return 1
        ev(d, "0" * 40, where=f"{fa}/evidence/pre", command=offline)
        if not check("a squashed history, re-run on HEAD",
                     attempt(root, env="pre", rerun=True, **on_head), None):
            return 1
    print(f"self-test ok ({len(cases) + 21} cases)")
    return 0


def main(argv):
    if "--self-test" in argv:
        return self_test()
    ap = argparse.ArgumentParser(description="no fake data: evidence + code scan")
    ap.add_argument("--root", default=".")
    ap.add_argument("--requirements", nargs="+")
    ap.add_argument("--evidence")
    ap.add_argument("--env")
    ap.add_argument("--only", type=lambda s: [x.strip() for x in s.split(",") if x.strip()])
    ap.add_argument("--live-host", nargs="+", default=[])
    ap.add_argument("--src", nargs="+")
    ap.add_argument("--test", nargs="+", default=[])
    ap.add_argument("--allow")
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--deployed", action="append")
    a = ap.parse_args(argv)
    if (a.record or a.deployed) and not a.rerun:
        ap.error("--record / --deployed go with a re-run: pass --rerun")
    root = pathlib.Path(a.root).resolve()
    print("check_live.py sha256", hashlib.sha256(pathlib.Path(__file__).read_bytes())
          .hexdigest())
    hits = run(root, [root / r for r in a.requirements or []] or None,
               root / a.evidence if a.evidence else None, a.only, a.env, a.live_host,
               a.src, a.test, root / a.allow if a.allow else None, a.rerun, a.record,
               a.deployed)
    for h in hits:
        print(h)
    if hits:
        print(f"\n{len(hits)} hit(s). Nothing is done until it runs on the real "
              "thing: wire it, probe it, record the evidence.")
        return 1
    print("live: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
