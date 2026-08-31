# Value-first conversion

LazyPromotion separates useful public work from commercial asks. A reply earns
trust by solving the stated problem; a campaign can present a real offer only
when the audience and channel permit it. Visits, leads, orders, and revenue must
be reported separately—none may be inferred from impressions or clicks.

## First USD 1,000 path

The clearest tool-aligned offer currently published is
[LazyingArt eInk](https://lazying.art/eink/): a USD 128 / CNY 999 pre-order tied
to a free local Kindle sender and free LinguaLeaf books. Eight USD 128 orders
would be USD 1,024 gross. That is a milestone calculation, not a forecast, and
excludes payment fees, shipping, tax, refunds, and fulfillment costs.

The campaign sequence is:

1. Show a real multilingual reading page.
2. Offer the free Kindle sender or public book shelf.
3. Ask what the reader needs from e-paper hardware.
4. Present the pre-order only to qualified readers.
5. Record an order only from confirmed payment or the operator's order ledger.

Every campaign link uses a stable `utm_campaign`. Postiz analytics can measure
channel reach and engagement, while confirmed leads and revenue remain private
operator records. The agent never fabricates conversions and never treats a
public reply, impression, or GitHub visit as a customer.

Other live LazyingArt offers may be tested later, but only as separate campaigns
with their own audience evidence. Mixing unrelated handmade goods into a
language-tool discussion would weaken trust and conversion quality.

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
