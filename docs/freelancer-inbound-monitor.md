# Freelancer inbound monitor

This read-only monitor watches the submitted Playwright regression, Android
APK-delivery, and KiCad plugin-testing bids without opening buyer messages or
responding. It reuses exactly one authenticated Freelancer project tab in the
dedicated LazyPromotion browser and visits the three owned proposal pages
sequentially.
Canonical, details, and submitted-proposal URLs are recognized. A logged-out
page fails the authentication gate instead of being mistaken for a missing
tab.

```bash
scripts/freelancer-inbound-check.sh
python freelancer_inbound_monitor.py once
python freelancer_inbound_monitor.py status
python freelancer_inbound_monitor.py loop --interval-minutes 30
```

The wrapper is the normal unattended one-shot route. It starts the dedicated
project desktop only when every stack component is stopped, reuses a fully
running stack without claiming ownership, runs one read-only observation, and
stops the stack only when it started it. A partial stack is refused. If the
browser-session login has expired, the wrapper can use the existing ignored,
owner-only restore helper and credential vault inside the same temporary
desktop, retry exactly once, and still clean up. It never prints the login or
password. If the private helper is absent, linked, or fails, the check stops.

The first portfolio observation creates a quiet baseline. A higher message
badge, an award/closure change, or an unknown proposal state raises a private
review flag. The loop refuses intervals below 15 minutes.

State, status, the append-only observation log, and any alert screenshot stay
under ignored `.local/` paths with private file permissions. The monitor stores
only campaign IDs, aggregate badge count, bid state, rank, and proposal count;
it stores no message body, customer data, credential, or payment detail. It
cannot open a conversation, accept work, change a bid, or send a reply.
