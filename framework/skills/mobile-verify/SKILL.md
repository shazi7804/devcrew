---
name: mobile-verify
description: How devcrew QA and Security verify a mobile app against the signed requirements — device matrix, OS-version matrix, runtime permissions, deep links, offline/sync, background tasks, and mobile-specific security (keychain/keystore, cert pinning, ATS, privacy manifest). The mobile counterpart to web-verify. Use when the project's platform strategy is a native/cross-platform mobile app.
triggers: mobile verify, device matrix, ios testing, android testing, app permissions, deep link test, offline test, mobile security, keychain, cert pinning, privacy manifest
---

# mobile-verify — verify a mobile app

The mobile counterpart to `web-verify`. Verifying an app is NOT verifying a web
page: there is no single browser to check, there is a matrix of devices and OS
versions, and there are OS-mediated surfaces (permissions, background, deep
links) a web app never has.

## QA — the device & scenario matrix
For every `Rn`/`Nn` acceptance condition, verify against the **built app on real
device classes**, not one simulator:

1. **Device matrix** — at least a compact + a large phone per platform; iPad if
   universal. Check layout, safe-area/notch/Dynamic Island, and touch targets.
2. **OS-version matrix** — the minimum supported OS (from the platform gate) AND
   the current OS. A feature that works on iOS 18 but crashes on the declared
   minimum is a FAIL.
3. **Runtime permissions** — camera, location, notifications, photos, mic:
   verify the request flow, the DENY path, and "changed in Settings later". A
   permission the app never gracefully handles being denied is a FAIL.
4. **Deep links / universal links / app links** — cold start and warm start into
   a deep link resolve to the right screen.
5. **Offline & sync** — airplane mode behavior, queued actions, conflict
   resolution on reconnect (if the design promises offline).
6. **Background & lifecycle** — background/foreground transitions, push
   notification handling (foreground vs background vs killed), background refresh.
7. **Interruptions** — incoming call, low battery, low memory kill + restore.

Produce a pass/fail table: requirement → device/OS → evidence (screenshot or
log) → verdict. A requirement with no evidence on the required device classes is
a FAIL.

## Security — mobile-specific surface (on top of the standard scan)
The standard dependency/secret/authz scan still applies. ADD:
1. **Secret storage** — secrets in iOS Keychain / Android Keystore, never in
   `UserDefaults` / `SharedPreferences` / plaintext / bundled in the binary.
2. **Certificate pinning / ATS** — TLS to the backend; iOS App Transport
   Security not globally disabled; pinning where the design requires it.
3. **Privacy manifest / data safety** — iOS `PrivacyInfo.xcprivacy` declares the
   data collected + required-reason APIs; Android Data Safety form matches actual
   collection. A mismatch is both a security AND a store-rejection risk.
4. **Binary hardening** — no debug logging of sensitive data, no test endpoints
   or debug flags left on in the release build, obfuscation where warranted.
5. **Permission scope** — the app requests only the permissions it actually uses
   (an over-broad permission is a review-rejection risk and a privacy finding).

Any blocker/high stops the release gate. The loop-back is to Implementation,
never to Phase 0.

## Resource discipline
Booting devices is heavy. On a memory-tight host (`resource_status` first),
verify one device class at a time and tear it down; do not spin up the whole
matrix at once.

## What "verified" means
Not "unit tests pass" — every required acceptance condition proven on the
required device/OS classes with attached evidence, plus the mobile security
surface cleared. Anything unproven on a required device class is unverified.
