# Bounty marketplace monitor

`bounty_marketplace_monitor.py` polls four distinct sources: Bounty's
authenticated agent endpoint, TaskBounty's public JSON Feed, Agent Bounties'
keyless canonical Base-mainnet feed with `claimable_only=true`, and
Freelancer's official public active-project API. Every path is deliberately
read-only. The monitor can retain minimal IDs, versions or fingerprints,
public titles and timestamps, and bounded budget, competition, contract,
terms, reward, and gross-margin fields. It cannot comment, claim, bid,
register, fork, message, download attachments, store a solver wallet, sign,
approve, fund, broadcast a transaction, configure payout, or submit work.

The Bounty API key stays in the ignored, mode-0600 credential vault.
TaskBounty, Agent Bounties, and Freelancer require no key for these public
reads. A synchronized encrypted copy is maintained in the private LazyingArt
area in Nutstore. The monitor state and log also stay under `.local/` with mode
0600; neither contains the credential, requester attachments, or raw project
descriptions.

```bash
python bounty_marketplace_monitor.py once
scripts/bounty-marketplace-monitor.sh start
scripts/bounty-marketplace-monitor.sh status
scripts/bounty-marketplace-monitor.sh stop
```

Each source gets an independent first-pass baseline without an alert. Later
passes alert only when an available Bounty ID is new or its version increases,
when a TaskBounty JSON Feed item is new or changes, or when a canonical Agent
Bounties item with positive gross cash margin is new or changes. Freelancer
gets its own first-pass baseline; later new or changed rows alert only after a
strong portfolio-term match, a USD 250 fixed or USD 25/hour ceiling, no more
than 25 bids, and removal of preferred-only, KYC-gated, commission/recruiting,
ongoing-employment, onsite, or live-remote-control work. An alert is a private
review prompt, not a claim, profit calculation, lead, contract, payment, or
revenue event. The public issue, reward or budget, actual scope, active
competition, controlling terms, client history, platform fee, bond, gas,
deadline, account gate, and payout eligibility must be inspected before
deciding whether work fits; external writes remain outside this monitor.

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

Agent Bounties was added on September 13 from its Apache-2.0 open-source
implementation and canonical claimable-work endpoint:

- `GET https://api.agentbounties.app/v1/base/autonomous-bounties/feed?network=base-mainnet&claimable_only=true`
  returned HTTP 200 and an empty JSON array;
- the endpoint requires no account, API key, wallet address, signature, token
  approval, or transaction;
- rows must already say `claimable`, `terms_valid=true`, and
  `verification_ready=true`; malformed or weaker rows fail the complete read;
- only rows with positive advertised gross cash margin can create a review
  alert, and gas, bond loss, deadlines, verifier rules, and actual settlement
  still require separate review;
- public terms and event bodies are fingerprinted but not retained. Only a
  confirmed canonical settlement can later support a payment claim.

Freelancer was added on September 13 through its official public active-project
API:

- one keyless GET asks only for current work matching MCP, Playwright, KiCad,
  local-AI/OCR, or SSH proof already present in the portfolio;
- broad Android, media, and imaging keywords were deliberately excluded after
  a live sample produced unrelated support and data-entry work;
- missing or malformed budgets, closed/private/local projects, low ceilings,
  crowded listings, preferred-only work, KYC-gated work, and obvious live or
  employment commitments are rejected before alerting;
- descriptions are used transiently for matching and fingerprinting but are
  never persisted. A candidate row keeps only the public title, URL, budget,
  bid count, matched capability, timestamp, and fingerprint;
- the monitor never authenticates, changes the account, spends a bid, sends a
  message, accepts terms, or starts delivery.

The private application-inbox configuration also contains an exact
sender-and-subject rule for that support thread. An explicit visible-browser
baseline found no matching reply. The pass opened no row or preview and stored
only aggregate counts. It runs when the project mailbox is deliberately
checked; it does not keep the noVNC browser open between reviews.

No work was claimed and no financial, tax, bank, or identity declaration was
submitted.
