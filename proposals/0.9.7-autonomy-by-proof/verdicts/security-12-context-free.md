# Security verdict — final 12 (security role, Claude, at 2c1049f)

Scope: main..2c1049f, judged against proposals/0.9.7-autonomy-by-proof/requirements.md
(R3's *Threat model* first, then R6 / N1), the AGENTS.md invariants, and the
security remit: the hooks and boot.py, every path that runs a shell command,
file and git operations on the user's repo, --deployed and --record, secrets in
evidence, the permission boundaries of the installed roles, and the supply chain.

Read: boot.py, hosts/claude-code.boot_host.py and the five hooks in
hosts/claude-code.md; check_live.py (unclean with the new info/attributes
refusal, at_head, HeadTree.files/_filtered/_add/get/close, _drifted, contract,
run_shell, probe_env, moved, the --deployed loop, --record, the code scan);
check_formal.py; check_tasks.py; tools/check_models.py; both CI workflows; every
role's frontmatter against main; the gate text in orchestrator, devops, release,
SKILL.md (§ Batches and interrupts, Phases 5 and 6), mobile-release,
requirements.template.md and the three host adapters.

Ran, in a throwaway clone and in scratch repositories, never in the user's repo:
- the three self-tests at 2c1049f: check_live 159 cases, check_tasks 59 and
  check_formal all ok.
- the election race from the adapter: 30 concurrent starts, then 30 concurrent
  takeovers of an expired claim. Exactly one orchestrator each time, and
  generations 1 and 2 left as evidence.
- two repros of the blocker below (an attributes file named in config, and a
  filter defined after checkout), plus a same-size, mtime-restored edit with
  trustctime=false and checkStat=minimal. That last one is caught: status
  shows it and the re-run refuses.
- check_tasks --rerun on a live Done item whose probe passes. It crashes (the
  debt S12-2 below).

I read verdicts/ only after this pass, and used it only as a regression list.

```yaml
verdict: FAIL
blockers:
  - requirement: "R3 (Threat model)"
    clause: >
      "On a re-run they SHALL never pass what the plain run fails -- except a
      stale record the re-run itself proves again at HEAD". Also "The sensors
      SHALL keep accidents out of a re-run". Round 4's fix ("a re-run refuses
      the repository's own info/attributes", C22) answers reviewer round 12's
      blocker. That blocker's required change was to resolve attributes and
      filtered content from isolated HEAD-only git metadata.
    problem: >
      The fix refuses one file, .git/info/attributes. Other git metadata outside
      HEAD's tree still decides what a re-run's scan reads.
      HeadTree.files() reads every filtered file through _filtered()
      (check-attr --source=HEAD) and `cat-file --filters`. Both run against the
      user's repository with the user's config. So the re-run reads the bytes
      the CURRENT config would smudge, while the plain scan reads the bytes on
      disk. Two configurations make them differ, and git status reports the
      tree clean in both, so unclean() lets the re-run start:
        (a) an attributes file named by core.attributesFile, or the default
            per-user $XDG_CONFIG_HOME/git/attributes. This is the same channel
            as info/attributes, at lower precedence.
        (b) a filter driver defined, or redefined, after checkout, for a
            filter=<x> attribute that HEAD's own committed .gitattributes
            already names. A clone made before `git lfs install`, or before a
            filter was set up, is this case. It is an accident, not a probe
            that sets out to fool the sensor: no probe runs, and no git object,
            ref or config is rewritten by a probe.
      In both cases the plain run fails on the fake in the working tree and the
      re-run passes. check_tasks --rerun (the Ship batch) and check_formal's
      escape-hatch scan read through the same HeadTree.files(), so they inherit
      the gap. For example, a `sorry` that a filter strips is not seen. A
      working-tree-encoding attribute set the same way makes the re-run read a
      file as binary and skip it.
      Fix: on a re-run, for every file a filter (or any attribute not from
      HEAD's tree) touches, scan the raw blob, the filtered output and the
      working-tree bytes, and fail on a hit in any of them. Or refuse the
      re-run when the filtered output differs from the working-tree file. Or do
      what reviewer 12 asked: read attributes from HEAD's tree only, with no
      core.attributesFile, no XDG attributes and no filter that HEAD's
      checkout did not use. Add self-tests for (a) and (b).
    repro: |
      git init -q r && cd r && mkdir -p .aidlc/evidence src
      printf -- '- **R1** — x\n  - *Verify*: local\n' > .aidlc/requirements.md
      echo 'export const temp = mockTemp();' > src/app.js
      echo '*.js filter=build' > .gitattributes        # variant (b); omit for (a)
      git add -A && git -c user.name=t -c user.email=t@t commit -qm a
      # .aidlc/evidence/R1.json: verify local, command "echo 'temp: 21'",
      #   expect "temp: \\d+", observed "temp: 21", sha = that commit; commit it
      # (b) a filter defined after checkout:
      git config filter.build.smudge 'sed s/mockTemp/realTemp/'
      git config filter.build.clean cat
      # (a) instead: echo '*.js filter=qq' > ../attrs;
      #     git config core.attributesFile $PWD/../attrs; define filter.qq.*
      git status --porcelain                          # (empty: the tree is clean)
      python3 check_live.py --root .                  # src/app.js:1: `mock` -- rc 1
      python3 check_live.py --root . --rerun          # live: ok -- rc 0
debts:
  - id: S12-1
    severity: medium
    problem: >
      This is S11-2, carried over: it is still unfixed and not in TASKS.md. The
      general judgment rule does not exclude Ship-batch items. That covers
      SKILL.md § Batches ("an irreversible action not on the pre-authorized
      list (do it or not -- either way a Cn)"), SKILL.md Phase 5, and
      orchestrator.md ("Irreversible actions ... One that is not on it is a
      judgment: decide (do it, or don't)"). It also covers
      requirements.template.md ("An empty table is a valid answer: then every
      such action is decided by the role about to act") and the
      mission-control skill. Read alone, each of these lets a store
      submission, a signing step or the merge be self-decided as a Cn.
      release.md, mobile-release and the merge rules (SKILL.md, reviewer.md,
      invariant 4) override it for each item, so no R6 item is dropped today.
      But every role loads SKILL.md, and the template is what a project signs.
      Add "except a Ship-batch item, which waits for the Ship batch unless it
      is pre-authorized". The open production-deploy question stays C21.
  - id: S12-2
    severity: medium
    problem: >
      check_tasks.check passes `False` as check_live's `proven` set. When a live
      Done item's re-run probe passes, `h in proven` raises TypeError
      (check_live.py:833), so `check_tasks --rerun`, the command the Ship batch
      requires, crashes with a traceback on any project with a live Done item.
      It fails closed, so it is not a safety loosening. But the Ship gate cannot
      run for live work, and that invites someone to skip it. Pass
      `frozenset()`, and add a self-test with one live Done item. Repro: a live
      R1 in Done, its probe `echo https://api.github.com/zen 'temp: 21'`, then
      `check_tasks --rerun` exits 1 with "argument of type 'bool' is not a
      container or iterable". Security 11 read this path as "only local records
      can be re-proved". It does not degrade that gracefully: it crashes.
  - id: S12-3
    severity: low
    problem: >
      get() puts the clone's config back with write_bytes, which follows a
      symlink. If a probe replaces .git/config in the clone with a link, the
      sensor itself writes the clone's config through it, for example over the
      user's .git/config. R3 rules this out of scope (a probe rewriting git's
      config), but the sensor should unlink and recreate the file rather than
      write through it. The same goes for the exists()/unlink() of the dropped
      git files.
notes:
  - "Round-4 fixes verified: the clone's origin is removed after checkout (S11-1 closed). Its config is put back and info/attributes, config.worktree, sparse-checkout and index are dropped before each reset, with clean run before checkout. --deployed now proves only the hosts its own URLs name, and a live record is fresh only when its target host is among them (Security 11's blocker is closed). A probe's command may also reach a third-party host that no --deployed proves. I read that as the service's dependency, not its environment."
  - "R6 / N1 sweep: no Ship item became a role's own judgment in a role prompt that governs that item. release.md and mobile-release keep store submission, rollout promotion and signing on the Ship batch or the pre-authorized list. Missing signing material is the missing-service interrupt. The merge stays with the CEO. Pre-authorizing a Ship item in the Intent batch is still a CEO signature. The wording gap is S12-1, and the production-deploy reading is C21."
  - "User's repo: the sensors only read it (status, ls-files, cat-file, diff, check-attr, merge-base, clone --shared, read-tree into a temp index). The one write is --record, which refuses a symlinked record, runs only after `moved()` and a secret scan of the excerpt, and needs a clean tree at start. Every reset, clean or rmtree targets only the clone under its own temp dir. A checkout swapped for a symlink to elsewhere is refused. A probe can still push or write by absolute path, a stated limit (C12, HeadTree's docstring). The self-tests scrub GIT_* and disable hooks, and their fixtures live in TemporaryDirectory."
  - "Election: the link(2) generation CAS held in every race I ran. An unreadable claim is treated as held, ORCHESTRATOR.top is only a hint, and release targets the generation the session read, so it cannot release a successor's claim. The hooks take session_id from stdin and always exit 0. board.py at SessionStart is repository code in the same trust domain as the hooks."
  - "Secrets: no credential in any added evidence or formal record. Open and not re-raised: D18, D21 and D22. D22 also covers the 80 chars printed for a failed --deployed."
  - "Permissions: no frontmatter grant widened against main. The reviewer has read/search/web and memory none. The auditor has no write or edit tool; its Bash is D19. Supply chain: the TLC jar is sha256-checked before use, both workflows are contents: read on pull_request, the sensors are stdlib only, and impeccable is pinned @4.1.0, with its hook installed only after the user agrees. Actions are pinned by tag (D20)."
  - "Already logged, not re-raised: C12, C21, D17, D18, D19, D20, D21, D22, D26, D27."
```

Retrospective: the round-4 fix shut the one file the reviewer named. The class
it belongs to is "git metadata outside HEAD's tree that changes how a blob
reads", and it has more members than that file. Next time, test a fix against
the reviewer's required change, not against the repro. A sensor's own
fail-closed crash (S12-2) is still a gate nobody can run.
