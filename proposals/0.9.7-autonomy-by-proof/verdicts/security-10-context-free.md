# Security verdict — final 10 (security role, Claude, at 2bf32b9)

Scope: main..2bf32b9, judged against proposals/0.9.7-autonomy-by-proof/requirements.md
(R3's *Threat model* first, then R6 / N1), AGENTS.md invariants 1-11, and the
security remit: the hooks and boot.py, every path that runs a shell command,
file and git operations on the user's repo, secrets in evidence, the permission
boundaries of the installed roles, and supply chain.

Read: check_live.py (HeadTree, unclean, at_head, _drifted, contract, run_shell,
probe_env, moved, --record, the code scan), check_formal.py, check_tasks.py,
boot.py + hosts/claude-code.boot_host.py + the five hooks, Election.tla's
process model, tools/check_models.py, both CI workflows, every role's
frontmatter, and the gate text in orchestrator / devops / release / architect /
designer / analyst, SKILL.md, mobile-release and the three host adapters,
compared with main.

Run, in a throwaway clone (never the user's repo):
- the three self-tests, with GIT_DIR / GIT_WORK_TREE / GIT_INDEX_FILE aimed at a
  sacrificial copy: check_live 153 cases, check_formal 66, check_tasks 59, all
  ok. Afterwards that copy's HEAD, refs, worktrees, stash and config were
  unchanged (so S9-1 is fixed). The same three ran again with curl and wget on
  PATH replaced by logging shims, and no network call was made.
- the adapter's race, three rounds: 32 concurrent starts gave 1 orchestrator,
  20 concurrent takeovers of an expired claim gave 1 winner, and 40 mixed beats
  on a second expired claim made exactly one new generation;
- the secret pattern against common credential shapes (D18, confirmed:
  Basic auth, AIza, sk_live_, Slack webhook, JWT and glpat- all pass unflagged);
- the stash repro below.

Re-run monotonicity, checked path by path. On a re-run the evidence, the allow
file, the formal sources and the requirements are read from HEAD's blobs; on a
plain run they are read from disk. In each of these cases the re-run fails
where the plain run reads a file, never the other way: an untracked or ignored
stand-in, a symlink out of the tree, a case clash, a filtered file, and an
absolute or `..` source. `_drifted` diffs both the working tree and HEAD, and
`unclean`, `at_head` and `moved` bracket every re-run. One way a re-run passes
what the plain run fails is by design: stale or orphan evidence that a re-run
just proved fresh. That is not an accident path. Apart from it I found none.
User work, however, can be lost (blocker 1).

The verdicts/ directory was read only after this pass, as a regression list.
QA rounds 5-6 raised `git stash` in one probe followed by `git stash pop` in
the next, as a channel between probes, and C12 accepts it. Nobody raised the
loss of the user's own stash, which the sensor itself tells the user to make.

```yaml
verdict: FAIL
blockers:
  - requirement: "R3 (Threat model, re-signed after the CEO's ruling of 2026-10-09, C13)"
    clause: "The sensors SHALL keep accidents out of a re-run: an uncommitted change, ... A probe that sets out to fool the sensor (rewriting git's objects, config or refs) is out of scope."
    problem: >
      A re-run refuses a dirty tree with the message "commit or stash ... first
      -- the working tree must be HEAD" (check_live.unclean, which
      check_formal and check_tasks share). But each probe runs in a linked
      worktree of the user's repository (`git worktree add`), and refs/stash is
      shared between worktrees. So a work-in-progress stash, made because the
      sensor asked for it, sits in the one place any probe can reach. A probe
      that is not trying to fool anything, using the common pre-commit idiom
      `git stash -q --keep-index; <tests>; git stash pop -q`, finds nothing to
      stash in its clean checkout. Its `pop` then applies the USER's stash
      inside the throwaway checkout and removes it from the user's stash list.
      The next reset (`checkout -f`, `reset --hard`, `clean -ffdx`) or
      `close()` then deletes it. The run reports green. The user's
      uncommitted change took part in the re-run's tree and was then
      destroyed, and the only trace is an unreachable commit that `git gc`
      prunes. `git stash drop` or `git stash clear` in a probe script does the
      same. This is an accident, not a probe that "sets out to fool the
      sensor", so the clause's out-of-scope carve-out does not reach it. C12
      (an open Cn, recorded before the C13 threat model) accepts writes into
      shared refs as a limit on the VERDICT. It does not weigh the loss of the
      user's work, which the sensor's own message invites.
    repro: >
      R=$(mktemp -d); cd $R; git init -q; mkdir -p .aidlc/evidence src;
      printf -- '- **R1** — x\n  - *Verify*: local\n' > .aidlc/requirements.md;
      echo x=1 > src/app.py; git add -A; git commit -qm init;
      write .aidlc/evidence/R1.json = {"id":"R1","verify":"local",
      "command":"git stash -q --keep-index; echo 'temp: 21'; git stash pop -q",
      "target":"this checkout","expect":"temp: \\d+","observed":"temp: 21",
      "result":"pass","sha":"<HEAD>","at":"..."}; git add -A; git commit -qm ev;
      echo 'precious uncommitted work' >> src/app.py; git stash -q;
      git stash list  -> "stash@{0}: WIP on main";
      python3 framework/tools/check_live.py --root $R --rerun  -> "live: ok", rc 0;
      git stash list  -> (empty); cat src/app.py -> "x=1"; the work survives only
      as an unreachable commit in `git fsck --unreachable`.
      Fix, any of: give the probe checkout its own refs, e.g. a
      `git clone --shared --no-checkout` of HEAD into the temp dir instead of a
      linked worktree, so no probe reaches the user's refs/stash, branches or
      tags; or snapshot `refs/stash` (and the reflog) before the first probe
      and fail loudly, restoring it, if it changed; and in every case stop
      telling the user to stash ("commit it, or move it out of the
      repository"). Add a self-test with the idiom above.
debts:
  - id: S10-1
    severity: medium
    problem: >
      framework/agents/designer.md (the award-grade loop, step 2) runs
      `npx impeccable detect <prototype>` with no version. The adapter pins
      impeccable@4.1.0 for install and verify, but the role body is copied
      verbatim, so the designer agent fetches and runs whatever `impeccable`
      npm serves at the time, under its shell grant. Pin it in the body
      (`npx impeccable@<pinned> detect`, the version named by the adapter or
      standards.md), or call the installed binary. Not in D1-D26.
  - id: S10-2
    severity: low
    problem: >
      Carried from security 9 and still not in TASKS.md. S9-2: two
      overlapping async beats of ONE session can tell the real holder "you
      are no longer the orchestrator" for one beat (safety holds;
      Election.tla's single pc per session leaves overlapping runs unmodelled
      and unstated in session-governance.md). S9-3: escape hatches are scanned
      only in the declared sources, not in modules they import or EXTEND.
      S9-4: SKILL.md's Phase 5 row ("production actions only from the
      pre-authorized list") still reads stricter than the paragraph under it
      and devops.md. Log them as Dn or close them.
notes:
  - "R6 / N1 sweep of role prompts, skills and host adapters: no Ship item became a role's own judgment. release.md and mobile-release/SKILL.md now make a store submission, a rollout promotion and a production release wait for the Ship batch unless pre-authorized (security 9's blocker is fixed). Missing signing material is the missing-service interrupt. The market verdict and platform strategy are in the intent batch, the prototype is in the design batch, and the merge stays the CEO's in every adapter. A signed Property, a local level and the design bar are not changed without the CEO."
  - "Contract-level ambiguity, for the CEO at the Ship batch: R6 puts 'production release' in Ship, while R8 and Aidlc.tla's JudgmentRecorded (signed in R12's Property) let a reversible production DEPLOY in Phase 5 that is not on the pre-authorized list run as a Cn before the Ship batch (devops.md item 3, SKILL.md Phase 5). For a service target the deploy is the release users see. The contract allows it as written. If that is not what the CEO means, the fix is a pre-authorized-list row or a devops.md line saying a first production deploy waits for Ship."
  - "Already logged, not re-raised: D12 (worktree left registered on SIGTERM), D17 (boot.py hint in shared temp, follows symlinks), D18 (secret pattern too narrow; confirmed again), D19 (auditor keeps Bash on Claude Code), D20 (actions pinned by tag), D21 (formal evidence not secret-scanned), D22 (failed-probe output unredacted), D26 (check_tasks has no --live-host; int() of DEVCREW_* at import)."
  - "Election: the link(2) CAS holds under 32-way and 20-way races; an unreadable top claim is held, not free; the hint file is only advisory; ORCHESTRATOR.top is verified against an existing claim and probed upward. The only git dir HeadTree may reset or remove is its own entry under <common>/worktrees/, checked before any probe."
  - "Supply chain: the TLC jar is sha256-pinned and checked before use; both workflows are contents: read on pull_request (not pull_request_target); the sensors are stdlib only; impeccable's third-party edit hook goes to settings.local.json only after the user says yes."
  - "Permissions: the reviewer is read/search/web with memory none; the auditor has no write/edit (its shell is D19); no other role's frontmatter grant widened against main."
```
