# Affiliate portfolio

LazyPromotion keeps affiliate work small, contextual, and evidence-gated. The
public source of truth is [`affiliate-programs.json`](../affiliate-programs.json);
it contains official program pages, truthful public economics, exact LazyingArt
matches, disclosures, unresolved facts, and activation gates. It contains no
issued link, referral code, account ID, cookie, or payout detail.

## Execution order

The first useful experiment is three different buyer intents rather than three
links on one generic page:

1. **LingQ** beside the Japanese grammar/practice guide in BLOG post 1752;
2. **Bookshop.org** beside the exact book discussed in BLOG post 1498; and
3. **Waveshare** beside the exact archived e-paper build in BLOG post 3096.

Postiz is the fourth application because LazyingArt can demonstrate its real
review-first CLI/MCP workflow. Kobo follows with the PocketPolyglot e-reader
comparison. These placements should each use one stable placement ID and a
nearby disclosure, preserve a plain official URL, and be measured separately.

This order is about fit, not the largest advertised percentage. Bookshop is a
better first book route than Amazon because the content has exact book intent
and the public program offers stronger book economics. Waveshare is weak as a
general revenue source but unusually strong as an exact, demonstrated hardware
match. Amazon stays delayed until three genuine qualifying sales within its
application review window are plausible.

## Tomorrow's operator checklist

For each program, start with its sanitized packet:

```bash
python affiliate.py list
python affiliate.py packet lingq
python affiliate.py packet bookshop
python affiliate.py packet waveshare
python affiliate.py packet postiz
```

Then, in the visible shared browser profile:

1. open only the official application URL printed by the packet;
2. let the operator enter account, tax, identity, bank, PayPal, Stripe, or KYC
   data—the agent does not inspect or copy those values;
3. review the exact accepted terms, rates, attribution, reversals, eligible
   countries/products, payout threshold, and prohibited channels;
4. copy an issued link only into the ignored private record shown by
   `python affiliate.py template PROGRAM_ID`;
5. test that it resolves to an allowlisted official/network host without making
   a self-purchase; and
6. mark every program-specific activation gate only after direct evidence.

The readiness check requires an explicit private-read acknowledgement and never
prints the issued URL:

```bash
python affiliate.py ready lingq --confirm-private-affiliate-read
```

A passing check does not authorize bulk publishing. It only means one exact CTA
may move to visible editorial review.

## Content and conversion contract

Every affiliate page must solve the problem without the referral link. Put the
plain-language disclosure before or beside the link, not only in the profile or
footer. Keep a plain official destination for readers who do not want affiliate
tracking. Never insert a referral link into individualized community replies,
unsolicited messages, unrelated repositories, automatically generated posts,
or third-party pages that disallow commercial promotion.

The conversion event is program-specific and appears in the registry. A tracked
click is attention. A signup is a provider event. A pending commission remains
unconfirmed. LazyPromotion records income only after money is actually received
with `affiliate_commission_received`; a verified clawback uses
`affiliate_commission_reversed`.

## Deliberate exclusions and holds

- **TradingView is on hold.** Public economics have conflicted, and its data-use
  terms do not authorize presenting it as a MicroQuant data source, execution
  route, webhook, or automated-decision input.
- **Amazon is delayed.** Apply when exact product pages can plausibly produce
  three organic qualifying sales, not merely because the catalog is broad.
- **DistroKid is conditional.** First distribute one wholly rights-cleared Musia
  master and document the real workflow.
- **DigitalOcean requires a rebuilt source page.** BLOG post 1569 must become a
  current provider-neutral deployment guide before any CTA.
- **Skrill requires written policy clarification.** Its public terms restrict
  disparagement and distinguish a US route. Confirm that neutral due diligence
  and the operator's eligibility are accepted before applying; the historical
  identifier in BLOG post 1379 remains inert regardless.
- **Temu, generic broker offers, coupon programs, and unrelated marketplace
  links are excluded.** There is no strong demonstrated asset-to-buyer match,
  and the trust cost is higher than the likely first-sale value.

## Revalidation

Affiliate offers change. Recheck the official program page and controlling
accepted terms before application, before the first placement, and whenever a
rate, product, network, destination, or policy changes. Update
`reviewed_at`, the relevant unknowns, and tests in the same commit. Never infer
current attribution from an old URL that still redirects.
