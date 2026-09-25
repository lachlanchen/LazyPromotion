# Native Android preview

Kotlin/Compose, not a browser wrapper. Debug identifier:
`art.lazying.promotion.preview`. This is an offline campaign-history preview,
not a public product release or an automated publisher.

One bundled JSON snapshot is shared with iOS. The parser checks schema version,
read-only capabilities, supported public URLs, published-copy hashes and unknown
outcome values. No account, analytics SDK, network permission, background job or
provider secret is included. External links and the native share chooser require
a deliberate tap; opening the chooser does not send a message.

## Build

Reuse installed JDK 21, Android SDK 36 and Gradle 8.14.3. No toolchain download
is performed; missing cached dependencies are an explicit offline build error.
Check available memory and existing project builds before compiling.

```bash
bash apps/android/build.sh :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
```

The launcher locks the project against overlapping builds, caps Gradle workers
at two and uses a short-lived daemon. Override `ANDROID_HOME`, `JAVA_HOME` or
`GRADLE_HOME` to point to another existing installation. It never stops another
project's process. Release tasks are disabled; debug signing does not configure
Google Play.

Output: `app/build/outputs/apk/debug/app-debug.apk` (ignored by Git).
Five JVM contract tests and the debug build passed on September 26, 2026 HKT.
Lint has no errors and three warnings: newer target API available, Android's
backup-rule recommendation and a URI extension style suggestion. Target/API and
backup behavior need a release-specific review, not a suppressed warning.

The API34 emulator UI check also passed: both products, unknown outcomes,
expand/collapse and native share chooser, with no recipient selected or message
sent. Product and share-sheet screenshots were visually reviewed. Physical
devices, tablet layouts, large text and accessibility remain unqualified.

## UI review

Use one project-owned emulator called `LazyPromotion_Review_API34`, reusing an
installed system image. The finite check refuses physical devices and other
projects' emulators:

```bash
python3 scripts/test-app-android-preview.py --adb /path/to/Android/Sdk/platform-tools/adb --serial emulator-5590
```

It checks both products, unknown outcomes, published copy and the system share
chooser without selecting a recipient. Screenshots go under ignored `.local/`.
It force-stops only this preview; the operator must also stop the emulator and
its session-owned desktop after inspection. No physical-device or store claim
follows from an emulator check.
