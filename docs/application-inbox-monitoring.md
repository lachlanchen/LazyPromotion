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
validated empty-state marker. The monitor does not open the browser or select a
folder automatically; it uses the existing isolated review session.

Matching metadata and temporary position keys remain in browser memory. SQLite
and status files retain campaign identifiers, counts, booleans, observation times
and an explicit coverage policy—not senders, subjects, message bodies or contacts.

Regression tests execute the real collector against a synthetic virtualized
DOM, including offscreen matches, overlap, pagination, incomplete metadata,
stalled scrolling, changed head rows, and folder switches.
