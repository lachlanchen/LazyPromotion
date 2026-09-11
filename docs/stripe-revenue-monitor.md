# Read-only Stripe revenue monitor

LazyPromotion watches successful live Stripe charges so a real payment is not
missed while social posts, applications, and fit checks run unattended.

```bash
python stripe_revenue_monitor.py once --confirm-private-financial-read
scripts/stripe-revenue-monitor.sh start
scripts/stripe-revenue-monitor.sh status
scripts/stripe-revenue-monitor.sh stop
```

The default window begins on 2026-08-31, the operating baseline for the first
USD 1,000 goal. The monitor calls only Stripe's read endpoint. It does not
create Products, Prices, Payment Links, charges, refunds, or payouts.

Private state under `.local/` contains aggregate amounts, timestamps, safe
offer metadata, and SHA-256 hashes of charge IDs. It never persists raw Stripe
IDs, receipt URLs, customer names, email addresses, payment methods, addresses,
or card details. The Stripe key remains in the sibling Stripe repository's
mode-600 `.env` file and is held only in process memory during a read.

A new successful charge or a later refund/dispute change produces a review
alert. It does not write `metrics.py` automatically: the payment must first be
matched to an accepted service scope, product order, or donation context. Only
then can the correct revenue or refund outcome be recorded with its private
reference. This prevents an unrelated, test, duplicated, refunded, or disputed
charge from being counted toward the USD 1,000 goal.
