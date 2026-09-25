# Native iOS preview

SwiftUI, not a WebView. The committed `LazyPromotion.xcodeproj` has a shared
scheme and uses no project generator or third-party runtime dependency. iOS 17+,
iPhone and iPad. Preview identifier: `art.lazying.promotion.preview`.

Products and expandable campaign history use the same dated public JSON snapshot
as Android. The Foundation/CryptoKit model checks the contract, body hashes,
public-link boundaries and unknown outcomes. `ShareLink` opens the native share
sheet only after a tap; there is no automatic send or network client.

## Verification state

Source, manifest/resource references and shared snapshot checks pass on Linux.
**Swift type checking, the XCTest suite, full Xcode compilation and device UI
testing have not been run for this app.** Linux source checks are not substitutes.
No Apple account, provisioning profile, team, paid plan or store record is used.
The preview has no store icon or release qualification yet.

On a Mac with an existing Xcode installation, after checking the shared build
slot and available resources, run these sequentially from the repository root:

```bash
swift test --package-path apps/ios --jobs 2
xcodebuild -project apps/ios/LazyPromotion.xcodeproj -scheme LazyPromotion \
  -configuration Debug -destination 'generic/platform=iOS Simulator' \
  -derivedDataPath apps/ios/build -jobs 2 CODE_SIGNING_ALLOWED=NO build
```

Keep `apps/shared` beside `apps/ios`; both the project and package tests reference
that one fixture rather than maintaining divergent copies. Use a project-owned
test simulator only after compilation passes. Check large text, iPhone/iPad
layouts, navigation, copy expansion and share cancellation; do not submit this
development preview to a store.

The current privacy manifest describes only this bundled-data implementation:
no tracking, collected data or required-reason API usage. Reassess it when adding
persistence, account connections, analytics or network access.
