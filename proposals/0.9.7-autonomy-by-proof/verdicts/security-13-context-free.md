# Security verdict — final 13 (security role, Claude, at 13c8936)

Scope: main..13c8936, judged against proposals/0.9.7-autonomy-by-proof/requirements.md
(R3's *Threat model* first, then R6 / N1 and R10), the AGENTS.md invariants, and the
security remit: hooks and boot.py, everything that runs a shell command, file and git
operations on the user's repo, --deployed and --record, filters and attributes,
secrets in evidence, role permissions, and the supply chain.

Read: check_live.py (unclean, at_head, HeadTree.files/_filtered/_cat/ls/blob/_add/get/
_scratch/close, _drifted, contract, not_live, run_shell, probe_env, moved,
_check_evidence, the --deployed loop, --record, scan/check_code), check_formal.py,
check_tasks.py, boot.py and hosts/claude-code.boot_host.py, the five hooks in
hosts/claude-code.md, tools/check_models.py, both workflows, the frontmatter of every
role, and the gate text in orchestrator, devops, release, designer, analyst, architect,
SKILL.md (§ Batches and interrupts, Phases 5 and 6), requirements.template.md,
mobile-release and the three host adapters.

Ran, only in a throwaway clone at 13c8936 and in scratch repositories:
- The self-tests: check_live 162 cases, check_formal 66, check_tasks 64, all ok;
  check_neutral and check_repo ok. I ran them again with GIT_DIR, GIT_WORK_TREE and
  GIT_INDEX_FILE pointing at the clone. The clone's refs, stash, worktrees,
  remotes, config, status and .git listing hashed the same before and after.
- The election race: 30 concurrent starts gave exactly 1 orchestrator. After the
  claim's mtime was aged, 30 concurrent takeovers gave exactly 1 winner, with
  generations 1 and 2 kept.
- A --rerun whose local probe does `git stash drop/clear`, deletes branches, checks
  out an orphan, prunes worktrees, sets config, adds a remote and pushes, runs
  `update-ref -d`, `gc --prune=now` and `reflog expire`. The user repo's refs,
  stash, worktrees, remotes, config, objects and status were unchanged.
- The repros of the two blockers below.

I read verdicts/ only after this pass, and used it only as a regression list.

```yaml
verdict: FAIL
blockers:
  - requirement: "R3 (Threat model); invariant 10"
    clause: >
      "On a re-run they SHALL never pass what the plain run fails -- except a
      stale record the re-run itself proves again at HEAD (... a live one whose
      environment --deployed proves runs HEAD)". Invariant 10: "each requirement
      needs fresh evidence from a probe against the real, deployed service".
    problem: >
      A live record counts as fresh, and --record stamps it sha=HEAD, when
      hostname(target) is in `proven`. That test does not bind the proof to the
      host the probe actually asked. There are two ways it fails.
      (a) `proven` collects the host of every URL in a --deployed command
      (`proven |= {h for t in urls ...}`), while the output only has to contain
      HEAD's sha once. `--deployed "curl -fsS https://api.acme.io/version &&
      curl -fsS https://auth.acme.io/health"` marks auth.acme.io as running HEAD
      when only api.acme.io printed it. The docstring's "one version probe per
      service" is not enforced.
      (b) The "the probe command never names <host>" rule is a substring test
      (`h not in cmd.lower()`). A record with target https://api.acme.io/login
      and command `curl -fsS https://staging-api.acme.io/login` passes that
      rule. A --deployed proof for api.acme.io then makes it fresh, so the
      staging answer is stamped as HEAD's proof on production.
      In both cases the plain run fails the record as stale, and the re-run
      passes and re-records it, although no --deployed output showed that the
      host it probed runs HEAD. Both are accidents a role makes in good faith
      (one environment check with two curls; a probe copied from staging),
      not a probe trying to fool the sensor. --live-host closes (b) only when
      it is exact; a `*.acme.io` glob does not.
      Fix: count a --deployed command as proving a host only when that host is
      its only URL host (or refuse a command with more than one). Grant
      freshness only when every URL host of the probe's command is in `proven`.
      Match the target host against the command's parsed URL hosts, not as a
      substring. Add self-tests for (a) and (b).
    repro: |
      # scratch repo; import check_live and stub resolve() to 8.8.8.8 as its self-test does
      # commit .aidlc/requirements.md "- **R1** — login works" and src/app.js, note sha OLD
      # write .aidlc/evidence/R1.json: verify live, sha OLD, expect '"ok": 1', observed '"ok": 1'
      #   (b) target https://api.acme.io/login,
      #       command: echo '"ok": 1' https://staging-api.acme.io/login
      #   (a) target https://auth.acme.io/login,
      #       command: echo '"ok": 1' https://auth.acme.io/login
      # change src/app.js, commit everything, HEAD=H
      run(R)                                    # ['... R1: stale -- code changed since ...']
      run(R, rerun=True, deployed=["echo H https://api.acme.io/version"])          # (b): []
      run(R, rerun=True, deployed=["echo H https://api.acme.io/version https://auth.acme.io/health"])  # (a): []
      # with record=True in either case: R1.json is rewritten with sha == H
  - requirement: "R3 (Threat model); R10"
    clause: >
      "On a re-run they SHALL never pass what the plain run fails". R10: the
      sensor fails a requirement "whose spec/proof sources hold an escape
      hatch".
    problem: >
      Round 5 made check_live's code scan read a filtered file both raw and
      through its filter (HeadTree.files keeps the pair). HeadTree.blob(), which
      every other re-run read goes through, returns only the raw element
      (`got = got[0] if isinstance(got, tuple)`). On --rerun, check_formal reads
      its sources through blob(), and so do its escape-hatch scan and its .tla
      definition check, and check_tasks --rerun with them. So for a filtered
      source, the plain run scans the working-tree file (the smudged content)
      and the re-run scans only the raw blob. A `sorry` / `Admitted` / `assume`
      that exists only in the filtered content fails the plain run and passes
      the re-run. Examples are a keyword-expanding or decrypting filter, or an
      LFS-tracked proof file whose blob is a pointer. The tree is clean
      (status is empty), and the filter is the repo's own committed attribute
      plus its config, set up before the run. It is the same class Security 12
      raised and the round-5 fix closed for check_live only. The same raw-only
      read also covers evidence JSON and the --allow file on a re-run.
      Fix: have blob() callers that scan content (check_formal's sources, and
      the allow file) scan every element of the pair, as check_code does. Add
      a check_formal self-test with a smudge filter.
    repro: |
      git init; printf '*.lean filter=kw\n' > .gitattributes
      git config filter.kw.smudge 'sed s/KWHOLE/sorry/'; git config filter.kw.clean 'sed s/sorry/KWHOLE/'
      # req/requirements.md: R1 Property "always safe", Formal checked, Conformance none
      # spec/P.lean "theorem t : True := by KWHOLE"; spec/check.py = check_formal.CHECKER
      git add -A; git commit -m a; rm spec/P.lean; git checkout -- spec/P.lean   # disk: "by sorry"
      # req/formal/R1.json: command "python3 spec/check.py spec/P.lean", sources [spec/P.lean,
      #   spec/check.py], bounds "3", vacuity "... --broken" (fail), sha = HEAD; commit it
      git status --porcelain                         # (empty)
      check_formal.check(R, R/"req/requirements.md")              # ['... escape hatch in P.lean:1 `... by sorry`']
      check_formal.check(R, R/"req/requirements.md", rerun=True)  # []
debts:
  - id: S13-1
    severity: medium
    problem: >
      S12-1 is carried over: it is still unfixed and is still not in TASKS.md.
      The general judgment rule does not exclude Ship-batch items. SKILL.md
      § Batches ("an irreversible action not on the pre-authorized list (do it
      or not -- either way a Cn)") and Phase 5, orchestrator.md and
      requirements.template.md ("An empty table is a valid answer: then every
      such action is decided by the role about to act") each, read alone, let
      a store submission, a signing step or the merge be self-decided as a Cn.
      release.md, mobile-release and the merge rules (SKILL.md's gate map,
      reviewer.md, invariant 4) override it item by item, so no R6 item is
      dropped today. Add "except a Ship-batch item, which waits for the Ship
      batch unless it is pre-authorized". The production-deploy reading stays
      C21.
  - id: S13-2
    severity: low
    problem: >
      On a re-run, a filtered evidence JSON (for example `*.json filter=lfs`) is
      read as the raw blob (an LFS pointer), so the re-run reports "not a JSON
      object" where the plain run passes. This fails closed, but it makes the
      Ship-batch re-run unusable for LFS users. The fix is the same as the
      second blocker's.
notes:
  - "User repo: the sensors only read it (status with fsmonitor, ignoreStat and untrackedCache off; ls-files -v; cat-file --no-replace-objects; diff; check-attr; merge-base; clone --shared; read-tree into a temp index). The one write is --record, which refuses a symlinked record, writes only after moved() and a secret scan of the excerpt, and needs a clean tree at start. Every reset, clean and rmtree targets the clone inside its own temp dir. A checkout or .git swapped for a link is refused or rebuilt. The clone's config is unlinked before it is restored (S12-3 closed), and its origin is removed. The --rerun TypeError is fixed with frozenset() (S12-2 closed). A probe can still write by absolute path; that is the stated limit (C12, HeadTree's docstring)."
  - "Election: in my races the link(2) generation CAS held, giving 1 of 30 on start and 1 of 30 on takeover. An unreadable claim counts as held, and release targets the generation the session read. The hooks take session_id from stdin, quote ${CLAUDE_PROJECT_DIR} and always exit 0. board.py at SessionStart is repository code, in the same trust domain as the hooks. A worker is not told not to write ORCHESTRATOR.pin; the pin is a human hatch enforced by prose only (pre-existing design)."
  - "Shell: probes run with start_new_session and a killpg at the end, their own TMPDIR, and only PATH/HOME/locale plus the variables the command names. --deployed runs in HEAD's checkout. off_net() resolves the host once and the probe resolves it again (DNS TOCTOU). Under the threat model that is the environment's, and I record it only as a note."
  - "R6 / N1 sweep: the intent items (requirements with Property, market verdict, pre-authorized list, platform strategy), the design items (design.md, standards.md, the prototype the CEO chooses) and the ship items (signing material as missing-service plus the ship batch, store submission and rollout promotion in release.md, the merge with the CEO) are each still the CEO's in the prompt that governs them. The wording gap is S13-1. devops' reversible production deploy as a Cn is C21, still pending."
  - "Secrets: no credential in any added file or in the branch's history, checked with check_live's SECRET pattern plus JWT, Google, Stripe, Slack and GitHub-PAT shapes. Not re-raised: D18, D21, D22."
  - "Permissions and supply chain: no frontmatter grant widened against main. The reviewer has read/search/web and memory none; the auditor has no write or edit (its Bash is D19). The TLC jar is sha256-pinned in check_models.py. Both workflows have contents: read. The sensors are stdlib only. impeccable is pinned @4.1.0, and its hook is installed only after the user agrees. Actions are pinned by tag (D20)."
  - "Already logged, not re-raised: C12, C15, C17, C19, C21, D17, D18, D19, D20, D21, D22, D26, D27."
```

Retrospective: the round-5 filter fix closed the read path the reviewer named,
not the accessor every other read goes through. Fixing it in blob() would have
covered check_formal too. When a proof is tied to a host, it has to be tied to
the host the probe actually asked: a substring or a whole command's URL set is
not that host.
