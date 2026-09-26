# Role verdict schemas — structured gate outputs

> Roles whose gate is a JUDGMENT — QA, Security, the efficiency Auditor,
> architecture-change review,
> self-evolution reviewer, market analyst — return their verdict in the fixed
> shape below, as a fenced ```yaml block at the end of the report. The
> orchestrator parses it; a missing or malformed block fails that gate (like any
> incomplete contract). FACT gates (Phase 3 tests+markers, Phase 5 smoke tests,
> Phase 6 signing/package sensors, Phase 2 CEO prototype sign-off) are enforced
> by deterministic sensors or a 🔴 CEO gate instead — see the aidlc skill — and
> do NOT use these blocks. Prose explanation still goes above the block.

## QA verdict (Phase 4)
```yaml
verdict: PASS | FAIL          # FAIL if ANY requirement unmet or any sensor red
scope: <the project scope>    # echoes requirements.md Scope
sensors:                      # deterministic checks run FIRST
  lint: pass | fail | n/a
  typecheck: pass | fail | n/a
  test: pass | fail | n/a
  build: pass | fail | n/a
requirements:                 # one row per Rn/Nn in requirements.md
  - id: R1
    verdict: PASS | FAIL
    evidence: <test name / screenshot path / device+OS>   # empty = FAIL
    traces_to: [PR#12]        # Rn: implementing PR/commit. Nn: evidence
                              #   (benchmark/audit/scan) if no single PR applies
blockers:                     # what stops the gate; empty list = clean
  - requirement: R4
    problem: <repro>
    loop_back_to: implementation   # never phase-0
```

## Security verdict (Phase 4)
```yaml
verdict: PASS | FAIL          # FAIL if any blocker/high open
scans:
  dependency: pass | fail
  secret: pass | fail
findings:
  - severity: blocker | high | medium | low
    area: <authz / injection / secret-storage / privacy-manifest / ...>
    detail: <what and where>
    fix: <the remediation>
    blocks_gate: true | false   # blocker/high => true
```

## Efficiency audit (Phase 4, auditor — only when the magnitude floor fires)
```yaml
verdict: PASS | PASS-WITH-DEBT | FAIL   # FAIL iff any finding has blocks_gate: true
                                        # PASS-WITH-DEBT = only medium/low findings
trigger: <which magnitude trigger fired: changed-lines | changed-files |
          new-dependency | multi-module | scope-greenfield | scope-refactor>
diff_size:
  added: <n>                  # from `git diff --shortstat` vs the base
  removed: <n>
  files: <n>
  excluded: [<lockfile / generated / vendored paths not counted>]
budget_source: standards.md | framework-default   # framework-default => say why
findings:                     # empty list = clean
  - severity: blocker | high | medium | low
    category: redundancy | duplication | over-abstraction | hot-path | running-cost | dependency-weight
    detail: <what and where — file:line>
    evidence: <measurement, or the duplicated pair / existing helper cited>
                              # no measurement => medium at most
    fix: <the concrete deletion, reuse target, or rewrite>
    saving: <LOC / ms / KB / $-per-month — estimate, or n/a>
    blocks_gate: true | false   # blocker/high => true
debt_logged:                  # medium/low findings carried to the ledger, not blocking
  - <one line each>
escalate_to_architect:        # empty unless a finding is really a design problem
  - <one line; the orchestrator decides whether to pull Phase 1 back in>
```

## Architecture-change review (mid-flight, architect)
```yaml
verdict: APPROVE | REQUEST-CHANGES | ESCALATE
change: <the proposed ADR change>
crosses_signed_boundary: true | false   # true => must ESCALATE to CEO
council_ran: true | false               # llm-council used for a load-bearing reversal
reason: <one line>
new_adr: <id, if APPROVE>
```

## Self-evolution review (reviewer)
```yaml
verdict: APPROVE | REQUEST-CHANGES | REJECT
model_used: <reviewer model id>          # must be a DIFFERENT vendor than author
author_model_vendor: <vendor>            # to prove cross-vendor
reviews_own_change: false                # MUST be false; else route to a 2nd reviewer
invariants_checked: [1,2,3,4,5,6,7]        # the design invariants from AGENTS.md
concerns:
  - <specific concern, empty if APPROVE>
```

## Market verdict (Phase 0.5, analyst)
```yaml
verdict: GO | PIVOT | NO-GO
confidence: high | medium | low
segment: <target segment>
competitors: [<name>, ...]
unverified_gaps: [<what could not be confirmed>]
pivot_framing: <only if PIVOT>
```
