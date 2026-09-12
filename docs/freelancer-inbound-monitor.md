# Freelancer inbound monitor

This read-only monitor watches the submitted Playwright regression and Android
APK-delivery bids without opening buyer messages or responding. It reuses
exactly one authenticated Freelancer project tab in the dedicated
LazyPromotion browser and visits the two owned proposal pages sequentially.
Canonical, details, and submitted-proposal URLs are recognized. A logged-out
page fails the authentication gate instead of being mistaken for a missing
tab.

```bash
python freelancer_inbound_monitor.py once
python freelancer_inbound_monitor.py status
python freelancer_inbound_monitor.py loop --interval-minutes 30
```

The first portfolio observation creates a quiet baseline. A higher message
badge, an award/closure change, or an unknown proposal state raises a private
review flag. The loop refuses intervals below 15 minutes.

State, status, the append-only observation log, and any alert screenshot stay
under ignored `.local/` paths with private file permissions. The monitor stores
only campaign IDs, aggregate badge count, bid state, rank, and proposal count;
it stores no message body, customer data, credential, or payment detail. It
cannot open a conversation, accept work, change a bid, or send a reply.
