# Security verdict — final 3 (security role, Claude, at ba572c4)

```yaml
verdict: FAIL
blockers:
  - requirement: R3
    clause: "Threat model: the sensors SHALL keep accidents out of a re-run: an uncommitted change, an untracked or ignored file ... On a re-run they SHALL never pass what the plain run fails."
    problem: >
      check_live.py --rerun runs every --deployed version probe with cwd = the user's
      working tree (`probe(cmd, root)` in _run), not in HeadTree's throwaway checkout of
      HEAD that every other re-run probe uses. An uncommitted edit to a committed helper,
      or an untracked file, therefore decides `proven`. `proven` makes a stale live item
      fresh and lets --record stamp new evidence with sha = HEAD. After that, even the
      plain run passes. The same path lets a --deployed command that writes a relative path
      (for example `curl -o version.json`) overwrite the user's uncommitted files. The
      docstring says "Every re-run runs in a throwaway checkout of HEAD"; --deployed is the
      exception, and only the audit noted it (audit-7, as a cost remark).
      Fix: run --deployed in tree.get(), like the other probes.
    repro: |
      git init; .aidlc/requirements.md with "- **R1** — temp" / "  - *Verify*: live";
      src/app.py; committed version.sh printing a wrong sha:
        printf '#!/bin/sh\necho "build 0000000000000000000000000000000000000000"\n' > version.sh
      commit; .aidlc/evidence/R1.json = {verify live, command "echo 'temp: 21' https://github.com/x",
        target https://github.com/x, expect "temp: \\d+", observed "temp: 21", result pass, sha <that commit>}; commit;
      edit src/app.py; commit                        # the evidence is now stale
      check_live.py                                  -> rc 1 "R1: stale -- code changed since ..."
      check_live.py --rerun --deployed "sh version.sh https://github.com/v"
                                                     -> rc 1 "the environment does not run HEAD"
      printf '#!/bin/sh\necho "build $(git rev-parse HEAD)"\n' > version.sh   # uncommitted
      check_live.py --rerun --deployed "sh version.sh https://github.com/v"   -> rc 0 "live: ok"
      untracked variant: v2.sh with the same body, never added:
      check_live.py --rerun --record --deployed "sh v2.sh https://github.com/v"
                                                     -> rc 0; evidence/R1.json rewritten at HEAD;
      check_live.py (plain)                          -> rc 0 "live: ok"
  - requirement: R3 / R4
    clause: "R3 Threat model: keep an uncommitted change out of a re-run; R4: SHALL fail when a Signed: hash no longer matches the file it names (the drift halt)"
    problem: >
      check_tasks.py --rerun, the run QA and the Ship batch rely on, hashes the signed files
      and reads TASKS.md and requirements.md from the working tree, not from HEAD. The
      probes and scans of the same invocation do read HEAD. A committed edit to the signed
      requirements.md (the drift that ships) is hidden by an uncommitted copy of the signed
      text. drifted() already guards this case for staleness ("an uncommitted edit that puts
      a file back as it was at sha does not make HEAD's change go away"); the signature
      check does not. The same holds for TASKS.md: HEAD's ledger can claim Done for an item
      the re-run never checks, because the working-tree copy moved it to Todo. Here the plain
      run passes too, so this fails the first sentence of the threat model, not the second.
      Fix: on --rerun, hash HEAD's blob of each signed file and parse HEAD's TASKS.md, as
      well as the working-tree copies.
    repro: |
      requirements.md with R1 (Verify local, Property none — prose); TASKS.md = the
        `check_tasks.py --sign requirements.md` line + "## Todo / - [ ] R1 log in"; commit;
      edit R1's Verify line in requirements.md; commit      # HEAD has drifted from the signature
      git checkout HEAD~1 -- requirements.md                # working tree back to the signed text, uncommitted
      check_tasks.py --rerun                                -> rc 0 "tasks: ok"
      git stash; check_tasks.py --rerun                     -> rc 1 "DRIFT -- requirements.md is sha256:..."
      ledger variant: HEAD's TASKS.md has "- [x] R1" with no evidence (--rerun on a clean tree:
        rc 1 "no evidence ... at HEAD"); an uncommitted TASKS.md moving R1 to Todo -> --rerun rc 0
debts:
  - "check_formal: canon() turns an absolute source into a repo-relative one on --rerun, while the plain run reads the absolute path. A source '/X/M.tla' with an in-tree mirror X/M.tla: the plain run fails on the out-of-tree file's escape hatch (OMITTED), and --rerun passes because it scans HEAD's clean X/M.tla. This needs a constructed mirror path, and the command must name the absolute source, so it is low severity. Fix: report any absolute source as a hit, in both modes."
  - "boot.py: a non-integer DEVCREW_STALE_SECONDS or DEVCREW_MARGIN_SECONDS raises at import time, outside main()'s try, so the script exits 1 with a traceback. Its docstring says it always exits 0. Claude Code does not block on exit 1, so this is low severity; MARGIN >= STALE also leaves no lease ever fresh, unchecked."
  - "--record overwrites the working-tree evidence file through a symlink if that path is one (write_text follows links); low severity."
notes:
  - "Already logged, not re-raised: D12 (worktree left on SIGTERM), D17 (hint file in the shared temp dir), D18 (secret pattern misses Basic, JWT, sk_live_, AIza, glpat-, github_pat_; confirmed), D19 (role permissions: KiroCrew spawn/memory, auditor Bash), D20 (actions pinned by tag), D21 (formal commands get the full environment)."
  - "Sensors pass at ba572c4: check_live --self-test (138 cases), check_formal (45), check_tasks (51), check_neutral, check_repo."
  - "boot.py raced in a throwaway tree: 30 concurrent starts gave exactly one orchestrator (generation 1); 30 concurrent takeovers of an expired lease gave exactly one winner (generation 2)."
  - "No credentials in the diff or in the committed evidence; every commit is by one author. CI permissions are contents: read. TLC is pinned by sha256 and checked before it runs, so the cached jar cannot be swapped."
  - "The user's repository is touched only by `worktree add/remove` (hooks off through QUIET_GIT) and by read-only git calls. No sensor checks out, resets or cleans the user's tree. The exception is blocker 1's --deployed path, which runs the command itself in the user's tree."
  - "The hooks and boot.py run repository code at every session start and tool call, and boot.py also runs .aidlc/tools/board.py if present. This is the same trust as the repo itself, and the host's project-trust prompt is what gates it. impeccable is installed with npx at a pinned version but without an integrity hash; the adapter asks the user before keeping its hook."
retrospective:
  - "The --deployed path was the one exception to 'every re-run in a checkout of HEAD'; the differential sweeps compared scans, not where each command ran."
  - "Drift on HEAD versus the working tree was guarded for staleness but not for the signatures: apply one rule to every read a --rerun makes."
  - "Racing boot.py took one minute and settled what the models claim; keep doing it."
```
