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
   LazyBlog guide, then offer the tracked sample report before the fit check;
   rely on the registered WordPress sitemap for repeat discovery.
4. Let the profile or one relevant link lead through the public sample report
   to the [private-by-design fit check](https://lazying.art/lkt/fit-check/).
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
The live LazyBlog bridge preserves an originating Reddit or X campaign when a
reader continues to the sample report or directly to the LKT fit check. It
forwards only `utm_source`, `utm_medium`, `utm_campaign`, and `utm_content`,
validates their characters and length, and changes only the exact HTTPS
`lazying.art/lkt/sample-report/` and `lazying.art/lkt/fit-check/` destinations.
Organic blog readers retain the article's normal `lazyblog` attribution. The
reviewed local email draft includes the resulting fields; it still sends
nothing automatically.
The same allowlist runs on the first-party LKT offer and sample-report pages,
so a Reddit, Instagram, or X visitor who reviews the evidence before continuing
keeps the original campaign fields. A live Reddit-profile click verified the
full article → sample report → fit check path without submitting the form. The
bridge never copies the extra query fields used for cache-bypassed verification.

The deployed fit-check contract was rechecked in a visible browser on September
2, 2026 with synthetic, non-customer answers. The review panel uses the explicit
`USD 250` currency label, visibly names `contact@lazying.art`, offers a copy
fallback for devices without a configured email app, retains all four
allowlisted attribution fields, and explains what happens next. It explicitly
says not to send source files before the fit decision and keeps Stripe after a
positive fit check and written scope acceptance. The form opened no additional
page and caused zero non-read network requests. The operator did not click the
mail link. This is conversion-path readiness evidence, not a fit inquiry,
qualified lead, or sale. The verified public deployment is LazyingArtWebsite
commit `8541e9c`.

The first-party search-discovery gate was also checked through Search Console's
visible URL Inspection and Sitemaps screens on September 2, 2026. The sample
report was already indexed. The LKT landing page and fit-check page were each
unknown to Google, so each received exactly one accepted indexing request; an
accepted priority-crawl request does not prove that either page has been
indexed. The root `https://lazying.art/sitemap.xml` was absent from the submitted
list, then submitted once and confirmed with status `Success` and seven
discovered pages. Do not resubmit those URLs merely to seek higher priority;
recheck their status in a later observation window.

The same visible 28-day report showed the Classical Mechanics Reader as the
second-ranked page with 22 clicks, up 47%. The live reader previously ended at
PDF and source links. LazyLearn commits `03ba09e` and `fa61690` now add one
tracked, cache-safe route to the complete LKT sample fit report beneath the
reader. The panel keeps the archive public and free, labels the report as
project-owned rather than a customer result, and contains no direct fit-check
or payment link. A successful Pages build plus a visible production render
verified the exact route and styling. Search clicks justified closing this
owned conversion dead end; they remain attention evidence, not a lead or sale.

On September 2, 2026, one fresh Hacker News question exposed a reusable need:
keeping an internal university research corpus offline while deciding whether
a small language model should rewrite queries or generate the final answer
under a limited context budget. Hacker News remains research-only, so no
agent-authored comment or direct message was sent. Instead, the existing owned
guide was expanded with a measurable retrieve-deduplicate-rerank experiment,
source identifiers, an abstention boundary, and a comparison of the small-model
roles. The English, Simplified Chinese, and Japanese versions were each checked
through their visible language controls; every version links once to the RAG,
Lost in the Middle, and query-rewriting papers and once to the LKT fit check.
The deployed source is LazyBlog commit `1631e82`. This is an owned response
asset, not evidence of public engagement, a lead, a sale, or revenue.

The same demand review deliberately left posts `1970` and `2994` without an LKT
commercial CTA. The former answers MetaTrader terminal-integration questions;
the latter packages a source-code repository for model context. Neither is the
bounded private book, dictionary, PDF, or document collection covered by the
current USD 250 sprint. Traffic overlap alone is not product fit.

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

`python inbound_monitor.py once` reads only the aggregate message and unread
counts exposed for the dedicated `LKT Fit Checks` iCloud folder. It does not
focus a tab, navigate, click a folder, open mail, or persist a sender, subject,
address, or body. The dedicated folder must already be selected in the restored
iCloud tab; otherwise the monitor fails closed. The controlled routing
probe is the initial baseline. A later increase creates a review alert—not a
qualified lead or sale—and the operator must inspect only that folder visibly
before recording any funnel outcome. Continuous mode uses
`python inbound_monitor.py loop --interval-minutes 15` and shares the browser
operation lock with discovery so it cannot race another CDP controller.
The project desktop restores the authenticated inbox tab after an owned stack
restart, while the monitor continues to read only the dedicated folder's
aggregate counts and never opens message content.

The rest of the portfolio supplies proof and implementation components rather
than competing calls to action. PocketPolyglot, LinguaLeaf, WordsCardEink, and
WordOrigins strengthen the multilingual pipeline; BLOG and Search Console show
existing demand; LazyPromotion finds needs and keeps the evidence ledger;
LazyEdge can support a later deployment. Other offers remain separate campaigns
and are mentioned only when they directly fit the stated need.

## Secondary experiment: Postiz affiliate

The [Postiz affiliate experiment](postiz-affiliate.md) is a capped secondary
route for readers who already need reviewed multi-platform scheduling. The
Postiz-branded Dub page currently advertises 30% per sale for the customer's
lifetime, but that percentage is not income evidence. No referral URL, paid
referral, or commission was verified at the 2026-09-01 zero baseline.

Lead with firsthand CLI/MCP guidance, provider pitfalls, and an honest
managed-versus-self-hosted decision. Put a clear commission disclosure beside
any eventual Dub-issued link. Keep Reddit community replies value-only and
Hacker News research-only. Aggregate dashboard clicks and signup/trial counts
remain private signals; record a paid referral separately, and count money
only after an `affiliate_commission_received` outcome is verified. This route
does not displace the fixed USD 250 LKT sprint unless received commission and
the experiment's acceptance criteria justify more work.

## Fit-first pilot path

[Local Knowledge Terminal](https://lazying.art/lkt/) publishes the bounded USD
250 collection-fit sprint for people with one private book or dictionary
collection. It is a service using the customer's existing machine, not
ready-to-ship hardware. The [free fit check](https://lazying.art/lkt/fit-check/)
precedes payment and builds a reviewable email draft without automatically
storing, uploading, or sending the answers. An inquiry is a lead at most; it is
never recorded as a sale without confirmed payment.

### Hardware is a separate quote

The USD 250 sprint remains valid because it uses the customer's existing
machine. A Raspberry Pi or assembled LKT device is never included at that
price. Before quoting supplied hardware, run the read-only economics check in
[`lkt-hardware-pricing.md`](lkt-hardware-pricing.md), confirm the full landed
BOM, and review shipping, tax, cancellation, return, warranty, and support
terms. Keep the service and device as separate line items and do not activate a
hardware checkout from an incomplete cost estimate.

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
