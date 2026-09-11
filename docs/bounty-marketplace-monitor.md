# Bounty marketplace monitor

`bounty_marketplace_monitor.py` polls Bounty's official agent endpoint for work
available to the project-owned LazyPromotion agent. The integration is
deliberately read-only: it can list IDs and versions, but it cannot comment,
claim, message, download attachments, or submit work.

The API key stays in the ignored, mode-0600 credential vault. A synchronized
encrypted copy is maintained in the private LazyingArt area in Nutstore. The
monitor state and log also stay under `.local/` with mode 0600; neither contains
the credential or requester attachments.

```bash
python bounty_marketplace_monitor.py once
scripts/bounty-marketplace-monitor.sh start
scripts/bounty-marketplace-monitor.sh status
scripts/bounty-marketplace-monitor.sh stop
```

The first successful pass creates a baseline and never raises an alert. Later
passes alert only when an available Bounty ID is new or its version increases.
An alert is a private review prompt, not a Claim, lead, contract, payment, or
revenue event. Current terms and attachments must be inspected before deciding
whether work fits; external writes remain outside this monitor.

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

No work was claimed and no financial, tax, bank, or identity declaration was
submitted.
