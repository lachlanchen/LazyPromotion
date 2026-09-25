# LazyPromotion app: development direction

September 26, 2026 (Hong Kong). Product work in progress, not a shipped app.

## What it should do

Help an independent developer turn an existing app into a small, appropriate
promotion campaign: establish what actually ships, find people with the matching
problem, prepare useful material, review the exact destination and wording, then
record what happened. L & N and Bunko are the first real projects used to test
this workflow. Building this interface must not stop their promotion.

This is not a mass-comment tool or a promise of automatic customers. Discovery,
matching, draft preparation, owned-channel scheduling and evidence collection
can reduce work. Community replies still need contextual review; approved
first-party schedules and replies to strangers are separate permissions.

## Lessons verified from Musia

Read the requested development session without resuming, interrupting or sending
it work. Checked its report against the implementation at Musia commit
`f740ae3f06fe2fae7836dd1abd182621e8f95df4`, particularly
`apps/README.md`, `apps/AGENTS.md`, `docs/learning-api.md`,
`docs/learning-delivery.md` and the Swift data models. The rollout remains
private and is not included here.

- Use native SwiftUI on iOS and Kotlin/Compose on Android, plus a separate PWA.
  Share the data contract, not a WebView wrapper.
- Build around one complete, useful workflow before adding every capability.
- Keep the public product separate from the private workstation/agent runtime.
  Musia's isolated learning API is a useful example: it does not publish its
  Studio, filesystem or generation controls.
- Distinguish a build from device qualification, internal testing, store review
  and public release. Musia's delivery record explicitly retains an unresolved
  iOS audio test; compilation is not proof of a working user experience.
- Reuse installed SDKs and build infrastructure, but keep app identifiers,
  signing material, provider permissions and release records project-specific.
- Represent missing evidence as unknown, not as an invented result.

Musia's own reference note names LazyOracle and AiMemo for native-app patterns;
Bunko, L & N and EchoMind for store operations; and LazyEdit/LazyEdge for
deployment. These are its documented sources, not a claim that every associated
session has been independently reviewed here. For LazyPromotion, reuse the
client/API separation and release discipline, not Musia's music-specific
features or another app's signing configuration.

Musia files and its live session were not modified. Its prices, permissions and
release decisions do not set prices or grant store approval for LazyPromotion.

## First complete workflow

1. Add a product's official links, one audience and a concrete problem it solves.
2. Review shipping features, price, useful media and unsupported claims.
3. Inspect an opportunity alongside its source, date and community rules.
4. Edit one channel-specific draft; preview full text and destination together.
5. Approve that exact revision for that destination and account. Edits invalidate
   approval. Scheduling and sending return durable receipts; uncertainty never
   triggers a blind retry.
6. Review actual feedback and distinguish delivery, visits, installs and money.

Four main screens are enough initially: **Products, Opportunities, Review,
Results**. Native share sheets and local draft editing should provide useful
mobile functionality, not merely links to a website. Read-only browsing can be
offline; an offline action must never silently turn into an approved send later.

## Reuse instead of rebuild

| Existing component | App role |
| --- | --- |
| `catalog.json`, campaign files | Product facts and reviewed public history |
| `promotion.py`, `community-policies.json` | Matching, draft state, approval binding and known restrictions |
| `network.py`, private evidence graph | Source-to-project relationships, exposed only through deliberate projections |
| `browser.py`, `desktop_lease.py` | Private operator-side execution, never shipped in a public client |
| Existing Postiz workflow | Reviewed first-party scheduling through an account-scoped backend adapter |
| Owned-channel monitors | Provider observations, not install or payment attribution |

The existing local operator database is not a multi-tenant backend. Do not put
it, its approval tokens, browser cookies, customer details or Postiz credentials
behind a public endpoint. A hosted edition needs authentication, tenant isolation,
scoped provider authorization, encrypted secret storage, revocation, deletion,
an action journal and idempotent publication reconciliation first.

## Implemented foundation

`app_workspace.py` projects four explicitly selected, already-public campaign
records into a versioned, read-only JSON view for the future clients. It does
not scan all campaigns or read the private database. It includes product links,
published copy, receipts and the recorded visibility level. Unknown installs,
customers and revenue are `null` with `not_connected` status, never fabricated
zeros or inferred from the number of publications.

```bash
python app_workspace.py --project bunko
python app_workspace.py --project l-and-n
python -m unittest discover -s tests -p 'test_app_workspace.py'
```

`app_api.py` now exposes this exact contract through a loopback-only, read-only
development HTTP service, with project-scoped reads, generic errors and tests
against a real local HTTP connection. It serves no filesystem or operator
endpoints and installs no background service. See the
[client API contract](promotion-app-api.md) for routes and client behavior.

The foundation now has a [local web client](../apps/README.md), served by
`app_preview.py`. It shows the two products, five selected published posts,
exact copy and public links, visibility evidence, and unconnected outcome data.
An explicit save keeps a timestamped public snapshot for read-only offline use;
the service worker caches only the fixed app shell. Desktop/mobile layouts,
offline reload, deletion and invalid-version recovery were checked through the
dedicated project browser. Thirty Python tests and six JavaScript checks pass.

This remains a local preview, **not** a deployed API or working
automatic-promotion service. PWA installation on native devices is unqualified.
Its source files are curated public
records, not arbitrary untrusted uploads; it is not a general-purpose secret
redactor. Authenticated action APIs remain to build.

### Native checkpoint

The requested Musia learning pass now also informs two native previews:
`apps/android` uses Kotlin/Compose and `apps/ios` uses SwiftUI. They share one
dated public snapshot of the existing version-one contract. Android compiles to
a debug APK and passes five contract tests. The SwiftUI sources, checked-in Xcode
project and XCTest suite are present; iOS compilation and device qualification
remain unverified. The clients do not copy Musia's music implementation, signing
configuration or public hostname.

Both show products, exact published text, source links, visibility evidence and
unconnected outcomes. Native sharing requires a user tap. Neither client has
provider credentials, a live account connection or a send path. The fixture is
a clearly labelled historical snapshot, not a dashboard presented as live data.
The existing PWA continues using its local read-only API and explicit offline
copies; no public endpoint was added.

The intended customer experience is still **add an app → find a matching need
→ prepare a useful campaign → review → publish → measure**. The phone is the
review and control surface; long-running discovery belongs in an authenticated
backend worker, not a promise that an iOS app runs indefinitely in the background.
Approved first-party schedules can run automatically under a bounded account,
channel and budget policy. Replies to strangers need their own contextual
decision, not an indiscriminate auto-comment switch.

The PWA now has a [local brief-to-draft flow](promotion-app-local-draft.md):
public app facts, a useful example, exact destination/account, an editable
starter, preview, explicit local persistence and JSON export. This is a
deterministic template, not source research or a model-generated campaign.
Preview/export does not approve or queue a publication. Native authoring parity
and authenticated approval/publishing remain to build. L & N and
Bunko remain the real campaign examples, but activity on their campaigns is not
evidence of demand for selling this new app.

Native implementation references: [SwiftUI navigation](https://developer.apple.com/documentation/swiftui/navigationstack)
and [Compose state](https://developer.android.com/develop/ui/compose/state).

Rechecked the requested Musia session and its delivery files on September 26.
The app implementation remains the `f740ae3` checkpoint; the later `f8605ef`
commit records Musia-specific store preparation, not a completed public native
release. No session was resumed, no extra Codex run was started, and no Musia
files, account settings or runtime were changed. Those store decisions are not
inherited by LazyPromotion.

## Delivery gates

- Compile and qualify the SwiftUI preview, then qualify native-device PWA installation and accessibility;
  Android and responsive web previews are available. Test
  loading, empty, error, offline and unverified-result states on each.
- Complete the workflow with project-scoped drafts and approvals, reusing the
  existing exact-content safeguards. Test cross-account and cross-project denial.
- Connect one reviewed first-party publishing integration with exact receipts,
  revocation and uncertain-send reconciliation before expanding channels.
- Test with L & N and Bunko and measure time saved and real responses. Do not
  reclassify campaign activity as evidence that customers will buy this product.
- Verify current provider terms and native-store requirements before connecting
  public customer accounts or preparing submissions. No registration, subscription,
  domain deployment or store price was selected in this checkpoint.
- Decide pricing only after delivery cost and customer demand are established;
  the first USD 1,000 remains a goal, not a forecast.
