# Value-first conversion

LazyPromotion separates useful public work from commercial asks. A reply earns
trust by solving the stated problem; a campaign can present a real offer only
when the audience and channel permit it. Visits, leads, orders, and revenue must
be reported separately—none may be inferred from impressions or clicks.

## First USD 1,000 path

The single primary offer is the
[Local Knowledge Terminal collection-fit sprint](https://lazying.art/lkt/): a
fixed USD 250 service for one customer-provided collection, one language goal,
and one existing machine. It includes a written data/privacy map, a small
browser proof from a representative sample when the source is usable, and a
go/no-go recommendation. Hardware, shipping, custom OCR, and a production
deployment are excluded. Four confirmed USD 250 payments would be USD 1,000
gross. That is a milestone calculation, not a forecast, and excludes payment
fees, tax, refunds, and delivery costs.

A [complete sample fit
report](https://lazying.art/lkt/sample-report/)
shows the three deliverables using LKT's own documented reference collection.
It is measured project-owned evidence, not a customer result, testimonial,
benchmark, sale, or paid-engagement claim.
Its [source report and corpus
ledger](https://github.com/lachlanchen/LocalKnowledgeTerminal/blob/main/docs/sample-fit-report.md)
remain public for reproducibility.

The campaign sequence is:

1. Find a current, explicit need involving a private collection, local/offline
   knowledge, citations, or multilingual study.
2. Answer the stated problem usefully before mentioning any LazyingArt work.
3. For a reusable problem, publish the complete answer as a searchable
   LazyBlog guide with one tracked fit-check link at the end; rely on the
   registered WordPress sitemap for repeat discovery.
4. Let the profile or one relevant link lead to the public sample report and
   [private-by-design fit check](https://lazying.art/lkt/fit-check/).
5. Confirm source rights, sample format, language goal, readers, privacy needs,
   and existing hardware.
6. Request the fixed USD 250 payment through Stripe only after both sides accept
   the bounded scope.
7. Deliver the map, representative browser proof when feasible, and go/no-go
   recommendation; record a sale only from confirmed payment.

Every campaign link uses a stable `utm_campaign`. Postiz analytics can measure
channel reach and engagement, while confirmed leads and revenue remain private
operator records. The agent never fabricates conversions and never treats a
public reply, impression, or GitHub visit as a customer.

`python owned_monitor.py once` checks the official Postiz publication records
and analytics without changing a post. It stores only hashed post identities in
the ignored local database; raw Postiz and integration IDs remain in memory.
An increase in comments or replies produces a visible-browser review alert, not
a lead, and never sends an automatic response. A persistent operator can use
`python owned_monitor.py loop --interval-minutes 15`; the lock allows only one
copy and the latest sanitized status stays in `.local/owned-monitor-status.json`.
The first observed transition from queued to published also creates a visible
release-verification alert. A published state without a public release URL is
unresolved evidence: inspect Postiz and the provider, and never reconnect or
resubmit until the exact public item is identified.

The rest of the portfolio supplies proof and implementation components rather
than competing calls to action. PocketPolyglot, LinguaLeaf, WordsCardEink, and
WordOrigins strengthen the multilingual pipeline; BLOG and Search Console show
existing demand; LazyPromotion finds needs and keeps the evidence ledger;
LazyEdge can support a later deployment. Other offers remain separate campaigns
and are mentioned only when they directly fit the stated need.

## Fit-first pilot path

[Local Knowledge Terminal](https://lazying.art/lkt/) publishes the bounded USD
250 collection-fit sprint for people with one private book or dictionary
collection. It is a service using the customer's existing machine, not
ready-to-ship hardware. The [free fit check](https://lazying.art/lkt/fit-check/)
precedes payment and builds a reviewable email draft without automatically
storing, uploading, or sending the answers. An inquiry is a lead at most; it is
never recorded as a sale without confirmed payment.

## Private evidence ledger

LazyPromotion keeps replies, leads, and money as different outcome types. A
positive comment is encouraging evidence, but it is not a lead or revenue. A
sale, donation, sponsorship, or refund enters the ledger only after a human has
verified it:

```bash
python metrics.py report

python metrics.py record \
  --kind sale_confirmed \
  --campaign-id eink-multilingual-reading \
  --project-id lazyingart-eink \
  --amount 128 \
  --currency USD \
  --reference PRIVATE_ORDER_LEDGER_ID \
  --confirm-verified-outcome
```

The SQLite ledger is private and ignored by Git. Store only the minimum proof
needed for an aggregate count or amount. Money outcomes require an order or
receipt reference for idempotency, but only its SHA-256 hash is stored. Never
use customer names, email addresses, bank details, card data, Stripe secrets,
or raw receipts as that reference.

## Private demand evidence

Search Console and similar first-party analytics answer a different question:
what people are already trying to find. They may prioritize a useful page or
offer, but they are not a lead or revenue. Import a private, versioned JSON
snapshot only with an explicit data acknowledgement:

```bash
python signals.py import-json .local/private/search-console-signals.json \
  --confirm-private-first-party-data
python signals.py report --source google_search_console
```

Demand rows, observed communities, and their graph entities remain private. The
sanitized public graph excludes subjects, queries, click counts, account
evidence paths, observed-community names, and their project relationships.
