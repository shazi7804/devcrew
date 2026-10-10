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
    in HEAD's history; the tree changed since the sha outside the evidence,
    the feature's own contract dir and TASKS.md -- a prompt or a doc is
    code here (stale -- verify what ships); the evidence holds what looks
    like a secret (credentials come from the environment, never the file).
    With --rerun each probe runs again, with only PATH/HOME/LANG and the
    variables its command names, and must exit 0 and match `expect`; its host
    must resolve, and only to global addresses. A service that answers proves
    the build it runs, not HEAD: --deployed CMD is the environment's version
    probe (one per service; each must ask a live host), and its output must
    contain HEAD's sha. Only then is a passing
    re-run fresh proof -- a stale or rewritten-history sha is not a hit -- and
    only then may --record write it back (sha = HEAD), for an item with no
    other hit. Every re-run runs in a throwaway checkout of HEAD, reset
    before each probe, and with --rerun the code scan below reads it too, so
    no uncommitted, untracked or ignored file can take part; a `local`
    probe touches no service, so its re-run there is HEAD's proof -- it
    needs no --deployed.

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
import posixpath
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import unicodedata
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


def git_env(**extra):
    """The environment for the sensors' own git calls: none of the caller's
    GIT_* variables -- run from a hook, GIT_DIR or GIT_INDEX_FILE would point
    them at the user's repository and index."""
    return {**{k: v for k, v in os.environ.items() if not k.startswith("GIT_")}, **extra}


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, env=git_env())


def at_head(root, *paths):
    """Why one of these files is not HEAD's, byte for byte, or None. A re-run
    reads the contract and the ledger from the working tree, so each must be
    the committed file -- not an ignored or untracked stand-in HEAD lacks."""
    for p in paths:
        rel = rel_to(root, p)
        r = subprocess.run(["git", "-C", str(root), "--no-replace-objects", "cat-file", "blob",
                            f"HEAD:{rel}"], capture_output=True, env=git_env())
        try:
            here = pathlib.Path(p).read_bytes()
        except OSError:
            here = None
        if r.returncode or here != r.stdout:
            return (f"a re-run judges HEAD: {rel} is not HEAD's -- commit it "
                    "(it is missing from HEAD or differs from it)")
    return None


def unclean(root):
    """Why a re-run cannot start here, or None. A re-run judges HEAD, so the
    working tree must be HEAD: with an uncommitted or untracked file, what it
    holds (a requirements file, an evidence record, a signed hash, a helper)
    could decide the verdict. Ignored files are the environment, not the tree."""
    # status without anything that lets git skip looking: no fsmonitor, no
    # ignoreStat, no untracked cache; and an index flag that hides an edit
    # from status (skip-worktree, assume-unchanged) is itself unclean
    st = git(root, "-c", "core.fsmonitor=false", "-c", "core.ignoreStat=false",
             "-c", "core.untrackedCache=false", "status", "--porcelain",
             "--untracked-files=all", "--ignore-submodules=none")
    ls = git(root, "ls-files", "-v")
    if st.returncode or ls.returncode:
        return f"not a git repository: {root}"
    # the repository's own attributes file: ignored, highest precedence, and
    # able to change how a file reads after it was checked out
    info = git(root, "rev-parse", "--git-path", "info/attributes")
    attrs = pathlib.Path(root) / out(info).strip() if not info.returncode else None
    if attrs and attrs.is_file() and attrs.read_text(errors="replace").strip():
        return (f"a re-run judges HEAD: {os.path.relpath(attrs, root)} would change how "
                "it reads files -- move it into a committed .gitattributes, or remove it")
    # bytecode Python writes beside a tracked module is regenerated from it and
    # never imported without it: the environment, not a file of the tree
    dirty = [ln[3:] for ln in out(st).splitlines()
             if ln.strip() and "__pycache__/" not in ln[3:] and not ln.endswith(".pyc")]
    dirty += [f"{ln[2:]} (flagged {ln[0]!r} in the index)" for ln in out(ls).splitlines()
              if ln and not ln.startswith("H ")]
    if dirty:
        more = f" (+{len(dirty) - 3} more)" if len(dirty) > 3 else ""
        return (f"a re-run judges HEAD: commit or stash {', '.join(dirty[:3])}{more} first "
                "-- the working tree must be HEAD")
    return None


def out(proc):
    return proc.stdout.decode("utf-8", "replace")


def fields(path):
    """{id: {field: text}} for every Rn/Nn item (bullet, bold line, heading or
    table row) and its `- *Field*: text` lines; a field's text runs on over
    the indented lines below it."""
    found, cur, key = {}, None, None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        # an item, not a mention: the id is followed by its closing `**`, a
        # space or a dash -- "**R12's note**" in prose is not R12
        m = re.match(r"\s*(?:[-*+]\s+|#{2,6}\s+)?\*\*([RN]\d+)(?=\*\*|\s|[—–.:-])", line) or \
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


# git with nothing a probe can plant in the repo's config taking part: no
# hook, no sparse checkout, no fsmonitor, no replace object.
QUIET_GIT = ("-c", "core.hooksPath=/dev/null", "-c", "core.sparseCheckout=false",
             "-c", "core.fsmonitor=false", "--no-replace-objects")


class HeadTree:
    """HEAD, pinned at first use, one per invocation. Two ways to read it:

    - files(): HEAD's blobs straight from the object store, read once before
      any command runs (a probe, --deployed) and never after -- what a scan
      reads, so no checkout state, hook, filter, attribute or rewritten
      object a probe leaves can change what it sees; ls() reads --src as
      git does, over HEAD;
    - get(): a throwaway checkout (a shared clone: refs, stash, config and
      hooks of its own, objects borrowed read-only) to run a probe in,
      reset every time it is handed out -- the commit is pinned, the index,
      sparse patterns and worktree config are dropped, `clean -ffdx` removes
      untracked, ignored and nested repositories, whatever a probe put beside
      the checkout goes, and no hook runs.

    What no reset undoes: a probe runs with the user's shell, so a process it
    detaches from its own group (setsid, a daemon) outlives the group kill and
    is the probe's to stop; and it can write outside the checkout (an absolute
    path, $HOME, the repository it was cloned from, by path) -- what a later
    probe runs can differ, though what the scan reads was read before the
    first probe. The sensor cannot sandbox a command; a reviewer reads the
    probe commands in the diff."""
    def want_dir(self, d):
        """Read every file under `d` (an evidence dir) up front as well."""
        if self.blobs is not None:
            raise SystemExit("HeadTree: a directory named after HEAD was read")
        if (name := canon(rel_to(self.root, d))):
            self.dirs.add(name)

    def __init__(self, root, want=()):
        self.root, self.path, self.tmp, self.sha, self.blobs = root, None, None, None, None
        self.index = None
        self.want = {canon(w) for w in want} - {None}  # read beyond the code
        self.dirs, self.gitdir, self.gitlinks = set(), None, []

    def head(self):
        if self.sha is None:
            self.sha = out(git(self.root, "rev-parse", "HEAD")).strip()
            if not re.fullmatch(r"[0-9a-f]{40}", self.sha):
                raise SystemExit(f"cannot read HEAD of {self.root}")
        return self.sha

    def _filtered(self, names):
        """The names a clean/smudge filter applies to at the pinned commit (an
        LFS file is a pointer in its blob and its content on disk)."""
        r = subprocess.run(["git", "-C", str(self.root), *QUIET_GIT, "check-attr", "-z",
                            "--stdin", f"--source={self.head()}", "filter"],
                           input="\0".join(names).encode("utf-8", "surrogateescape"),
                           capture_output=True, env=git_env())
        if r.returncode:
            raise SystemExit(f"cannot read HEAD's attributes in {self.root}")
        f = r.stdout.decode("utf-8", "surrogateescape").split("\0")
        return {f[i] for i in range(0, len(f) - 2, 3) if f[i + 2] not in ("unspecified", "unset")}

    def _cat(self, oids):
        """[bytes] of these objects, streamed one at a time (no replace object);
        a missing one is a message, not a traceback."""
        with tempfile.TemporaryFile() as ids:
            ids.write("".join(f"{o}\n" for o in oids).encode())
            ids.seek(0)
            cat = subprocess.Popen(["git", "-C", str(self.root), *QUIET_GIT, "cat-file",
                                    "--batch"], stdin=ids, stdout=subprocess.PIPE,
                                   env=git_env())
            got = []
            for _ in oids:
                head = cat.stdout.readline().split()
                if len(head) != 3:
                    cat.kill()
                    raise SystemExit(f"cannot read HEAD's objects in {self.root} -- "
                                     "the repository is incomplete")
                got.append(cat.stdout.read(int(head[2]) + 1)[:-1])
            cat.wait()
        return got

    def files(self):
        """{path: bytes} at the pinned commit: what a check reads -- the code
        (CODE suffixes, .env*), each symlink as the file it resolves to in
        HEAD's tree, component by component as the kernel does (what runs is
        the target), and the files named in `want`. A symlink that does not
        resolve to a file of HEAD's tree -- out of it, absolute, a loop, a
        case the tree does not have -- maps to None: the scan reports it
        rather than skip what it cannot read. Read before the first probe,
        and only that, so no probe can rewrite an object under the scan and a
        large tree costs only its code."""
        if self.blobs is None:
            ls = git(self.root, *QUIET_GIT, "ls-tree", "-r", "-z", "--full-tree", self.head())
            if ls.returncode:
                raise SystemExit(f"cannot read HEAD's tree in {self.root}")
            # the index --src is read against, built now, before any command
            self.index = tempfile.mkdtemp()
            if subprocess.run(["git", "-C", str(self.root), *QUIET_GIT, "read-tree", self.head()],
                              env=git_env(GIT_INDEX_FILE=self.index + "/index"),
                              capture_output=True).returncode:
                raise SystemExit(f"cannot read HEAD's tree in {self.root}")
            names = ls.stdout.decode("utf-8", "surrogateescape")
            ents = {rel: (meta.split()[0], meta.split()[2]) for meta, rel in
                    (e.split("\t", 1) for e in names.split("\0") if "\t" in e)
                    if meta.split()[0] in ("100644", "100755", "120000")}
            self.gitlinks = [rel for meta, rel in
                             (e.split("\t", 1) for e in names.split("\0") if "\t" in e)
                             if meta.split()[0] == "160000"]
            links = [r for r, (m, _) in ents.items() if m == "120000"]
            dest = dict(zip(links, (b.decode("utf-8", "surrogateescape")
                                    for b in self._cat([ents[r][1] for r in links]))))

            # every name a path passes -- each directory, each link, each file --
            # and the ones a case-insensitive or normalizing filesystem folds
            # into another spelling: which of them is on disk depends on the
            # checkout, so nothing read through one is trusted
            fold = {}
            for r in ents:
                parts = r.split("/")
                for i in range(1, len(parts) + 1):
                    at = "/".join(parts[:i])
                    fold.setdefault(unicodedata.normalize("NFD", at).casefold(), set()).add(at)
            clash = {at for group in fold.values() if len(group) > 1 for at in group}
            dirs = {r.rsplit("/", 1)[0] for r in ents if "/" in r}
            dirs |= {d.rsplit("/", i)[0] for d in list(dirs) for i in range(d.count("/") + 1)}
            DIR = object()
            hit = {}                                # name read -> the folded name it passed

            def passes(rel, at):
                if at in clash:
                    hit.setdefault(rel, at)

            def resolve(rel):
                done, todo, hops = [], rel.split("/"), 0
                while todo:
                    c = todo.pop(0)
                    if c in ("", "."):
                        continue
                    if c == "..":
                        if not done:
                            return None             # out of the tree
                        done.pop()
                        continue
                    at = "/".join(done + [c])
                    passes(rel, at)
                    if at in dest:
                        hops += 1
                        if hops > 40 or dest[at].startswith("/"):
                            return None             # a loop, or absolute
                        todo = dest[at].split("/") + todo
                        continue
                    done.append(c)
                at = "/".join(done)
                if at in dirs:
                    return DIR                      # an in-tree directory: listed on its own
                return at if at in ents and at not in dest else None
            read = {r: resolve(r) if r in dest else r for r in ents
                    if is_code(r) or r in self.want or r in dest
                    or any(r.startswith(d + "/") for d in self.dirs)}
            for r in ents:                          # every name, read or not
                parts = r.split("/")
                for i in range(1, len(parts) + 1):
                    passes(r, "/".join(parts[:i]))
            need = sorted({t for r, t in read.items() if t and t is not DIR and r not in hit})
            body = dict(zip(need, self._cat([ents[t][1] for t in need])))
            # a filtered file reads as the repository's own filter writes it to
            # disk -- read now, before any probe, with the user's own config
            for t in self._filtered(need):
                r = subprocess.run(["git", "-C", str(self.root), *QUIET_GIT, "cat-file",
                                    "--filters", f"{self.head()}:{t}"], capture_output=True,
                                   env=git_env())
                if r.returncode:
                    raise SystemExit(f"cannot read {t} through its filter at HEAD")
                # the raw blob AND its filtered read: a filter defined or changed
                # after checkout changes the read, not what is on disk -- a fake
                # in either is a hit, so a re-run is never weaker than the plain run
                if r.stdout != body[t]:
                    body[t] = (body[t], r.stdout)      # scanned one after the other
            self.blobs = {}
            for r in hit.keys() - read.keys():      # a data file a probe may read
                self.blobs[r] = (f"{hit[r]} collides with another name of HEAD's tree "
                                 "on a case-insensitive filesystem -- which one is on disk "
                                 "depends on the checkout")
            for r, t in read.items():
                if t is DIR:
                    continue
                if r in hit:
                    self.blobs[r] = (f"{hit[r]} collides with another name of HEAD's tree "
                                     "on a case-insensitive filesystem -- which runs depends "
                                     "on the checkout")
                elif t:
                    self.blobs[r] = body[t]
                else:                               # any link that leaves the tree
                    self.blobs[r] = ("a symlink that does not resolve to a file of HEAD's "
                                     "tree -- what it runs cannot be scanned")
        return self.blobs

    def ls(self, src):
        """The names `src` selects at the pinned commit, as git reads the
        pathspec (magic, `..`) -- the plain scan's ls-files, over HEAD."""
        self.files()
        ls = subprocess.run(["git", "-C", str(self.root), *QUIET_GIT, "ls-files", "-z", "--",
                             *(src or ["."])], capture_output=True,
                            env=git_env(GIT_INDEX_FILE=self.index + "/index"))
        if ls.returncode:
            raise SystemExit(f"--src {' '.join(src or [])}: git cannot read it over HEAD")
        return ls.stdout.decode("utf-8", "surrogateescape").split("\0")

    def reads(self, rel):
        """Every form of one file read up front -- its raw blob, and its
        filtered read when a filter applies -- or []: a name no check
        registered is not read at all (after a probe the object store is not
        to be trusted)."""
        name = canon(rel)
        got = self.files().get(name) if name else None
        got = got if isinstance(got, tuple) else (got,)
        return [g for g in got if isinstance(g, bytes)]

    def blob(self, rel):
        """The raw blob of one file read up front, or None."""
        got = self.reads(rel)
        return got[0] if got else None

    def _add(self):
        """A shared clone of HEAD: its objects borrowed read-only from the
        repository (alternates, nothing copied), but refs, stash, config and
        hooks of its own -- so a probe's `git stash pop`, a branch or a commit
        stay in the clone -- and nothing registered in the user's repository."""
        tree = pathlib.Path(self.tmp) / "head"
        g = ["git", *QUIET_GIT]
        if subprocess.run([*g, "clone", "-q", "--shared", "--no-checkout", str(self.root),
                           str(tree)], capture_output=True, env=git_env()).returncode or \
                subprocess.run([*g, "-C", str(tree), "checkout", "-q", "--detach", "-f",
                                self.head()], capture_output=True, env=git_env()).returncode:
            raise SystemExit(f"cannot check out HEAD of {self.root} for a re-run")
        self.path = tree
        # no remote: a probe's `git push` / `fetch` cannot reach the user's refs
        subprocess.run(["git", "-C", str(tree), "remote", "remove", "origin"],
                       capture_output=True, env=git_env())
        # the only git dir we ever reset or remove is the clone's own, inside
        # our temp dir -- named now, never asked of the checkout later
        gitdir = (tree / ".git").resolve()
        if not (tree / ".git").is_dir() or (tree / ".git").is_symlink() or \
                pathlib.Path(self.tmp).resolve() not in gitdir.parents:
            raise SystemExit(f"cannot name the git dir of the checkout of HEAD at {tree} "
                             "-- the re-run stops rather than touch another repository")
        self.gitdir = gitdir
        self.config = (gitdir / "config").read_bytes()    # restored before every reset

    def get(self):
        if self.path is None:
            self.files()
            self.tmp = tempfile.mkdtemp()
            self._add()
            return self._scratch()
        for p in pathlib.Path(self.tmp).iterdir():
            if p != self.path:
                shutil.rmtree(p) if p.is_dir() and not p.is_symlink() else p.unlink()
        dotgit = self.path / ".git"
        # a probe that took or replaced the clone's .git, or initialised a
        # submodule (a repository of its own no reset of ours reaches into):
        # the checkout is made again
        if dotgit.is_symlink() or not dotgit.is_dir() or dotgit.resolve() != self.gitdir \
                or any(os.path.lexists(self.path / g / ".git") for g in self.gitlinks):
            if pathlib.Path(self.tmp).resolve() not in self.path.resolve().parents:
                raise SystemExit(f"refusing to remove {self.path}: not our checkout")
            shutil.rmtree(self.path, ignore_errors=True)          # the clone, git dir and all
            self._add()
            return self._scratch()
        # git state a probe can leave in its clone: its index, sparse patterns,
        # worktree config and attributes are dropped, its config put back
        for f in ("index", "info/sparse-checkout", "config.worktree", "info/attributes"):
            if (self.gitdir / f).exists():
                (self.gitdir / f).unlink()
        cfg = self.gitdir / "config"
        if cfg.is_symlink() or cfg.exists():
            cfg.unlink()                       # never write through a link a probe made
        cfg.write_bytes(self.config)
        wt = ["git", f"--git-dir={self.gitdir}", f"--work-tree={self.path}", "-C",
              str(self.path), *QUIET_GIT]
        # clean first: an untracked file a probe left (a .gitattributes) must
        # not take part in the checkout that follows
        if any(subprocess.run([*wt, *c], capture_output=True, env=git_env()).returncode for c in (
                ("clean", "-qffdx"), ("checkout", "-q", "--detach", "-f", self.sha),
                ("reset", "-q", "--hard", self.sha), ("clean", "-qffdx"))):
            raise SystemExit(f"cannot reset the checkout of HEAD at {self.path}")
        return self._scratch()

    def _scratch(self):
        """A fresh TMPDIR beside the checkout for the next probe (the old one
        went with the other siblings of the checkout)."""
        scratch = pathlib.Path(self.tmp) / "scratch"
        shutil.rmtree(scratch, ignore_errors=True)
        scratch.mkdir()
        SCRATCH[str(self.path)] = str(scratch)
        return self.path

    def close(self):
        SCRATCH.pop(str(self.path), None)
        for d in (self.tmp, self.index):
            if d:
                shutil.rmtree(d, ignore_errors=True)


_DRIFTED = {}


def drifted(root, sha, *evidence):
    key = (str(root), sha, *map(str, evidence))
    if key not in _DRIFTED:            # one answer per sensor invocation (D23)
        _DRIFTED[key] = _drifted(root, sha, *evidence)
    return _DRIFTED[key]


def _drifted(root, sha, *evidence):
    """Why evidence recorded at `sha` does not prove what ships now, or None:
    'bad' (not a full commit id), 'orphan' (not in HEAD's history), 'stale'
    (the tree changed since outside the evidence dirs, the state and the
    ledger -- a Markdown prompt is code, so no suffix is exempt)."""
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        return "bad"
    if git(root, "merge-base", "--is-ancestor", sha, "HEAD").returncode:
        return "orphan"
    spec = ["--", ".",
            # an evidence dir is exempt for its records only, not a helper put there
            *(f":(exclude,glob){os.path.relpath(e, root)}" + ("/**/*.json" if e.is_dir() else "")
              for e in evidence), ":!TASKS.md",
            # under the state dir, only the run's record: the signed contracts,
            # the ledger, verdicts, evidence and formal records, the claims --
            # a feature's spec or a probe's helper kept there is code
            *(f":(exclude,glob){STATE}/{g}" for g in (
                "**/requirements.md", "**/design.md", "**/standards.md", "**/TASKS.md",
                "**/verdicts/**", "**/evidence/**/*.json", "**/formal/**/*.json",
                "claims/**"))]
    # against the working tree and against HEAD: an uncommitted edit that puts
    # a file back as it was at `sha` does not make HEAD's change go away
    if any(git(root, "diff", "--quiet", sha, *at, *s).returncode
           for at in ((), ("HEAD",)) for s in (spec,)):
        return "stale"
    return None


def contract(root, reqfile):
    """The run's record beside the requirements, which is not code: the
    hash-signed contracts (a change there is drift, not staleness), TASKS.md,
    the verdicts and the evidence records. Anything else there -- a model, a
    probe's helper -- is code like the rest."""
    d = reqfile.parent
    paths = [reqfile] + [d / f for f in ("design.md", "standards.md", "TASKS.md")]
    if d.resolve() != pathlib.Path(root).resolve():
        paths += [d / "verdicts" / "**", d / "evidence", d / "formal"]
    return paths


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


SCRATCH = {}        # a HeadTree checkout -> the fresh TMPDIR its next probe gets


def run_shell(cmd, cwd, timeout, env=None):
    """(exit code, output) of a shell command in its own process group, which
    is killed when the command ends: nothing it left running in the
    background takes part in the next one. In a HeadTree checkout it also
    gets a TMPDIR of its own, emptied before the next probe. Raises
    TimeoutExpired."""
    if (scratch := SCRATCH.get(str(cwd))):
        env = {**(os.environ if env is None else env), "TMPDIR": scratch, "TMP": scratch,
               "TEMP": scratch}
    p = subprocess.Popen(cmd, shell=True, cwd=cwd, env=env, start_new_session=True,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        text, _ = p.communicate(timeout=timeout)
        return p.returncode, text.decode("utf-8", "replace")
    finally:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        p.wait()


def probe_env(cmd):
    """A probe's environment: PATH, HOME, the locale, TMPDIR, and only the
    variables its command names."""
    keep = {"PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "SYSTEMROOT"}
    keep |= set(re.findall(r"\$\{?([A-Za-z_]\w*)", cmd))
    return {k: v for k, v in os.environ.items() if k in keep}


def probe(cmd, root):
    return run_shell(cmd, root, 300, probe_env(cmd))


def moved(root, tree):
    """Why HEAD is no longer the commit this re-run pinned and proved, or None."""
    now = out(git(root, "rev-parse", "HEAD")).strip()
    if tree.sha and now != tree.sha:
        return (f"HEAD moved during the re-run ({tree.sha[:12]} -> {now[:12]}): it proved "
                "the pinned commit, not this one -- nothing recorded; re-run")
    return None


def check_evidence(root, reqfile, evidence, only, live_hosts, rerun, record, proven,
                   tree=None):
    own = tree is None
    tree = tree or HeadTree(root)
    if own and rerun:
        tree.want_dir(evidence)
    try:
        return _check_evidence(root, reqfile, evidence, only, live_hosts, rerun,
                               record, proven, tree)
    finally:
        if own:
            tree.close()


def _check_evidence(root, reqfile, evidence, only, live_hosts, rerun, record, proven,
                    tree):
    req = requirements(reqfile)
    if not req:
        return [f"{reqfile}: no Rn/Nn items -- nothing is verified"]
    if only:
        unknown = sorted(set(only) - set(req))
        if unknown:
            return [f"{reqfile}: --only names {', '.join(unknown)}, not in the requirements"]
        req = {k: v for k, v in req.items() if k in only}
    head = tree.head()          # the one HEAD this re-run pins, probes and stamps
    hits = []
    for rid, level in req.items():
        tag, n0 = f"{os.path.relpath(reqfile, root)} {rid}", len(hits)
        if level not in LEVELS:
            hits.append(f"{tag}: Verify `{level}` is not a level ({' | '.join(LEVELS)})")
            continue
        f = evidence / f"{rid}.json"
        # a re-run proves HEAD, so it runs HEAD's record of the probe
        got = tree.blob(rel_to(root, f)) if rerun else (f.read_bytes() if f.is_file() else None)
        if got is None:
            hits.append(f"{tag}: no evidence ({os.path.relpath(f, root)})"
                        f"{' at HEAD' if rerun else ''} -- unverified")
            continue
        raw = got.decode("utf-8", "replace")
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
        why = drifted(root, sha, evidence, *contract(root, reqfile))
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
                rc, text = probe(e["command"], tree.get())
                if rc:
                    hits.append(f"{tag}: re-run exited {rc}: {text.strip()[:120]}")
                elif not (m := expect.search(text)):
                    hits.append(f"{tag}: re-run output does not match expect")
                elif not bad:
                    # The service answered -- it is HEAD's proof only if a
                    # --deployed version probe showed THIS host runs HEAD. A
                    # local probe ran on a checkout of HEAD: it is HEAD's proof.
                    fresh = not live or (bool(h) and h in proven)
                    excerpt = text[max(0, m.start() - 80):m.end() + 80].strip()
            except subprocess.TimeoutExpired:
                hits.append(f"{tag}: re-run timed out after 300s")
        if (stale or orphan) and not fresh:
            why = (f"sha {sha[:12]} is not in HEAD's history" if orphan else
                   f"stale -- code changed since {sha[:12]}")
            hint = ("; the re-run passed, but nothing proves the environment runs HEAD "
                    "(--deployed)" if excerpt and h not in proven else "; re-run the probe")
            hits.append(f"{tag}: {why}{hint}")
        if record and f.is_symlink():
            hits.append(f"{tag}: {os.path.relpath(f, root)} is a symlink -- --record will not "
                        "write through it")
        elif record and fresh and len(hits) == n0 and not SECRET.search(excerpt) and \
                not moved(root, tree):
            now = datetime.datetime.now(datetime.timezone.utc)
            f.write_text(json.dumps({**e, "observed": excerpt, "sha": head,
                                     "at": now.isoformat(timespec="seconds"),
                                     "result": "pass"}, indent=2,
                                    ensure_ascii=False) + "\n", encoding="utf-8")
    return hits


def allowed(allow, text=None):
    rules = []
    if not allow:
        return rules
    try:
        text = allow.read_text(encoding="utf-8") if text is None else text
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


def scan(root, tree, rerun, src, tests, allow):
    """The code scan as a gate runs it: on a re-run, over HEAD's blobs (the
    allow file too); otherwise over this checkout's tracked files."""
    if not rerun:
        return check_code(root, src, tests, allowed(allow))
    rel = rel_to(root, allow) if allow else None
    text = tree.blob(rel) if rel else None
    if rel and text is None:
        raise SystemExit(f"--allow {rel}: not in HEAD")
    rules = allowed(allow, text.decode("utf-8", "replace")) if rel else []
    return check_code(root, src, tests, rules, tree)


def canon(rel):
    """A repo-relative name as HEAD's tree spells it (no `./`, no `//`), or
    None for one with a `..`: the kernel resolves that through links, so
    collapsing it here could name a different file."""
    parts = [c for c in str(rel).replace(os.sep, "/").split("/") if c not in ("", ".")]
    return None if ".." in parts or not parts else "/".join(parts)


def rel_to(root, path):
    """`path` relative to the repo, without collapsing a `..` it was given."""
    p = pathlib.Path(path)
    try:
        return str(p.relative_to(root)) if p.is_absolute() else str(p)
    except ValueError:
        return os.path.relpath(p, root)


def is_code(rel):
    p = pathlib.PurePosixPath(rel)
    return p.suffix in CODE or p.name.startswith(".env")


def check_code(root, src, tests, rules, tree=None):
    """tree: scan HEAD's blobs (a HeadTree) instead of this checkout, on a re-run."""
    blobs = tree.files() if tree else None
    if blobs is None:
        ls = git(root, "ls-files", "-z", "--", *(src or ["."]))
        if ls.returncode:
            return [f"not a git repo: {root}"]
        names = out(ls).split("\0")
    else:
        names = [r for r in tree.ls(src) if r in blobs]
    # what the checkout holds but cannot be read as it runs is reported over
    # all of HEAD: --src narrows the scan, not the tree a probe runs in
    hits = [f"{r}: {v}" for r, v in sorted((blobs or {}).items()) if isinstance(v, str)]
    for rel in names:
        p = root / rel
        if blobs is not None and isinstance(blobs.get(rel), str):
            continue
        if not rel or not is_code(rel) or TEST_DIR.search(rel) or TEST_FILE.search(rel) \
                or NOT_CODE.search(rel) or any(fnmatch.fnmatch(rel, g) for g in tests) \
                or (blobs is None and not p.is_file()):
            continue
        got = p.read_bytes() if blobs is None else blobs[rel]
        # a filtered file is (raw blob, filtered read): a fake in either is a hit
        for data in (got if isinstance(got, tuple) else (got,)):
            if b"\0" in data[:8192]:
                continue
            hits += scan_lines(rel, data, rules)
    return list(dict.fromkeys(hits))


def scan_lines(rel, data, rules):
    hits = []
    for n, line in enumerate(data.decode("utf-8", "replace").splitlines(), 1):
        toks = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", line)
        words = {t.lower() for t in toks}
        why = [f"`{w}`" for w in sorted(words & FAKE_WORDS)]
        why += [f"`{t}`" for t in toks if t.isupper() and len(t) > 4
                and t.lower().startswith(ROOTS) and t.lower() not in FAKE_WORDS]
        why += [w for rx, w in FAKE_TEXT if rx.search(line)]
        if why and not any(fnmatch.fnmatch(rel, g) and rx.search(line) for g, rx in rules):
            hits.append(f"{rel}:{n}: {', '.join(dict.fromkeys(why))}: {line.strip()[:90]}")
    return hits


def default_requirements(root):
    found = [root / STATE / "requirements.md"]
    found += sorted((root / STATE / "features").glob("*/requirements.md"))
    return [p for p in found if p.is_file()]


def run(root, reqfiles=None, evidence=None, only=None, env=None, live_hosts=(),
        src=None, tests=(), allow=None, rerun=False, record=False, deployed=None):
    _DRIFTED.clear()
    tree = HeadTree(root, [rel_to(root, allow)] if allow else ())
    try:
        return _run(root, reqfiles, evidence, only, env, live_hosts, src, tests, allow,
                    rerun, record, deployed, tree)
    finally:
        tree.close()


def _run(root, reqfiles, evidence, only, env, live_hosts, src, tests, allow, rerun,
         record, deployed, tree):
    if rerun and (why := unclean(root)):
        return [why]
    reqfiles = reqfiles or default_requirements(root)
    if rerun and (why := at_head(root, *[rf for rf in reqfiles if rf.is_file()])):
        return [why]
    if rerun:
        for rf in reqfiles:
            tree.want_dir(evidence or rf.parent / "evidence")
        tree.files()        # HEAD's blobs before any command runs, --deployed's too
    if (only or evidence) and len(reqfiles) != 1:
        raise SystemExit("--only / --evidence apply to one feature: pass "
                         "--requirements <its requirements.md>")
    if record and not deployed:
        raise SystemExit("--record stamps HEAD: pass --deployed <the probe that prints "
                         "the build the environment runs>")
    hits = [] if reqfiles else [f"no requirements file under {root / STATE} -- nothing is verified"]
    proven = frozenset()        # the hosts a --deployed version probe showed run HEAD
    if rerun and deployed:
        # One version probe per service; each must ask a live host and print HEAD.
        head, n0 = tree.head(), len(hits)
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
                rc, text = probe(cmd, tree.get())       # in HEAD's checkout, like every probe
            except subprocess.TimeoutExpired:
                rc, text = 1, "timed out after 300s"
            if rc or head[:12] not in text.lower():
                hits.append(f"--deployed {cmd!r}: the environment does not run HEAD "
                            f"{head[:12]} ({text.strip()[:80]!r}) -- deploy it, then re-run")
            else:
                proven |= {h for t in urls if (h := hostname(t))}
    for rf in reqfiles:
        if not rf.is_file():
            hits.append(f"no requirements file at {rf} -- nothing is verified")
            continue
        ev = evidence or rf.parent / "evidence"
        hits += check_evidence(root, rf, ev / env if env else ev, only, live_hosts,
                               rerun, record, proven, tree)
    # A re-run proves HEAD, so the scan reads HEAD too, not this checkout.
    hits += scan(root, tree, rerun, src, tests, allow)
    if rerun and (why := moved(root, tree)):
        hits.append(why)
    return hits


def self_test():
    # the fixtures' git never reaches the caller's repository (run from a hook,
    # GIT_DIR / GIT_INDEX_FILE would point it there), and no hook runs
    for k in [k for k in os.environ if k.startswith("GIT_")]:
        del os.environ[k]
    os.environ.update(GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="core.hooksPath",
                      GIT_CONFIG_VALUE_0="/dev/null")
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

    def ev(d, head, rid="R1", where=f"{STATE}/evidence", commit=True, **kw):
        e = {"id": rid, "verify": "live", "target": "https://api.prod.acme.io/v1/weather",
             "command": "curl -fsS https://api.prod.acme.io/v1/weather",
             "expect": r'"temp":\s*-?\d+', "observed": '{"temp": 21}',
             "result": "pass", "sha": head, "at": "2026-10-06T00:00:00Z", **kw}
        write(d, {f"{where}/{rid}.json": json.dumps(e)})
        if commit:      # a re-run proves HEAD's record of the probe, so commit it
            git(d, "add", f"{where}/{rid}.json")
            git(d, *quiet, "commit", "-qm", "evidence", "--", f"{where}/{rid}.json")

    ran = []

    # a case clash cannot be checked out cleanly on a case-insensitive
    # filesystem, so there git shows it dirty and a re-run refuses it: either
    # refusal is right
    def clash(want):
        return (want, "commit or stash")

    def check(label, got, want):
        if isinstance(want, tuple):
            want = next((w for w in want if any(w in h for h in got)), want[0])
        ran.append(label)
        if isinstance(want, str) and want.startswith("!"):        # "!x": no hit says x
            if not any(want[1:] in h for h in got):
                return True
            print(f"self-test FAILED: {label}: expected no {want[1:]!r}, got {got}")
            return False
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
        ("a prose mention is not an item", {req: base[req] + "## Notes\n- **R1's text** changed\n"},
         None, {}, None),
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
        git(d, "add", "-A")                     # a re-run needs the working tree to be HEAD
        git(d, *quiet, "commit", "-qm", "temp 1")
        ev(d, sha, command="echo https://nowhere.acme.io/x https://api.prod.acme.io/v1/weather")
        if not check("a probe URL that does not resolve", run(root, rerun=True),
                     "nowhere.acme.io does not resolve"):
            return 1
        ev(d, sha, command="echo https://api.prod.acme.io/v1/weather")
        if not check("a re-run that never reached the service", run(root, rerun=True),
                     "re-run output does not match"):
            return 1
    # A local item: a re-run refreshes it, because it runs on a checkout of
    # HEAD -- an untracked, ignored or uncommitted file beside it takes no part.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        lreq = {req: "- **R1** — x\n  - *Verify*: local\n"}
        sha = commit(d, {**base, **lreq, ".gitignore": "out/\n"})
        ev(d, sha, verify="local", target="this checkout", command="echo 'temp: 21'",
           expect=r"temp: \d+", observed="temp: 21")
        write(d, {"src/app.js": "export const temp = 2;\n"})
        git(d, "add", "-A")
        git(d, *quiet, "commit", "-qm", "y")
        if not check("a local re-run on HEAD", run(root, rerun=True), None):
            return 1
        for name, f, want in (("an untracked", "src/helper.sh", "commit or stash"),
                              ("an ignored", "out/helper.sh", "re-run exited")):
            write(d, {f: "echo 'temp: 21'\n"})
            ev(d, sha, verify="local", target="this checkout", command=f"sh {f}",
               expect=r"temp: \d+", observed="temp: 21")
            if not check(f"a local probe that needs {name} file", run(root, rerun=True), want):
                return 1
            (root / f).unlink()
        tree = HeadTree(root)
        try:
            probe("echo 'echo temp: 21' > planted.sh", tree.get())
            planted = probe("sh planted.sh", tree.get())[0]
            probe("git init -q nested && echo 'echo temp: 21' > nested/p.sh", tree.get())
            nested = probe("sh nested/p.sh", tree.get())[0]
            probe("git checkout -q -b evil && echo 'echo temp: 21' > c.sh && git add c.sh && "
                  "git -c user.email=a@b -c user.name=a commit -qm c", tree.get())
            committed = probe("sh c.sh", tree.get())[0]
            probe("echo 'echo temp: 21' > ../b.sh", tree.get())
            beside = probe("sh ../b.sh", tree.get())[0]
        finally:
            tree.close()
        if not check("a probe that runs what an earlier probe planted",
                     [] if planted else ["the planted file took part"], None):
            return 1
        if not check("a probe that runs what an earlier probe planted in a nested repo",
                     [] if nested else ["the nested repo took part"], None):
            return 1
        if not check("a probe that runs what an earlier probe committed on a branch",
                     [] if committed else ["the commit took part"], None):
            return 1
        if not check("a probe that runs what an earlier probe put beside the checkout",
                     [] if beside else ["the file beside it took part"], None):
            return 1
        write(d, {"src/app.js": "export const temp = 3;\n"})
        ev(d, sha, verify="local", target="this checkout", command="cat src/app.js",
           expect=r"temp = 3", observed="temp = 3")
        if not check("a local probe that needs an uncommitted edit", run(root, rerun=True),
                     "commit or stash"):
            return 1
        write(d, {"src/app.js": "export const temp = 2;\n"})
        ev(d, out(git(d, "rev-parse", "HEAD")).strip(), verify="local",
           target="this checkout", command="echo 'temp: 21'", expect=r"temp: \d+",
           observed="temp: 21")
        if not check("evidence at HEAD", run(root), None):
            return 1
        write(d, {"AGENTS.md": "a prompt is code\n"})
        git(d, "add", "-A")
        git(d, *quiet, "commit", "-qm", "prompt")
        if not check("evidence older than a changed Markdown prompt", run(root), "stale"):
            return 1
    # Beside a feature's requirements, only the record is exempt from staleness:
    # the signed contracts, TASKS.md, verdicts and evidence JSON -- not a model
    # or a helper put there. And a re-run scans HEAD, not an edit that hides a fake.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        f = "proposals/x"
        rf = [root / f / "requirements.md"]
        sha = commit(d, {f"{f}/requirements.md": "- **R1** — x\n  - *Verify*: local\n",
                         "src/app.js": base["src/app.js"],
                         f"{f}/model.tla": "a\n", f"{f}/evidence/helper.sh": "a\n"})
        ev(d, sha, where=f"{f}/evidence", verify="local", target="this checkout",
           command="echo 'temp: 21'", expect=r"temp: \d+", observed="temp: 21")
        write(d, {f"{f}/TASKS.md": "x\n", f"{f}/design.md": "x\n", f"{f}/verdicts/qa.md": "x\n"})
        git(d, "add", "-A")
        git(d, *quiet, "commit", "-qm", "record")
        if not check("a change to the record beside the requirements", run(root, rf), None):
            return 1
        for name, path in (("a model", f"{f}/model.tla"),
                           ("a helper in the evidence dir", f"{f}/evidence/helper.sh")):
            write(d, {path: "b\n"})
            git(d, "add", "-A")
            git(d, *quiet, "commit", "-qm", name)
            if not check(f"{name} beside the requirements changed", run(root, rf), "stale"):
                return 1
            git(d, *quiet, "reset", "-q", "--hard", "HEAD~1")
        write(d, {"src/app.js": "export const temp = mockTemp();\n"})
        git(d, "add", "-A")
        git(d, *quiet, "commit", "-qm", "fake")
        write(d, {"src/app.js": base["src/app.js"]})
        if not check("a re-run never scans an edit that hides a fake",
                     run(root, rf, rerun=True), "commit or stash"):
            return 1
        git(d, *quiet, "checkout", "-q", "--", ".")     # back to HEAD for the re-runs below
        # --src is read as git reads a pathspec, over HEAD, as the plain scan does
        for spec in (":!lib", ":(glob)src/**/*.js", "src/x/.."):
            if not check(f"--src {spec!r} on a re-run", run(root, rf, rerun=True, src=[spec]),
                         "src/app.js:1"):
                return 1
        # a probe -- --deployed's too -- that rewrites HEAD's object for app.js
        # changes nothing the scan reads: the blobs were read before it ran.
        # The helpers live outside the repository: a re-run needs a clean tree.
        H = tempfile.mkdtemp()
        write(H, {"rewrite.py": "import os, subprocess, sys, zlib\n"
                                "oid = subprocess.run(['git', 'rev-parse', 'HEAD:src/app.js'],"
                                " capture_output=True, text=True).stdout.strip()\n"
                                f"p = '{root}/.git/objects/' + oid[:2] + '/' + oid[2:]\n"
                                "os.chmod(p, 0o644)\n"
                                "body = sys.argv[1].encode() + b'\\n'\n"
                                "open(p, 'wb').write(zlib.compress(b'blob %d\\0' % len(body)"
                                " + body))\n"})
        head_now = out(git(d, "rev-parse", "HEAD")).strip()
        deployed = [f"echo https://api.prod.acme.io/version {head_now} && "
                    f"python3 {H}/rewrite.py 'export const t = 3;'"]
        if not check("a --deployed probe that rewrites HEAD's object",   # the fake found, or the re-run refuses
                     attempt(root, rerun=True, deployed=deployed, reqfiles=rf),
                     ("src/app.js:1", "cannot")):
            return 1
        probe(f"python3 {H}/rewrite.py 'export const temp = mockTemp();'", root)   # put it back
        shutil.rmtree(H)
        git(d, *quiet, "reset", "-q", "--hard")
        # A probe that alters the checkout -- index flags, sparse patterns, a
        # hook, a smudge filter -- changes nothing the scan reads: it reads blobs.
        tricks = {
            "skip-worktree": "git update-index --skip-worktree src/app.js && "
                             "echo 'export const t = 3;' > src/app.js",
            "sparse checkout": "git sparse-checkout set --no-cone /proposals/ >/dev/null 2>&1",
            "a smudge filter": "git config filter.qq.smudge 'sed s/mockTemp/realTemp/' && "
                               "git config filter.qq.clean cat && echo '*.js filter=qq' > "
                               "\"$(git rev-parse --git-common-dir)/info/attributes\" && "
                               "echo x >> src/app.js"}
        os.symlink("../tests/fixture.js", root / "src/link.js")
        write(d, {"tests/fixture.js": "export const t = mockTemp();\n"})
        git(d, "add", "-A")
        git(d, *quiet, "commit", "-qm", "link")
        for rr in (False, True):
            if not check(f"a production symlink to a fixture{' on a re-run' if rr else ''}",
                         run(root, rf, rerun=rr), "src/link.js:1"):
                return 1
        git(d, *quiet, "reset", "-q", "--hard", "HEAD~1")
        # resolved as the kernel does: through a directory link, `..` after one;
        # one that leaves the tree, is absolute or misses the case is reported
        write(d, {"tests/sub/.keep": "", "tests/fixture.js": "export const t = mockTemp();\n",
                  "fixture.js": "x()\n"})
        os.symlink("tests", root / "prod")
        os.symlink("tests/sub", root / "dd")
        unread = "does not resolve to a file of HEAD's tree"
        forms = {"through a directory link": ("src/a.js", "../prod/fixture.js", "1: `mock`"),
                 "`..` after a directory link": ("src/b.js", "../dd/../fixture.js", "1: `mock`"),
                 "out of the tree": ("src/c.js", "../../outside.js", unread),
                 "absolute": ("src/e.js", str(root / "tests/fixture.js"), unread),
                 "in another case": ("src/f.js", "../TESTS/fixture.js", unread)}
        for _, (link, dest, _) in forms.items():
            os.symlink(dest, root / link)
        git(d, "add", "-A")
        git(d, *quiet, "commit", "-qm", "links")
        got = run(root, rf, rerun=True)
        for name, (link, _, why) in forms.items():
            if not check(f"a production symlink {name}, on a re-run", got, f"{link}:{why}"
                         if why != unread else f"{link}: a symlink that {why}"):
                return 1
        git(d, *quiet, "reset", "-q", "--hard", "HEAD~1")
        for rel, text in (("tests/X.js", "x()\n"), ("tests/x.js", "export const t = mockTemp();\n")):
            oid = subprocess.run(["git", "-C", d, "hash-object", "-w", "--stdin"],
                                 input=text.encode(), capture_output=True).stdout.decode().strip()
            git(d, "update-index", "--add", "--cacheinfo", f"100644,{oid},{rel}")
        oid = subprocess.run(["git", "-C", d, "hash-object", "-w", "--stdin"],
                             input=b"../tests/X.js", capture_output=True).stdout.decode().strip()
        git(d, "update-index", "--add", "--cacheinfo", f"120000,{oid},src/g.js")
        git(d, *quiet, "commit", "-qm", "case")
        if not check("a symlink into two names that differ only in case, on a re-run",
                     run(root, rf, rerun=True), clash("src/g.js: tests/X.js collides")):
            return 1
        for rel, mode, body in (("TESTS", "120000", b"e"), ("e/x.js", "100644", b"x()\n"),
                                ("src/h.js", "120000", b"../TESTS/x.js")):
            oid = subprocess.run(["git", "-C", d, "hash-object", "-w", "--stdin"],
                                 input=body, capture_output=True).stdout.decode().strip()
            git(d, "update-index", "--add", "--cacheinfo", f"{mode},{oid},{rel}")
        git(d, *quiet, "commit", "-qm", "prefix case")
        if not check("a symlink through a directory link that folds into a real directory",
                     run(root, rf, rerun=True), clash("src/h.js: TESTS")):
            return 1
        git(d, *quiet, "reset", "-q", "--hard", "HEAD~2")
        for name, trick in tricks.items():
            ev(d, sha, where=f"{f}/evidence", verify="local", target="this checkout",
               command=f"{trick}; echo 'temp: 21'", expect=r"temp: \d+", observed="temp: 21")
            if not check(f"a probe that hides a committed fake by {name}",
                         run(root, rf, rerun=True), "src/app.js:1"):
                return 1
            git(d, "config", "--unset-all", "filter.qq.smudge")
            (root / ".git/info/attributes").unlink(missing_ok=True)
    # ...nor what the next probe runs: each is handed a checkout reset to HEAD
    # with no index flag, sparse pattern, worktree config or hook carried over.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        commit(d, {"fail.sh": "exit 3\n", "src/app.js": "x()\n", "assets/big.bin": "0" * 4096,
                   "spec/M.tla": "a\n"})
        hook = "$(git rev-parse --git-common-dir)/hooks/post-checkout"
        tree = HeadTree(root, ["./spec/M.tla", "spec/x/../M.tla"])
        try:
            got = tree.files()
            if not check("HEAD's blobs: the code and the named files, not the rest",
                         [] if set(got) == {"fail.sh", "src/app.js", "spec/M.tla"}
                         else [f"read {sorted(got)}"], None):
                return 1
            if not check("a name read up front with `./`; one with `..` refused; nothing read later",
                         [] if tree.blob("./spec/M.tla") == b"a\n" and
                         tree.blob("spec/x/../M.tla") is None and
                         tree.blob("assets/big.bin") is None else ["blob() read it"], None):
                return 1
            for name, trick, then in (
                    ("skip-worktree", "git update-index --skip-worktree fail.sh && "
                                      "echo 'echo ok' > fail.sh", "sh fail.sh"),
                    ("sparse checkout", "git sparse-checkout set --no-cone /src/ >/dev/null 2>&1",
                     "test ! -e fail.sh"),
                    ("a post-checkout hook", f"printf '#!/bin/sh\\necho echo ok > fail.sh\\n' "
                                             f"> \"{hook}\" && chmod +x \"{hook}\"", "sh fail.sh")):
                probe(trick, tree.get())
                rc = probe(then, tree.get())[0]
                if not check(f"a probe that runs what an earlier probe set up by {name}",
                             [] if rc else [f"{name} carried over"], None):
                    return 1
        finally:
            tree.close()
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
             "web.prod.acme.io/version 0123456789ab': the environment does not run HEAD"),
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
        git(d, "add", "-A")                     # what --record wrote is committed
        git(d, *quiet, "commit", "-qm", "recorded")
        ev(d, "0" * 40, where=f"{fa}/evidence/pre", command=offline)
        if not check("a squashed history, re-run on HEAD",
                     attempt(root, env="pre", rerun=True, **on_head), None):
            return 1
    # Security's accidents (R3's threat model), each a test before its fix.
    # (1) evidence is stale against HEAD, whatever the working tree holds
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        sha = commit(d, base)
        ev(d, sha, command="echo https://api.prod.acme.io/v1/weather '\"temp\": 21'")
        write(d, {"src/app.js": "export const temp = 2;\n"})
        git(d, "add", "src/app.js")
        git(d, *quiet, "commit", "-qm", "v2")
        write(d, {"src/app.js": base["src/app.js"]})            # uncommitted, back to A
        if not check("evidence stale at HEAD, the working tree back at its sha",
                     run(root, rerun=True), "commit or stash") or \
                not check("...and without a re-run", run(root), "stale"):
            return 1
    # (2) a repo's own clean/smudge filter (LFS-like): the re-run reads what is
    # checked out, as the plain scan does
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        git(d, "init", "-q")
        git(d, "config", "filter.fake.clean", "sed s/mockData/POINTER/")
        git(d, "config", "filter.fake.smudge", "sed s/POINTER/mockData/")
        lreq = {req: "- **R1** — x\n  - *Verify*: local\n"}
        sha = commit(d, {**lreq, ".gitattributes": "*.js filter=fake\n",
                         "src/app.js": "export const t = mockData;\n"})
        ev(d, sha, verify="local", target="this checkout", command="echo 'temp: 21'",
           expect=r"temp: \d+", observed="temp: 21")
        for rr in (False, True):
            if not check(f"a fake behind the repo's own filter{' on a re-run' if rr else ''}",
                         run(root, rerun=rr), "src/app.js:1"):
                return 1
    # QA's: a re-run runs HEAD's record of the probe, not an uncommitted edit of
    # it; a data file in a case clash, and a link that leaves the tree, are
    # reported whatever their name
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        lreq = {req: "- **R1** — x\n  - *Verify*: local\n"}
        sha = commit(d, lreq)
        ev(d, sha, verify="local", target="this checkout", command="exit 3",
           expect=r"temp: \d+", observed="temp: 21")
        git(d, "add", "-A")
        git(d, *quiet, "commit", "-qm", "evidence")
        ev(d, sha, verify="local", target="this checkout", command="echo 'temp: 21'",
           expect=r"temp: \d+", observed="temp: 21", commit=False)   # uncommitted edit
        if not check("a re-run beside an uncommitted edit of the evidence",
                     run(root, rerun=True), "commit or stash"):
            return 1
        git(d, *quiet, "checkout", "-q", "--", ".")
        (root / "data").mkdir()
        os.symlink("/etc/hosts", root / "data/hosts.txt")      # checked out, so clean
        git(d, "add", "data/hosts.txt")
        git(d, *quiet, "commit", "-qm", "link")
        if not check("a data link that leaves the tree, on a re-run",
                     run(root, rerun=True), "data/hosts.txt: a symlink"):
            return 1
        for rel, body in (("data/Value.txt", b"1\n"), ("data/value.txt", b"2\n")):
            oid = subprocess.run(["git", "-C", d, "hash-object", "-w", "--stdin"],
                                 input=body, capture_output=True).stdout.decode().strip()
            git(d, "update-index", "--add", "--cacheinfo", f"100644,{oid},{rel}")
        git(d, *quiet, "commit", "-qm", "data")
        if not check("a data file in a case clash, on a re-run", run(root, rerun=True),
                     clash("data/value.txt: data/value.txt collides")):
            return 1
    # --record never writes through a symlink: an evidence record that is a
    # link would overwrite whatever it points to
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        sha = commit(d, base)
        ev(d, sha, command="echo https://api.prod.acme.io/v1/weather '\"temp\": 21'", commit=False)
        (root / "src/real.json").write_bytes((root / STATE / "evidence/R1.json").read_bytes())
        (root / STATE / "evidence/R1.json").unlink()
        os.symlink("../../src/real.json", root / STATE / "evidence/R1.json")
        before = (root / "src/real.json").read_bytes()
        git(d, "add", "-A")
        git(d, *quiet, "commit", "-qm", "linked record")
        head_now = out(git(d, "rev-parse", "HEAD")).strip()
        got = attempt(root, rerun=True, record=True,
                      deployed=[f"echo https://api.prod.acme.io/version {head_now}"])
        if not check("--record through a symlinked evidence record",
                     [] if (root / "src/real.json").read_bytes() == before and
                     any("symlink" in h for h in got) else [f"overwrote it, or no hit: {got}"], None):
            return 1
    # Security final 11: --deployed proves a host, not the environment -- a
    # stale record of a service no version probe asked stays stale
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        two = {req: "- **R1** — a\n- **R2** — b\n", "src/app.js": "x()\n"}
        sha = commit(d, two)
        for rid, host in (("R1", "api.a.acme.io"), ("R2", "api.b.acme.io")):
            ev(d, sha, rid=rid, target=f"https://{host}/v1/x",
               command=f"echo https://{host}/v1/x '\"temp\": 21'")
        write(d, {"src/app.js": "y()\n"})
        git(d, "add", "-A")
        git(d, *quiet, "commit", "-qm", "both stale")
        head_now = out(git(d, "rev-parse", "HEAD")).strip()
        got = attempt(root, rerun=True, record=True,
                      deployed=[f"echo https://api.a.acme.io/version {head_now}"])
        r2 = json.loads((root / STATE / "evidence/R2.json").read_text())["sha"]
        if not check("a service no version probe asked, on a re-run", got, "R2: stale") or \
                not check("...and --record left its record alone",
                          [] if r2 == sha else ["R2 stamped HEAD"], None) or \
                not check("...while the asked service is fresh", got, "!R1: stale"):
            return 1
    # Security final 12: a filter defined after checkout (the user's repo config)
    # changes how a blob reads, not what is on disk -- a re-run scans both the
    # raw blob and its filtered read, so it is never weaker than the plain run
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        lreq = {req: "- **R1** — x\n  - *Verify*: local\n"}
        sha = commit(d, {**lreq, ".gitattributes": "*.js filter=build\n",
                         "src/app.js": "export const t = mockTemp();\n"})
        ev(d, sha, verify="local", target="this checkout", command="echo 'temp: 21'",
           expect=r"temp: \d+", observed="temp: 21")
        git(d, "config", "filter.build.smudge", "sed s/mockTemp/realTemp/")
        git(d, "config", "filter.build.clean", "cat")
        if not check("a filter defined after checkout, plain", run(root), "src/app.js:1") or \
                not check("...and on a re-run", attempt(root, rerun=True), "src/app.js:1"):
            return 1
    # the clone's config is put back without following a symlink a probe made
    with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as out_dir:
        root = pathlib.Path(d)
        commit(d, {"src/app.js": "x()\n"})
        target = pathlib.Path(out_dir, "victim")
        target.write_text("keep\n")
        tree = HeadTree(root)
        try:
            probe(f"rm .git/config && ln -s {target} .git/config", tree.get())
            tree.get()
        except SystemExit:
            pass
        finally:
            tree.close()
        if not check("a clone config a probe replaced with a symlink",
                     [] if target.read_text() == "keep\n" else ["it wrote through the link"], None):
            return 1
    # Audit final 7: an attributes file a probe writes into its clone's git dir
    # takes no part in the next probe's checkout
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        commit(d, {"data.txt": "a\nb\n"})
        tree = HeadTree(root)
        try:
            probe("mkdir -p .git/info && printf '* text eol=crlf\\n' > .git/info/attributes",
                  tree.get())
            crlf = probe("od -c data.txt | grep -q '\\\\r'", tree.get())[0]
        finally:
            tree.close()
        if not check("an attributes file an earlier probe left in its clone",
                     [] if crlf else ["the next probe saw converted bytes"], None):
            return 1
    # Audit final 6: git config a probe sets in its clone (a filter driver)
    # takes no part in the next probe's checkout
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        commit(d, {".gitattributes": "*.txt filter=x\n", "data.txt": "a\n"})
        tree = HeadTree(root)
        try:
            probe("git config filter.x.smudge 'sed s/a/b/' && git config filter.x.clean cat",
                  tree.get())
            kept = probe("grep -q a data.txt", tree.get())[0]
        finally:
            tree.close()
        if not check("git config an earlier probe set in its clone",
                     [] if kept == 0 else ["the next probe's checkout used it"], None):
            return 1
    # Reviewer final 11: the repository's own .git/info/attributes is ignored
    # state with the highest precedence -- it could change how a re-run reads
    # a file and not how the checkout was written, so a re-run refuses it
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        lreq = {req: "- **R1** — x\n  - *Verify*: local\n"}
        sha = commit(d, {**lreq, "src/app.js": "x()\n"})
        ev(d, sha, verify="local", target="this checkout", command="echo 'temp: 21'",
           expect=r"temp: \d+", observed="temp: 21")
        (root / ".git/info").mkdir(exist_ok=True)
        (root / ".git/info/attributes").write_text("*.js filter=fake\n")
        if not check("a re-run beside the repository's own info/attributes",
                     attempt(root, rerun=True), "info/attributes"):
            return 1
    # QA final 10: an untracked .gitattributes an earlier probe left takes no
    # part in the reset -- it is cleaned before git checks anything out
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        commit(d, {"data.txt": "a\nb\n"})
        tree = HeadTree(root)
        try:
            probe("printf '* text eol=crlf\\n' > .gitattributes", tree.get())
            crlf = probe("od -c data.txt | grep -q '\\\\r'", tree.get())[0]
        finally:
            tree.close()
        if not check("an untracked .gitattributes an earlier probe left",
                     [] if crlf else ["the next probe saw converted bytes"], None):
            return 1
    # Security final 10: a probe's checkout has refs of its own -- the common
    # `git stash; <tests>; git stash pop` idiom cannot pop the user's stash
    # into it (where the next reset would wipe it), nor leave a branch behind
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        lreq = {req: "- **R1** — x\n  - *Verify*: local\n"}
        sha = commit(d, {**lreq, "src/app.js": "x()\n"})
        ev(d, sha, verify="local", target="this checkout",
           command="git stash -q; git checkout -q -b probe-branch; "
                   "git push -q origin HEAD:refs/heads/pushed 2>/dev/null; echo 'temp: 21'; "
                   "git stash pop -q", expect=r"temp: \d+", observed="temp: 21")
        write(d, {"src/app.js": "y()  // the user's work, stashed\n"})
        git(d, *quiet, "stash", "-q")
        stash = out(git(d, "stash", "list")).strip()
        run(root, rerun=True)
        kept = out(git(d, "stash", "list")).strip() == stash and stash and \
            not out(git(d, "branch", "--list", "probe-branch", "pushed")).strip()
        if not check("a probe that pops a stash or makes a branch",
                     [] if kept else ["the user's stash or branches changed"], None):
            return 1
    # A sensor run from a git hook inherits GIT_DIR / GIT_INDEX_FILE: its own
    # git calls must not touch the user's index, HEAD or other worktrees.
    with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as other:
        root = pathlib.Path(d)
        lreq = {req: "- **R1** — x\n  - *Verify*: local\n"}
        sha = commit(d, lreq)
        ev(d, sha, verify="local", target="this checkout", command="echo 'temp: 21'",
           expect=r"temp: \d+", observed="temp: 21")
        git(d, "worktree", "add", "-q", "--detach", str(pathlib.Path(other) / "w"))
        shutil.rmtree(pathlib.Path(other) / "w")         # the user's, gone for now
        write(d, {"staged.py": "x = 1\n"})
        git(d, "add", "staged.py")
        saved = {k: os.environ.get(k) for k in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE")}
        os.environ.update(GIT_DIR=str(root / ".git"), GIT_INDEX_FILE=str(root / ".git/index"),
                          GIT_WORK_TREE=str(root))
        try:
            got = run(root, rerun=True)
            tree = HeadTree(root)
            try:
                probe("rm -rf .git", tree.get())
                tree.get()                              # made again
            finally:
                tree.close()
        finally:
            for k, v in saved.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        kept = (out(git(d, "diff", "--cached", "--name-only")).strip() == "staged.py" and
                out(git(d, "symbolic-ref", "-q", "HEAD")).strip() and
                str(pathlib.Path(other) / "w") in out(git(d, "worktree", "list")))
        if not check("a re-run from a git hook's environment", got, "commit or stash") or \
                not check("...leaves the user's index, HEAD and worktrees alone",
                          [] if kept else ["the user's repository changed"], None):
            return 1
    # Security final 5: under the state dir only the run's record is exempt from
    # staleness -- a feature's spec or helper there is code; and bytecode the
    # sensors' own imports leave is the environment, not an untracked file
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        f = f"{STATE}/features/x"
        sha = commit(d, {f"{f}/requirements.md": "- **R1** — x\n  - *Verify*: local\n",
                         f"{f}/spec/M.tla": "a\n"})
        ev(d, sha, where=f"{f}/evidence", verify="local", target="this checkout",
           command="echo 'temp: 21'", expect=r"temp: \d+", observed="temp: 21")
        if not check("a feature's record under the state dir", run(root), None):
            return 1
        write(d, {f"{f}/spec/M.tla": "b\n"})
        git(d, "add", "-A")
        git(d, *quiet, "commit", "-qm", "spec")
        if not check("a feature's spec under the state dir changed", run(root), "stale"):
            return 1
        write(d, {f"{STATE}/tools/__pycache__/check_live.cpython-3.pyc": "x"})
        if not check("a re-run beside the sensors' own bytecode",
                     attempt(root, rerun=True), "!commit or stash"):
            return 1
    # Security final 6: a re-run proves the HEAD it pinned -- a commit made
    # while it runs is neither probed nor stamped by --record
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        sha = commit(d, base)
        ev(d, sha, command="echo https://api.prod.acme.io/v1/weather '\"temp\": 21'")
        pinned = out(git(d, "rev-parse", "HEAD")).strip()
        dep = [f"echo https://api.prod.acme.io/version {pinned} && git -C {root} -c user.name=t "
               f"-c user.email=t@t commit -q --allow-empty -m moved"]
        got = attempt(root, rerun=True, record=True, deployed=dep)
        kept = json.loads((root / STATE / "evidence/R1.json").read_text())["sha"] == sha
        if not check("HEAD moved during a re-run", got, "HEAD moved") or \
                not check("...and --record stamped nothing", [] if kept else ["stamped"], None):
            return 1
    # QA final 2: --src narrows the scan, not the reports of what the checkout
    # holds; a submodule a probe initialised is gone before the next probe
    with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as sub:
        root = pathlib.Path(d)
        lreq = {req: "- **R1** — x\n  - *Verify*: local\n"}
        sha = commit(d, {**lreq, "app/a.js": "x()\n"})
        for rel, body in (("tools/Run.sh", b"exit 1\n"), ("tools/run.sh", b"echo ok\n")):
            oid = subprocess.run(["git", "-C", d, "hash-object", "-w", "--stdin"],
                                 input=body, capture_output=True).stdout.decode().strip()
            git(d, "update-index", "--add", "--cacheinfo", f"100644,{oid},{rel}")
        git(d, *quiet, "commit", "-qm", "clash")
        ev(d, sha, verify="local", target="this checkout", command="echo 'temp: 21'",
           expect=r"temp: \d+", observed="temp: 21")
        if not check("a case clash outside --src, on a re-run",
                     run(root, rerun=True, src=["app"]), clash("collides")):
            return 1
        git(d, *quiet, "reset", "-q", "--hard", "HEAD~2")
        commit(sub, {"lib.txt": "x\n"})
        git(d, "-c", "protocol.file.allow=always", "submodule", "add", "-q", sub, "vendor/lib")
        git(d, *quiet, "commit", "-qm", "submodule")
        tree = HeadTree(root)
        try:
            probe("git -c protocol.file.allow=always submodule update --init -q && "
                  "echo left > vendor/lib/out.txt", tree.get())
            left = probe("test ! -e vendor/lib/out.txt", tree.get())[0]
        finally:
            tree.close()
        if not check("a file an earlier probe wrote inside a submodule",
                     [] if left == 0 else ["it took part"], None):
            return 1
    # The CEO's ruling (C16): a re-run judges HEAD only from a clean working
    # tree -- an uncommitted or untracked file refuses it, so nothing the
    # working tree holds can decide what HEAD is judged against; and
    # --deployed's version probe runs in HEAD's checkout like every probe.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        lreq = {req: "- **R1** — x\n  - *Verify*: local\n"}
        sha = commit(d, {**lreq, ".gitignore": "*.local.sh\n"})
        ev(d, sha, verify="local", target="this checkout", command="echo 'temp: 21'",
           expect=r"temp: \d+", observed="temp: 21")
        if not check("a re-run on a clean tree", run(root, rerun=True), None):
            return 1
        for name, files in (("an uncommitted edit", {req: "- **R1** — x\n  - *Verify*: live\n"}),
                            ("an untracked file", {"helper.sh": "echo hi\n"})):
            write(d, files)
            if not check(f"a re-run beside {name}", attempt(root, rerun=True),
                         "commit or stash"):
                return 1
            git(d, *quiet, "checkout", "-q", "--", ".")
            (root / "helper.sh").unlink(missing_ok=True)
        for flag in ("--skip-worktree", "--assume-unchanged"):     # an edit git status hides
            write(d, {req: "- **R1** — x\n  - *Verify*: live\n"})
            git(d, "update-index", flag, req)
            if not check(f"a re-run beside an edit hidden by {flag}", attempt(root, rerun=True),
                         "commit or stash"):
                return 1
            git(d, "update-index", flag.replace("--", "--no-"), req)
            git(d, *quiet, "checkout", "-q", "--", ".")
        write(d, {"v.local.sh": f"echo {out(git(d, 'rev-parse', 'HEAD')).strip()}\n"})  # ignored
        dep = [f"echo https://api.prod.acme.io/version && sh v.local.sh"]
        if not check("a --deployed probe that needs a file HEAD does not have",
                     attempt(root, rerun=True, deployed=dep), "the environment does not run HEAD"):
            return 1
    # (3) a process a probe left running takes no part in the next probe;
    # (4) a probe that removes its checkout's .git cannot turn the reset on the
    # repository around the temp dir
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        commit(d, {".gitignore": ".tmp/\n", "src/app.js": "x()\n"})
        write(d, {"src/app.js": "y()  // the user's uncommitted work\n"})
        (root / ".tmp").mkdir()
        before, tempfile.tempdir = tempfile.tempdir, str(root / ".tmp")
        tree = HeadTree(root)
        try:
            probe("echo 'echo temp: 21' > \"$TMPDIR/cache.sh\"", tree.get())
            cached = probe("sh \"$TMPDIR/cache.sh\"", tree.get())[0]
            probe("(while :; do echo 'echo temp: 21' > planted.sh; sleep 0.1; done)"
                  " >/dev/null 2>&1 &", tree.get())
            bg = probe("sleep 0.5; sh planted.sh", tree.get())[0]
            probe("rm -rf .git", tree.get())
            again = tree.get()
            ok = (again / "src/app.js").read_text() == "x()\n"
        finally:
            tree.close()
            tempfile.tempdir = before
        if not check("a file an earlier probe left in its TMPDIR",
                     [] if cached else ["it took part"], None):
            return 1
        if not check("a process an earlier probe left running",
                     [] if bg else ["it took part"], None):
            return 1
        if not check("a probe that removes its checkout's .git",
                     [] if ok and (root / "src/app.js").read_text().startswith("y()") and
                     out(git(d, "symbolic-ref", "-q", "HEAD")).strip()
                     else ["the user's repository was reset"], None):
            return 1
    print(f"self-test ok ({len(ran)} cases)")
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
