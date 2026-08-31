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

The campaign sequence is:

1. Find a current, explicit need involving a private collection, local/offline
   knowledge, citations, or multilingual study.
2. Answer the stated problem usefully before mentioning any LazyingArt work.
3. Let the profile or one relevant link lead to the free fit check.
4. Confirm source rights, sample format, language goal, readers, privacy needs,
   and existing hardware.
5. Request the fixed USD 250 payment through Stripe only after both sides accept
   the bounded scope.
6. Deliver the map, representative browser proof when feasible, and go/no-go
   recommendation; record a sale only from confirmed payment.

Every campaign link uses a stable `utm_campaign`. Postiz analytics can measure
channel reach and engagement, while confirmed leads and revenue remain private
operator records. The agent never fabricates conversions and never treats a
public reply, impression, or GitHub visit as a customer.

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
ready-to-ship hardware. The free fit check precedes payment. An inquiry is a
lead at most; it is never recorded as a sale without confirmed payment.

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
