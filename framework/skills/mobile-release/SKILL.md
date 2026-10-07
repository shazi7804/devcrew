---
name: mobile-release
description: How the release role ships a mobile app — code signing (certs/provisioning/keystore), fastlane automation, TestFlight and Play testing tracks, store submission package (screenshots, privacy declarations, IAP), staged rollout, and rollback. The mobile counterpart to deploy-web. Stores the RULE and the gates, not a pinned toolchain version. Use when the platform strategy is a native/cross-platform mobile app.
triggers: mobile release, code signing, provisioning profile, keystore, fastlane, testflight, play console, app store submission, staged rollout, app review, privacy nutrition label, data safety
---

# mobile-release — ship a mobile app to users

The mobile counterpart to `deploy-web`. A web release is a deploy to a host you
control; a **mobile release goes through Apple/Google**, needs *their* signing
material and *their* review, and is not "done" until *they* approve it. This is
the hardest, most external part of a mobile pipeline — treat every 🔴 below as a
hard stop.

Unlike every other phase, this one is a **state machine with an external actor in
it**, so the terminal state is not yours to declare:

```
  a versioned, verified build exists
        │
        ▼
  🔴 SIGNING GATE — does the CEO's signing material exist?
        │
        ├── missing ──▶ SUSPEND. Tell the CEO exactly what to provide.
        │               NEVER generate a throwaway cert/keystore: a mismatched
        │               identity locks the app out of every FUTURE update.
        ▼ present
  build the signed artifact       .ipa (gym/xcodebuild) · .aab (bundleRelease)
        │
        ▼  the channel ladder — a first release never skips a rung
     INTERNAL TEST ─────────▶ BETA ────────────────▶ PRODUCTION
     TestFlight internal      TestFlight external    App Store submission
     Play Internal track      (light Apple review)   Play Production track
                              Play Closed/Open
        │
        ▼
  🔴 SUBMISSION GATE — state what goes out, to whom, and the rollback. Then WAIT
     (promoting a staged rollout past its FIRST phase is a 🔴 of its own)
        │
        ▼
  STORE REVIEW ── an EXTERNAL actor decides. "submitted" ≠ "released".
        │
        ├── REJECTED ──▶ loop back to whichever owns the fix:
        │                implementation, OR the submission package.
        │                Never to Phase 0. ──┐
        │   ◀─────────────────────────────── ┘ re-submit
        │
        └── APPROVED ──▶ staged rollout (Play %, App Store 7-day phased)
                         │   halt criteria: crash / ANR spike
                         ▼
                    APPROVED AND LIVE ──▶ only now is the pipeline complete
```

Two properties of this machine that a web deploy does not have: the terminal
state is granted by Apple/Google rather than reached by you, and the back edge
from a rejection is a **re-submission**, not a rollback — see the rollback
reality check below.

## 🔴 The signing gate (external dependency — the CEO owns the keys)
You (the agent) do NOT hold signing material. A real release needs:
- **iOS**: Apple Developer Program membership, a distribution certificate, and a
  provisioning profile for the app id + distribution method. Managed via App
  Store Connect / Xcode.
- **Android**: a release **keystore** (the app's permanent signing identity —
  losing it means you can never update the app) and, for Play, Play App Signing
  enrollment.
- **Store accounts**: App Store Connect (iOS), Google Play Console (Android),
  each with the app record created.

If any is missing, **SUSPEND and tell the CEO exactly what to provide**. Never
generate a throwaway certificate/keystore for a real release — a mismatched
signing identity locks you out of future updates. This is a CEO gate, not
something the agent works around.

## Signing & build automation
Prefer **fastlane** (cross-platform, scriptable, the industry default) over
hand-run Xcode/Gradle steps, so the release is reproducible:
- `fastlane match` (iOS) manages certs/profiles in a git repo — RULE: the CEO
  controls that repo and its passphrase; the agent uses it, does not own it.
- `fastlane gym` / `xcodebuild -exportArchive` → signed `.ipa`.
- `./gradlew bundleRelease` + the keystore → signed `.aab`.
- `web_search` the current fastlane/toolchain commands before running — do not
  assume a flag from stale memory.

## Distribution channels — never jump straight to production
| Stage | iOS | Android |
|---|---|---|
| Internal test | TestFlight internal group | Play Internal testing track |
| Beta | TestFlight external (needs a light Apple review) | Play Closed/Open testing |
| Production | App Store submission | Play Production track |

A first release goes internal → beta → production, not straight to prod.

## 🔴 Store submission package (incomplete = rejected, not warned)
Before submitting, assemble and verify:
- **Release notes / what's new** per locale.
- **Screenshots** per required device class (App Store & Play both mandate
  specific sizes — generate from the `mobile-build` device matrix).
- **Privacy declarations**: iOS privacy nutrition label + `PrivacyInfo.xcprivacy`
  required-reason APIs; Android Data Safety form. These MUST match what
  `mobile-verify` found the app actually collects.
- **Age rating**, category, support URL, marketing.
- **IAP / subscriptions** configured and in the right state if the app monetizes
  (a paid app submitted with unconfigured IAP is rejected).

Submitting to a store, and promoting a staged rollout past its first phase, is a
🔴 CEO decision — state what goes out, to whom, and the rollback, then wait.

## Staged rollout & rollback
- Use **Play staged rollout** (start small %, ramp) and **App Store phased
  release** (7-day auto-ramp) where available, with criteria to halt on a crash/
  ANR spike.
- **Rollback reality check**: you cannot instantly un-ship a store release like a
  web deploy. Rollback means halting the staged rollout, submitting an expedited
  fix, or (Play) a "remove from sale" — state which BEFORE shipping.

## Store review is the true terminal state
"Submitted" ≠ "released". Apple review is typically 1–3 days and can reject on
privacy, IAP, design, or metadata grounds; Play review is faster but also
rejects. Track the review outcome. A rejection loops back to the phase that owns
the fix (Implementation or the submission package), **never to Phase 0**. The
pipeline is complete for a store app only when it is **approved and live**.

## Record for reproducibility
Every release records: version/build number, commit hash, signing identity used,
channel, rollout %, and review outcome. Same commit + same signing material must
reproduce the same artifact.
