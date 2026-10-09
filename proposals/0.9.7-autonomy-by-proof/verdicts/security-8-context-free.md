# Security verdict — final 8 (security role, Claude, at 67b05bf)

Scope: main..67b05bf, judged against proposals/0.9.7-autonomy-by-proof/requirements.md,
with R3's *Threat model* read first. I read boot.py, its Claude Code adapter and
the five hooks. In check_live.py I read HeadTree, unclean, at_head, drifted,
run_shell, probe_env, moved and --record. I also read check_formal.py,
check_tasks.py (sensor and self-test), check_models.py, both CI workflows, the
role frontmatter, and each adapter's permission mapping.

What I ran, in a separate clone of the repo:
- the three sensor self-tests: 151 / 51 / 56 cases, each exits 0. check_neutral.py
  and check_repo.py are both ok;
- the boot.py race from hosts/claude-code.md: 32 concurrent starts gave exactly 1
  orchestrator, and 20 concurrent takeovers of one expired claim gave exactly 1
  winner. A 15-way beat stampede on an expired claim made exactly one new
  generation. Empty stdin exits 0;
- a secret grep over every added line in the range: no real credential and no
  home-directory path;
- a hatch probe of check_formal.hatches() over Lean, Coq, Dafny, Verus, TLA+,
  Agda and Quint forms;
- the two repros below, each run in its own throwaway repository.

I read verdicts/ only after this pass, and used it only as a regression list.
All five blockers of the final review are fixed at 67b05bf:
- boot.py treats an unreadable claim as held (ScanFail is in Election.tla);
- moved() runs at the end of check_tasks and check_formal;
- the scan catches TLA+ AXIOM, ASSUME and ASSUMPTION;
- the TASKS template signs design.md;
- check_neutral covers .tla and .cfg files.

```yaml
verdict: FAIL
blockers:
  - requirement: R3 (Threat model -- "The sensors SHALL keep accidents out of a re-run"; the re-run's HeadTree) and R4 (check_tasks --rerun, which drives it)
    clause: a re-run runs every probe in a throwaway checkout of HEAD and resets it before each probe; it must never act on the user's repository
    problem: >
      HeadTree._add records the checkout's git dir as
      Path(out(git(tree, "rev-parse", "--absolute-git-dir")).strip()). It
      checks neither the exit code nor the value. If that one git call fails
      (this run already had git stop mid-session, see C6), the value is
      Path(''), which is '.': the process's working directory, which is the
      user's repository root when the sensor runs from there. A later get()
      takes the rebuild path when the checkout's .git differs or a submodule
      .git appears. The trigger can be an ordinary probe that runs
      `git submodule update --init`, the same case the self-test uses. The
      rebuild path then calls shutil.rmtree(self.gitdir, ignore_errors=True),
      which is rmtree('.'). That deletes the user's whole working tree,
      .git included. The non-rebuild path unlinks ./index,
      ./info/sparse-checkout and ./config.worktree in the working directory.
      Everywhere else, a failed git call in the sensors raises SystemExit and
      fails closed; this call fails open into a recursive delete. Security
      final 7 raised this as a debt, and it is still not logged in TASKS.md.
      With a repro that wipes the repository, I am raising it to a blocker.
      Fix: in _add, check the return code and refuse any value that is not
      an absolute path under `git rev-parse --git-common-dir`/worktrees/
      (raise SystemExit). Before every unlink or rmtree in get(), assert the
      same thing. Add a self-test case with a git on PATH that fails
      --absolute-git-dir and a probe that initialises a submodule, asserting
      the repository is untouched.
    repro: |
      # W = a scratch dir; $W/bin/git fails only the --absolute-git-dir call:
      #   for a in "$@"; do [ "$a" = "--absolute-git-dir" ] && exit 69; done; exec <real git> "$@"
      # R = a repo with a submodule at vendor/lib, work.txt, and
      #   .aidlc/requirements.md: R1, R2, each `*Verify*: local`
      # .aidlc/evidence/R1.json: local, command
      #   "git -c protocol.file.allow=always submodule update --init -q && echo ok",
      #   expect "ok", sha = HEAD
      # .aidlc/evidence/R2.json: same, command "echo ok"
      # everything committed; git status is clean
      cd "$R"; ls -A                    # .aidlc .git .gitmodules vendor work.txt
      PATH="$W/bin:$PATH" python3 <sensors>/check_live.py --rerun
      #   -> "cannot check out HEAD of <R> for a re-run"
      ls -A                             # -> (empty): work.txt, .git, everything gone
      # also reproduced with R1's probe "rm -f .git; echo ok" in place of the
      # submodule init
  - requirement: R4 (the check_tasks sensor and its --self-test) and R5 ("each adapter installs check_tasks.py and runs its self-test at verify", inside the user's project)
    clause: a sensor's git calls must not touch the user's index, HEAD or branch when they run from a git hook (the rule git_env() states and check_live's self-test asserts)
    problem: >
      check_tasks.py --self-test makes its fixtures with 20 bare
      subprocess.run(["git", "-C", d, ...]) calls. These inherit the
      caller's environment: no git_env(), and no core.hooksPath=/dev/null.
      git exports GIT_DIR and GIT_INDEX_FILE to hooks. A pre-commit hook or
      any wrapper that runs the self-test therefore points the fixture's
      `add -A` and `commit` at the user's repository. The user's index is
      replaced by the fixture tree, which stages the deletion of every user
      file. A commit "x" lands on the user's current branch. With
      GIT_INDEX_FILE alone, the user's index is left pointing at objects
      that do not exist ("fatal: unable to read <oid>"), and what the user
      had staged is lost from it. check_live and check_formal do not do
      this, because their self-tests go through git_env(). The framework
      itself names this hazard (git_env's docstring; check_live's case "a
      re-run from a git hook's environment"), so check_tasks is the one
      sensor that misses it. Fix: route every self-test git call through
      check_live.git(), with core.hooksPath=/dev/null and
      commit.gpgsign=false. Add a case that runs the self-test with GIT_DIR
      and GIT_INDEX_FILE pointing at a scratch repository, and asserts that
      repository's HEAD, branch and index are unchanged.
    repro: |
      # R = any repo with one commit and a staged edit to work.txt
      GIT_DIR=$R/.git GIT_INDEX_FILE=$R/.git/index python3 <sensors>/check_tasks.py --self-test
      git -C $R log --oneline     # -> a new commit "x" on the user's branch
      git -C $R status --short    # -> " D req/requirements.md ...", "?? work.txt": the user's file left the index
      # GIT_INDEX_FILE=$R/.git/index alone -> git -C $R status: "fatal: unable to read <oid>"
      # the same environment with check_live.py / check_formal.py --self-test leaves R unchanged
debts:
  - "R10 'and their kin': the escape-hatch scan misses Lean `sorryAx` (`\\bsorry\\b` does not match it), Coq `Admit Obligations` (the rule is a case-sensitive `admit`), Dafny `{:extern}` and bodiless lemmas, Verus `assume_specification` / `external_fn_specification` / `#[verifier(external)]`, and Agda `postulate`. Every hatch R10 names is caught. Add these, with one self-test case each (medium)."
  - "Unlogged since Security final 7, still present: (a) check_tasks has no --live-host, so a Done live item outside the environment's hosts passes check_tasks while check_live --live-host fails it; (b) --record writes evidence/<ID>.json through an in-tree symlink, overwriting the tracked file it points to; (c) a probe that daemonises with setsid survives run_shell's process-group kill and can serve a later probe, and HeadTree's docstring does not say so; (d) boot.py runs int() on DEVCREW_STALE_SECONDS / DEVCREW_MARGIN_SECONDS at import, so DEVCREW_STALE_SECONDS=45m exits 1 with a traceback, which breaks 'always exits 0' (low). Log each as a Dn item."
notes:
  - "Already logged, re-confirmed, not re-raised: D12 (a SIGTERM leaves the worktree registered), D17 (boot.py's hint follows symlinks in the shared temp dir), D18, D21 and D22 (secret-pattern coverage in evidence, formal records and failed-probe output), D19 (KiroCrew spawn/memory for every role; the Claude Code auditor keeps Bash), D20 (actions pinned by tag)."
  - "R3 wording, as in final 7: a re-run passes a local item whose stored evidence is stale but whose probe passes on HEAD's checkout. That is stronger proof (C8), not a weaker gate. Apart from that, I found no case where a re-run passes what the plain run fails. On --src, symlinks, case and NFD clashes, sparse and skip-worktree flags, filters, working-tree-encoding, an ignored allow or requirements file, and moved HEAD, the re-run is equal or stricter."
  - "check_live.py --self-test run with GIT_DIR / GIT_INDEX_FILE set leaves the user's repository alone, but it reports one false failure ('a probe that hides a committed fake by skip-worktree'): its fixture helpers inherit GIT_*. This is harmless; it goes away with the same fix as blocker 2."
  - "Hooks and boot.py: link(2) CAS on fully written generations; nothing else in the tree is touched; always exits 0 except debt (d). It runs the repo's own .aidlc/tools/board.py at SessionStart, the same trust level as the hooks themselves."
  - "Supply chain: the sensors and boot.py are stdlib-only (N3). TLC is pinned by version and sha256, and check_models.py verifies the hash before use, so a poisoned cache is refused. Both workflows have contents: read and no pull_request_target. impeccable is pinned at 4.1.0 with no integrity hash, and its edit hook needs the user's yes."
  - "Secrets: no credential in any added line. The evidence and formal records hold no machine path."
```

Retrospective: the framework knew the git-hook hazard and the fail-closed rule,
and applied both everywhere except one self-test file and one unchecked
`rev-parse`. Both slipped through because no case ran the sensor while git
itself was misbehaving. Any sensor path that ends in rmtree or a git write
should be tested with a git that fails, and with a hook's environment.
