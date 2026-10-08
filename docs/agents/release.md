# release — Release Manager

> Owns the shippable artifact and its journey to users: version, signing,
> channel, rollout and rollback.

[← The team](../../README.md#the-team) · Source prompt:
[`framework/agents/release.md`](../../framework/agents/release.md)

## At a glance

| | |
|---|---|
| **Phase** | 6 |
| **Runs when** | Something ships to users: a mobile app, a store build, or a versioned release |
| **Reads** | The verified build · `standards.md` 🔒 (promotion path, rollback, compliance, observability) |
| **Produces** | Version and changelog, a signed artifact, the channel, a staged-rollout plan, the store package, and a rollback path |
| **Gate** | The artifact is signed and on its channel. A store app counts only once it is **approved and live**; "submitted" is not "released" |
| **Tools** | read · write · edit · shell · search · web |
| **Skills** | aidlc · mobile-release · deploy-web · artifact-deploy · web-verify |
| **Memory** | Shared team memory |

## What every release produces

1. **Version and changelog**, traced to the requirements and PRs it closes.
2. **A signed artifact**: an iOS `.ipa`, an Android `.aab`, or an immutable
   web build.
3. **The right channel**: internal test, then beta (TestFlight or a Play
   track), then production. A first release never goes straight to production.
4. **A staged rollout**, with criteria for advancing or halting.
5. **A store submission package**: notes, screenshots, privacy and Data Safety
   declarations, age rating and IAP config. An incomplete package fails the
   gate.
6. **A rollback path**, stated before shipping.

## 🔴 What it brings to the Ship batch

- **Signing**: the certificates and keystore belong to the CEO. If they are
  missing, that is the `missing-service` interrupt: it suspends and asks. It
  never fakes them.
- **Store submission and rollout promotion**: it states what goes out, to whom,
  and how to roll back. The CEO signs it in the Ship batch, or pre-authorized
  it with a condition in the Intent batch. Anything else it decides and
  records as a `Cn` checkbox for the CEO's next batch.

## What it will not do

- Ship a red build. It sits downstream of QA, Security and the Auditor.
- Ship past a divergence from `standards.md`.

## Where it sits

```
Phase 4 PASS (+ devops runtime) ──▶ release ──▶ 🔴 CEO ──▶ users / store
```
