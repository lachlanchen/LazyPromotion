# Social inbox monitor

`social_inbox_monitor.py` checks only aggregate unread badges and whether an
allowlisted campaign participant is present in the loaded Instagram or Reddit
inbox. It never opens a conversation, reads a preview or body, sends a reply,
or turns activity into a lead or revenue event.

Reddit Chat has a separate homepage counter from legacy messages and
notifications. The monitor reads that counter independently, so a new chat is
not hidden by an unchanged notification count. Missing or unrecognized chat
controls request review; they are not treated as zero unread chats. A newly
observed nonzero chat counter also requests review, including the first check.
No chat conversation or preview is opened to obtain the counter.

Unread counters cannot discover replies that have already been marked read.
Scheduled application reviews remain necessary. The legacy-inbox participant
match is not evidence of coverage of Reddit Chat conversations.

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
