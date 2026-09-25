# LazyPromotion clients

The first client is a local, read-only web preview of selected public campaign
records. It is not yet the automatic-promotion product or a public service.

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

The service worker caches only the six application-shell paths explicitly listed
in `web/sw.js`. API responses are never put in that cache. The optional campaign
snapshot is separate browser storage and contains the selected public data only.
Removing the saved copy removes that campaign data, not the app shell. A manifest
and icon are included; installation has not been qualified on iOS or Android.
There are no offline actions waiting to publish when connectivity returns.

## Verify

```bash
python3 -m unittest discover -s tests -p 'test_app_*.py'
node --test tests/test_app_web.mjs
```

With the single LazyPromotion desktop already running and port 18936 free:

```bash
.venv/bin/python scripts/test-app-preview-browser.py
```

The finite check owns its temporary HTTP listener, reuses one project browser
tab, checks product switching, copy expansion, 320/390/780/1320 px layouts,
offline reload, snapshot deletion and invalid-version recovery, and saves
private screenshots and a receipt. It closes the tab it creates and stops its
HTTP listener. Its caller owns the desktop lifecycle. No public post is sent.

## Next

Native SwiftUI and Kotlin/Compose clients should consume the same versioned
contract. Neither native client is implemented here yet. Before customer-facing
actions, complete authentication, project isolation, opportunity review, editable
drafts, exact-revision approvals, a supported publisher and durable receipts.
See [the app plan](../docs/promotion-app-plan.md) and
[the shared API](../docs/promotion-app-api.md).

The offline implementation follows the browser platform's
[service-worker lifecycle](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers).
A manifest is not proof of platform installation; see
[PWA installation requirements](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable).
