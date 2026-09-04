# LKT hardware pricing boundary

The public USD 250 Local Knowledge Terminal offer is a collection-fit service
on a customer's existing machine. It is not a Raspberry Pi price, device
deposit, or promise to ship hardware.

A supplied-device offer is a separate commercial decision. Raspberry Pi raised
memory-bearing product prices repeatedly in 2026: the official February notice
added USD 30 to 8 GB products, and the official April notice added a further
USD 50 to 8 GB Raspberry Pi 4 and 5 variants. Revalidate the exact approved-
reseller quote before every hardware batch:

- <https://pip-assets.raspberrypi.com/categories/892-raspberry-pi-5/documents/RP-008348-DS-4-raspberry-pi-5-product-brief.pdf>
- <https://www.raspberrypi.com/news/more-memory-driven-price-rises/>
- <https://www.raspberrypi.com/news/a-new-3gb-raspberry-pi-4-for-83-75-and-more-memory-driven-price-increases/>

## Quote model

For a price `P`, use:

```text
landed variable cost = hardware + storage + enclosure + power + assembly
                     + packaging + support/return reserve + included shipping

contribution = P - payment fee - landed variable cost
margin       = contribution / P

minimum P = (landed variable cost + fixed payment fee)
            / (1 - percentage payment fee - target margin)
```

If shipping is not in landed cost, it must be charged separately and described
before payment. Tax and duty treatment must also be explicit. Do not keep an
actual supplier quote, serial number, address, credential, or payment reference
in Git.

The calculator is read-only and cannot publish a price or create a payment:

```bash
python lkt_hardware_pricing.py \
  --hardware-cost-cny CNY_AMOUNT \
  --cny-per-usd CURRENT_RATE \
  --price-usd PROPOSED_PRICE \
  --other-variable-cost-usd ALL_OTHER_VARIABLE_COSTS \
  --payment-fee-percent EXPECTED_PERCENT \
  --payment-fee-fixed-usd EXPECTED_FIXED_FEE \
  --target-margin-percent TARGET_MARGIN
```

Only add `--costs-confirmed --commercial-terms-reviewed` after the complete BOM
and the shipping, tax, cancellation, return, warranty, and support terms have
actually been reviewed. A passing calculation is still not evidence of demand,
inventory, a sale, or received revenue.

## Working device floor, not a public offer

Do not advertise the earlier USD 498 device idea. If the base device really
costs CNY 2,500, USD 498 leaves too little room for storage, enclosure, power,
cooling, assembly, packaging, support and returns, shipping, or payment fees.

The current internal planning case uses CNY 2,500 at CNY 6.5 per USD, USD 150
for all other variable costs, a conservative 5.4% + USD 0.30 payment-fee
assumption, and a 25% contribution-margin target. Under those assumptions:

- total variable cost is USD 534.62;
- the minimum 25%-margin price is USD 768.56;
- USD 798 leaves USD 220 contribution, or 27.57%.

USD 798 is therefore a **proposed internal floor**, not an active price. Keep
the public device line quote-only until the complete landed BOM and fulfillment
terms are confirmed. Shipping, duties, and tax must either be included in that
calculation or quoted separately before payment.

## Offer ladder

1. Keep the free metadata-only fit check.
2. Keep the founding USD 250 collection-fit sprint for an existing machine.
3. Keep a supplied device quote-only; use USD 798 only as a proposed internal
   floor until the exact build and fulfillment contract pass the gates above.
4. State the service and hardware as separate line items. Never imply that USD
   250 buys the device or that a device quote includes unbounded collection work.
