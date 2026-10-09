# Security verdict — final 7 (security role, Claude, at fe47490)

Scope: main..fe47490, judged against proposals/0.9.7-autonomy-by-proof/requirements.md
with R3's *Threat model* first. Read: boot.py, its Claude Code adapter and the
five hooks; check_live.py (HeadTree, unclean, at_head, drifted, run_shell,
probe_env, moved, --record); check_formal.py; check_tasks.py; check_models.py;
the CI workflows; the role frontmatter and each adapter's permission mapping.

Ran in a separate clone:
- the three sensor self-tests (151 / 47 / 54 cases, all exit 0);
- check_neutral.py and check_repo.py (both ok);
- check_tasks on this proposal's TASKS.md (tasks: ok);
- a secret grep over every added line in the range (no real credential);
- a boot.py race: 30 concurrent starts gave exactly one orchestrator, and 30
  concurrent takeovers of one expired claim gave exactly one winner;
- the repros below.

I read verdicts/ only after this pass, and used it only as a regression list.

```yaml
verdict: FAIL
blockers:
  - requirement: R3 (Threat model -- "On a re-run they SHALL never pass what the plain run fails"; "Done only when its live and formal evidence are fresh at HEAD"); R4 (check_tasks is the sensor for R1-R3)
    clause: a passing check_tasks --rerun is the Ship batch's proof that every Done item is proven at HEAD
    problem: >
      Security final 6 found that a re-run proves the HEAD it pinned, not the
      HEAD that exists when it ends. The fix (95f04ca) added moved() to
      check_live._run only. check_tasks.check never calls it, and neither does
      check_formal.check. Both build one HeadTree, run every probe and formal
      command on the pinned commit, and then return no hit when HEAD moved
      while they ran. drifted() compares against the live HEAD, so an item
      checked after the move is stale. For a local item a passing re-run on
      the pinned commit counts as fresh, so the item still passes. For a
      formal item, drifted() runs before the commands, so a move during the
      check or vacuity run goes unseen. The result: check_tasks --rerun prints
      "tasks: ok" and exits 0, while HEAD is a commit that no probe ran on and
      that both the plain run and a fresh re-run fail. The trigger is an
      accident this release exists to govern: a second session commits during
      a re-run that takes minutes (QA timed this one at 8 min 40 s). check_live
      --rerun in the same situation correctly reports "HEAD moved". Fix: call
      check_live.moved(root, tree) at the end of check_tasks.check and of
      check_formal.check when rerun is set. Add a self-test case to each,
      modelled on check_live's "HEAD moved during a re-run" case.
    repro: |
      # fresh repo; .aidlc/tools/ = the three sensors
      # requirements.md: R1, R2, each `*Verify*: local`, `*Property*: none — prose`
      # app.sh: `echo temp: 21`
      # TASKS.md: Signed: requirements.md sha256:<12>; R1 and R2 under ## Done
      # evidence/R1.json: command "sleep 4; sh app.sh", expect "temp: \d+", sha = HEAD
      # evidence/R2.json: command "sh app.sh", same expect, sha = HEAD
      # everything committed; git status is clean
      python3 .aidlc/tools/check_tasks.py --rerun > out.txt &
      sleep 1.5; echo 'echo broken' > app.sh; git commit -qam "another session's commit"; wait
      cat out.txt                            # -> tasks: ok   (exit 0)
      python3 .aidlc/tools/check_tasks.py    # same HEAD, plain -> R1, R2 stale (exit 1)
      python3 .aidlc/tools/check_tasks.py --rerun   # -> re-run exited 1: broken (exit 1)
      # the same setup with check_live.py --requirements requirements.md --rerun
      #   -> "HEAD moved during the re-run" (exit 1)
debts:
  - "Security final 6's three debts are still open, and none is logged in TASKS.md: (a) check_tasks has no --live-host, so a Done live item whose target is outside the environment's hosts passes check_tasks while check_live --live-host fails it; (b) --record writes evidence/<ID>.json through an in-tree symlink, overwriting the tracked file it points to; (c) a probe that daemonises with setsid survives run_shell's process-group kill and can serve a later probe, and HeadTree's docstring does not say so. Log them as Dn items."
  - "HeadTree._add stores the worktree's git dir from `git rev-parse --absolute-git-dir` without checking it. If that call fails (git did fail mid-session in this run, see C6), the value is Path('.'). get() then unlinks ./index, ./info/sparse-checkout and ./config.worktree in the process's working directory, and the rebuild path runs shutil.rmtree on it. Refuse anything that is not an absolute path under `git rev-parse --git-common-dir`/worktrees/."
  - "boot.py parses DEVCREW_STALE_SECONDS and DEVCREW_MARGIN_SECONDS with int() at import time, before main()'s try. A malformed value exits 1 with a traceback, which breaks the 'always exits 0' contract. Claude Code does not block on exit 1, so this is low severity."
notes:
  - "Wording: R3 says a re-run never passes what the plain run fails. Literally, check_live --rerun and check_tasks --rerun do pass a local item whose stored evidence is stale, if its probe passes on a checkout of HEAD (reproduced; the plain run says stale). By design (C8) that is stronger proof, not weaker, so I do not count it as a breach. Tightening the text to 'never weaker than the plain run' (C13's own words) would close the gap between the contract and the code."
  - "unclean() skips any status line under __pycache__/ or ending in .pyc, tracked files included. A modified tracked file there lets a re-run proceed while the plain scan reads the working-tree copy. The re-run judges HEAD correctly, so this is not a breach. Narrowing the skip to untracked entries would be cleaner."
  - "R8 / SKILL.md Phase 5: an irreversible action that is not on the pre-authorized list may be taken on the role's own judgment and recorded afterwards as a Cn. This removes a stop, but it was ruled by the CEO and recorded under invariant 8, so it is not a weakened gate. Security advice: make the default for an unlisted irreversible action 'do not do it; record a Cn'."
  - "Already logged, re-confirmed, not re-raised: D12, D17, D18, D19 (KiroCrew spawn/memory for every role; the Claude Code auditor keeps Bash), D20 (actions pinned by tag), D21, D22."
  - "User's work: apart from --record's evidence file, the sensors write nothing to the user's index, refs or working tree. git_env strips GIT_*. HEAD's index is built in a private GIT_INDEX_FILE. The probe checkout is reset under an explicit --git-dir/--work-tree with hooks, fsmonitor and sparse checkout disabled. rmtree skips symlinked siblings and the checkout path. Each probe gets its own TMPDIR (check_formal's commands too) and only PATH, HOME, the locale and the variables it names."
  - "Hooks and boot.py: boot.py always yields to the session. Claims are made by link(2) of a fully written file, generations are never deleted, and nothing else in the tree is touched. It runs the repo's own .aidlc/tools/board.py at session start, which is the same trust level as the hooks. The pin file can be written by any session that has a write tool; it is a human escape hatch, not an access control."
  - "Supply chain: the sensors and boot.py use only the standard library (N3). TLC is pinned by version and sha256, and check_models.py verifies the hash before any use, so a poisoned cache entry is refused. Both workflows have contents: read and use no pull_request_target. impeccable is pinned at 4.1.0 (npm, no integrity hash; its git-tag fallback is mutable), and its edit hook goes to settings.local.json only after the user says yes."
  - "Secrets: no credential in any added line. The only matches are the self-test's seeded fakes and earlier verdicts quoting them. No home directory or machine path appears in evidence or formal records."
```

Retrospective: a fix for a sensor's isolation has to land in every sensor that
re-runs, not just the one the repro named. check_live got the pinned-HEAD guard,
but check_tasks, which is the actual Ship-batch gate, did not. Each new
re-run guard should come with a self-test case in all three sensors.
