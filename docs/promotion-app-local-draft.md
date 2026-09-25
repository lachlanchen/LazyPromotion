# Local campaign authoring checkpoint

September 26, 2026. Implemented in the PWA only. Android and iOS still show the
dated public campaign snapshot; neither has this editor yet.

## Useful loop

Enter public product facts, the audience and problem, one shipping feature, a
useful tip, price and a supporting URL. Supply the intended public account and
destination. Build a deterministic starter, edit it, preview the complete copy
and destination, then explicitly save it in this browser or export JSON.

The starter puts the useful example first and discloses the author's connection
with “I work on…”. It does not call a model, fetch source pages, discover a need,
confirm ownership of the named account or verify any claim. The author still
needs to check source facts and the destination's rules. It is not an automatic
promotion result, a paid product or evidence of demand.

## Separate contract

`apps/web/draft-model.mjs` validates the following version-one export. It does
not change the read-only workspace API or its capability flags.

```text
LocalCampaignDraft {
  version: 1,
  kind: "local_campaign_draft",
  state: "draft",
  savedAt: UTC timestamp,
  brief: {
    name, productUrl, audience, problem, feature, useful, price,
    limitation, evidenceUrl, destinationUrl, account
  },
  title, body,
  sourceVerification: "user_supplied_unverified",
  publication: "not_connected"
}
```

All text is bounded; `limitation` may be empty. URLs must be public-shaped HTTPS
addresses without credentials, fragments, custom ports or local/IP hosts. They
are not fetched or guaranteed to exist. This validation is not a credential
scanner: no private identifiers or customer information should be entered.

The parser reconstructs supported fields, rejects unsupported versions and
publication/approval states, and never preserves injected secret or approval
fields. All preview content is rendered as literal text, never HTML. Export is
a local download, not an instruction that any agent or backend may execute.

## Data and edits

- One explicit browser-local save under `lazypromotion.local-draft.v1`.
- No autosave, cloud sync, cookies, provider tokens or remote write requests.
- On reload, choose Load saved draft; unsaved text is not silently replaced.
- Save rejects a record changed in another tab since it was loaded or saved.
- Rebuilding or loading over unsaved text asks before replacing it.
- Brief edits require regeneration before save/export; title or body edits
  hide the previous preview and require a new preview before export.
- Removing the saved draft asks first and leaves unsaved text on screen.
- Saved drafts and saved public-history snapshots have independent removal.
- Offline authoring works after the current app shell has finished installing.
  The service worker caches only fixed client assets, never API responses.

Browser storage persists across sessions but can be unavailable or cleared;
it is not encrypted backup storage. The implementation follows the platform's
[localStorage behavior](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage)
and keeps storage failures visible without turning them into successful saves.

## Verified

Seven draft-model tests, six history-model tests and 34 Python app tests pass.
The isolated-browser checks covered creation and editing, exact export, explicit
save/reload, literal HTML, stale-brief rejection, offline draft preview, deletion,
and 320/390/780/1320 px layouts. Desktop and mobile screenshots were inspected.
No mutation network requests or JavaScript page errors occurred in the draft
test. Existing history/offline/error checks also pass.

The first offline-upgrade check exposed incomplete shell takeover. Installation
now waits for the full shell before activation, and a version handshake confirms
readiness visibly. The repeat check passed. No SDK, model, cloud service or new
browser stack was installed.

Next: implement the same local authoring contract in the native clients, compile
iOS, and connect sourced discovery plus exact-review publishing through a
separate authenticated backend. Do not expose the workstation's operator state.
