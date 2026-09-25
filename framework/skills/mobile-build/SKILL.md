---
name: mobile-build
description: How a devcrew role builds a mobile app (native iOS/Android or cross-platform) onto a simulator/emulator and captures screenshots for verification — the mobile equivalent of web-preview. Use whenever the project's platform strategy (see the aidlc skill's platform gate) is a native or cross-platform mobile app rather than a web/backend target. Covers the stack-conditional build/run/screenshot loop; it stores the RULE, not a pinned toolchain version.
triggers: mobile build, ios build, android build, simulator, emulator, flutter build, react native, xcode build, gradle assemble, app screenshot
---

# mobile-build — build & preview a mobile app

This is the mobile counterpart to `web-preview`. A web app previews as a URL in
a browser panel; a mobile app previews as a **build running on a simulator/
emulator**, screenshotted from the device frame. The `web-preview` /
`web-verify` skills do NOT apply to a native app — use this instead.

## Rule 0 — the stack is decided at the platform gate, not here
The concrete stack (Flutter / React Native / Kotlin Multiplatform / native
Swift+Kotlin) is chosen per project at the **platform strategy gate** in Phase 0
and recorded in `requirements.md` / `design.md`. This skill stores the *shape*
of the build loop, not a pinned toolchain. Read the project's decided stack
first, then use the matching column below. Always `web_search` the current
toolchain/command surface before assuming a flag — mobile toolchains move fast.

## The build → run → screenshot loop (stack-conditional)

| Stack | Build | Run on simulator/emulator | Screenshot |
|---|---|---|---|
| **Flutter** | `flutter build ios` / `flutter build apk` | `flutter run -d <device-id>` | `flutter screenshot` or platform tool below |
| **React Native** | Metro + `xcodebuild` / `gradlew assembleDebug` | `npx react-native run-ios` / `run-android` | platform tool below |
| **Native iOS (Swift)** | `xcodebuild -scheme <s> -sdk iphonesimulator` | `xcrun simctl boot <udid>` + install | `xcrun simctl io <udid> screenshot out.png` |
| **Native Android (Kotlin)** | `./gradlew assembleDebug` | `emulator -avd <name>` + `adb install` | `adb exec-out screencap -p > out.png` |
| **KMP** | per-platform (Xcode for iOS, Gradle for Android) | both simulators | both platform tools |

### iOS simulator essentials
- List devices: `xcrun simctl list devices available`
- Boot: `xcrun simctl boot "<udid>"` ; open Simulator.app to see it
- Install: `xcrun simctl install <udid> <path>.app`
- Launch: `xcrun simctl launch <udid> <bundle-id>`
- Screenshot: `xcrun simctl io <udid> screenshot /abs/path.png`
- **Requires Xcode + command line tools on the host.** If unavailable, say so —
  do not claim a build ran.

### Android emulator essentials
- List AVDs: `emulator -list-avds` ; devices: `adb devices`
- Screenshot: `adb exec-out screencap -p > /abs/path.png`
- **Requires Android SDK + an AVD on the host.** If unavailable, say so.

## Verify at the right device sizes
A mobile UI must be checked at **real device classes**, not one size:
- iOS: at least one compact (iPhone SE / mini) and one large (Pro Max), and iPad
  if the app is universal. Check safe-area / notch / Dynamic Island handling.
- Android: a small and a large phone, and check different densities.
Capture a screenshot per device class and show them to the CEO/design gate as
the mobile equivalent of the web hi-fi preview.

## Resource discipline
Simulators and emulators are heavy (each can be >1GB RAM). On a memory-tight
host (`resource_status` first): boot ONE device at a time, build one platform at
a time, and tear down the simulator/emulator when done. Never boot a wide matrix
of devices in parallel on a constrained host.

## What "preview works" means
Not "the build compiled" and not "HTTP 200" — a mobile preview is proven only by
a screenshot from the running app on the device frame showing the actual screen.
Attach the screenshot path; do not assert a screen renders you have not captured.
