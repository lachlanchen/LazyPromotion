# LKT hardware pricing boundary

The public USD 250 Local Knowledge Terminal offer is a collection-fit service
on a customer's existing machine. It is not a Raspberry Pi price, device
deposit, or promise to ship hardware.

A supplied-device offer is a separate commercial decision. Raspberry Pi raised
memory-bearing product prices repeatedly in 2026: the official February notice
added USD 30 to 8 GB products, and the official April notice added a further
USD 50 to 8 GB Raspberry Pi 4 and 5 variants. Revalidate the exact approved-
reseller quote before every hardware batch:

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

## Offer ladder

1. Keep the free metadata-only fit check.
2. Keep the founding USD 250 collection-fit sprint for an existing machine.
3. Keep a supplied device quote-only until the exact build and fulfillment
   contract pass the gates above.
4. State the service and hardware as separate line items. Never imply that USD
   250 buys the device or that a device quote includes unbounded collection work.
