# Security verdict — final 9 (security role, Claude, at ca1433f)

Scope: main..ca1433f, judged against proposals/0.9.7-autonomy-by-proof/requirements.md
(R3's *Threat model* first), AGENTS.md invariants 1-11, and the security role's
remit: hooks + boot.py, every shell-running path, git/file operations on the
user's repo, secrets in evidence, installed-role permissions, supply chain.

Read: boot.py, hosts/claude-code.boot_host.py and the five hooks; check_live.py
(HeadTree, unclean, at_head, drifted, contract, run_shell, probe_env, moved,
--record, the code scan, the self-test fixtures); check_formal.py;
check_tasks.py; tools/check_models.py; both CI workflows; Election.tla's
process model; every role's frontmatter; the release/devops/SKILL.md gate text
against main's.

Run, in a separate clone (never the user's repo):
- self-tests: check_live 152 cases, check_formal 55, check_tasks 56 -- all ok;
- the adapter's race: 32 concurrent starts gave exactly 1 orchestrator, 20
  concurrent takeovers of one expired claim gave exactly 1 winner;
- the three self-tests with GIT_DIR / GIT_INDEX_FILE / GIT_WORK_TREE pointing at
  a sacrificial repository (as a git hook would set them), with a before/after
  snapshot of that repository (repro under debts);
- same-session concurrent beats on a claim in its margin window (repro under
  debts);
- a credential grep over every added line of main..ca1433f and of each commit in
  the range: only self-test fixtures (`hunter2pass`) and prose; no home-directory
  path in evidence or formal records.

R3 re-run monotonicity, re-checked path by path: the evidence, the allow file,
the formal sources and the requirements are read from HEAD's blobs on a re-run
and from disk otherwise; an ignored/untracked stand-in, a symlink leaving the
tree, a case clash, a filtered file and an absolute or `..` source each make the
re-run fail where the plain run reads a file, never the other way. `drifted()`
reads both the working tree and HEAD, so a probe that writes into the user's
tree can only make evidence staler. I found no case where `--rerun` passes what
the plain run fails. The git-dir guard added after final 8 holds: the shim that
breaks `--absolute-git-dir` stops the re-run and the user's repository is
untouched.

The verdicts/ directory was read only after this pass, as a regression list. The
blocker below is not in D1-D26 and no earlier verdict raises it (reviewer 9 asked
for the opposite: fold the extra mobile stops into the batches. 01d1c3a did that,
and this one clause went past folding).

```yaml
verdict: FAIL
blockers:
  - requirement: "R6 + N1; invariant 8"
    clause: "R6: no item that the CEO signs today SHALL be dropped -- Ship: production release, signing material, store/production submission, the merge. N1: every item the CEO signs today is still signed, only grouped."
    problem: >
      The installed release role may submit an app to the App Store / Play with
      no CEO signature. framework/agents/release.md (the "Store submission (Ship
      batch)" bullet) says submission is signed in the Ship batch or
      pre-authorized in the Intent batch, then "Anything not signed either way
      is a judgment: decide, and record a `Cn` ... for the CEO to tick at the
      next batch". Its Discipline section says the same for every "store-facing"
      action ("anything else is a judgment -- decide it"). On main, store
      submission was a CEO sign-off (the SKILL.md "Submission gate";
      release.md: "then wait for sign-off"). In this change it is still a Ship
      item in R6, in SKILL.md's gate map ("P6 -- store / production submission
      | ship batch"), in the Phase 6 GATE ("the store/prod submission is signed
      off") and in mobile-release/SKILL.md ("Submitting to a store is signed in
      the ship batch"). So the prompt the release agent actually runs on is
      weaker than the contract and than the skill. A public binary release goes
      out on the agent's own judgment, and the CEO sees it only as a checkbox
      afterwards. That drops a signed Ship item; it does not group it. R8's
      generic "an action not on the list is decided and recorded as a Cn" does
      not reach an item that R6 names as signed in the Ship batch, and the
      Ship batch is one of the three stops R7 allows, so waiting for it is not
      a new stop.
    repro: >
      grep -n "Anything not signed either way" framework/agents/release.md;
      grep -n "store-facing" framework/agents/release.md; compare with
      grep -n "P6 — store / production submission" framework/skills/aidlc/SKILL.md,
      grep -n "the store/prod submission is signed off" framework/skills/aidlc/SKILL.md,
      grep -n "Submitting to a store is signed in the" framework/skills/mobile-release/SKILL.md,
      and git show main:framework/agents/release.md | grep -n "then wait for sign-off".
      Fix: in release.md, a store or production submission that the Intent
      batch did not pre-authorize waits for the Ship batch. It is never a
      `Cn`, and it is excluded from the Discipline line's "anything else".
      (Promoting a staged rollout past its first phase as pre-authorized or a
      `Cn` is R8 and the CEO's second ruling; that part is not raised.)
debts:
  - id: S9-1
    severity: medium
    problem: >
      check_live.py --self-test is not hermetic when the caller's GIT_* are set,
      e.g. when run from a git hook. Five fixture calls
      `subprocess.run(["git", "-C", d, "hash-object", "-w", "--stdin"], ...)`
      skip git_env(), so their objects go into the CALLER's object store, the
      fixture commits built from them break, and the self-test reports
      "self-test FAILED: a probe that hides a committed fake by skip-worktree".
      Repro: export GIT_DIR=<a sacrificial repo>/.git, GIT_INDEX_FILE=<it>/.git/index
      and GIT_WORK_TREE=<it>, then run check_live.py --self-test. It exits 1,
      and that repo gains 5 loose objects. Its HEAD, index, worktree,
      worktree list and stash are unchanged, so no user work is lost.
      check_formal and check_tasks self-tests pass under the same environment.
      Fix: pass env=git_env() to those five calls, or scrub GIT_* at the top of
      self_test() as check_tasks does.
  - id: S9-2
    severity: low
    problem: >
      boot.py: two hook runs of ONE session can overlap, because the adapter
      makes the PostToolUse and Stop beats async. If both find the holder's own
      claim in its margin window, both try to create n+1. The loser returns
      worker/"raced", and the actual holder is told "You are no longer the
      orchestrator -- the claim now belongs to another session". The next beat
      re-injects the orchestrator role. Safety holds (one session), but for one
      beat the protocol tells the holder to stop (A3), and Election.tla gives
      each session a single pc, so overlapping runs of one session are outside
      the model. Repro: hold a claim, set its mtime to 42 minutes ago, write
      the hint as orchestrator, then run 3 concurrent `beat` with the holder's
      session_id. Over 5 rounds, 2 rounds printed the demotion to the holder.
      Fix: in elect(), when a create fails for a session whose own claim it
      was renewing, re-scan, and if the top is now this sid, return kept. Or
      take a per-session flock around a hook run. Then state the assumption in
      session-governance.md.
  - id: S9-3
    severity: low
    problem: >
      check_formal scans for escape hatches only in the evidence's declared
      `sources`, not in the modules they import or EXTEND. A `sorry` in an
      imported Lean module, or an AXIOM in an EXTENDed TLA+ module, is not
      seen, and Lean's build exits 0 on `sorry` with only a warning. R10's
      "spec/proof sources" is satisfied literally, but an accidental hatch one
      import away is not. Fix: follow EXTENDS/import/Require within the tree,
      or require the sources to list the module closure.
  - id: S9-4
    severity: low
    problem: >
      SKILL.md's Phase 5 row ("production actions only from the
      pre-authorized list") reads stricter than the paragraph and devops.md
      that follow it (an action not on the list is decided and recorded as a
      `Cn`). Make the row say the same as the paragraph, so the permission
      boundary has one reading.
notes:
  - "Carried, not re-raised: D12 (worktree on SIGTERM), D17 (hint file in shared temp, follows symlinks), D18/D22 (secret pattern too narrow; failed-probe output unredacted), D19 (auditor keeps Bash on Claude Code; KiroCrew spawn/memory for every role), D20 (CI actions by tag), D21 (formal evidence not secret-scanned), D25 (hatch kin), D26 (check_tasks --live-host; --record through an in-tree symlink; setsid daemons; int() at import)."
  - "Supply chain: TLC is pinned by sha256 in check_models.py and fetched over HTTPS from the tlaplus release; both workflows run with contents: read; the sensors import only the standard library; impeccable is pinned (4.1.0) and its third-party hook goes to settings.local.json only after the user says yes."
  - "Election: the two races hold (1 of 32, 1 of 20); an unreadable top claim is held, not free; a git dir outside <common>/worktrees/ is never reset or removed; the throwaway checkout and its TMPDIR live in a 0700 mkdtemp; each probe runs in its own process group, killed after it ends."
  - "The TLA+ hatch rule flags every ASSUME, including the ones TLC evaluates and checks. That is over-strict, never weaker, so it is not a safety finding."
  - "Permission boundaries otherwise match the contract: the reviewer has read/search/web and no memory; the auditor maps to no Write/Edit on Claude Code (its Bash is D19)."
```

Retrospective: what worked was checking that a re-run is at least as strict by
reading both paths side by side for each input. What failed: eight earlier
security rounds looked at the sensors, and none diffed the role prompts' gate
text against main. Next time: grep every installed role for each signed batch
item before reading any code.
