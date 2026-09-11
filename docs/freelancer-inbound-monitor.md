# Freelancer inbound monitor

This read-only monitor watches the submitted Playwright regression bid without
opening the buyer's messages or responding. It requires exactly one
authenticated tab for that project in the dedicated LazyPromotion browser.
Both the submitted-proposal URL and Freelancer's canonical project redirect
are recognized. A logged-out canonical page fails the authentication gate
instead of being mistaken for a missing tab.

```bash
python freelancer_inbound_monitor.py once
python freelancer_inbound_monitor.py status
python freelancer_inbound_monitor.py loop --interval-minutes 30
```

The first observation creates a quiet baseline. A higher message badge, an
award/closure change, or an unknown proposal state raises a private review
flag. The loop refuses intervals below 15 minutes.

State, status, the append-only observation log, and any alert screenshot stay
under ignored `.local/` paths with private file permissions. The monitor stores
no message body, customer data, credential, or payment detail. It cannot open
a conversation, accept work, change a bid, or send a reply.
