# Security verdict — final 5 (security role, Claude, at f21b821)

```yaml
verdict: FAIL
blockers:
  - requirement: R10 (stale), R3 (Done only with formal evidence fresh at HEAD); C10's stated intent
    clause: "fails a requirement whose formal evidence is ... stale (the code changed since its sha)"
    problem: >
      check_live.drifted() excludes the whole state dir (`:!.aidlc`) from staleness
      and carves back only `.aidlc/tools`. check_formal and check_tasks reuse it. A
      product feature lives at .aidlc/features/<slug>/, and its formal evidence at
      .aidlc/features/<slug>/formal/. So a spec, a checker script or a probe helper
      kept beside the feature can change after the evidence sha, and the evidence
      still reads as fresh. C10 narrowed this exemption for proposals/<slug>/ only.
      The blanket state-dir rule cancels it for the product layout. Plain
      check_formal and plain check_tasks are the machine bound between batches
      (invariant 11). Both accept a broken model as fresh Done. Only --rerun catches
      it, and that runs at the Ship batch. This is the most ordinary accident there
      is: someone edits the model after recording its evidence.
    repro: |
      throwaway repo; copy framework/tools/check_*.py to .aidlc/tools/; .gitignore __pycache__/
      .aidlc/features/x/requirements.md: R1, Verify local, Property "Safe holds", Formal checked
      .aidlc/features/x/spec/{M.tla,check.sh}: check.sh prints "No error has been found" iff M.tla says GOOD
      commit (sha S). Write formal/R1.json and evidence/R1.json at sha S, the command naming
      spec/check.sh spec/M.tla, with a failing vacuity run. TASKS.md beside it:
      Signed requirements.md, `- [x] R1 a`. Commit.
      check_tasks.py --tasks .aidlc/features/x/TASKS.md            -> tasks: ok
      edit M.tla so the model is broken (GOOD -> BAD); commit
      check_formal.py --requirements .aidlc/features/x/requirements.md -> formal: ok   (stale not detected)
      check_tasks.py --tasks .aidlc/features/x/TASKS.md            -> tasks: ok   (Done on a broken model)
      check_tasks.py ... --rerun                                   -> rc 1, "re-run of the check exited 1"
      Fix: exempt only the record under the state dir (requirements/design/standards/TASKS,
      verdicts, and evidence/formal *.json), the way contract() does for proposals/.
      Add a self-test case that edits a source under .aidlc/features/<slug>/ after the sha.
debts:
  - "Plain-mode sensors that import check_live from .aidlc/tools/ write .aidlc/tools/__pycache__/. In a project that does not gitignore it, every later --rerun then refuses with 'commit or stash .aidlc/tools/__pycache__/...' (reproduced). The rule fails closed, so nothing passes that should not, but the installed sensor makes the tree unclean by running. Add __pycache__/ to the adapter's .gitignore block, or run with -B / PYTHONDONTWRITEBYTECODE."
  - "When a probe or --deployed fails, its raw output is printed: the first 120 characters on a re-run failure, 80 for --deployed. Nothing is redacted, so a token echoed by a failing probe lands in a terminal or CI log. Same remedy as D18: redact by default."
notes:
  - "Already logged, not re-raised: D12 (worktree left registered on SIGTERM), D17 (hint file in the shared temp dir), D18 (narrow secret pattern), D19 (role permissions: KiroCrew spawn/memory, auditor Bash), D20 (actions pinned by tag), D21 (formal evidence not secret-scanned; formal commands get the full environment)."
  - "Re-run versus plain run: on a clean HEAD I found no case where the re-run is weaker. Tried: symlinked evidence, requirements, TASKS and allow files (in-tree and out-of-tree), a wrong-case --requirements or --evidence path, a sparse checkout, skip-worktree and assume-unchanged, an untracked or ignored allow file, untracked formal sources, a nested repo, a dirty submodule, and working-tree-encoding. In each the re-run is equal or stricter."
  - "Data safety on the user's repo: the only write to the user's tree is --record. It needs --rerun on a clean tree plus --deployed, writes only <evidence>/<ID>.json, and only when the item has no other hit and the excerpt holds no secret. HeadTree removes only its own temp dir and its own worktree entry, and reads the entry's git dir before any probe. Hooks are off for every git call it makes. GIT_* is stripped from the environment, so a hook-launched run cannot point git at the user's index. A reset that fails (for example on read-only files a probe left) exits with an error. I found no path that deletes or rewrites tracked work."
  - "Permissions: no role's tools or memory changed in this diff (frontmatter is the same as main). The reviewer stays read/search/web with memory none, and the auditor has no write/edit."
  - "Supply chain: the TLC jar is fetched over HTTPS and its sha256 is checked before use. impeccable is pinned to a version via npx but has no integrity hash; the adapter requires the user's yes for its hook. The sensors are stdlib only."
  - "boot.py: the claim is still the link(2) compare-and-swap. The hooks quote ${CLAUDE_PROJECT_DIR}. Session id and cwd come from the host and are written into the claim. A newline in either cannot override the first session_id: line, because scan() reads the first match."
```
