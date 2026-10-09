# Security verdict — final 6 (security role, Claude, at f65222c)

Scope: main..f65222c against proposals/0.9.7-autonomy-by-proof/requirements.md,
R3's *Threat model* first. Read: boot.py and its Claude Code adapter and hooks,
check_live.py (HeadTree, unclean, at_head, drifted, probe, run_shell, --record),
check_formal.py, check_tasks.py, the CI workflows, the role frontmatter and the
adapter's permission mapping. Ran in a separate clone: all three sensor
self-tests (149 / 46 / 54 cases, exit 0), check_neutral.py (ok), a secret grep
over every patch in the range (no hit), and the two repros below. I read the
verdicts/ directory only after this pass, as a regression list. Both blockers
take their root cause from a logged debt (D16, D21). Those debts record the
defect as a duplication or as low-severity secret exposure. The repros show a
breach of a signed clause, so I re-rate them and do not count them as new
defects.

```yaml
verdict: FAIL
blockers:
  - requirement: R3 (Threat model -- "on a re-run they SHALL never pass what the plain run fails"); invariant 10
    clause: a passing re-run is HEAD's proof; --record stamps sha = HEAD
    problem: >
      check_live pins HEAD once in HeadTree (tree.head()) and runs every probe on
      that commit. But _run compares --deployed's output against a fresh
      `git rev-parse HEAD`, and _check_evidence reads HEAD again later for the
      sha that --record writes. If HEAD moves during the re-run (another
      session commits, or the CEO commits in a second window -- the
      multi-session case this release governs), three things follow. The
      evidence is stamped with a commit that was never probed, and never
      proven deployed. The re-run reports "live: ok" for it. The plain run
      then passes that commit's code, which it would otherwise call stale.
      This has the same root cause as D16, which logs it only as a duplicated
      git spawn; audit-8 asked QA to confirm which sha is meant, and nobody
      did. Fix: use tree.head() in both places (and check that HEAD still
      equals it before --record writes).
    repro: |
      # repo: .aidlc/requirements.md "- **R1** — x / *Verify*: local";
      # src/app.js; evidence R1.json (local, command "echo temp: 21",
      # sha = an older commit), all committed; H1 = HEAD
      ( sleep 1.5; echo 'export const temp = 999;' > src/app.js
        git add src/app.js; git commit -qm "other session" ) &
      DEPLOYED_SHA=$H1 python3 check_live.py --root . --rerun --record \
        --deployed 'curl -fsS https://api.github.com/zen >/dev/null && sleep 3 && echo "build $DEPLOYED_SHA"'
      # -> live: ok; R1.json sha = the other session's commit (temp = 999),
      #    which no probe ran on and --deployed never proved
      git commit -qam record; python3 check_live.py --root .   # -> live: ok
  - requirement: R3 (Threat model -- "keep accidents out of a re-run ... an untracked or ignored file"); R10 (--rerun)
    clause: >
      only a tool on PATH or a variable the command uses is the environment,
      and "the reviewer reads it in the command"; check_formal's re-run runs
      "as check_live's re-runs are"
    problem: >
      check_formal.run_cmd hands each check, vacuity run and conformance check
      the caller's whole environment (check_live.git_env()), not the
      PATH/HOME/LANG-plus-named-variables set that check_live.probe uses. A
      variable the command never names -- PYTHONPATH, NODE_PATH,
      JAVA_TOOL_OPTIONS, LD_PRELOAD, often set by direnv to a path inside the
      repo -- therefore loads an ignored file from the user's working tree into
      the throwaway checkout of HEAD. A check that fails on HEAD alone passes.
      unclean() lets ignored files through by design, so nothing refuses this.
      check_tasks --rerun (the Ship-batch proof) goes through the same path.
      This has the same root cause as D21, which logs it as a low-severity
      secret exposure; this repro shows a re-run decided by the tree. Fix: run
      the formal commands with check_live.probe's environment.
    repro: |
      # tracked: p/requirements.md (R1, Property Safe, checked, conformance none),
      # spec/M.tla (Safe == TRUE), tools/chk.py (`import helper; print(helper.MSG)`,
      # `--broken` prints "Invariant is violated" and exits 1); .gitignore: gen/
      # ignored, not in HEAD: gen/helper.py  MSG="No error has been found"
      # p/formal/R1.json at HEAD's sha, committed; git status is clean
      PYTHONPATH=$PWD/gen python3 check_formal.py --root . --requirements p/requirements.md --rerun
      #   -> formal: ok   (exit 0)
      env -u PYTHONPATH python3 check_formal.py --root . --requirements p/requirements.md --rerun
      #   -> re-run of the check exited 1 ... (exit 1)
debts:
  - "check_tasks --rerun calls check_evidence with live_hosts=() and has no --live-host option, so a Done live item whose target lies outside standards.md's environment hosts passes check_tasks while check_live --live-host fails it. Add the option and pass it through."
  - "--record writes evidence/<ID>.json through whatever is at that path in the working tree; an in-tree symlink there makes the record overwrite the tracked file it points to. Refuse to record through a symlink (or write with O_NOFOLLOW)."
  - "run_shell kills the probe's process group, but a tool that daemonises with setsid (a build daemon, `ssh -f`) survives into later probes. A later probe can then pass because of a process an earlier one started. Stated nowhere; add it to HeadTree's docstring of what no reset undoes."
notes:
  - "Already logged, re-confirmed, not re-raised: D12 (worktree left registered on SIGTERM), D17 (hint file in the shared temp dir follows symlinks), D18 (narrow secret pattern), D19 (auditor keeps Bash; KiroCrew spawn/memory), D20 (actions pinned by tag), D22 (failed probe output unredacted). D16 and D21 are re-rated above, not new."
  - "User's work: nothing in the sensors writes to the user's index, refs or working tree except --record's evidence file. git_env strips GIT_*, so a hook's GIT_DIR or GIT_INDEX_FILE cannot redirect the sensors. HEAD's index is built in a private GIT_INDEX_FILE. A rebuild removes only the sensor's own worktree admin dir (read before any probe), and rmtree refuses a checkout path a probe swapped for a symlink. git worktree add names its admin dir with an atomic mkdir, so concurrent re-runs (Phase 4 runs qa and security in one batch) do not collide."
  - "boot.py always exits 0 and never blocks a session. The claim is made by link(2) of a fully written file, and nothing else in the tree is touched. It does run the repo's own .aidlc/tools/board.py at every session start, which is the same trust as the hooks themselves."
  - "Supply chain: no new runtime dependency; the sensors use only the standard library (N3). TLC is pinned by version and sha256, checked by check_models.py before use. Workflows have contents: read. impeccable is pinned at 4.1.0, and its edit hook goes to settings.local.json only after the user says yes."
  - "Secrets: no credential in any patch of the range. Evidence is scanned with SECRET, and --record refuses an excerpt that matches it (pattern breadth is D18)."
```

Retrospective: the re-run's isolation is now careful about the tree, so the
remaining gaps are at its edges: which HEAD it means, and what the environment
carries in. Both blockers were already logged as low-severity debts, and only a
repro showed what they actually do. A debt that touches the threat model should
come with a repro before anyone rates it.
