# security — Security

> Finds security problems before they ship, and blocks deploy and release on
> real risk.

[← The team](../../README.md#the-team) · Source prompt:
[`framework/agents/security.md`](../../framework/agents/security.md)

## At a glance

| | |
|---|---|
| **Phase** | 4, in parallel with `qa` and `auditor`. Its floor pulls it into any scope that touches auth, data or secrets |
| **Reads** | `design.md` (including its threat model) · the implementation PRs |
| **Produces** | Findings by severity, and the Security verdict YAML |
| **Gate** | Zero blocker/high findings. A blocker or high stops **both** Phase 5 and Phase 6 |
| **Tools** | read · write · edit · shell · search · web |
| **Skills** | aidlc · mobile-verify |
| **Memory** | Shared team memory |

## What it does

1. **Threat-models the surface**: entry points, trust boundaries, data flows,
   and what an attacker would target.
2. **Dependency scan**: known CVEs, loose version pins, typosquat-looking names.
3. **Secret scan**: code, config and git history.
4. **AuthN/Z review**: sessions, input validation, SQL, command and XSS
   injection, and sensitive data.
5. **Runs the scans as commands.** They are deterministic sensors, not
   eyeballing.

On a mobile app it also checks: Keychain / Keystore (never `UserDefaults`), TLS
and ATS, certificate pinning, a privacy manifest and Data Safety declaration
that match the app's real behavior, no debug flags in the release build, and
least-privilege permissions.

## What it will not do

- Weaken a security control to make a check pass.
- Fix the code itself. It reports the risk and the fix, and the work loops back
  to implementation.

## Where it sits

```
frontend · backend PRs ──▶ qa ∥ security ∥ auditor ──▶ gate ──▶ devops / release
```
