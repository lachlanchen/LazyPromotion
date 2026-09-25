# LazyPromotion client API — development checkpoint

2026-09-26. Read-only local development service; not deployed or store-ready.

The first shared client contract renders the same reviewed public campaign
history in a future SwiftUI app, Compose app and PWA. It does not wrap the private
operator database in HTTP or give clients access to the workstation.

## Run

Python 3.10+ standard library only; no SDK, framework or model installation.

```bash
python app_api.py --port 18936
curl http://127.0.0.1:18936/api/v1/workspace
curl http://127.0.0.1:18936/api/v1/projects/bunko
python -m unittest discover -s tests -p 'test_app_*.py'
```

The server binds only to `127.0.0.1`. Stop it with Ctrl-C when finished. It does
not launch a desktop or install a persistent service. If the port is occupied,
choose another unused port; never stop a different project's service.

`wsgiref` is a development server, not a production deployment. A mobile phone's
loopback is that phone, not this workstation. Native device testing will need a
separately reviewed development route; there is no public API URL yet. Do not
work around this by binding the workstation service to every network interface.

## Routes

| GET or HEAD | Result |
| --- | --- |
| `/healthz` | `{"status":"ok"}`; liveness only, not provider/catalog health |
| `/api/v1/workspace` | Version-one workspace for L & N and Bunko |
| `/api/v1/projects/l-and-n` | Same workspace envelope, only L & N |
| `/api/v1/projects/bunko` | Same workspace envelope, only Bunko |

There are no query parameters, redirects, static files, credentials, cookies,
websockets or mutation routes. HEAD returns the GET headers without its body.
Other methods return 405, unknown paths 404, invalid queries/bodies/hosts 400,
cross-origin browser requests 403, and invalid source records 503. Errors contain
a generic `error` identifier, never file paths or source contents.

All responses are `no-store`. Host is restricted to literal loopback authorities;
forwarded headers are ignored. There is no CORS permission. The preview must not
be embedded in an external site or reverse-proxied as a production service.

## Version-one model

`app_workspace.py` is the contract implementation. It projects only four named,
curated campaign files, checks published-text hashes and exports allowlisted
fields. Files are reread on each request. It never loads `.local`, provider
configuration, customer details or the private graph. The projection is **not a
general-purpose secret redactor**; adding sources requires editorial review.

```text
Workspace {
  version: 1,
  mode: "public_campaign_preview",
  capabilities: {
    readPublishedCampaigns: true,
    discover: false, draft: false, approve: false,
    publish: false, paymentAttribution: false
  },
  projects: [{
    id, name,
    links: { apple?, google?, reader?, video?, repository? },
    publications: [{
      id, platform, community: string | null, title: string | null,
      body, bodySha256, publishedAt, recordCheckedOn, url,
      visibilityEvidence: "public_verified" | "account_verified" | "unverified"
    }],
    outcomes: {
      installs: { state: "not_connected", value: null },
      customers: { state: "not_connected", value: null },
      receivedGrossUsd: { state: "not_connected", value: null }
    }
  }]
}
```

`publishedAt` is UTC (`YYYY-MM-DDTHH:MM:SSZ`); `recordCheckedOn` is a calendar
date, not a promise the source remains visible now. Bodies are plain text, not
HTML. Clients must not change an account-only visibility check into public
verification, or display missing outcome data as zero. A successful publication
is not evidence of an install, customer or payment.

Clients must reject unsupported major versions, hide unavailable actions, and
render errors without substituting invented data. If they save an offline
snapshot, label it with its fetch time and keep it read-only. No offline approval
or queued publish exists in this version.

## Next complete product loop

This API is a transport foundation, not automatic promotion. The smallest useful
customer workflow remains: add product facts → find a sourced opportunity →
prepare one useful draft → review destination and copy → publish through a
supported authorized channel → retain a provider receipt and actual feedback.

Before exposing actions to customers, implement authenticated per-project access,
provider-specific permissions and secret storage, edit-invalidated approvals,
idempotent sending, uncertain-delivery reconciliation, revocation and deletion.
The existing operator checks in `promotion.py` inform that design; its database
and local approval tokens must not be exposed directly.

No iOS/Android UI, PWA, store listing, customer account, paid plan or automated
publishing integration is delivered by this checkpoint. The platform plan and
verified Musia lessons are in [promotion-app-plan.md](promotion-app-plan.md).
