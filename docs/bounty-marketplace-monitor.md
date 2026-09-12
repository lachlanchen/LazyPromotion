# Bounty marketplace monitor

`bounty_marketplace_monitor.py` polls two distinct sources: Bounty's
authenticated agent endpoint and TaskBounty's public JSON Feed. Both paths are
deliberately read-only. The monitor can retain minimal IDs, versions or
fingerprints, public titles, and timestamps, but it cannot comment, claim,
register, fork, message, download attachments, configure payout, or submit
work.

The Bounty API key stays in the ignored, mode-0600 credential vault. TaskBounty
requires no key for its public feed. A synchronized
encrypted copy is maintained in the private LazyingArt area in Nutstore. The
monitor state and log also stay under `.local/` with mode 0600; neither contains
the credential or requester attachments.

```bash
python bounty_marketplace_monitor.py once
scripts/bounty-marketplace-monitor.sh start
scripts/bounty-marketplace-monitor.sh status
scripts/bounty-marketplace-monitor.sh stop
```

Each source gets an independent first-pass baseline without an alert. Later
passes alert only when an available Bounty ID is new or its version increases,
or when a TaskBounty JSON Feed item is new or changes. An alert is a private
review prompt, not a Claim, lead, contract, payment, or revenue event. The
public issue, reward, active competition, controlling terms, and payout
eligibility must be inspected before deciding whether work fits; external
writes remain outside this monitor.

The five-minute floor is intentionally quieter than Bounty's example polling
interval while the agent is unverified. It can be reconsidered only after the
platform confirms verification, payout readiness, and a real work feed.

Current platform boundaries were verified on September 11, 2026:

- the account and Agent Card exist;
- replacement API authentication succeeds after the initially displayed key
  was revoked;
- the unverified agent currently receives zero available Bounties;
- Stripe payout onboarding remains `Action required` because the hosted page
  exposed no onboarding fields after email verification;
- Bounty's public buyer terms do not yet state agent fees, payout timing,
  work-product ownership, or agent-side dispute/revision rules;
- one concise support email asked the official terms contact for those facts,
  the Stripe fix, verification instructions, and an unverified-agent test path.

TaskBounty was added on September 12 from its official public feed and
open-source MCP implementation:

- `GET https://www.task-bounty.com/api/v1/bounties.json?limit=100` works without
  authentication and returned a valid JSON Feed with zero current items;
- the official solver guide says work is funded from real GitHub issues, is
  competitively awarded to the first passing submission, pays 80% to the
  solver, and requires a new regression test plus the existing test suite;
- registration, repository access, PR submission, and payout setup remain
  separate guarded actions and are never performed by this monitor;
- public descriptions and other untrusted task bodies are not retained in the
  monitor state. A later alert stores only the bounded feed summary needed to
  trigger visible review.

The private application-inbox configuration also contains an exact
sender-and-subject rule for that support thread. An explicit visible-browser
baseline found no matching reply. The pass opened no row or preview and stored
only aggregate counts. It runs when the project mailbox is deliberately
checked; it does not keep the noVNC browser open between reviews.

No work was claimed and no financial, tax, bank, or identity declaration was
submitted.
