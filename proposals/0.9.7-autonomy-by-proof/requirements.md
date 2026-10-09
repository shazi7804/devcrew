# Requirements — devcrew 0.9.7: autonomy earned by proof

> Signed intent contract for a change to devcrew's own framework. Every gate of
> this change re-reads this file.
> Status: SIGNED (CEO rulings) — 2026-10-08: 「好。加進去後直接做」 on the draft,
> then 「全部 commit and sign. 不要再問我簽不簽的問題」 on this text, with the
> post-review corrections and the Cn rule; both verbatim under *Constraints*.
> Scope: feature (framework: `framework/` · `hosts/` · `AGENTS.md` · docs · CI)

## Vision
The team runs longer without stopping the CEO, because what it may do on its
own is bounded by things a machine checks, not by a model's say-so. Three
changes, one idea:

1. **TASKS.md replaces the ledger.** One small file says what is done, what is
   in flight (with its status) and what is left. History is not kept in it;
   git already keeps history.
2. **The CEO signs in three batches** — intent, design, ship — instead of at
   every 🔴 stop. Between batches the run is autonomous and stops only on an
   interrupt that a sensor raises.
3. **Formal methods carry the trust the stops used to carry.** Every signed
   requirement has a machine-checked property, and the AIDLC protocol itself is
   a model that is checked in CI. The CEO signs the *properties*; the machine
   checks the *conformance*.

## Users & context
- Primary user: the CEO, who today is stopped up to seven times per run
  (Phase 0, 0.5, 2, 6 signing, 6 submission, ∞ merge, plus escalations) and
  wants to be stopped three times.
- Secondary users: every role agent; every project devcrew is installed into.
- The gap this closes (found comparing devcrew 0.9.6 with
  awslabs/aidlc-workflows 2.10 on 2026-10-07): the intent hash, the drift halt,
  the loop bound and the ledger are described as mechanical but have no code;
  on Claude Code the ledger is "⚠ NOT DEFINED". More autonomy on top of
  prompt-only bounds would be autonomy on trust. This change makes the bounds
  code first.

## Functional requirements (EARS)

### TASKS.md — the current state, nothing more
- **R1** — The framework SHALL define `TASKS.md` at the project root (for a
  framework change: `proposals/<slug>/TASKS.md`) as the run's only ledger, with
  exactly three sections in this order:
  - `## Done` — `- [x] <ID> <title>`, one line, no status, no record;
  - `## In progress` — `- [~] <ID> <title> — <status> · <owner> · <n>/<max> · next: <step>`,
    where `<status>` is one of `building | verifying | fixing | blocked`, and
    `blocked` SHALL name what it waits on;
  - `## Todo` — `- [ ] <ID> <title>`.
  A header holds only the current signatures and the open gate, if any:
  `Signed: requirements.md sha256:<12> · standards.md sha256:<12>` and
  `Gate: 🔴 <batch> — awaiting CEO`.
  - *Acceptance*: `contracts/tasks.template.md` exists with that format; SKILL.md
    and `ARCHITECTURE.md` §6 call it the ledger; every mention of "the ledger"
    resolves to it.
  - *Verify*: local
  - *Property*: none — prose in templates, SKILL.md, roles or adapters; its acceptance is read and grepped, there is no behaviour to model
- **R2** — Every requirement ID (`Rn`, `Nn`) of the signed requirements SHALL
  appear in TASKS.md exactly once, and an ID SHALL NOT appear that the
  requirements do not define, except `Dn` tech-debt items (the Phase-4
  audit's medium/low findings), which live in `## Todo`, and `Cn` judgment
  records (R7), which live in `## Todo` or `## Done`.
  - *Acceptance*: the TASKS sensor (R4) fails on a missing, duplicated or
    unknown ID, and passes `Dn` and `Cn`.
  - *Verify*: local
  - *Property*: none — the acceptance is the sensor's self-test: example cases, each asserting the reason it fails; sampling, not a formal method
- **R3** — An item SHALL move to `## Done` only when its live evidence (R2 of
  0.9.6) and its formal evidence (R10) are fresh at HEAD; on moving, its status
  line SHALL be dropped. A `Cn` is a recorded judgment, not a requirement:
  it carries no evidence, and moves to `## Done` when it is resolved or the
  CEO ticks it.
  - *Threat model* (the CEO's ruling of 2026-10-09): a probe command is
    trusted -- a role writes it and the reviewer reads it in the diff. The
    sensors SHALL keep accidents out of a re-run: an uncommitted change, an
    untracked or ignored file, what an earlier probe left behind, a symlink,
    a name two filesystems spell differently. On a re-run they SHALL never
    pass what the plain run fails. A probe that sets out to fool the sensor
    (rewriting git's objects, config or refs) is out of scope, stated in
    HeadTree's docstring. A tool on PATH or named by an environment variable
    the command uses -- wherever it lives, a virtualenv in an ignored
    directory included -- is the environment the probe runs in, not the
    tree; the reviewer reads it in the command. Each probe gets a TMPDIR of
    its own.
  - *Acceptance*: the TASKS sensor fails a `[x]` whose `check_live.py --only <ID>`
    or `check_formal.py --only <ID>` fails, and fails a `[x]` line that still
    carries a status.
  - *Verify*: local
  - *Property*: none — the acceptance is the sensor's self-test: example cases, each asserting the reason it fails; sampling, not a formal method
- **R4** — The framework SHALL ship `framework/tools/check_tasks.py`, a
  deterministic sensor that checks R1–R3, and SHALL fail when a `Signed:` hash
  no longer matches the file it names (the drift halt, now code), or when an
  attempt count exceeds its bound (Loop A: 3 stalled or 5 in total).
  - *Acceptance*: `check_tasks.py --self-test` exits 0, each case asserting the
    REASON it fails: a missing section; sections out of order; a bad status; a
    `blocked` with no reason; a missing, duplicated or unknown ID; a `[x]`
    without fresh evidence; a `[x]` with a status; a drifted
    `requirements.md`; a drifted `standards.md`; `6/5` attempts. No hit on a
    clean TASKS.md.
  - *Verify*: local
  - *Property*: none — the acceptance is the sensor's self-test: example cases, each asserting the reason it fails; sampling, not a formal method
- **R5** — Every host adapter SHALL use TASKS.md as its ledger. A host ledger
  primitive MAY mirror it; when they disagree, TASKS.md wins.
  - *Acceptance*: `hosts/claude-code.md`, `hosts/kirocrew.md` and
    `hosts/mission-control.md` say so; the "⚠ NOT DEFINED" ledger line in
    `hosts/claude-code.md` is gone; each adapter installs `check_tasks.py` and
    runs its self-test at verify.
  - *Verify*: local
  - *Property*: none — prose in templates, SKILL.md, roles or adapters; its acceptance is read and grepped, there is no behaviour to model

### Three batch sign-offs
- **R6** — The 🔴 gates SHALL be grouped into three batches, and no item that
  the CEO signs today SHALL be dropped from them:
  - **Intent** — `requirements.md` (with every `Property:`, R9), the market
    verdict when Phase 0.5 runs, and the pre-authorized actions (R8);
  - **Design** — `design.md` + `standards.md` (Phase 1) and the chosen
    prototype (Phase 2); skipped when scope routing skips both phases;
  - **Ship** — production release, signing material, store/production
    submission, and the merge.
  Each batch SHALL be presented as one SITREP and SHALL end the turn.
  - *Acceptance*: SKILL.md's phase table and gate sections name the batch each
    former 🔴 gate belongs to; a table in SKILL.md maps old gate → batch, one
    row per old gate, none unmapped.
  - *Verify*: local
  - *Property*: none — prose in templates, SKILL.md, roles or adapters; its acceptance is read and grepped, there is no behaviour to model
- **R7** — Between batches the run SHALL NOT stop for the CEO, except on an
  interrupt a machine raises, and the interrupts SHALL be exactly these: a
  `Signed:` hash drifted; a file signed in the design batch changed; a Loop-A
  bound is reached; a real service or credential is missing (no live evidence
  can exist); the protocol model check (R12) fails. A judgment SHALL NOT stop
  the run: the role decides it and records it as a `Cn` checkbox in TASKS.md,
  which the CEO ticks at the next batch.
  - *Acceptance*: SKILL.md lists the five interrupts, each with the sensor
    that raises it (`check_tasks.py`, `check_live.py`, the model check);
    `check_tasks.py` accepts `Cn` in Todo or Done and refuses it in progress;
    `orchestrator.md` says a judgment is decided and recorded as a `Cn`, and
    any other question waits for the next batch.
  - *Verify*: local
  - *Property*: none — prose in templates, SKILL.md, roles or adapters; its acceptance is read and grepped, there is no behaviour to model
- **R8** — The Intent batch SHALL carry a pre-authorized action list — each
  irreversible action the run may take on its own (for example "deploy to
  production when every sensor is green") with its condition — and an action
  not on the list SHALL be decided by the role about to act and recorded as a
  `Cn` checkbox, never a stop.
  - *Acceptance*: `requirements.template.md` has a *Pre-authorized actions*
    table (action · condition · environment); SKILL.md Phases 5–6 consult it;
    `Aidlc.tla`'s `JudgmentRecorded` holds (a deploy that was not
    pre-authorized never passes unrecorded).
  - *Verify*: local
  - *Property*: none — prose in templates, SKILL.md, roles or adapters; its acceptance is read and grepped, there is no behaviour to model

### Formal methods — the product
- **R9** — The requirements template SHALL give every `Rn`/`Nn` a `Property:`
  — a formal statement of its acceptance — a *formal level* and a
  *conformance*:
  - levels, weakest first: `tested` (generated-input or stateful property
    testing — sampling, NOT a formal method, and named so), `checked` (model
    checking of a design model, its bounds stated), `proved` (a
    machine-checked proof, unbounded);
  - conformance — how the code is tied to the model: `trace` (real runs are
    logged and the checker accepts every trace as a behaviour of the model),
    `refinement` (a proof that the code refines the model) or `none`.
  A component that `standards.md` marks load-bearing SHALL be at least
  `checked` with conformance other than `none`. A `Property: none` SHALL need
  a reason the CEO signs, as `local` does.
  - *Acceptance*: `requirements.template.md` has the `Property:`, `Formal:`
    and `Conformance:` lines on every example item and the definitions;
    `standards.template.md` has a *Formal verification* section naming the
    load-bearing components, the tool per level and the bounds.
  - *Verify*: local
  - *Property*: none — prose in templates, SKILL.md, roles or adapters; its acceptance is read and grepped, there is no behaviour to model
- **R10** — The framework SHALL ship `framework/tools/check_formal.py`, a
  deterministic sensor that fails a requirement whose formal evidence is
  missing; stale (the code changed since its sha); from a property whose text
  differs from the signed one; below the signed level or conformance;
  `checked` with no stated bounds; failed; without a vacuity run (R11); or
  whose spec/proof sources hold an escape hatch — a proof that is not a proof
  (`sorry`, `admit`, `Admitted`, `axiom`, `assume`, `{:axiom}`, `OMITTED`,
  `assume(false)` and their kin).
  - *Acceptance*: `check_formal.py --self-test` exits 0, each case asserting
    the REASON: no evidence; stale sha; a property edited after signing; a
    level below the signed one; conformance below the signed one; `checked`
    without bounds; a failed check; no vacuity proof; a vacuity run that
    passed; each escape hatch. No hit on a clean set. With `--rerun` it
    re-executes the check and the vacuity run.
  - *Verify*: local
  - *Property*: none — the acceptance is the sensor's self-test: example cases, each asserting the reason it fails; sampling, not a formal method
- **R11** — Every formal check SHALL prove it is not vacuous: its evidence
  SHALL include one run that is expected to fail — a seeded mutant of the code,
  or the negated property — and did.
  - *Acceptance*: the evidence schema in SKILL.md has a `vacuity` block
    (command, observed, result: fail); `check_formal.py` fails evidence
    without it or with a vacuity run that passed.
  - *Verify*: local
  - *Property*: none — the acceptance is the sensor's self-test: example cases, each asserting the reason it fails; sampling, not a formal method

### Formal methods — the protocol itself
- **R12** — The AIDLC protocol SHALL have a formal model in the repo, checked
  in CI at stated bounds, with the fairness it assumes written down, proving:
  - *safety* — (a) no phase starts past an unsigned batch; (b) between
    batches the run stops only on an interrupt of R7; (c) an item reaches
    Done only with live and formal evidence; (d) at most one session acts as
    orchestrator, under lease expiry, concurrent takeover and a holder that
    resumes (`boot.py`);
  - *liveness* — (e) Loop A terminates within its bound; (f) the run never
    deadlocks between batches: it reaches the next batch, Done, or an
    interrupt the CEO sees; (g) an orchestrator is eventually elected once
    the holder is gone.
  - *Acceptance*: CI runs the model checker on each model at its stated
    bounds and every property holds; a CI step proves the check can fail by
    checking a seeded broken variant and expecting a counterexample.
  - *Verify*: local
  - *Property*: Election: AtMostOneActing /\ ActingHoldsTop at 3 sessions, HooksEnd /\ ElectedAfterGone /\ ElectedOnceGone at 2; Aidlc: NoPhasePastUnsignedBatch /\ DoneHasEvidence /\ AtBoundNoProgress /\ AsksOnlyForBatchOrInterrupt /\ JudgmentRecorded /\ StopsOnlyForCEO /\ NeverStuck /\ LoopTerminates /\ BoundInterrupts /\ TroubleReachesCEO
  - *Formal*: checked
  - *Conformance*: none
- **R13** — The model and the code SHALL NOT drift. `boot.py` SHALL be
  trace-validated: sampled real concurrent runs log every step that touches
  the claim, and the model checker SHALL accept each sampled trace as a
  behaviour of the model -- a sample, not every run; exhaustiveness is the
  model's (R12). The phases, batches and interrupts in the AIDLC model SHALL equal the
  sets in SKILL.md.
  - *Acceptance*: CI runs N concurrent `boot.py` elections and takeovers with
    tracing on and checks every trace against the model; a CI step proves it
    can fail by checking a trace of a seeded broken `boot.py` and expecting a
    rejection; `tools/check_repo.py` compares the two sets and fails on a
    difference.
  - *Verify*: local
  - *Property*: every trace of the boot.py runs CI samples with DEVCREW_TRACE (scripted, stampede, seeded concurrent crowds) is a behaviour of Election.tla
  - *Formal*: checked
  - *Conformance*: trace
- **R14** — Autonomy SHALL be an invariant: AGENTS.md SHALL state that the run
  may proceed between batches only on bounds a machine checks, and the
  reviewer SHALL check it.
  - *Acceptance*: AGENTS.md lists invariant 11; `reviewer.md` checks `[1..11]`.
  - *Verify*: local
  - *Property*: none — prose in templates, SKILL.md, roles or adapters; its acceptance is read and grepped, there is no behaviour to model
- **R15** — Whatever the protocol model (R12 d, g) finds wrong in `boot.py`
  SHALL be fixed in this change, and the assumptions the fix still needs
  (timing bounds a model cannot remove) SHALL be stated in
  `framework/session-governance.md`, not left implicit.
  - *Acceptance*: the model of the shipped `boot.py` holds; the model of the
    previous `boot.py` is the seeded broken variant of R12 and yields a
    counterexample; `session-governance.md` names every assumption the model
    takes as a constant.
  - *Verify*: local
  - *Property*: boot.py satisfies AtMostOneActing /\ ActingHoldsTop under assumptions A1-A4
  - *Formal*: checked
  - *Conformance*: trace

## Non-functional requirements
- **N1** — No gate is weakened: every item the CEO signs today is still signed
  (R6), only grouped; every stop that is removed is replaced by a sensor (R7).
  - *Acceptance*: the reviewer checks the R6 mapping table and invariants 1–11
    and finds no loosening.
  - *Verify*: local
  - *Property*: none — prose in templates, SKILL.md, roles or adapters; its acceptance is read and grepped, there is no behaviour to model
- **N2** — Formal methods add to live verification; they never replace it.
  Done needs both (R3).
  - *Acceptance*: invariant 10's text is unchanged; `check_tasks.py` requires
    both sensors.
  - *Verify*: local
  - *Property*: none — the acceptance is the sensor's self-test: example cases, each asserting the reason it fails; sampling, not a formal method
- **N3** — The sensors are stdlib Python and host-neutral; the protocol model's
  checker is a pinned version that runs headless in CI.
  - *Acceptance*: `check_tasks.py` and `check_formal.py` import only the
    standard library; `tools/check_neutral.py` exits 0; CI pins the checker
    version.
  - *Verify*: local
  - *Property*: none — prose in templates, SKILL.md, roles or adapters; its acceptance is read and grepped, there is no behaviour to model
- **N4** — Small on purpose: this change is judged by the auditor against
  invariant 7. TASKS.md is one file; no new role.
  - *Acceptance*: the auditor's verdict has no blocker/high finding.
  - *Verify*: local
  - *Property*: none — the auditor's verdict is a judgment, not a property

## Explicit non-goals
- No history in TASKS.md (git keeps it) and no req→PR→test map (the `Closes`
  lines and the sensors replace it).
- No choice of a product's formal tool in this file: each project's architect
  selects at its Phase 1, after a current web search (invariant 5), and
  writes it into `standards.md`. Candidates include TLA+ (TLC / Apalache),
  Quint, Alloy 6, P, Dafny, Lean 4, Verus, and per-language property-testing
  libraries. For the framework's own protocol models this change picks one
  (see `design.md`).
- No branching-time or strategic properties (CTL / ATL — "the orchestrator
  can force progress whatever the other agents do"): linear-time model
  checking cannot state them. A known limit, recorded, not solved.
- No hook that records the CEO's batch signature from the human's own message
  (as awslabs does with a prompt hook). Worth a later proposal; out of scope
  here.
- No change to the reviewer's cross-vendor rule.

## Constraints & dependencies
- **CEO ruling (2026-10-08), verbatim:** 「好。加進去後直接做」 — on this draft,
  after the four revisions from reading Reasonable's TLA+ article (2026-09-25)
  were proposed: honest formal levels, conformance (trace validation),
  liveness with stated fairness and bounds, an escape-hatch scan. The ruling
  is the signature, recorded under invariant 8. It waives nothing else: CI,
  `qa` against this file and an independent review still run, and the merge
  remains the CEO's.
- **CEO decisions (2026-10-08), recorded under invariant 8:**
  - the ledger keeps only current state — done (no record), in progress (with
    status), todo — in the checkbox format;
  - sign-off is batched in three: intent / design / ship;
  - formal verification covers both the delivered product and the framework's
    protocol.
- The `Property` / `Formal` / `Conformance` lines on each item were added
  while implementing this change, after the ruling, because R9 (which this
  change introduces) requires them of every item. They state how each item
  is verified; no item's intent or acceptance changed. Where an item is prose
  or is proven by a sensor's self-test, it says `none` and why, rather than
  dressing an example test up as a formal method.
- **A correction to the R12 Property after review (2026-10-08):** the model
  replaced `LoopBounded` with `AtBoundNoProgress` and `BoundInterrupts`
  (reviewer round 2, QA), and gained `JudgmentRecorded` with the Cn rule. A
  change to signed text: `check_tasks.py` reported DRIFT until the CEO
  re-signed it (the second ruling below).
- **CEO ruling (2026-10-08, second), verbatim:** 「"不確定就停" 我要求 LLM
  先自我判斷，但是產生 checkbox 讓我判斷。不要一直停下來。或是提前跟我確認。
  這樣效率太差. 全部 commit and sign. 不要再問我簽不簽的問題」 — recorded under
  invariant 8, since it removes stops: a judgment is no longer a fail-closed
  stop but a decision the role makes and records as a `Cn` checkbox; what
  needs the CEO is confirmed up front in the pre-authorized list. It signs
  this file and `design.md` (the design batch).
- This change edits `reviewer.md`, so the reviewer may not review it alone; if
  no other vendor is callable, review runs as a council of independent agents
  with no team memory and is recorded as degraded.
- Depends on 0.9.6 (`check_live.py`), which is not merged yet.

## Verification (invariant 10 applied to this change)
Every item is `Verify: local`: this change touches no external service and no
remote data. The evidence goes under `evidence/`, one file per item, from the
command that proves its acceptance, recorded against the commit that
delivered it.

## Open questions blocking design
None. The formal tool is a Phase-1 choice (see *Non-goals*).
