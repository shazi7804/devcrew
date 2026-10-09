# Changelog

## 0.9.7 — 2026-10-08

**Autonomy earned by proof: the CEO signs three times, machines check the rest.**
Signed intent: `proposals/0.9.7-autonomy-by-proof/requirements.md` (R1–R15,
N1–N4). The CEO's ruling 「好。加進去後直接做」 is the signature. Design and
tool choice: `proposals/0.9.7-autonomy-by-proof/design.md`.

Why: the CEO wanted the team to run longer without stopping, and stops were
carrying the trust. Comparing devcrew 0.9.6 with awslabs/aidlc-workflows 2.10
showed that several bounds were described as mechanical but had no code: the
intent hash, the drift halt, the loop bound, and the ledger (on one host it
was "not defined"). Autonomy on top of prompt-only bounds is autonomy on trust,
so the bounds became code first.

- **TASKS.md is the only ledger** (R1–R5). It holds Done (one line, no record),
  In progress (status · owner · attempts · next) and Todo, plus a `Signed:` line
  of hashes and the open gate. History lives in git.
  `framework/tools/check_tasks.py` fails on any of these:
  - a missing, duplicated or unknown requirement ID;
  - a Done item without fresh live **and** formal evidence;
  - a bad status;
  - an attempt count past Loop A's bound;
  - a signed file whose hash moved. This is the drift halt, finally as code.
  - a requirement at Loop A's bound (`5/5`, `stalled 3/3`) that isn't
    `blocked on loop-bound`;
  - a design-batch file (`design.md`, an ADR) that moved: `cross-design`.

  `--rerun` re-runs every Done item's live probes and formal checks: stored
  evidence is its writer's claim, a re-run is the proof. A Done item is `check_live --only <ID>` green, code
  scan included (`--src` / `--test` / `--allow` pass through). 51 self-test cases.
  Every host uses it; a host primitive may mirror it.
- **Three batch sign-offs: intent, design, ship** (R6–R8). Every item the CEO
  signed before is still signed, now grouped, and SKILL.md maps each former
  🔴 gate to its batch. Between batches the run stops only on five
  interrupts, each raised by a machine: drift, cross-design (a design-batch
  file moved), loop-bound, missing-service, model-fail.
- **A judgment is never a stop** (the CEO's second ruling). An irreversible
  action that is not on the pre-authorized list, code that departs from an
  unchanged design, a spent budget: the role decides, records a `Cn`
  checkbox in TASKS.md, and goes on. The next batch's SITREP lists every open
  `Cn` for the CEO to tick. What needs the CEO beforehand is confirmed up
  front, in the pre-authorized list. `Aidlc.tla` proves an unauthorized
  deploy never passes unrecorded (`JudgmentRecorded`).
- **Formal methods, honestly levelled** (R9–R11). Every requirement carries a
  `Property:`, a level and a conformance:
  - levels are `tested` (property testing, named as *not* formal), `checked`
    (model checking at stated bounds) and `proved`;
  - conformance is `none`, `trace` or `refinement`.

  `framework/tools/check_formal.py` fails evidence that:
  - is stale, or comes from a property edited after signing;
  - is below the signed level or conformance;
  - is `checked` with no bounds;
  - has no vacuity run (a run that must fail and did);
  - has a proof containing an escape hatch (`sorry`, `admit`, `Admitted`,
    `axiom`, `assume`, `{:axiom}`, `OMITTED` …);
  - has a command that names none of its sources or does nothing;
  - has no `expect`, or output (stored or re-run) that doesn't match it.

  45 self-test cases. Formal adds to live and never replaces it.
- **A re-run proves HEAD, and a prompt is code** (review round 4). Every
  `--rerun` probe and formal check now runs in one throwaway checkout of
  HEAD per invocation, pinned to its commit and reset before each probe, so
  no uncommitted, untracked or ignored file, and nothing an earlier probe
  wrote, committed or set up (index flags, sparse patterns, hooks) can take
  part in it. The no-fake scan and the escape-hatch scan read HEAD's blobs
  from the object store -- only the code, symlink targets and the files a
  check names, streamed, once, before any command runs -- so nothing a probe
  does to a checkout or the object store changes what they see, and a large
  tree costs only its code. A symlink resolves as the kernel does; one that
  leaves the tree, or two names that differ only in case, are reported, not
  guessed. `--src` is read as git reads a pathspec, in both modes.
  Found by a context-free QA and Security round and fixed test-first:
  evidence is stale against HEAD as well as the working tree; a re-run runs
  HEAD's record of the probe; a file behind the repository's own filter
  (LFS) is read as checked out; a probe's background processes die with it;
  the checkout's git dir is recorded before any probe, so a probe that
  removes `.git` cannot turn the reset on the repository around it; every
  case clash and every link that leaves the tree is reported. The sensors' own
  git calls drop the caller's `GIT_*` variables, so run from a git hook they
  cannot write into the user's index or detach the user's HEAD. What the checkout
  holds but cannot be read as it runs is reported over all of HEAD, not only
  `--src`; a submodule a probe initialised makes the checkout be made again.
  Then the whole class closed at once (the CEO's ruling): a re-run refuses a
  working tree with any uncommitted or untracked file, so nothing in it can
  decide what HEAD is judged against (git status runs with fsmonitor, ignoreStat
  and the untracked cache off, and an index flag that hides an edit --
  skip-worktree, assume-unchanged -- is itself unclean; the ledger, the
  requirements and every signed file must be HEAD's byte for byte; the
  sensors' own bytecode is the environment), each probe gets a TMPDIR of
  its own, a formal command gets a probe's environment, one HEAD is pinned
  for the whole re-run (`--record` stamps nothing if HEAD moved), and `--deployed`
  runs in HEAD's checkout. What no reset undoes is stated: a probe runs with the user's
  shell, so it can write outside the checkout and into the repo's shared
  refs and config; a reviewer reads the probe commands. Evidence
  goes stale on any change outside the run's record (the signed contracts,
  TASKS.md, verdicts, evidence JSON): a Markdown file is no longer exempt,
  since a prompt is what this framework ships, and neither is a model or a
  helper kept beside the requirements, or under the state directory.
- **The framework's own protocols, model-checked** (R12–R13, TLA+ / TLC 1.7.4
  in CI):
  - `framework/formal/Election.tla` checks the orchestrator election: safety
    at 3 sessions (10.2M states), liveness at 2.
  - `framework/formal/Aidlc.tla` checks batches, interrupts, Loop A and
    Done-needs-evidence, for safety and liveness under stated fairness.
  - Each model has a seeded broken variant that must fail, for safety and
    for liveness.
  - Sampled real runs of `boot.py` are checked against the model (trace
    validation): concurrent runs log every step with its generation number
    and outcome, and TLC must accept each trace as a behaviour of the model.
    Three mutants must be rejected. This samples runs; exhaustiveness is the
    model's job. A run that broke
    an assumption is re-run and never counted as a pass.
  - `tools/check_repo.py` keeps SKILL.md's stages, batches and interrupts
    equal to the model's.
- **The model found a real bug in 0.9.6's election, and it is fixed** (R15).
  TLC found two acting orchestrators in 14 steps. A holder resuming a stale
  lease refreshed it with `utime`, while a newcomer that had read it as stale
  renamed it away. `rename` and `utime` act on the path, not on the file that
  was read. The race test had passed all along.

  `boot.py` now claims by generation: `ORCHESTRATOR.<n>.claim`, written in
  full and published with `os.link`, is a compare-and-swap, and names are
  never reused. The holder re-wins its own lease once it is older than
  STALE−MARGIN. Any beat may take a free claim, so a crashed orchestrator is
  replaced without a new window.

  A beat now runs after every tool call. Without it, a long autonomous turn
  outlives its lease (assumption A2). The assumptions the fix still needs
  (A1–A5) are written in `framework/session-governance.md` § 8.
- **Invariant 11** in AGENTS.md (R14): between batches the run proceeds only on
  bounds a machine checks.
- **Reviewed across vendors.** The reviewer ran on `gpt-5.6-sol` with no team
  memory and returned REJECT. It found 12 problems, among them a model that
  let build start before the intent batch, a Loop-A bound that passed at
  equality, and formal evidence that `command: true` satisfied. Every
  finding except the two that are the CEO's is fixed
  (`proposals/0.9.7-autonomy-by-proof/design.md` § 6).

## 0.9.6 — 2026-10-06

**No fake data: nothing is done until it runs on the real service.**
Signed intent: `proposals/0.9.6-live-verification/requirements.md` (R1–R10,
N1–N2). The CEO waived the sign-off turn by ruling: 「我無法接受任何假資料的開發。」

Why: on ttfriday every gate passed while the product was fake. The backend was
never deployed, 244 backend tests ran on fake upstreams, 3610 UI assertions ran
on a fake DOM, and the data was hardcoded seeds. Two features were still closed
and reported done. QA's question ("has a commit, an assertion, and is it
green?") is answered yes by a fake. The CEO's earlier 「全部接真的」 was a
sentence, so it never ran.

- **`framework/tools/check_live.py` — a deterministic sensor** (R2). Every
  `Rn`/`Nn` needs `<dir of its requirements.md>/evidence/<env>/<id>.json` from
  a read-only probe against the real, deployed service. Each environment keeps
  its own evidence. The check goes red when evidence is missing or names
  another id, or when the target or any URL in the probe is not live: loopback
  or private in any notation, a bare service name, a reserved, cluster or
  loopback-DNS domain, a public mock service, a mock-named host, or a host
  outside `--live-host`. It is also red when the probe failed, `expect` matches
  anything or `observed` doesn't match it, the sha isn't a full commit, the
  working tree changed since the sha, or the file holds a secret. `--rerun`
  re-runs each probe with only the credentials it names, and its fresh output
  must match `expect`. A service that answers proves the build it runs, not
  HEAD, so a passing re-run is fresh proof (and `--record` writes it back,
  for an item with no other hit) only when `--deployed` — one version probe
  per service, each asking a live host — prints HEAD's sha. It also scans production code (lockfiles and stories excluded) for
  mock/fake/stub/dummy identifiers, illustrative-only data, TODOs to wire
  things up, and imports from test paths (JS, Python, Go). Allow-file lines
  that exempt a whole tree are rejected. `--requirements <feature> --only`
  checks a PR's `Closes` set at Phase 3. The gate hashes the installed copy
  itself and compares all 64 hex with the framework's. 89 self-test cases each assert the reason
  they fail, and a mutation sweep confirmed that deleting any rule fails the
  self-test. Run read-only on ttfriday, it caught the backend server importing
  `tests/stubs.mjs`.
- **`Verify: live` by default** (R1). The requirements template gives every item
  a level. A missing line means `live`; `local` is only for work that touches no
  service and no remote data. No level accepts a fake. A new *Real services &
  data* table lists every service and who owns its credential, and a missing one
  is an open question for the CEO.
- **QA** runs the live sensor first and fails anything proven only on a fake.
  The verdict YAML gains `sensors.live` and a `verify` field per requirement
  (R3).
- **Implementers** may not ship fakes in production code, stop BLOCKED on a
  missing service or credential, and write `Refs Rn` (not `Closes Rn`) until the
  feature is live (R4).
- **Phase 5 can't be skipped by a note** (R5). If the repo has a runtime, Phase
  5 runs. Smoke tests probe every `live` requirement on the deployed service,
  because a health check only shows the service is up.
- **SITREP**: fake-backed work is `BLOCKED — 未接真服務`, never DONE (R6).
- **A CEO ruling on verification becomes a mechanism the same day** (R7).
- **Invariant 10** in AGENTS.md (R8). The reviewer measures it with the
  self-test, and CI runs the self-test as well.
- All three host adapters install the sensor as `.aidlc/tools/check_live.py`
  and verify it (R9). `standards.template.md` gains *Real data &
  integrations*, which covers production paths, test paths, the live
  environment, the probe for each service, and the allow file (R10).

## 0.9.5 — 2026-10-01

**Award-grade design, a readable README, and a framework that names no host.**
Signed intent: `proposals/0.9.5-award-design-docs-neutrality/requirements.md`
(R1–R10, N1). It is the first framework change to start from its own Phase-0
contract.

- **designer reaches award grade by iterating on itself** (R1). It uses
  [impeccable](https://impeccable.style/) (pbakaus/impeccable, Apache-2.0), and
  its bar is the Awwwards / Webby / FWA jury standard. Each round runs
  screenshot → `critique` + `audit` + `npx impeccable detect` → score against a
  weighted rubric → refine, and is recorded in `design-scorecard.md`. The loop
  exits on the bar, or stops at a plateau and reports the gap to the CEO; a
  sub-bar design is never passed off as done. Phase 2 of `SKILL.md` gains step ⑤
  and the scorecard gate.
- **README rewritten** (R2–R5). New sections: setup, how to talk to the
  orchestrator, architecture, the team, native skills, See it work, docs,
  license. Each of the 12 roles has its own page under `docs/agents/`. See it
  work shows only output from commands that were actually run. There is now a
  Traditional Chinese README (`README.zh-TW.md`), with a language switch at the
  top of both.
- **Invariant 9: host- and machine-neutral** (R6, R7). "The 128GB EC2 gateway"
  and other host tool names (`spawn_run`, `ask_question`, `resource_status`,
  the Browser panel, …) had sat in the neutral source since 0.4.0. The reviewer
  reads diffs, and a line that already exists is never in one. Now:
  - `framework/`, `ARCHITECTURE.md` and `docs/` use neutral terms (`spawn`, the
    ledger, the gate primitive, a structured question, a resource check, a
    browser preview), and each `hosts/*.md` maps them.
  - `tools/check_neutral.py` scans the whole tree, not just the diff.
  - `reviewer` REJECTs on a non-zero exit.
- **Invariant 8 written down:** no gate is weakened without a recorded CEO
  decision.
- **A framework change starts at Phase 0** (R8). Loop C is now: signed
  `proposals/<slug>/requirements.md` → PR (`Closes Rn`) → CI → `qa` (against
  the proposal) ∥ `reviewer` → CEO merge. Before this, QA had nothing to verify
  a framework change against, and the reviewer had no intent to judge it by.
- **CI** (R9). `.github/workflows/checks.yml` runs `check_neutral.py` (and its
  self-test), `tools/check_repo.py` (relative links and anchors, role
  frontmatter, reviewer mounts no memory, auditor holds no write tool) and
  `tools/diagram.py check`.
- **boot.py speaks neutral output** (`message` / `context` / `quiet`). The
  Claude Code hook field names moved to `hosts/claude-code.boot_host.py`,
  installed next to it as `boot_host.py`. With the adapter installed, the
  output is byte-identical to 0.9.4, and the race still elects exactly one.
- **check_neutral.py deny-lists widened** after review: host config files and
  hook fields (`CLAUDE.md`, `settings.json`, `.claude/`, `mcp__`, …), any
  `<n>GB` size, GCP / Azure regions, and more file types. Four leaks it then
  found were fixed.
- **impeccable pinned** (`impeccable@4.1.0`) in every host guide. The edit hook
  it installs is shown to the user before it is enabled, and the designer has a
  by-hand path, recorded as `detect: unavailable`, when it cannot be installed.
- **MIT license** (R10).

How it was gated:
- QA failed attempt 1 on R4 and R8: an unsourced example was called "real", and
  four stale descriptions of the self-evolution path were missed by a
  literal-string grep. Attempt 2 passed R1–R10.
- No other vendor's model is available on this host, and the CEO's choice
  (Fable) was not callable. The review therefore ran as the degraded council
  fallback in `SKILL.md`, recorded in the proposal: two independent reviewers
  with no team memory, Opus 5.5 and Sonnet 4.5. It was degraded, because both
  are the same vendor and Opus is the author's own model. Opus returned
  REQUEST-CHANGES: a host leak in boot.py, gaps in the deny-list, impeccable
  unpinned, CI ordering, and a principle missing from the README. All of these
  were fixed in this change. Sonnet returned APPROVE.

## 0.9.4 — 2026-09-30

**Every report is a SITREP.** The roles reported to each other in typed contracts
(verdict YAML, contract paths), but nothing shaped what reached the CEO. In a
real repo the orchestrator's median turn-end message ran ~900 characters, up to
~4,700: done-work first, the CEO's ask in the middle or the last line, bold on
nearly every sentence, internal codes (`N1`, `C2f′`) left undecoded, and worker
messages relayed verbatim. The CEO's verdict: too much noise to decide from.

New: **`contracts/sitrep.template.md`** — a fixed four-field block, adapted from
[joshuaboys/SITREP](https://github.com/joshuaboys/SITREP) (MIT), chosen by the
CEO over Rundown / Attention-kind (alexgreensh/attention-span) and BLUF
(jarbasmoraes/human-comms) from side-by-side rewrites of the same real report.

```
SITUATION  where things stand
ACTION     what was done (max 3 lines)
STATUS     DONE | IN PROGRESS | BLOCKED | FAIL
NEXT       CEO：numbered asks, or 無
           我：what happens next with no input
```

The load-bearing rule is that `NEXT` **always** has a `CEO：` line: one line tells
the CEO whether a message can be skipped.

Wired into: a *Cross-cutting rule* in `SKILL.md` (binds every role), the
orchestrator's Discipline, `verdicts.template.md` (SITREP on top, YAML at the
bottom), both texts `boot.py` injects at session start, and the `CLAUDE.md`
sections in `hosts/claude-code.md` — the injected copy and the `CLAUDE.md` copy
changed in the same commit, as that adapter requires.

## 0.9.3 — 2026-09-26

**The framework assumed one session. Hosts don't.** Every diagram in
`ARCHITECTURE.md` draws one orchestrator, and `hosts/claude-code.md` said it
outright: *"ONE interactive session = the dispatcher."* That is true of the flow
and false of the runtime the moment the human opens a second window — which they
do, because one session is slow and its context window is small. Observed in a
real repo: two sessions each signing a Phase-0 contract for the same intent; two
sessions working one card; one session deciding another was dead and overwriting
live work. The rule *"check who the orchestrator is before you start"* was in
that repo's always-loaded instructions the whole time.

New: **`framework/session-governance.md`** — the neutral spec — and
**`framework/tools/boot.py`**, a stdlib reference implementation.

| Mechanism | Why that one |
|---|---|
| The role is an `O_EXCL` lock, `<state>/claims/ORCHESTRATOR.claim` | Same kernel guarantee as `set -C`. Nothing depends on every session remembering to look first |
| Its **mtime is a lease**, refreshed every turn | Liveness is asserted by the holder, never inferred by an observer |
| Takeover after a stale lease goes through `rename`, never `rm` + create | Two processes can both succeed at `rm`; exactly one can `rename` the same source. That difference is one orchestrator vs. two |
| A human can **pin** the role (`ORCHESTRATOR.pin`) to suspend the election | Asymmetric on purpose: a human overrides the machine, never the reverse |
| Wired to host **lifecycle events**, never to a prompt rule | See below — this is the whole point |

**The constraint that shaped it: no human input, per session, ever.** The first
fix attempt was a boot prompt for the CEO to paste into each new window. Their
verdict was one sentence — *"I am not going to type this every time, your
approach is terrible"* — and it retired an entire class of design. A mechanism
that charges the human per session will be skipped, and a rule the model must
remember to execute is the same failure wearing different clothes. So the
election is a script the harness runs: `start` elects and injects the role,
`beat` refreshes the lease, `end` releases it. Every decision tree leaf is one of
two words; there is no "ask a human" leaf.

**Two things it refuses to do**, because both were measured wrong on a live host:

- **Infer liveness from a socket or pid file.** A socket file was present, its
  process was alive, and it was an orphan — detached from any terminal, absent
  from the host's session list, unreachable. Waiting on it waits forever. Those
  filenames are *process* identity; the session key is the host's `session_id`.
- **Match by name.** A lock said `brand-lockup` while the session list said
  `session-5b` — the same live session under two names, one false positive.

Verified by racing, not reading: 32 concurrent elections → exactly 1
orchestrator; 20 concurrent takeovers of one expired lock → exactly 1 winner;
malformed and empty stdin → exit 0, no lock created; a non-holder's `end` →
nothing released. The copy-pasteable loops are in the adapter, and `AGENTS.md`
Step 4 now asks the installer to run them: *a layer claiming kernel-level mutual
exclusion that was never made to demonstrate it is a claim, not a mechanism.*

**Diagrams: 18 → 25.** The component view (human → lifecycle events → three
modes → lock + hatch → board → injected context), the election decision tree, the
lease timeline (clean exit costs nothing; the threshold only covers crashes), the
`rm`-vs-`rename` race side by side, the "AIDLC assumes / what actually happens"
pair, the human-overrides-machine asymmetry, and the hook wiring in the adapter.
All pass `tools/diagram.py check`. The tree and the race
diagram are the two that pay for themselves: the tree because *every* branch has
to terminate in a role for the mechanism to be a mechanism, and the race because
two `rm`s both succeeding is invisible in prose and obvious in two columns.

Also: `ARCHITECTURE.md` §9 and Layer 2's harness list now name session election;
`hosts/claude-code.md` L1 says N sessions instead of one, carries the four-hook
`settings.json`, and lists "nothing stops a second session from also being the
orchestrator" as a **fixable, non-inherent** degradation; `README.md` adds
principle 8.

**Honest limits**, stated in §8 of the spec rather than discovered later:
`O_EXCL` and `rename` degrade to advisory on NFS/SMB and in sync folders
(Dropbox, iCloud, OneDrive) — this is not a distributed lock. It does not reach a
dispatcher living outside the repo. And it decides *who may decide*, not what to
work on: two workers can still both start one card if the claim namespace is
loose enough that their filenames never collide, which is a separate rule. Only
the Claude Code adapter is wired; KiroCrew and Mission Control dispatch from a
single daemon, so they do not have this problem in the same shape — but neither
adapter has been audited for it here.

## 0.9.2 — 2026-09-26

**Diagrams: 4 → 18.** An audit of every place the docs explain a *mechanism*
found the four existing figures covered the pipeline spine and the host wirings,
while the parts hardest to hold in your head were prose only.

| Where | Added |
|---|---|
| `ARCHITECTURE.md` | where the 3 loops **attach** to the spine · Loop A's bound · the contract graph + hash-checkpoint timeline · new §*Three kinds of state* (contracts vs ledger vs memory) |
| `framework/skills/aidlc/SKILL.md` | **gate anatomy** (① sensors → ② verdict → ③ 🔴 human) · four-jobs cycle · scope routing + floors · magnitude floor as an OR-gate · P0 platform strategy · P∞ decision tree · P3 merge order |
| `framework/skills/mobile-release/SKILL.md` | P6 as a state machine with STORE REVIEW's rejection back-edge |
| `hosts/kirocrew.md` · `hosts/claude-code.md` | the L3/L2/L1 wiring both were missing |
| `AGENTS.md` | one-source→three-trees fan-out + per-host capability comparison |

The two that pay for themselves: the **gate anatomy**, because it replaced an
"(a)/(b)/(c)" prose definition and the *order* is the whole point — a red sensor
fails the gate before anybody reads for intent; and **Loop A's bound**, because
"3 on the same gate" means 3 *stalled* attempts, not 3 attempts.

**`SKILL.md` restructured for the thing it actually is — a prompt payload.** It
is injected whole into all 12 roles on every dispatch, and `backend` was reading
Phase 0.5 market validation, Phase 2 design pixels and Phase 6 store submission.
Now:
- A **role routing table** at the top ("read your row, not this whole file").
  Relevant content per role drops from 100% to **16–31%**.
- Every phase opens with a fixed **`ROLE · IN · DO · GATE · OUT · FAIL`** block,
  so a role pattern-matches instead of parsing prose. Prose survives only where a
  rule needs its *reason* — a rule whose reason is missing gets argued away.
- The 13 harness headings stated their own archaeology (`### Loop bounds (fixes
  finding: unbounded fix loop)`) — provenance from a 0.4.0 audit shipped into
  every prompt forever, with the rule buried behind it. They now state the rule:
  `### Sensors run first, and the model may not overrule them`.
- **Honest limit**: this redirects *attention*, not tokens. The payload is
  unchanged (~7.5k words) because one file still ships whole. Cutting the token
  cost needs per-role phase files, which would change the install step on all
  three hosts — not done here.

**Six already-shipped boxes were misaligned, and nobody could see it.** The
diagrams mix characters of different display width — 🔴 and ①②③④ take two terminal
columns, not one — so a box whose source lines are equal length still renders
ragged, and proofreading cannot catch it. New **`tools/diagram.py`** (`check` /
`fix`) measures columns: it fixed border/content mismatches in `ARCHITECTURE.md`
(a layer box at 63 vs 64, a Phase-3 box at 76 vs 65, four more) and re-flowed
`hosts/mission-control.md`'s 0.8.0 diagram from 84 columns to 80.
- Scoped to **true rectangles only**. Branch connectors (`┌──┴──┐`), arrow spines
  and cycle art use the same characters without being boxes, so there is no width
  to check and a checker that guessed would emit false failures — which is how a
  checker gets ignored. 22 boxes across 21 fences verify; the rest are
  eyeball-only, which is itself a reason to prefer a real box.
- **The repo's first non-markdown file, and it is optional.** Nothing depends on
  it; delete it and the diagrams still read correctly. It exists because those six
  boxes shipped without it.

**Two real gaps surfaced by drawing the Claude Code wiring.** Forcing every
harness rule onto a host primitive left two arrows pointing at nothing, now in a
*Known degradation* section: **no durable ledger primitive** (nothing survives a
`/clear`, so Loop A's bound, both hashes and the requirement→PR→test map silently
reset — reuse the `.aidlc/` layout Mission Control already establishes) and **no
scheduler** (the Phase-∞ meta-review runs when the CEO asks; the docs now say so
instead of implying a periodic review happens).

**Closed a gap in 0.9.1's own claim.** That entry said "no file left in the repo
still describes the old five triggers as current" and named `auditor`'s
frontmatter `description` specifically — but the line still held the five-trigger
text. It is the delegation-trigger text a host routes on, so the stale version was
deciding when the auditor got dispatched. Now matches the signed two-trigger floor.

Touched: `ARCHITECTURE.md`, `AGENTS.md`, `README.md`,
`framework/skills/aidlc/SKILL.md`, `framework/skills/mobile-release/SKILL.md`,
`framework/agents/auditor.md` (frontmatter only),
`hosts/{kirocrew,claude-code,mission-control}.md`, `tools/diagram.py` (new).

## 0.9.1 — 2026-09-26
- **The magnitude floor is now two size triggers, not five.** `> 1000 changed
  lines` and `> 20 changed files` stay; *any new runtime dependency*, *spans ≥ 3
  modules / alters deploy topology*, and *scope is `greenfield`/`refactor`* are
  removed from the framework defaults and become **opt-in per project** in
  `standards.md`. CEO decision, recorded here with its reasoning.
  - Why: both surviving triggers are read straight off `git diff --shortstat`, so
    neither can be argued with at the gate. The three removed ones each needed a
    judgment call ("is this ≥ 3 modules?", "is this really a refactor?"), and a
    trigger that needs arguing is a trigger that gets argued away — or that fires
    on changes nobody thinks warrant an audit, which trains the team to ignore it.
  - **What this gives up, stated rather than hidden**: a size floor cannot catch a
    small expensive change — a one-line `<script src>` pulling in 200 KB, a loop
    turned O(n²), one line added to `package.json`. The docs now say so in every
    place the floor is described, instead of implying the floor is complete.
    Those cases are covered earlier (the implementer roles' reuse-first,
    no-new-runtime-dependency rule) and, for dependencies, by the **Security**
    floor, which has no size condition. `auditor.md` also gains a standing
    instruction: if you notice one while auditing a large diff, report it anyway
    and recommend the project add that trigger to its own `standards.md`.
- **`reviewer` invariant 7 tightened in the same change.** Removing a trigger is
  itself a loosening of a safety floor, so the review checklist now states that
  raising a threshold *or removing a trigger* is a CEO decision recorded in
  `standards.md` with reasoning — an agent doing either on its own authority, or a
  change that drops a trigger without saying what catches that case instead, is a
  REJECT. This change complies with the rule it adds.
  - The rule is **enforceable, not aspirational**: the skill's *Magnitude floor*
    section now carries the deterministic check the reviewer runs — did the diff
    delete a trigger row or raise a number, and does the SAME diff record the CEO
    decision, the reasoning and what is no longer caught? Missing ⇒ REJECT, with
    no judgment call. (Added after a cross-vendor review of this very change
    objected that the new invariant said what was forbidden but not how it would
    be caught.)
- Touched: `framework/skills/aidlc/SKILL.md` (floor table + an explicit note on
  what the floor does not catch),
  `framework/skills/aidlc/contracts/standards.template.md` (audit-trigger bullet,
  with the removed triggers listed as suggested opt-ins),
  `framework/skills/aidlc/contracts/verdicts.template.md` (`trigger` enum),
  `framework/agents/{orchestrator,auditor,reviewer}.md` — including `auditor`'s
  frontmatter `description`, which is the delegation-trigger text a host reads, so
  no file left in the repo still describes the old five triggers as current —
  `AGENTS.md`, `README.md`,
  `ARCHITECTURE.md`, `hosts/claude-code.md`,
  `hosts/aidlc-mission-control.skill.md`.

## 0.9.0 — 2026-09-26
- **New role `auditor` (Code Quality & Efficiency Auditor) — the waste gate on
  product code.** Closes a real hole: nothing in the pipeline asked *"was this the
  amount of code it takes, and does it cost what it should to run?"*. QA proved
  intent, Security proved safety, and `reviewer` explicitly covers only devcrew's
  own framework — so an implementer could ship a diff that was green, traceable
  and CVE-free while being twice its needed size, re-implementing helpers that
  already existed, and issuing a query per row. The auditor audits the delivered
  diff in exactly six categories (redundancy/dead code · duplication & missed
  reuse · over-abstraction · hot-path inefficiency · running cost · dependency
  weight) and is explicitly barred from style nits (lint owns those), intent (QA),
  vulnerabilities (Security) and re-litigating architecture (it escalates instead).
- **It runs in Phase 4 beside QA and Security, but only on big changes** — a new
  **magnitude floor** joins the existing safety floors, so it applies whatever the
  scope claims to be (a "bugfix" that rewrites 1500 lines is not small). The
  trigger is a deterministic measurement, not a judgment:
  `git diff --shortstat <base>...HEAD`. Framework defaults — > 1000 changed lines
  (excluding lockfiles/generated/vendored), > 20 files, any new runtime dependency,
  ≥ 3 modules / a deploy-topology change, or `greenfield`/`refactor` scope — are a
  fallback only: the real thresholds live in the project's `standards.md`, per the
  "numbers belong to the project" invariant. Fail-closed: near the threshold or
  unmeasurable ⇒ audit.
- **Graded verdict, so the gate is usable.** New efficiency-audit block in
  `contracts/verdicts.template.md`: `blocker`/`high` set `blocks_gate` and fail
  Phase 4 back to Phase 3; `medium`/`low` are logged as tech debt in the ledger and
  do not block. Discipline built into the role: a perf/cost claim with no
  measurement is medium at most, and every finding must carry a concrete fix plus
  the saving — "a finding without a fix is an opinion".
- **The auditor holds no write/edit tool, by design** — an auditor that fixes its
  own findings is auditing itself, so the orchestrator routes findings to the
  implementing role. Enforced per host: Claude Code pins its `tools` list (never
  omit it to inherit all), KiroCrew adds a write-deny rule, and Mission Control
  records an honest degradation — `agents.json` has no per-agent tool allowlist, so
  there the prohibition is instruction-only and must be reported as such.
- **Prevention, not only detection**: `frontend` and `backend` each gained a
  reuse-first clause (search the repo before writing; no abstraction with one
  implementation, no knob nothing sets, no layer "for later") naming the concrete
  costs they own — batching/indexing/pagination and loop-invariant work on the
  backend, re-render/re-fetch storms and bundle size on the frontend — and pointing
  at the budget they will be audited against.
- **`standards.md` gained a *Code quality & efficiency budget* section** (audit
  trigger, performance budget, running-cost ceiling, dependency policy, duplication
  tolerance, blocking rule), so the CEO signs the numbers at Phase 1 and the
  auditor may not invent thresholds. New **design invariant 7** ("waste is a gate
  failure, not a style note") with a matching `reviewer` check so a future
  self-evolution pass cannot fold the auditor into QA, downgrade it to advisory, or
  quietly raise its floor out of reach. Also separated two things that were easy to
  conflate: the harness `Budgets` section governs the cost of *running the team*;
  the auditor governs the cost of *the code the team produces*.
- Roster is now 12 roles; README/AGENTS/ARCHITECTURE/host adapters updated in step.

## 0.8.1 — 2026-09-26
- **Closed a 0.7.0 gap: the standards layer was only half-installed.** That entry
  claimed "Implementation/QA/Release all read `standards.md`", but only
  `architect`, `devops`, and `reviewer` mentioned the contract — `frontend`,
  `backend`, `qa`, and `release` never did, so on a fresh install three of the
  four consumers would never open the file the CEO signed. Each now reads it with
  a role-specific clause naming the sections that bind it: frontend (naming, API
  call style, client observability, what may not be logged), backend (API contract
  style, schema source + migration tool, security/observability baselines), qa
  (re-checks the **standards hash** for drift and traces the `Nn` conditions that
  live in `standards.md` rather than `requirements.md`), release (environments +
  promotion path decide the channel, agreed rollback, compliance regimes drive the
  store declarations, observability gates a staged rollout). In all four, a
  divergence is a gate failure — the fix is to get the standard re-signed, not to
  deviate quietly.

## 0.8.0 — 2026-09-26
- **Third host: Mission Control** (`hosts/mission-control.md` +
  `hosts/aidlc-mission-control.skill.md`). On mc the JSON files are the bus, so
  the harness is realized as data: neutral `spawn` → tasks with `assignedTo` +
  `blockedBy`; 🔴 CEO gate → a **pending row in `decisions.json`** (nothing
  dispatches a task that has one, so the gate physically suspends the run);
  ledger → `missions.json` `taskHistory` + `loopDetection`; budgets →
  `daemon-config.json`; outward P5/P6 actions → Field Ops tasks with
  `approvalRequired`. The AIDLC protocol installs as a skill-library entry that
  is injected into every role prompt.
- **Three-layer wiring diagram** in the adapter: mc as the runtime (JSON bus, the
  `scheduler → dispatcher → prompt-builder → security → runner` chain), devcrew as
  the AIDLC flow on top, and the adapter in between shown as what it really is —
  half a one-time install transform (which source file becomes which host file),
  half a data convention that mc's own functions enforce. Every box is labelled with
  the real file/function, plus a second diagram for how board mode cuts the daemon
  out. Recorded there: the role prompt is assembled from `agents.json` +
  `skills-library.json` by `buildTaskPrompt()` — `.claude/commands/<id>/user.md` is
  a mirror read only by `buildScheduledPrompt()`, never the dispatch path; skill
  links resolve from both `agent.skillIds` and `skill.agentIds`; `task.notes` IS
  injected into the prompt, which is why the contract path and intent hash go there.
- **Two install modes, because mc has no per-project cwd.** The daemon pins
  `cwd` to the mc repo root and spawns a non-interactive `claude -p`, so when the
  live data dir belongs to another product repo the adapter installs **board
  mode**: mc is the CEO's board and the interactive session dispatches. Only when
  the mc repo itself is the workspace does the daemon run the roles.
- **Data-dir trap documented as Step 0**: the live directory is
  `MC_DATA_DIR` / `.mc-data-dir` / `<app root>/data`; the repo's
  `mission-control/data/` is seed data, and installing there silently changes
  nothing the running app sees.
- **Honest degradation recorded**: mc can only spawn the `claude` binary
  (`ALLOWED_BINARIES`) and has no per-agent model field, so the self-evolution
  reviewer's cross-vendor rule (invariant 4) cannot be met on that host. Per
  ARCHITECTURE §7 the change is reviewed on KiroCrew or HELD unmerged with a
  pending decision — never silently self-approved.
- `AGENTS.md` host detection gains a Mission Control row plus a precedence rule
  (a mc workspace also has `.claude/`; install the mc way — the Claude Code
  artifacts are a subset).

## 0.7.0 — 2026-09-26
- **Standards layer (single source of truth)**: new `standards.md` contract
  (contracts/standards.template.md) produced WITH the CEO at Phase 1 and locked
  by a "standards hash" like the intent hash. It holds the per-project
  cross-cutting standards the whole team follows: deploy/environment targets, API
  contract style, DB schema source, compliance, naming, observability, security
  baseline. Implementation/QA/Release all read it; a divergence is a gate failure.
- **De-hardcoded deploy target**: removed "Local for test → AWS for production"
  from framework source (devops/reviewer/ARCHITECTURE/README/AGENTS invariant 6).
  The concrete env is the product's, defined in standards.md — the framework
  stores only the rule, not the cloud.

## 0.6.0 — 2026-09-25
Harness enhancements from a survey of recent AI-DLC / multi-agent guidance
(AWS AI-DLC methodology, GitHub multi-agent engineering, spec-drift research):
- **Scope routing**: Phase 0 classifies work (greenfield / feature / bugfix /
  hotfix / refactor / chore) into a `Scope:` field; a scope→phase table decides
  which phases run, so a typo fix no longer walks the full P0–P6 spine. Safety
  floors force a phase back in (ADR change→Architect, auth/data→Security,
  UI→Design) whatever the scope; skipped phases are logged, not dropped.
- **Structured verdict schemas** (`contracts/verdicts.template.md`): QA,
  Security, architecture-change review, self-evolution reviewer, and market
  analyst each end with a machine-checkable YAML verdict block. The orchestrator
  parses it to decide the gate; a missing/malformed block fails the gate.
- **Deterministic sensors**: every gate runs real lint/typecheck/test/build and
  dep/secret scans as commands FIRST (green before any LLM judgment), so
  "CI green" is observed output, not a claim.
- **Traceability**: PR/commit messages carry `Closes Rn`; QA builds a coverage
  table (requirement→PR→test) and the orchestrator keeps the map in the ledger.
  An Rn with no PR, or a PR claiming no Rn, is a gate failure — turning silent
  spec/code drift into a detectable one.

## 0.5.0 — 2026-09-25
- **Mobile AIDLC**: the pipeline now handles native/cross-platform apps, not just
  web/service targets. Added a 🔴 platform-strategy gate at Phase 0 (iOS/Android/
  both, min OS, native vs cross-platform — the concrete stack is per-project,
  never hardcoded in source). Design gains dual HIG + Material 3 guidance; Frontend,
  QA, and Security gain conditional mobile clauses.
- **New role `release` (Release Manager)**: owns each release's version,
  changelog, code signing (Apple certs/profiles, Android keystore), distribution
  channel (TestFlight / Play tracks / store submission), staged rollout, and
  rollback — distinct from DevOps (runtime). Pipeline split: Phase 5 Deploy
  (runtime) + Phase 6 Release (ship artifact). Store review is the true terminal
  state ("submitted" ≠ "released").
- **Architecture-change guard**: a mid-flight change to a signed ADR is
  re-reviewed by architect (llm-council for load-bearing reversals) and
  escalates to a 🔴 CEO/human gate when it crosses a signed boundary (breaks a
  requirement, changes platform strategy, or reverses a CEO-approved ADR).
  architect is now a standing guardian, not only a Phase-1 role.
- New skills: `mobile-build` (simulator/emulator build + screenshot, the mobile
  web-preview), `mobile-verify` (device/OS matrix, permissions, deep links,
  offline, mobile security — the mobile web-verify), `mobile-release` (signing,
  fastlane, tracks, submission, staged rollout — the mobile deploy-web).

## 0.4.0 — 2026-09-20
- Harness hardening: closed 11 AIDLC audit findings — loop bounds (3/5 fix-loop
  cap), budgets, CEO-gate suspension mechanism, intent hash (drift lock),
  contract schema checks, independent gate verification, security left-shift,
  reviewer availability fallback, retrospective capture.
- Added ARCHITECTURE.md (flow, harness layers, the three loops).
- New role analyst (Market Analyst): Phase 0.5 market-validation gate
  with live research, charts, and a GO/PIVOT/NO-GO verdict before build spend.

## 0.3.1 — 2026-09-19
- Reviewer vendor RULE (no hardcoded version in source): dev team = Anthropic, so
  reviewer runs the strongest OpenAI model currently available. The
  installer resolves this to a concrete model version at install time by querying
  the host's model catalog and pins that version into the generated agent
  artifact only. A future clone re-resolves to whatever is strongest then.

## 0.3.0 — 2026-09-19
- Removed the GitHub Action / Bedrock external-review path.
- Self-evolution review now happens INSIDE AIDLC via a new role, reviewer,
  dispatched on a DIFFERENT model family than the change's author and with no team
  memory mounted (unbiased). It never reviews its own change and never merges; the
  CEO makes the final merge.

## 0.2.0 — 2026-09-19
- Self-evolution is now reviewed by an INDEPENDENT external reviewer, not by
  devcrew itself: a GitHub Action (.github/workflows/framework-review.yml) runs
  a Bedrock model from a different family on every PR touching framework/, hosts/,
  or AGENTS.md, checks it against the design invariants, and posts a verdict.
- devcrew NEVER pushes main or self-merges framework changes; the CEO merges.
- Added docs/self-evolution-review.md (flow + one-time GitHub/OIDC/branch-protection setup).

## 0.1.0 — 2026-09-19
- Initial devcrew AIDLC team: orchestrator + 7 role agents (Architect, Design,
  Frontend, Backend, QA, Security, DevOps).
- AIDLC collaboration protocol (phases, gates, contract hand-offs, adversarial
  decision points, gated self-evolution).
- Host-neutral source under framework/ with KiroCrew and Claude Code adapters.
- Shared team memory (lessons, ADRs, retrospectives).
- AI-bootstrap install via AGENTS.md (no human-run installer).
