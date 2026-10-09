# Security verdict — final 4 (security role, Claude, at 6110064)

Judged: `feat/0.9.7-autonomy-by-proof` at 6110064 (main..6110064) against
`proposals/0.9.7-autonomy-by-proof/requirements.md` (signed sha256:7b665be99e78),
R3's *Threat model* included. All runs were in a fresh clone and in throwaway toy
repositories on APFS. The sensors were run from outside the toy trees with `python3 -I`.
I read `verdicts/` only after this pass, and used it only as a regression list.

Sensors (rc 0): `check_live.py --self-test` (143 cases), `check_formal.py --self-test` (46),
`check_tasks.py --self-test` (52). SECRET pattern over every evidence/formal JSON
under proposals/: no hit. `git log -p main..6110064` grepped for key shapes (AWS,
PEM, gh*_, sk-, xox*): no hit.

```yaml
verdict: FAIL
blockers:
  - requirement: R3 (and R4's drift halt; R10's --rerun reads the same file)
    clause: "Threat model: the sensors SHALL keep accidents out of a re-run: an uncommitted change ..."
    problem: >-
      C16 closes the class "the working tree decides what HEAD is judged against"
      with one guard: check_live.unclean() refuses a re-run when `git status
      --porcelain --untracked-files=all` lists anything. It does not check whether
      the contract files match HEAD. After the guard, a re-run still reads
      requirements.md, TASKS.md and every signed file from the working tree.
      `git status` by design does not report an edit to an index entry flagged
      skip-worktree or assume-unchanged. It also does not report one under
      core.ignoreStat, and it trusts the user's core.fsmonitor, because unclean()
      runs git without QUIET_GIT. With such a flag, an uncommitted TASKS.md or
      requirements.md decides the Ship-gate re-run. Both variants of Security
      final 3's blocker 2 (the drift that ships; HEAD's ledger claiming an
      unverified Done) pass again. A skip-worktree flag on a high-churn ledger
      file is an ordinary git habit for keeping local edits out of commits. Nobody
      sets it to fool the sensor, and the threat model's out-of-scope clause covers
      only a probe that rewrites git's objects, config or refs. Fix: on --rerun,
      read TASKS.md, requirements.md and each signed file from HeadTree, which
      already pins HEAD and can carry them in `want`. Alternatively, refuse when the
      working-tree bytes of each file the sensor reads differ from HEAD's blob. Do
      not rely on git status. Run unclean()'s git with QUIET_GIT and
      --no-optional-locks.
    repro: |
      Ledger variant (check_tasks --rerun, the Ship gate):
        f/requirements.md = "- **R1** — a" / "  - *Verify*: local" / "  - *Property*: none — prose"
        f/TASKS.md = "Signed: requirements.md sha256:<its 12>" + "## Done / - [x] R1 a" + empty In progress / Todo; commit
        check_tasks.py --tasks f/TASKS.md --rerun   -> rc 1 "Done but not live: ... R1: no evidence ... at HEAD"
        git update-index --skip-worktree f/TASKS.md
        rewrite f/TASKS.md with R1 in progress ("- [~] R1 a — building · be · 1/5 stalled 0/3 · next: x")
        git status --porcelain                       -> (empty)
        check_tasks.py --tasks f/TASKS.md --rerun    -> rc 0 "tasks: ok"   (HEAD's ledger still says [x] R1)
      Drift variant:
        same requirements.md + TASKS.md with "- [ ] R1 a" in Todo, signed; commit
        edit R1's Verify line; commit                 # HEAD drifted from the signature
        check_tasks.py --tasks f/TASKS.md --rerun    -> rc 1 "DRIFT -- requirements.md is sha256:..."
        git update-index --skip-worktree f/requirements.md; git show HEAD~1:f/requirements.md > f/requirements.md
        git status --porcelain                       -> (empty)
        check_tasks.py --tasks f/TASKS.md --rerun    -> rc 0 "tasks: ok"
      check_live variant: .aidlc/requirements.md with R1 (local, fresh evidence) and R2 (live, no evidence); commit;
        check_live.py --rerun -> rc 1 "R2: no evidence ... at HEAD"; --assume-unchanged (or --skip-worktree)
        on requirements.md, drop R2 in the working tree; git status empty; check_live.py --rerun -> rc 0 "live: ok"
debts: []
notes:
  - "Previously raised and still open (Security final 3 notes, not D items): check_formal's canon() turns an absolute source into a repo-relative one on --rerun, so with a constructed in-tree mirror the plain run fails and the re-run passes. --record writes evidence through a symlinked evidence path. Both are low severity, but the first is literally 'a re-run passes what the plain run fails'. Report any absolute source as a hit, and open the record target with O_NOFOLLOW."
  - "HeadTree._add trusts `git rev-parse --absolute-git-dir` output without validating it. If git ever returned nothing, self.gitdir would be Path('.'), and get() would rmtree it (the caller's cwd, usually the user's repo) and unlink ./index. I could not trigger it, because the value is read before any probe. Defensive fix: assert it is absolute and under `--git-common-dir`/worktrees."
  - "run_shell kills the probe's process group, but a daemon that calls setsid (a build daemon, a dev server that double-forks) survives and can write into the reused checkout between the reset and the next probe. The docstring claim '(3) a process a probe left running takes no part' holds only for the group. State it as a limit, or re-create the checkout instead of resetting it."
  - "The plain code scan treats a file with a NUL in its first 8 KiB as binary, so a source checked out with working-tree-encoding=UTF-16 is skipped on the plain run. The re-run scans the UTF-8 blob, so it is stricter, not weaker. It is a gap in the plain sensor, not in R3."
  - "Already logged and not re-raised: D12 (a SIGTERM leaves the worktree registered), D17 (boot.py hint in the shared temp dir), D18/D21 (secret pattern breadth; formal evidence not scanned, full env), D19 (role permissions on KiroCrew/auditor Bash), D20 (actions pinned by tag). The TLC jar is sha256-pinned in check_models.py. The impeccable install is version-pinned and asks the user before its hook is kept. The governance hooks run only repo-local boot.py with session_id sanitised for file names."
  - "Verified as fixed: Security final 3 blocker 1 (--deployed now runs in tree.get(); a --deployed that needs an ignored helper fails 'the environment does not run HEAD'). Security final 3 blocker 2 is fixed only while git status sees every edit (the blocker above)."
```

Retrospective:
- C16 replaced "read the contract from HEAD" with "require git status to be clean". That trades a direct read for a proxy, and the proxy has documented blind spots.
- A guard should compare the bytes it consumes with HEAD, not ask a porcelain command whether they differ.
- The probe-side index-flag tricks were tested in earlier rounds. No round turned the same flags on the sensor's own inputs.
