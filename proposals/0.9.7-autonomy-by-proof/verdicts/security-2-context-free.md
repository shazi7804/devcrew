# Security verdict — final 2 (security role, Claude, at 83603a0)

Scope: main..83603a0 against proposals/0.9.7-autonomy-by-proof/requirements.md,
R3's *Threat model* included. Read: boot.py and its host adapter, the five
Claude Code hooks, check_live.py / check_formal.py / check_tasks.py (HeadTree,
drifted, probe, run_shell, --record), tools/check_models.py and the other CI
tools, both workflows, role frontmatter, the committed evidence. Everything was
run in a throwaway clone. Secret scan (regex over the diff and over
`git log -p main..83603a0`): clean. No dependency outside the stdlib. TLC is
pinned by sha256.

```yaml
verdict: FAIL
blockers:
  - requirement: R3
    clause: "Threat model: the sensors SHALL keep accidents out of a re-run (and the objective: no sensor path may modify or lose the user's work)"
    problem: >
      HeadTree's git calls (worktree add, rev-parse --absolute-git-dir, and the
      per-probe checkout -f / reset --hard / clean) inherit the caller's GIT_*
      variables. With GIT_INDEX_FILE (absolute) set, `worktree add` and the reset
      write HEAD's tree into the USER's index. With GIT_DIR set, self.gitdir
      resolves to the user's .git: the next get() deletes the user's .git/index
      and `checkout --detach` detaches the user's HEAD. Git itself exports an
      absolute GIT_INDEX_FILE to a pre-commit hook on `git commit -a` or
      `git commit <paths>`, so running a sensor's --rerun from a hook (an
      ordinary place to run a gate) makes git record an EMPTY commit. The
      user's staged changes are dropped from the commit and the index, a newly
      added file becomes untracked, and the sensor prints "live: ok". No probe
      misbehaves. This is an accident of the environment the sensor itself
      runs in, not something a probe command names. check_formal.run_cmd
      also hands the full environment, GIT_* included, to the check commands.
      The probe environment of check_live already strips these variables.
    repro: |
      git init u && cd u && mkdir -p .aidlc/evidence
      printf -- '- **R1** — x\n  - *Verify*: local\n' > .aidlc/requirements.md
      echo 'print(1)' > a.py && git add -A && git commit -qm x; H=$(git rev-parse HEAD)
      echo '{"id":"R1","verify":"local","command":"python3 a.py # a.py","target":"a.py","expect":"^1","observed":"1","result":"pass","sha":"'$H'","at":"x"}' > .aidlc/evidence/R1.json
      git add -A && git commit -qm ev
      printf '#!/bin/sh\npython3 <devcrew>/framework/tools/check_live.py --root . --rerun >&2 || exit 1\n' > .git/hooks/pre-commit; chmod +x .git/hooks/pre-commit
      echo 'print(2)' > b.py && git add b.py && echo more >> a.py
      git commit -aqm wip      # hook prints "live: ok"
      git show --stat HEAD     # empty commit; git status: " M a.py", "?? b.py"
      # variant: GIT_DIR=$PWD/.git check_live.py --root . --rerun (two local items)
      #   -> `git status`: "HEAD detached at <sha>", staged b.py now untracked
      # fix: drop every GIT_* variable (GIT_DIR, GIT_WORK_TREE, GIT_INDEX_FILE,
      #   GIT_OBJECT_DIRECTORY, GIT_COMMON_DIR, GIT_NAMESPACE, GIT_CEILING_DIRECTORIES,
      #   GIT_CONFIG*) from the env of git() / every HeadTree subprocess and from
      #   check_formal.run_cmd; add a self-test that runs --rerun with GIT_DIR and
      #   GIT_INDEX_FILE pointing at the repo and asserts its index and HEAD are unchanged
debts:
  - id: new-1 (medium)
    text: >
      HeadTree.get() runs a bare `git worktree prune` on the user's repository
      when a probe has disturbed the checkout's .git file. That prunes EVERY
      worktree of the user whose directory is missing at that moment (an
      unmounted volume, a moved directory), not only the sensor's own. Repro:
      user repo with `git worktree add ../wt -b side`, then `mv ../wt ../wt2`; a
      probe runs `rm .git && git init -q` in its cwd; the next get() runs
      prune; `mv ../wt2 ../wt`, and `git status` in it says "fatal: not a git
      repository". The worktree's index and HEAD are lost (the branch
      survives). Fix: remove only the sensor's own admin dir (or run
      `worktree remove --force` on its own path). D12's proposed fix
      ("git worktree prune on the next run") has the same breadth and should
      be narrowed the same way.
  - id: new-2 (low)
    text: >
      check_formal evidence (formal/<ID>.json, observed excerpts of the check,
      vacuity and conformance runs) is never secret-scanned, unlike
      check_live's. Its commands also run with the full environment, so a
      token can be echoed into a committed excerpt unflagged. Apply
      check_live.SECRET to the raw formal evidence. Strip the environment as
      probe() does: names the command uses, plus PATH/HOME/LANG.
  - already logged, re-confirmed, not new: D12, D17 (hint file in shared TMPDIR follows symlinks), D18 (secret pattern breadth), D19 (auditor keeps Bash; KiroCrew spawn/memory), D20 (actions pinned by tag, not sha)
notes:
  - "Re-run vs plain (R3: never pass what the plain run fails), checked on a clean checkout: the --rerun scan reads HEAD's blobs. It is at least as strict as the plain scan for symlinks (in-tree and escaping), case and Unicode collisions, filtered and LFS files, working-tree-encoding, sparse checkouts, non-UTF-8 names, an allow file outside the repo, and formal sources that are absolute, escaping or missing. I found no case where the re-run passes and the plain run fails."
  - "Probe isolation: check_live probes get an env allow-list, their own process group (killpg) and a reset detached checkout (index, sparse and worktree config dropped, clean -ffdx); hooks are off via core.hooksPath=/dev/null. --record refuses an excerpt that matches SECRET. Stated limits (C12, C15) are accepted as the CEO's threat model."
  - "boot.py: the claim is an atomic os.link of a staged file, claims are never deleted, it fails open on its own errors, and a missing session id elects nobody. It runs .aidlc/tools/board.py from the repo on SessionStart. That is the same trust as the project's .claude/settings.json hooks, so it is a note, not a finding."
  - "CI: both workflows have contents: read and no secrets; check_models verifies the TLC jar's sha256 before trusting a verdict."
  - "Committed evidence JSON holds no secrets and no machine paths."
retro:
  - The blocker came from running the sensor where users actually run gates (a git hook), not from reading the code.
  - The sensor's own git environment never appeared in the threat model's list of accidents; nine rounds focused on what probes do.
  - The fix is small and should carry a self-test so the GIT_* environment stays out.
```
