# Requirements — devcrew 0.9.6: no fake data, verified live

> Signed intent contract for a change to devcrew's own framework. Every gate of
> this change re-reads this file.
> Status: WAIVED (CEO ruling) — 2026-10-06: the CEO waived the sign-off turn;
> the ruling is recorded verbatim under *Constraints*.
> Scope: feature (framework: `framework/` · `hosts/` · `AGENTS.md` · docs · CI)

## Vision
Delivered work runs on the real services and real data, and the framework can
prove it mechanically. Today an AI implementer can make every sensor green with
fakes and QA passes it, because "has a commit, has an assertion, assertion is
green" is true of a fake. After this change, no requirement passes, closes, or
is reported done without evidence from the real, deployed service.

## Users & context
- Primary user: the CEO, who must be able to trust "done".
- Secondary users: every role agent, and every project devcrew is installed
  into.
- The incident (ttfriday, reported by its orchestrator session on 2026-10-06):
  the backend was never deployed (the CDN returned a placeholder, the API host
  did not resolve, the weather key did not exist), yet two features were closed
  `Closes Rn` and QA said PASS. 244 backend tests ran on fake upstreams; 3610
  UI assertions ran on a fake DOM with fake native bridge, network and storage.
  Exchange rates, demo trips, marketplace and members were hardcoded seeds;
  invites/collaboration had no backend; checkout was UI-only. Phase 5 was
  skipped by a stale project note ("no runtime"). The CEO had ruled "全部接真的"
  earlier; it never became a mechanism.

## Functional requirements (EARS)

- **R1** — The requirements template SHALL give every `Rn`/`Nn` a verification
  level, `live` by default (a missing line means `live`), with `local` only for
  work that touches no external service and no remote data; no level SHALL
  accept a fake. It SHALL list every real service with its credential owner, and
  a missing one SHALL be an open question blocking design.
  - *Acceptance*: `requirements.template.md` has the `*Verify*:` line on every
    example item, the level definitions, and the *Real services & data* table.
  - *Verify*: local
- **R2** — The framework SHALL ship a deterministic sensor that fails when any
  requirement lacks fresh evidence from the real service, or when production
  code carries fakes.
  - *Acceptance*: `framework/tools/check_live.py --self-test` exits 0, and each
    case asserts the REASON it fails, so removing a rule fails the self-test:
    no requirements; no evidence; loopback (incl. `user@`, decimal, IPv4-mapped,
    link-local, a bare service name, a docker-internal host, a query string); a
    target with no host or naming a mock; a host outside `--live-host`; a probe
    that names its target only in a comment; a failed probe; `observed` not
    matching `expect`; `local` evidence where `live` is required; a wrong id; a
    short sha; stale evidence (the working tree changed); a secret in the
    evidence; a `--rerun` whose fresh output does not match; a `mock*`
    identifier (also all-caps, in SQL, in a non-ASCII path, in a non-UTF-8
    file); illustrative-only data; placeholder copy; a TODO to wire it; and
    production importing a test path (JS, Python, Go). Inet shorthand and
    loopback-DNS hosts, public mock services, a probe that reaches another
    host, and an allow line that exempts a whole tree are hits too. Two
    features: one PR's run is scoped, another feature's code makes old
    evidence stale, a passing `--rerun` is fresh proof only when `--deployed`
    proves the environment runs HEAD, and only then does `--record` write it
    back, and production evidence does not overwrite pre-production evidence.
    And no hit on a clean repo, `downsample`, an illustrative diagram, a
    lockfile, a story, or an allowed exemption. Run read-only against the ttfriday repo, it reports the
    production stub import in its backend server and the requirements of
    `ai-itinerary` as unverified.
  - *Verify*: local
- **R3** — QA SHALL run the live sensor first and SHALL fail any requirement
  proven only on a fake; the QA verdict SHALL record each requirement's level.
  - *Acceptance*: `qa.md`, SKILL.md Phase 4 (DO + GATE ①) and the gate anatomy
    name the sensor; `verdicts.template.md` has `sensors.live` and a per-row
    `verify` field, with "below the signed level = FAIL".
  - *Verify*: local
- **R4** — Implementers SHALL ship no fake data in production code, SHALL stop
  and report BLOCKED on a missing service or credential, and SHALL NOT write
  `Closes Rn` without live evidence.
  - *Acceptance*: `frontend.md`, `backend.md` and SKILL.md Phase 3 (DO + GATE ④)
    say so.
  - *Verify*: local
- **R5** — Phase 5 SHALL run whenever the project has a runtime, decided from
  the repo as it is, not from a project note; smoke tests SHALL probe every
  `live` requirement on the deployed service.
  - *Acceptance*: SKILL.md *Scope routing* and Phase 5, and `devops.md`, say so;
    skipping it is a recorded CEO decision.
  - *Verify*: local
- **R6** — No report SHALL call fake-backed work done or green.
  - *Acceptance*: `sitrep.template.md` and `orchestrator.md` require
    `BLOCKED — 未接真服務` naming what is not live.
  - *Verify*: local
- **R7** — A CEO ruling on how work is verified SHALL become a mechanism the
  same day, or the orchestrator SHALL tell the CEO it has not.
  - *Acceptance*: SKILL.md *No fake data* and `orchestrator.md` state it.
  - *Verify*: local
- **R8** — The rule SHALL be a design invariant that the reviewer measures.
  - *Acceptance*: AGENTS.md lists invariant 10; `reviewer.md` runs the
    self-test and checks `[1..10]`; CI runs the self-test.
  - *Verify*: local
- **R9** — Every host adapter SHALL install the sensor into the project and
  verify it.
  - *Acceptance*: `hosts/claude-code.md`, `hosts/kirocrew.md`,
    `hosts/mission-control.md` and `hosts/aidlc-mission-control.skill.md` copy
    it to `.aidlc/tools/check_live.py` and run `--self-test` at verify.
  - *Verify*: local
- **R10** — `standards.md` SHALL say where the rule applies for a project:
  production paths, test paths, the live hosts per environment, the probe per
  service, and the allow file — each one an option of the sensor, so the
  phases can run it: Phase 3 on the PR's `Closes` set against pre-production,
  Phase 5 against production.
  - *Acceptance*: `standards.template.md` *Real data & integrations* names
    `--src`, `--test`, `--env` + `--live-host`, `--deployed`, `--allow`; the
    sensor accepts them and `--only`; SKILL.md says which phase passes which.
  - *Verify*: local

## Non-functional requirements
- **N1** — No weakened gate: this change only adds sensors and rules.
  - *Acceptance*: reviewer checks invariants 1–10 and finds no loosening.
  - *Verify*: local
- **N2** — Host-neutral and stdlib-only.
  - *Acceptance*: `tools/check_neutral.py` exits 0; `check_live.py` imports
    only the standard library.
  - *Verify*: local

## Explicit non-goals
- No change to ttfriday itself. Its own inventory and downgrade of fake
  `Closes` stays with its session (`.aidlc/proposals/2026-10-06-live-verification-gate.md`).
- No new role.
- No attempt to detect hardcoded data that carries no marker word; the
  evidence check covers it (a hardcoded rate cannot produce live evidence).

## Constraints & dependencies
- **CEO ruling (2026-10-06), verbatim:** 「不用簽，你直接做完。我無法接受任何假資料的
  開發。」 Earlier the same day: 「所有的資料跟整合的功能都必須驗證真實資料跟真實服務」.
  The CEO waived a separate sign-off turn for this proposal; the ruling is the
  signature. It is recorded here under invariant 8. It waives nothing else: CI,
  `qa` against this file, and an independent review still run, and the merge
  remains the CEO's.
- This change edits `reviewer.md`, so the reviewer may not review it. Review
  runs as an adversarial council of independent agents with no team memory,
  same vendor (only Anthropic models are callable here) — degraded, and said so.

## Verification (invariant 10 applied to this change)
Every item is `Verify: local`: this change touches no external service and no
remote data. The evidence is under `evidence/`, one file per item, each from the
command that proves its acceptance (the self-test, `check_neutral.py`, a grep),
recorded against the commit that delivered it.

## Open questions blocking design
None.
