# Repeatable LKT collection-fit delivery packet

`lkt_delivery.py` is a small, deterministic preflight and packet renderer for
the fixed USD 250 Local Knowledge Terminal collection-fit sprint. It mirrors
the public sample report's useful boundaries without treating that report as a
customer result: rights and privacy first, one bounded collection and language
goal, a representative browser-proof plan, checkable citations, a written
go/no-go decision, and explicit exclusions.

This tool is **not a corpus intake path**. Never give it a real customer
document, excerpt, filename, path, URL, name, email, account identifier, or
payment record. Prepare the small JSON input separately using only sanitized
categories, counts, booleans, and language tags.

## Run the project-owned example

```bash
python lkt_delivery.py examples/lkt-collection-fit-intake.example.json \
  --output /tmp/lkt-delivery-packet.md
```

For an operator-prepared, metadata-only fit summary, copy the second template
to an approved private delivery location and sanitize it there:

```bash
python lkt_delivery.py \
  /approved/private/location/lkt-sanitized-fit-summary.json \
  --output /approved/private/location/lkt-delivery-packet.md
```

[`examples/lkt-collection-fit-intake.operator.example.json`](../examples/lkt-collection-fit-intake.operator.example.json)
shows that contract without containing real customer data. Do not commit a
real fulfillment input or packet to this repository.

Omit `--output` to print the packet. The same valid JSON always renders the
same Markdown; the program has no network calls, timestamps, random values, or
model calls.

The example uses only facts already disclosed in LKT's public sample report:
the project-owned reference collection is bounded at 19,119 structured records,
the example processing boundary is local, the machine class is 8 GiB without a
discrete accelerator, and citations can retain stable record provenance. The
new packet still labels its proof as planned. It does not claim that this
renderer reproduced the public report's browser captures or measurements.

## Input contract

The machine-readable contract is
[`schemas/lkt-collection-fit-intake.json`](../schemas/lkt-collection-fit-intake.json).
The Python validator is authoritative at runtime and additionally checks real
ISO dates, duplicate JSON keys, cross-field rights consistency, sample size,
and a 32 KiB metadata limit.

The privacy fields `sample_payload_included` and
`sensitive_identifiers_included` must both be `false`.
Use `sanitized_example_only` with `sanitized_hypothetical` or
`project_owned_public_example` for demonstrations. Use
`sanitized_metadata_only` with `operator_prepared_fit_summary` for the
operator-prepared summary that drives a real fulfillment workflow. The latter
does not assert that a fit inquiry, payment, or proof exists; it says only who
prepared the sanitized metadata.

Unknown fields fail closed; there is intentionally nowhere to store free-form
descriptions, customer names, contact details, source content, file locations,
URLs, or commercial status. These structural checks cannot prove that an
operator did not encode identifying information in an otherwise valid slug or
category, so human sanitization before the file reaches this tool remains
mandatory.

Fit failures are different from privacy failures:

- Unconfirmed rights, an unbounded collection, an unresolved privacy boundary,
  or missing citation locators render `NO-GO`.
- Custom OCR, hardware/shipping, production deployment, uptime/SLA work, or a
  request other than the fixed browser proof render `SEPARATE SCOPE` when no
  harder blocker exists.
- Embedded payloads, identifiers, unknown fields, invalid types, and ambiguous
  JSON are rejected before rendering.

`GO TO REPRESENTATIVE-PROOF PLAN` is only an intake-stage decision. It is not
evidence that source extraction, retrieval, citation resolution, rendering, or
performance succeeded.

## Safe operating sequence

1. In the approved private delivery location, create a new
   `sanitized_metadata_only` JSON record from categories only. Keep the real
   inquiry and all source material outside this repository and outside the
   renderer input.
2. Render and human-review the packet.
3. If it is a go, select and handle the representative source set only inside
   the separately approved execution environment. Never add that set to the
   intake JSON.
4. Retain extraction notes, an index manifest, question/miss evidence,
   citation checks, and browser captures in the approved private delivery
   location.
5. After the proof, write the final evidence-backed go/no-go recommendation.
   Do not convert planned text into a result without checkable evidence.

The renderer does not contact an inbox, CRM, payment provider, or analytics
system. It cannot create a lead, checkout, payment, sale, testimonial, or
revenue record.
