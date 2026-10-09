<!-- reviewer round 5 (gpt-5.6-sol via kiro-cli, read-only, no team memory) at f4b3e15 -->
# Review result: REQUEST-CHANGES

```yaml
verdict: REQUEST-CHANGES
model_used: gpt-5.6-sol
author_model_vendor: Anthropic
reviews_own_change: false
invariants_checked: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

round4_open_items:
  - id: original-3-formal-tool-binding
    status: CEO-decided
    why: >-
      TASKS.md:33 records C4: check_formal binds evidence to a named tool and
      source but cannot prove that an arbitrary program faithfully implements
      that tool. This is an honestly stated mechanical limit for the CEO to
      accept. The proposal's actual R12/R13 commands lead to
      tools/check_models.py, which invokes TLC rather than merely naming it.

  - id: original-4-requirements-file-identity
    status: resolved
    why: >-
      check_tasks.py requires the first Signed path to be exactly
      requirements.md and retains the nested-decoy self-test.

  - id: original-5-intent-and-design-signatures
    status: CEO-decided
    why: >-
      The corrected requirements and design carry the recorded CEO ruling.
      TASKS.md:1 has their current hashes and requirements.md was re-signed
      after the round-4 amendments.

  - id: original-10-judgment-stops
    status: CEO-decided
    why: >-
      The signed CEO ruling expressly replaces judgment stops with role
      decisions recorded as Cn items. Five machine-raised interrupts remain;
      no sixth judgment-based interrupt is silently removed.

  - id: original-11-final-gate-records
    status: not resolved
    why: >-
      qa-3.md records PASS and audit-3.md records PASS-WITH-DEBT at 1d76120,
      resolving the absence identified in round 4 for the 7d7aff4 and 0417190
      changes. HEAD nevertheless adds the C9 per-probe reset afterward, and
      TASKS.md:37 explicitly says it has not received another QA round.
      A reviewer and a self-test do not replace the mandatory QA judgment on
      the delivered tree. CI awaiting PR creation is expected and is not this
      item's reason.

  - id: new-r12-property-and-signature
    status: CEO-decided
    why: >-
      The corrected property remains in the signed contract, the requirements
      were re-signed after the latest amendments, and the TASKS hash matches
      that re-signing.

  - id: new-requirements-identity
    status: resolved
    why: >-
      Exact relative-path equality plus the nested requirements.md decoy test
      closes the identity bypass.

  - id: new-formal-tool-binding
    status: CEO-decided
    why: >-
      This is the same stated limitation covered by C4, not a claim that the
      sensor can establish semantic equivalence between an arbitrary checker
      program and its declared tool.

  - id: glm-1-cross-design-judgment
    status: CEO-decided
    why: >-
      Moving a signed design file remains a machine-raised cross-design
      interrupt. Questions within the signed boundary are intentionally
      architect judgments recorded as Cn under the signed CEO ruling.

  - id: glm-4-universal-trace-conformance
    status: resolved
    why: >-
      requirements.md:202-216 and formal/R13.json now consistently limit the
      claim to the scripted, stampede and seeded concurrent runs CI samples.
      They no longer claim universal validation of every boot.py execution.

  - id: glm-7-budget-judgment
    status: CEO-decided
    why: >-
      A spent token/time budget is intentionally decided by the orchestrator
      and recorded as Cn rather than introduced as an unsensored interrupt.

  - id: glm-8-unauthorized-action-judgment
    status: CEO-decided
    why: >-
      An action absent from the pre-authorized list is intentionally decided
      by the acting role and recorded as Cn. The requirements template now
      states the same rule, including for an empty list.

  - id: round3-untracked-local-evidence
    status: resolved
    why: >-
      check_live.py:203-228 runs probes in a detached checkout of HEAD;
      ordinary untracked, ignored and .git/info/exclude files from the main
      working tree cannot participate. drifted() also no longer exempts all
      Markdown. The separate cross-probe nested-repository hole is reported
      below.

  - id: round3-create-failure-trace
    status: resolved
    why: >-
      boot.py still records staging/create failures as explicit failed-create
      trace events represented by the model.

  - id: round3-lowered-loop-bounds
    status: resolved
    why: >-
      check_tasks.py continues to require denominators of exactly 5 total and
      3 stalled, with raised and lowered bounds covered by self-tests.

  - id: round4-finding-cn-contract-contradiction
    status: resolved
    why: >-
      requirements.md:57-75 now explicitly permits Cn in Todo or Done, exempts
      Cn from live/formal evidence, and says when it moves to Done. The
      amended contract was re-signed and now matches check_tasks.py.

  - id: round4-finding-local-freshness
    status: resolved
    why: >-
      Markdown changes now make evidence stale and rerun commands execute in a
      throwaway HEAD checkout rather than the mutable main working tree.
      QA round 3 exercised ordinary untracked, ignored, excluded and
      uncommitted-file cases.

  - id: round4-finding-r8-evidence
    status: resolved
    why: >-
      evidence/R8.json:4-7 now invokes check_models.py --holds Aidlc:Aidlc and
      records Aidlc/Aidlc: holds. AidlcJudgmentBroken.cfg is also wired into
      MODELS and was observed to violate JudgmentRecorded when DropRecord is
      true.

  - id: round4-finding-stale-model-comments
    status: resolved
    why: >-
      Aidlc.tla:7-10 now distinguishes machine-raised trouble from judgments,
      and line 164 refers to exactly five interrupts.

findings:
  - severity: high
    file_line: "framework/tools/check_live.py:487-560; framework/tools/check_formal.py:243-266"
    finding: >-
      Rerun commands use HeadTree, but the no-fake and formal-source safety
      scans still read the mutable main working tree.
    why: >-
      check_live.check_code reads tracked files through root/rel after the
      isolated evidence reruns have completed. check_formal likewise reads
      sources and scans escape hatches through root/src, while only the three
      commands run under tree.get(). An uncommitted edit can therefore hide a
      fake shipped at HEAD or remove an axiom/assume escape hatch from the
      scanner's view while the isolated command runs against HEAD. That can
      produce a green result for a HEAD tree the mandatory static sensor never
      inspected, contrary to R10 and invariants 10 and 11. On --rerun, every
      source-dependent scan and allow file must be read from the same HEAD
      checkout as the commands.

  - severity: high
    file_line: "framework/tools/check_live.py:211-220"
    finding: >-
      The C9 reset does not guarantee that nothing written by an earlier probe
      survives into the next probe.
    why: >-
      git clean -fdx deliberately preserves untracked nested Git repositories
      unless force is supplied twice. A first probe can create or clone such a
      directory and a later probe can consume it after HeadTree.get() reports
      a successful reset. This directly contradicts the class invariant and
      C9's stated proof boundary. Use a fresh worktree per probe or a cleanup
      mechanism that demonstrably removes nested repositories, and add the
      adversarial case to the self-test.

  - severity: high
    file_line: "framework/tools/check_live.py:231-253,420; framework/tools/check_formal.py:268-269"
    finding: >-
      contract() exempts an entire nested contract directory from evidence
      staleness, although not every possible file there is signed or merely
      evidence.
    why: >-
      For nested requirements, contract() returns reqfile.parent and drifted()
      excludes that whole subtree. check_tasks hashes only the files named on
      Signed, while check_live/check_formal can also run independently.
      Consequently an unsigned model, probe support source or specification
      stored beside a proposal's requirements can change without invalidating
      stored evidence. Exempt the specific record/evidence paths and
      hash-checked contract files, not an unrestricted parent directory.

  - severity: medium
    file_line: "framework/tools/check_tasks.py:77-79,176"
    finding: >-
      The Done-status sensor still permits explicit residual status words in
      malformed tails.
    why: >-
      DONE_STATUS catches building, verifying and fixing after a joint, but
      catches blocked only as blocked on. Thus a line such as
      '- [x] R1 title · blocked' passes even though R3 says a Done line carries
      no status. Similar punctuation/casing forms documented in qa-3.md remain
      outside the rule. At minimum, a status word directly after a recognized
      joint should be rejected independently of whether the former in-progress
      status was well-formed.
```

The re-signed R2/R3/R13 amendments, R8 TLC evidence, judgment mutant, template correction, Markdown staleness change, and ordinary HEAD-worktree isolation all resolve their round-4 targets. Approval remains blocked because HEAD lacks a current QA verdict and because the new isolation boundary still permits mutable-tree scans, cross-probe contamination, and stale unsigned contract-local sources. CI’s pre-PR absence is not treated as a finding.
