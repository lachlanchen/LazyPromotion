# Application inbox coverage

The application monitor matches sender and subject metadata against private
campaign rules. It never activates a message, reads a preview or message body,
or sends a reply. Matching counts are review signals, not qualified leads.

Use the root **Inbox** when the intended scope includes all iCloud inbox
categories. **Primary** is only one category; a successful Primary snapshot
cannot establish whether a reply is present elsewhere in Inbox.

The message list is virtualized. The collector starts at the top, scans
overlapping viewports until it covers the newest **50 thread positions** (or a
smaller nonempty list), checks the head again for changes, and restores the
previous scroll position. Each position is counted once within the observation.
Incomplete metadata, gaps, changed identities, unavailable lists, and ambiguous
folder selection fail the observation rather than reporting zero matches.

This is a bounded recent-window check, not a complete mailbox search. Older
threads, spam, other folders, unrecognized sender/subject variants, and activity
that does not change the thread or unread count still require a separate scoped
review. An empty list is not accepted as a verified zero without an independently
validated empty-state marker. The low-level collector does not open the browser
or select a folder; it uses an existing isolated review session. The optional
finite coordinator below supplies that session and selects only known folders.

Matching metadata and temporary position keys remain in browser memory. SQLite
and status files retain campaign identifiers, counts, booleans, observation times
and an explicit coverage policy—not senders, subjects, message bodies or contacts.

Regression tests execute the real collector against a synthetic virtualized
DOM, including offscreen matches, overlap, pagination, incomplete metadata,
stalled scrolling, changed head rows, and folder switches.

## Finite hourly checks

`mail_inbound_check.py` combines the application counter with the dedicated
fit-check folder counter. It uses the existing signed-in project profile, never
the personal browser. It does not log in, restore credentials, enter MFA codes,
activate a message row, inspect a message body, or send a reply.

Configure the existing private application rules first. The collector accepts
only the configured folder and campaign rules; it cannot recognize every new
sender or conversation. Root Inbox is the intended scope for the project setup.
An aggregate change is a request for scoped review, not proof of a human reply,
qualified buyer, or sale.

```bash
# One finite check; no unattended worker is enabled by this command.
python mail_inbound_check.py once

# Optional folder-label-only screenshots for a validation run.
python mail_inbound_check.py once --capture-evidence

# Hourly checks in one project-owned tmux session.
scripts/mail-inbound-monitor.sh start
scripts/mail-inbound-monitor.sh status
scripts/mail-inbound-monitor.sh stop
```

The recurring worker checks no more often than once an hour and respects the
previous check time on startup. `MAIL_INBOUND_INTERVAL_MINUTES` can lengthen the
interval, but cannot make it shorter than 60 minutes. An existing active or
partial desktop, a held lifecycle lease, or memory pressure causes a skip—not
an attempted takeover. Skips retain the last successful observation time and
are never presented as a fresh mailbox check.

`desktop_lease.py` coordinates manual `scripts/desktop.sh start`, `stop`, and
`restart` operations with finite checks. The coordinator holds a lifecycle lock
through startup, collection, and cleanup. The mail-folder selection and both
collectors share one browser-operation lock without nesting it. A collection
has a 180-second timeout; startup and cleanup have separate finite limits.
Cleanup verifies PID birth identities and refuses to stop a replacement
runtime. Successful collection is not reported as healthy if cleanup failed.

Only the desktop started by the check is stopped. The worker uses one existing
project stack and does not refresh or open a Firefox viewer. Resource checks
require at least 24 GiB available memory and no more than 75% swap use. It
pauses for an unavailable mail session, a cleanup ownership problem, or three
consecutive failed checks. `stop` sends one graceful signal so an in-progress
check can perform cleanup; it does not forcibly kill the tmux session.

Aggregate status, observations, alerts and logs stay under ignored `.local/`
with private permissions:

- `mail-inbound-monitor-status.json`: current lifecycle state and
  `last_successful_checked_at`;
- `mail-inbound-observation.json`: run-bound child result, validated before use;
- `mail-inbound-monitor.jsonl`: aggregate history, including change alerts;
- the existing application and fit-folder databases: counts only.

Failed child observations include a fixed `failure_stage` label for connection,
tab/frame readiness, application or fit-folder selection/counting, restoration,
or evidence capture. No folder name, locator, URL, subject, or browser exception
text is copied into this field. It identifies the failed operation, not the
cause or login state, and does not change timeouts, retries, or pause rules.
An already-running loop starts a fresh collector subprocess each cycle, so the
next normal child can record these labels without restarting the worker. Older
parent processes may omit the label from their status file; inspect the matching
run-bound child observation rather than forcing an early check.

The loop does not take screenshots. Optional validation screenshots are cropped
to the known Inbox folder option and replace the previous before/after images;
they never capture the message list or message content. Private evidence and
browser profiles must not be committed.

## Optional scoped Gmail coverage

Some earlier applications were sent through Gmail, not iCloud. The iCloud
counts do not cover those conversations. `gmail_application_monitor.py` adds
separate, opt-in checks inside the same finite hourly desktop session; it does
not start another browser or worker.

Configure an ignored, owned mode-0600 file at
`.local/private/gmail-application-monitor.json`:

```json
{
  "account_email": "operator@example.net",
  "campaigns": [
    {
      "campaign_id": "example-application",
      "subject": "The exact existing application subject",
      "sender_domain": "example.org",
      "after": "2026-09-08"
    }
  ]
}
```

Use only existing, reviewed application subjects and their known sender
domains. Up to four rules are supported, within a 60-second provider budget.
The collector checks the visible Google-account marker and page title, then
uses incoming-domain, exact-subject and date-constrained Gmail searches across
folders. It reloads the document to avoid accepting cached results from the
previous search and requires three matching observations. Zero requires the
explicit visible empty-result marker; positive results must have complete
pagination and matching subject metadata. Ambiguous or changed UI fails the
observation, not the account login.

It never opens a message, reads a preview, sends mail, marks a message read,
changes forwarding, logs in or handles MFA. Only campaign IDs, counts, times
and opaque snapshot/configuration digests are saved. A changed last-message
identity can signal activity even when the thread count stays constant; the
identity itself is not retained. Positive first observations also require
review. Signals remain pending until a scoped review clears the private
`alerts` list; they are not automatically acknowledged on the next poll.
Pending activity is also surfaced as one `gmail_application_activity_pending`
entry in the coordinator's aggregate alerts, without any message metadata.

The coordinator's `gmail` field reports `not_configured`, `checked`,
`session_unavailable` or `observation_failed`. Failed checks have no zero
counts. The detailed private status at
`.local/gmail-application-monitor-status.json` retains the last successful
observation separately, including its original timestamp. A Gmail failure
does not stop healthy iCloud/fit-folder observations: the coordinator's `ok`
still describes those observations and owned-desktop cleanup, while Gmail's
state must be checked separately.

Transient iCloud startup failures remain possible. A failed child check keeps
only a fixed diagnostic category, never the browser exception text, and the
worker retains the last successful observation time. Do not treat that old
timestamp as a fresh check or weaken list-completeness checks to get a zero.

This covers only the configured incoming domains and subject lines, not all
mail. Replies from another domain, changed subjects, or outside the date range
still require a scoped manual review. A matching result is an activity signal,
not proof of an authentic human reply, accepted assignment or revenue.

Tests execute the collector against a synthetic browser DOM with unread and
read results, incomplete pagination, mismatched duplicate links, open messages,
missing/hidden empty markers, and preview access traps. Live validation uses
the actual empty reply searches and one existing operator-sent application as
a positive metadata probe; that probe is not stored as a buyer response.
