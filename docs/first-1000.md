# First USD 1,000: one repeatable offer

The primary offer is the **Local Knowledge Terminal collection-fit sprint** at
**USD 250**. The milestone is four confirmed payments, or USD 1,000 gross before
fees, tax, refunds, and delivery costs. It is a target and operating constraint,
not a revenue promise.

## Fixed scope

One sprint covers one customer-provided collection, one language goal, and one
existing machine. It delivers:

1. a written data, citation, and privacy map;
2. a small browser proof from a representative sample when the source is usable;
3. a clear go/no-go recommendation and the boundary of any larger deployment.

Hardware, shipping, custom OCR, and production deployment are excluded. The
customer must have the right to use the source. A free fit check comes first;
Stripe payment is requested only after both sides accept the scope.

The verified fit-check page is
<https://lazying.art/lkt/fit-check/>. It validates the minimum questions and
builds a reviewable email draft inside the current browser tab. It stores,
uploads, and sends nothing automatically; the prospective customer controls the
final email send.

### Inbox readiness gate

The public `contact@lazying.art` address has iCloud MX routing and accepted a
controlled delivery test without an observed bounce. That proves routing, not
operator monitoring: iCloud Mail is not authenticated in the promotion
browser, so mailbox access remains explicitly unverified. Do not promise a
response time, mark an email as a qualified lead, or infer a conversion until
an operator has opened the mailbox and reviewed the actual inbound message.
Before increasing distribution, verify the inbox login and establish a simple
fit-check label or folder without copying customer content into this repository.

## Qualification gate

Before payment, collect only the minimum facts needed to decide fit:

- collection and intended use;
- language goal and intended readers;
- source rights, format, and approximate size;
- privacy or offline requirement;
- existing hardware.

Reject or redirect the inquiry when the customer lacks source rights, needs an
unbounded data migration, needs custom OCR inside this scope, expects shipped
hardware, or needs a production SLA. Do not store customer documents, email,
payment data, or private corpus text in the promotion repository.

## Repeatable promotion loop

1. Discover one current, specific problem involving private documents, local
   search, citations, or multilingual reading.
2. Give the person a useful standalone answer. On communities with strict
   self-promotion norms, keep the reply value-only and let the profile do the
   quiet discovery work.
3. When the problem is reusable, turn the answer into one owned, searchable
   guide. Put the complete solution first and one tracked fit-check link last.
   The first proved example is [the confidential-PDF search
   guide](https://blog.lazying.art/html/computer_internet/3619/search-confidential-pdfs-locally-without-overbuilding-rag.html).
4. Publish the guide through LazyBlog, verify its translations and boundaries,
   and let the successful WordPress sitemap registered in Search Console carry
   future discovery. Manual URL indexing is an optional acceleration, not a
   substitute for the sitemap.
5. Send qualified readers to <https://lazying.art/lkt/fit-check/>, never
   directly to payment.
6. Record a `qualified_lead` only after a real fit inquiry.
7. After scope acceptance, use a reviewed Stripe request for USD 250.
8. Record `sale_confirmed` only after verified payment, using a private receipt
   reference whose hash enters the ledger.
9. Deliver the sprint, then ask—without pressure—whether an anonymized outcome
   or referral may be shared.

No automated generated comments are posted to Hacker News. Reddit community
rules are checked before any reply. The first-party LKT X and Instagram posts
were visibly reviewed and queued for September 8, 2026 at 01:00 and 11:31 UTC;
their exact copy, uploaded visuals, direct fit-check destinations, provider
settings, and future state were confirmed before scheduling.

The confidential-PDF guide also has two value-first distribution assets. A
concise X pointer is queued for September 1 at 14:00 UTC. A longer standalone
decision tree is queued for September 1 at 02:00 UTC on the connected Reddit
account's own profile—not in a third-party community—so people arriving from
value-only replies can find useful context without a second promotional reply.
Both use tracked guide links, and the Reddit resource includes an explicit
maintainer disclosure.

## How the portfolio contributes

The portfolio is evidence and implementation leverage, not a list of calls to
action:

- LocalKnowledgeTerminal is the offer and delivery core.
- PocketPolyglot and LinguaLeaf support multilingual source preparation.
- WordsCardEink and WordOrigins supply proven card and graph patterns.
- BLOG and Search Console reveal existing educational demand.
- LazyPromotion finds explicit needs and keeps the private funnel ledger.
- Postiz carries reviewed first-party posts.
- LazyEdge may support a separately scoped later deployment.
- LazyEarn and HowYouGotRich may document verified lessons only after real
  outcomes exist.

Every other repository remains searchable in the public inventory and may be
matched to a separate real need. It should not be inserted into the LKT sprint
pitch merely to promote more projects.

## Truthful measurement

The operational funnel is:

`helpful interaction → fit inquiry → qualified lead → scope accepted → Stripe payment → delivered sprint`

Visits, likes, replies, GitHub stars, and positive comments are not revenue.
Run `python metrics.py report` for the private aggregate. After a verified USD
250 payment, record it with the campaign `local-knowledge-terminal-pilot` and
project `localknowledgeterminal`; never put the raw Stripe receipt in Git.
