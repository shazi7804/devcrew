# Security verdict — final 11 (security role, Claude, at 22565c0)

Scope: main..22565c0, judged against proposals/0.9.7-autonomy-by-proof/requirements.md
(R3's *Threat model* first, then R6 / N1), the AGENTS.md invariants, and the
security remit: the hooks and boot.py, every path that runs a shell command,
file and git operations on the user's repo, secrets in evidence, the permission
boundaries of the installed roles, and the supply chain.

Read: boot.py, hosts/claude-code.boot_host.py and the five hooks; check_live.py
(HeadTree with the new shared clone, get()/reset, unclean, at_head, _drifted,
contract, run_shell, probe_env, moved, the --deployed loop, --record, the code
scan); check_formal.py; check_tasks.py; tools/check_models.py; both CI
workflows; every role's frontmatter compared with main; and the gate text in
orchestrator, devops, release, architect, designer, analyst, SKILL.md,
mobile-release and the three host adapters.

Ran, in a throwaway clone and never in the user's repo:
- the three self-tests: check_live 155 cases, check_formal 66, check_tasks 59,
  all ok. check_neutral and check_repo are ok too.
- check_tasks --self-test with GIT_DIR, GIT_WORK_TREE and GIT_INDEX_FILE
  pointed at a decoy repo that held a stash, a branch, a staged file and an
  unstaged edit. Its refs, stash, worktree list, status, index hash and file
  content were byte-identical before and after.
- the adapter's race, nine rounds. Each round ran 32 concurrent starts, then 20
  concurrent takeovers of an expired claim, then the expired holder's beat
  racing 10 newcomers. Every round produced exactly one orchestrator. When the
  holder lost, it was told it is no longer the orchestrator. Empty stdin,
  garbage stdin and an unknown mode all exit 0.
- three repros: --deployed scope (the blocker), a probe pushing through the
  clone's origin, and clone config persisting across resets.
- a secret-pattern sweep over every added line of the diff. The only hit is a
  self-test fixture.

I read verdicts/ only after this pass, and used it only as a regression list.

```yaml
verdict: FAIL
blockers:
  - requirement: "R3 (Threat model) + invariant 10"
    clause: >
      "On a re-run they SHALL never pass what the plain run fails -- except a
      stale record the re-run itself proves again at HEAD (a local probe, or a
      live one whose environment --deployed proves runs HEAD)"; invariant 10:
      each requirement needs fresh evidence from the real, deployed service.
    problem: >
      `proven` is one global flag. It is set once every --deployed command has
      printed HEAD's sha (check_live._run). After that, every live record in
      the run counts as re-proved at HEAD, whatever service it probes. Nothing
      ties a requirement's target host, or the URLs in its probe, to a host
      that a --deployed command asked. The docstring says "one per service",
      but the code does not enforce it. So in a project with two services,
      passing the version probe of only one of them is enough. A re-run then
      clears the stale hit of a requirement whose service still runs an old
      build, and --record stamps that record sha = HEAD. From then on the plain
      run, check_tasks and the Ship batch's check_tasks --rerun all accept it as
      fresh. That record's environment was never proven to run HEAD, so it is
      outside R3's one exception. The cause is an accident, not a probe that
      sets out to fool anything: --deployed is a gate-time argument, not a
      committed command, so no reviewer reads its absence in the diff. No
      earlier verdict raised this. Security 10 judged the exception "by design"
      without checking which environment the proof covered.
      Fix: count a live record as fresh only when its target host (and each
      URL host in its command) equals, or fnmatch-es, a host asked by a
      --deployed command that printed HEAD. Add a self-test with two services
      and one --deployed.
    repro: |
      # stdlib harness; resolve() patched to a public IP, as the self-test does
      repo: .aidlc/requirements.md "- **R1** — a" / "- **R2** — b" (live)
      evidence R1.json: target https://api.a.acme.io/v1,
        command "echo https://api.a.acme.io/v1 'temp: 21'", sha = v1 commit
      evidence R2.json: same with api.b.acme.io; commit; then change src/a.js
        and commit (HEAD = H)
      check_live.run(d)
        -> R1 stale, R2 stale                                   (plain: FAIL)
      check_live.run(d, rerun=True,
          deployed=["echo https://api.a.acme.io/version H"])   # only A proven
        -> []                                                   (re-run: PASS)
      same with record=True -> R2.json sha == H                 (True)
debts:
  - id: S11-1
    severity: medium
    problem: >
      The shared clone keeps `origin` = the user's repository. A probe that
      runs `git push origin ...` (or `--delete`, or `-f` to a branch that is
      not checked out) writes the user's refs through a remote the sensor
      itself configured. Repro: a local R1 whose command is `git commit
      --allow-empty -m probe-commit && git push -q origin
      HEAD:refs/heads/main-probe; echo 'temp: 21'`. `check_live --rerun`
      reports `[]`, and the user's repo now has refs/heads/main-probe. A probe
      is trusted and should be read-only, so this is not a blocker. But the
      commit message's "nothing registered in the user's repository" is not
      true of refs a push can reach. HeadTree's docstring covers it only
      loosely ("the repository it was cloned from, by path"). Fix cheaply:
      `git remote remove origin` in the clone after the checkout, or set a
      `pushurl` that cannot resolve.
  - id: S11-2
    severity: low
    problem: >
      The SKILL.md § Batches judgment paragraph ("an irreversible action not
      on the pre-authorized list (do it or not -- either way a Cn)") and the
      matching sentence in hosts/aidlc-mission-control.skill.md do not exclude
      a Ship-batch item. release.md and mobile-release/SKILL.md do exclude it,
      correctly: a store submission or rollout promotion waits for the Ship
      batch. Every role loads SKILL.md, so make the general rule say "except a
      Ship-batch item". This is separate from C21, the open question about a
      production deploy.
notes:
  - "R6 / N1 sweep: no Ship item became a role's own judgment in a role prompt. release.md and mobile-release keep store submission, rollout promotion and production release on the Ship batch or the pre-authorized list. Missing signing material is the missing-service interrupt. The market verdict and platform strategy are in the intent batch, the prototype and standards in the design batch, and the merge stays with the CEO (reviewer.md, every adapter). The production-deploy reading is C21, an open Cn and not re-raised. S11-2 is a wording gap in the generic rule."
  - "Re-run monotonicity, apart from the blocker: on a re-run the evidence, allow file, formal sources, requirements, TASKS.md and signed files come from HEAD, or are at_head-checked. Each divergence I tried makes the re-run stricter: an untracked, ignored or out-of-tree stand-in, a symlinked evidence dir, a case clash, a w-t-encoding file, a sparse or skip-worktree index, or a subdirectory --root. check_formal never clears staleness on a re-run. check_tasks passes proven=False, so for check_tasks itself only local records can be re-proved. An orphan (rewritten-history) record is cleared like a stale one. I read that as within 'proving HEAD is what a re-run is for'."
  - "Reset of the clone: get() refuses to clean or remove anything whose .git does not resolve to the clone's own git dir under the temp dir. A probe that swaps the checkout for a symlink to the user's repo is refused, not followed. The clone's .git/config and .git/info/attributes do survive resets. Repro: `git config core.autocrlf true` plus `* text eol=crlf` in info/attributes, after which the next probe sees CRLF. R3 places rewriting git's config out of scope, and qa-6 logged the class under C12, so this is not a new finding."
  - "User's repo: the sensors only read it (status, ls-files, cat-file, diff, check-attr, clone --shared, plus read-tree into a temp index). The one write is --record to <evidence>/<ID>.json, on a tree that was clean at start. The self-tests scrub GIT_* and disable hooks; the decoy run above confirms it. Security 10's stash blocker is fixed: the clone has its own refs and stash, and the self-test covers the stash/branch idiom."
  - "Election: the link(2) generation CAS holds under every race I ran, including the expired holder's resume against newcomers. An unreadable top claim is treated as held. ORCHESTRATOR.top is only a hint. The hooks pass session_id from stdin and always exit 0. boot.py runs the repo's own .aidlc/tools/board.py at SessionStart, which is the same trust domain as the hooks in .claude/settings.json. A session id containing a newline would misparse its own claim, but host ids are UUIDs, so this is not reachable."
  - "Secrets: no credential in any evidence or formal record or in the added lines. Still open and not re-raised: D18 (narrow pattern), D21 (formal evidence not scanned), D22 (unredacted failure output, which also covers the 80 chars printed for a failed --deployed)."
  - "Permissions: no role's frontmatter grant widened against main. The designer gained the impeccable skill, pinned @4.1.0 in its body and in all three adapters, so Security 10's S10-1 is fixed (transitive npm deps are still unlocked). The reviewer is read/search/web with memory none. The auditor has no write/edit; its Bash is D19."
  - "Supply chain: the TLC jar is sha256-pinned and checked before use, and a missing or wrong jar exits 2 (no verdict). Both workflows are `contents: read` on pull_request, not pull_request_target. The sensors are stdlib only. Actions are pinned by tag (D20)."
  - "Already logged, not re-raised: D17, D18, D19, D20, D21, D22, D26 (check_tasks has no --live-host), D27, C12, C21."
```

Retrospective: the shared clone closed the stash class cleanly. The most useful
check was asking what each re-run exception actually proves, and for which
service. Next time, start the re-run sweep from the arguments a gate passes on
the command line, not only from what the diff commits.
