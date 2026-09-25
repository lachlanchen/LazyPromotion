# LazyPromotion clients

Local campaign history for web/PWA, native Android and native iOS, with a
browser-only campaign starter in the PWA.
They are not yet the automatic-promotion product or a public service.

| Client | Current checkpoint |
| --- | --- |
| Web/PWA | Read-only history API, offline snapshots, local editable briefs and draft export |
| [Android](android/README.md) | Kotlin/Compose; debug build and five contract tests pass |
| [iOS](ios/README.md) | SwiftUI source, Xcode project and tests; Xcode compilation not yet verified |

The native clients use one [bundled public snapshot](shared/workspace-preview.json),
labelled with its capture time. They do not connect to the operator's accounts or
pretend their copy is live. Both provide product navigation, expandable published
copy, separate visibility labels, unknown outcome states and a native share sheet
for a user-selected public link. Android requests no network permission; iOS has
no networking implementation. Sharing opens a system chooser, not an automatic send.

```bash
python3 app_preview.py
```

Open `http://127.0.0.1:18936/` on this workstation. Stop with Ctrl-C. This uses
the existing Python standard-library API; no new dependencies, account, API key,
model or background service is needed. Do not expose it through a public tunnel.

## Available

- Switch between L & N and Bunko and inspect five selected published posts.
- Open exact public product and publication links; read the recorded copy.
- Distinguish public visibility checks from signed-in-only checks.
- Keep installs, customers and revenue visibly unconnected rather than inventing
  conversion statistics.
- Explicitly save a dated campaign snapshot in this browser, read it offline,
  and remove it. Refresh does not silently replace a saved copy.
- Prepare a campaign from public app facts, an audience, a useful example,
  price, source and intended account/destination. Edit the starter, preview it,
  explicitly save/load one local draft or export JSON. No model, source fetch,
  account connection or publication happens. Sources remain unverified.
- Brief changes invalidate the draft preview; text edits also require another
  preview before export. A stale save cannot overwrite a draft changed in
  another tab. Browser storage is not encrypted or a secret vault.

The service worker caches only the eight application-shell paths explicitly listed
in `web/sw.js`. API responses are never put in that cache. The optional campaign
snapshot is separate browser storage and contains the selected public data only.
Removing the saved copy removes that campaign data, not the app shell. A manifest
and icon are included; installation has not been qualified on iOS or Android.
There are no offline actions waiting to publish when connectivity returns.
The local draft is stored separately; removing a history snapshot does not remove
a draft. The page confirms the current offline shell is ready before offline
use. Draft export is not approval and cannot be submitted to an action API.
See [the local draft contract](../docs/promotion-app-local-draft.md).

## Verify

```bash
python3 -m unittest discover -s tests -p 'test_app_*.py'
node --test tests/test_app_web.mjs
node --test tests/test_app_draft.mjs
```

With the single LazyPromotion desktop already running and port 18936 free:

```bash
.venv/bin/python scripts/test-app-preview-browser.py
.venv/bin/python scripts/test-app-draft-browser.py
```

The finite check owns its temporary HTTP listener, reuses one project browser
tab, checks product switching, copy expansion, 320/390/780/1320 px layouts,
offline reload, snapshot deletion and invalid-version recovery, and saves
private screenshots and a receipt. It closes the tab it creates and stops its
HTTP listener. Its caller owns the desktop lifecycle. No public post is sent.
The second check covers draft creation, editing, save/reload, exact JSON export,
literal HTML, stale-brief rejection, offline preview and removal of its own test
draft. Both refuse to overwrite pre-existing saved user content.

## Next

Native SwiftUI and Kotlin/Compose previews now consume the same versioned
contract from the bundled snapshot. Before live customer-facing
actions, complete authentication, project isolation, opportunity review, native
draft parity, exact-revision approvals, a supported publisher and durable receipts.
See [the app plan](../docs/promotion-app-plan.md) and
[the shared API](../docs/promotion-app-api.md).

The offline implementation follows the browser platform's
[service-worker lifecycle](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers).
A manifest is not proof of platform installation; see
[PWA installation requirements](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable).
