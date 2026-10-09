# Security verdict — final (security role, Claude, at d74ff6a)

Scope: `main..d74ff6a` judged against the signed
`proposals/0.9.7-autonomy-by-proof/requirements.md`, mainly R3's *Threat model*
(a probe command is trusted; the sensors keep accidents out of a re-run; a re-run
never passes what the plain run fails). Every finding below was reproduced in a
throwaway clone. The three sensor self-tests pass (check_live 126 cases,
check_formal 45, check_tasks 51), and so does `tools/check_neutral.py`. The
TLA+ jar was downloaded fresh from the v1.7.4 release and its hash matches the
pinned `TLA_SHA256`.

```yaml
verdict: FAIL
blockers:
  - requirement: R3
    clause: "Threat model: the sensors SHALL keep accidents out of a re-run: an uncommitted change"
    problem: >
      check_live.drifted() decides staleness with `git diff --quiet <sha> -- .`,
      which compares the evidence sha with the WORKING TREE, not with HEAD.
      Say the uncommitted tree happens to match the evidence sha, but HEAD
      changed code since that sha. Then a `--rerun` (no --deployed) passes a
      live item that the same re-run fails on a clean tree. HeadTree pins HEAD
      for the scan and the probes, but the staleness test never reads it.
      check_tasks.py --rerun (the Done gate before Ship) and check_formal.py
      call the same function. In CI the tree is HEAD, which hides the bug
      there, but local runs are exposed.
    repro: |
      commit A: src/app.js "v1", .aidlc/requirements.md "- **R1** — x / *Verify*: live";
      commit .aidlc/evidence/R1.json {verify: live, target https://api.prod.acme.io/v1,
        command "echo https://api.prod.acme.io/v1 '\"temp\": 21'", expect "\"temp\": \\d+",
        result pass, sha A}
      commit B: src/app.js "v2"
      check_live.run(root, rerun=True)  -> ["... R1: stale -- code changed since <A>; the re-run
                                            passed, but nothing proves the environment runs HEAD"]
      echo v1 > src/app.js              # uncommitted; git status: " M src/app.js"
      check_live.run(root, rerun=True)  -> []      (PASS)
      (to run it offline, patch check_live.resolve to return a public address, as the self-test does)
      fix: on --rerun (better, always) also require `git diff --quiet <sha> <pinned HEAD> -- <same pathspec>`.
  - requirement: R3
    clause: "Threat model: on a re-run they SHALL never pass what the plain run fails"
    problem: >
      On --rerun the code scan reads HEAD's raw blobs (`cat-file --batch`, no
      filters). The plain run reads the checked-out files. A path stored
      through a clean/smudge filter (Git LFS is the common case: a
      `.gitattributes` line such as `src/data/*.json filter=lfs`) is a pointer
      in the blob and real content on disk. So seed data or fakes kept under
      LFS fail the plain scan and pass the re-run, on a clean tree at HEAD. The
      self-test covers a smudge filter planted by a probe, but not the
      repository's own filter.
    repro: |
      git config filter.lfs.clean/smudge = a 20-line stand-in for git-lfs (clean stores the
        bytes and emits an LFS pointer; smudge restores them); filter.lfs.required=true
      .gitattributes: "src/data/*.json filter=lfs -text"
      src/data/trips.json: [{"id": 1, "name": "mock trip"}]; commit; git status is clean
      check_live.check_code(root, None, (), [])              -> ['src/data/trips.json:1: `mock`: ...']
      check_live.check_code(root, None, (), [], HeadTree(root)) -> []   (blob = "version https://git-lfs...")
      fix: in files(), before the first probe, read filtered paths with `cat-file --batch --filters`
        (the config is still the user's own at that point), or fail closed: report as unscannable
        any code path that `git check-attr filter` marks.
  - requirement: R3
    clause: "Threat model: keep out of a re-run ... what an earlier probe left behind"
    problem: >
      probe() / run_cmd() run `shell=True` and return as soon as the shell
      exits. A background process the probe started keeps running into the
      next probe: a dev server, a watcher, `npm start &` for a local item. The
      per-probe reset (checkout, reset --hard, clean -ffdx) cleans the files
      but cannot stop a live process. That process then writes into the
      "reset" checkout, or answers on a port, while the next probe runs. The
      next probe can pass on the earlier probe's process.
    repro: |
      t = HeadTree(root)
      probe("(while :; do echo 'echo temp: 21' > planted.sh; sleep 0.2; done) >/dev/null 2>&1 &", t.get())  -> (0, '')
      probe("sleep 1; sh planted.sh", t.get())   -> (0, 'temp: 21')   # planted.sh is not in HEAD
      fix: start each probe with start_new_session=True and killpg its group after it exits
        (and on timeout). Add the case above to the self-test.
  - requirement: R3
    clause: "Threat model: keep out of a re-run ... what an earlier probe left behind (and the brief's 'git operations on the user's repo')"
    problem: >
      HeadTree.get() takes the gitdir from `git rev-parse --absolute-git-dir`,
      run inside the checkout, and trusts the answer. It then unlinks
      index / info/sparse-checkout / config.worktree there and runs
      `checkout -f`, `reset --hard` and `clean`. A probe can remove the
      checkout's `.git` file, for example a packaging step that strips VCS
      metadata. git then discovers the nearest enclosing repository. If TMPDIR
      is inside the user's project (a common CI or sandbox setting), or inside
      any other repository (a $HOME dotfiles repo), the reset runs against
      THAT repository. It deletes the user's index, detaches their HEAD, and
      `checkout -f` / `reset --hard` overwrite their uncommitted work. The
      sensor then exits "cannot reset" (it fails closed), but the damage is
      already done.
    repro: |
      TMPDIR=<project>/.tmp (gitignored); in <project>: modify tracked src/app.js, stage new src/new.js
      t = HeadTree(project); probe("rm -rf .git", t.get()); t.get()   -> SystemExit "cannot reset ..."
      afterwards: src/app.js is back at HEAD (uncommitted edit lost), src/new.js unstaged,
        HEAD detached (was refs/heads/main)
      fix: record the worktree's gitdir at `worktree add` (<common-dir>/worktrees/<name>) and pass
        --git-dir/--work-tree explicitly. Refuse to touch anything if the checkout's .git no longer
        points there, then re-create the checkout instead.
debts:
  - "boot.py writes its per-session hint to $TMPDIR (falling back to the shared system temp dir) with Path.write_text, which follows symlinks. On a shared Linux temp dir, another local user can learn the session id (it is written in .aidlc/claims/ORCHESTRATOR.<n>.claim) and plant <tempdir>/devcrew-orchestrator-<sid> as a symlink: every start/beat then truncates the victim's file to 'orchestrator' or 'worker' (reproduced). Use a per-user 0700 directory or the gitignored state dir, and open with O_NOFOLLOW."
  - "SECRET misses common credential shapes: Stripe sk_live_..., JWTs (eyJ...), Google AIza..., 'Authorization: Basic', Slack webhook URLs, Set-Cookie session values. All of these pass, reproduced. --record writes 80 characters around the match of a REAL service response into a committed file. Broaden the pattern, or redact by default and run a maintained secret scanner (e.g. gitleaks) at the gate."
  - "KiroCrew permission boundary (pre-existing template, not introduced here): every role, reviewer and auditor included, gets `kirocrew-core/*` allowed, which includes spawn_run (dispatch a write-capable agent) and learn_add (write to team memory). That bypasses 'auditor holds no write tool' (invariant 7) and 'reviewer mounts no memory' (invariant 4). The reviewer.json installed on this machine has exactly this grant, and no auditor.json is installed. Deny spawn_run/spawn_sub_agents/learn_add/session_ledger for reviewer and auditor."
  - "On Claude Code the auditor is 'read-only' but keeps Bash (Read,Grep,Glob,Bash,WebFetch,WebSearch), and Bash can write files. This predates the change. If invariant 7 means it mechanically, add permission deny rules for write-like Bash or run the auditor in a sandbox; otherwise say 'no Write/Edit tool'. The reviewer's mapping (read, search, web) is correct, but unlike the auditor's it has no install-time check that the generated .claude/agents/reviewer.md grants no Write/Edit/Bash."
  - "GitHub Actions are pinned by tag (checkout@v7, setup-python@v7, setup-java@v6, cache@v6), not by commit SHA. Both workflows are pull_request with contents: read, so the exposure is low. Pinning by SHA closes it."
  - "On --rerun the requirements file and the evidence JSON are still read from the working tree. An uncommitted edit (e.g. Verify live -> local) takes part. check_tasks' Signed: hash catches the requirements edit; check_live --rerun on its own does not."
  - "D12 stands: a killed run leaves a registered worktree in the user's .git/worktrees. Prune devcrew's stale worktrees at start."
notes:
  - "Supply chain: tla2tools 1.7.4 downloaded fresh from the GitHub release hashes to 936a2620...0e88 = TLA_SHA256. check_models.py refuses any other jar with exit 2, so a poisoned actions/cache entry cannot run. The release asset is mutable (updated 3 days after publish), which is exactly why the pin is the right control."
  - "Hooks: boot.py always exits 0 and runs no network. Its command in settings.json is quoted. Mutual exclusion uses os.link generations. board.py, if present, runs from the repo at SessionStart: that is repo code, the same trust as the hook itself."
  - "Probes run with the user's shell and an environment reduced to PATH/HOME/LANG/LC_ALL/TMPDIR plus the variables the command names. This is consistent with the signed threat model, and HeadTree's docstring states the limit."
  - "The --rerun scan's other accident defences held under test: blobs read before any command, symlinks resolved in HEAD's tree, case and normalization clashes reported, index flags / sparse / worktree config / hooks dropped. In these areas the re-run was stricter than the plain run, never weaker. One plain-only weakness: names are decoded with 'replace', so a non-UTF-8 path is silently skipped by the plain scan (Linux only)."
  - "No secrets or home-directory paths in the diff's evidence/formal JSON. All evidence parses."
d13_ruling: >
  Conditionally as sound, and only with every condition below; otherwise not.
  (1) Treat ANY `ls-files -v` tag other than `H` as a flag (an allow-list, not
  a deny-list), and treat a failing or unparseable ls-files as a flag.
  (2) Run ls-files, checkout and reset with core.trustctime=true,
  core.checkStat=default and core.ignoreStat=false pinned, besides the
  existing core.fsmonitor=false and core.sparseCheckout=false.
  (3) Keep dropping info/sparse-checkout and config.worktree on every reset.
  (4) Add a self-test that sets the user's own core.trustctime=false and
  core.checkStat=minimal, has a probe rewrite a tracked file at the same size
  and restore its mtime (cp -p / touch -r), and asserts that the next probe
  sees HEAD's bytes.
  Why: with a flag-free index, `checkout -f` + `reset --hard` rest on git's
  stat check, and the pins are load-bearing. Reproduced: same size, mtime
  restored, `ls-files -v` shows only `H`. With trustctime=false, reset --hard
  leaves the probe's bytes in place. With trustctime=true it restores HEAD's.
  The untracked cache does not matter, because clean -x does not use it
  (tested).
  What it gives up, compared with dropping the index every time: it no
  longer holds on filesystems that do not update ctime (some FUSE or
  network mounts under TMPDIR), or against a forged index stat. Both are
  outside R3's accident model, but dropping the index every time is immune
  to both. Fix the four blockers first: the 2-3 s it saves is not worth
  merging with them open.
```

Retrospective:
1. In this round, real defects sat where the re-run still trusted the working tree or the process: the drift test, filters, live child processes, the discovered gitdir. The object-store reads it had hardened were sound.
2. The self-tests guard against hostile probes. They have no case for the repo's own config (LFS) or for an accidental leftover (a background server), and those turned out to be the gaps.
3. Next time, check every git call against "which HEAD and which gitdir does this resolve, after a probe ran" before reading the rest.
