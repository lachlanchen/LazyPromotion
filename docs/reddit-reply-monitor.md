# Public Reddit direct-reply monitor

This monitor watches direct replies to the single public r/mcp comment already
recorded in `campaigns/mcp-boundary-review.json`. It does not require Reddit
login, browser cookies, Chrome, Xvfb, or noVNC.

```bash
python reddit_reply_monitor.py once
scripts/reddit-reply-monitor.sh start
scripts/reddit-reply-monitor.sh status
scripts/reddit-reply-monitor.sh stop
```

The loop reads at most once per hour. Each pass makes one unauthenticated `GET`
of the exact allowlisted comment permalink. Reddit's public HTML exposes comment
relationships as `thingid` and `parentid` attributes. The parser retains only
those attributes in memory, counts records whose parent is the allowlisted
comment, and discards all page text. The response is capped at 8 MiB.

Private ignored state under `.local/` stores only aggregate counts, timestamps,
the already-public target, and SHA-256 fingerprints of reply IDs. It never
stores comment bodies, authors, browser state, cookies, authentication data, or
raw reply IDs. The first successful pass establishes a baseline. A later new
direct-reply fingerprint creates a manual-review alert; deletion, reordering,
or reappearance of a previously seen reply does not create another alert.

HTTP errors, rate limits, redirects, oversized pages, a missing target, or a
Reddit markup change leave the previous seen state untouched. The monitor does
not retry immediately and does not switch to another scraper. A layout-change
alert means the exact public comment should be inspected visibly on demand.

Reply activity is not a lead, customer, payment, or revenue event. The monitor
cannot compose, send, vote, follow, message, or otherwise mutate Reddit.
