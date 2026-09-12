# Social inbox monitor

`social_inbox_monitor.py` checks only aggregate unread badges and whether an
allowlisted campaign participant is present in the loaded Instagram or Reddit
inbox. It never opens a conversation, reads a preview or body, sends a reply,
or turns activity into a lead or revenue event.

The ignored owner-readable configuration is `.local/private/social-inbox-monitor.json`:

```json
{
  "version": 1,
  "campaigns": [
    {
      "campaign_id": "example-instagram-campaign",
      "platform": "instagram",
      "participant": "public.handle"
    },
    {
      "campaign_id": "example-reddit-campaign",
      "platform": "reddit",
      "source_url": "https://www.reddit.com/r/example/comments/example/example/"
    }
  ]
}
```

Run it only while the dedicated LazyPromotion browser is active:

```bash
python social_inbox_monitor.py once
python social_inbox_monitor.py status
```

The state, status, and log files under `.local/` contain campaign IDs, counts,
and booleans only. Participant terms remain in the ignored private config. A
new count or match requests visible review; it does not authorize an automatic
reply or any funnel transition.
