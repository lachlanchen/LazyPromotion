# LazyPromotion client boundaries

- iOS uses SwiftUI and Android uses Kotlin/Compose. Do not substitute WebViews.
- The versioned public workspace contract is shared with the web client.
- Native previews currently use `shared/workspace-preview.json`: a dated,
  bundled copy, not a live account connection or a new publication.
- Never bundle the operator database, provider configuration, browser sessions,
  private receipts, source transcripts or credentials.
- Discovery, approvals, publishing and payments are not enabled in this preview.
  Do not add convincing-looking inactive send buttons or invented analytics.
- Share public links only through a deliberate user action. No background sends.
- Reuse installed SDKs. No app-store registration or signing is part of a debug
  build. Keep generated builds and runtime evidence outside Git.
- Preserve separate evidence for compilation, UI/device testing and public release.
