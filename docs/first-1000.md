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

A live visible-browser smoke test on September 2, 2026 used synthetic,
non-customer answers and stopped at that review panel. It verified the exact
`USD 250` wording, intended address and subject, and all four allowlisted UTM
fields with no non-read network request or additional page. The mail action was
not clicked. This proves only that the review-first path is ready; it is not a
lead, sale, or revenue event.

Prospective customers can inspect a
[complete sample fit report](https://lazying.art/lkt/sample-report/)
before sharing any material. It applies the three deliverables to LKT's own
documented reference collection, including measured record and index counts and
explicit no-go boundaries. It is project-owned evidence—not a customer result,
testimonial, benchmark, sale, or claim of a paid engagement.
The [source report and corpus
ledger](https://github.com/lachlanchen/LocalKnowledgeTerminal/blob/main/docs/sample-fit-report.md)
remain public for reproducibility.

### Inbox readiness gate

The public `contact@lazying.art` address has iCloud MX routing and accepted a
controlled delivery test without an observed bounce. Authenticated iCloud Mail
then displayed that exact test subject, and the operator created a dedicated
`LKT Fit Checks` folder. This verifies routable, reviewable operator access; it
does not prove that every future message is a qualified lead. A narrow iCloud
rule moves only messages whose subject contains the live fit-check contract,
`Local Knowledge Terminal — free collection fit check`, into that folder. Do
not assume that configuration alone proves delivery: an end-to-end controlled
probe started from a clear destination folder, used the exact live subject and
no customer data, received Gmail's sent acknowledgement, and then appeared
automatically inside `LKT Fit Checks`. This proves the narrow routing path, not
a response SLA or sale. Do not promise a response time, copy message contents
into this repository, or infer a conversion until the actual inbound request
has been reviewed against the qualification gate below.

`python inbound_monitor.py loop --interval-minutes 15` records only the exact
folder's aggregate message and unread counts. The one controlled probe is its
baseline. It never opens mail or persists message metadata; an increased count
is only a prompt for visible review, not a qualified lead or sale.
The single project-owned desktop now restores the inbox and campaign tabs after
an owned restart and pins its campaign and affiliate browser windows to separate
full-size noVNC lanes, preventing focus-order swaps from interrupting the
aggregate monitor.

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
   search, citations, or multilingual reading. Buyer-intent routes require the
   hydrated body—not only search syntax—to prove ownership, a search task, and
   a local/privacy constraint before spending model quota.
2. Give the person a useful standalone answer. On communities with strict
   self-promotion norms, keep the reply value-only and let the profile do the
   quiet discovery work.
3. When the problem is reusable, turn the answer into one owned, searchable
   guide. Put the complete solution first, then the tracked sample report and
   fit check.
   The first proved example is [the confidential-PDF search
   guide](https://blog.lazying.art/html/computer_internet/3619/search-confidential-pdfs-locally-without-overbuilding-rag.html).
4. Publish the guide through LazyBlog, verify its translations and boundaries,
   and let the successful WordPress sitemap registered in Search Console carry
   future discovery. Manual URL indexing is an optional acceleration, not a
   substitute for the sitemap.
5. Let qualified readers inspect the public sample report, then send them to
   <https://lazying.art/lkt/fit-check/>, never directly to payment.
6. Record a `qualified_lead` only after a real fit inquiry.
7. After scope acceptance, use a reviewed Stripe request for USD 250.
8. Record `sale_confirmed` only after verified payment, using a private receipt
   reference whose hash enters the ledger.
9. Deliver the sprint, then ask—without pressure—whether an anonymized outcome
   or referral may be shared.

No automated generated comments are posted to Hacker News. Reddit community
rules are checked before any reply. The first-party LKT X and Instagram posts
were visibly reviewed and queued for September 8, 2026 at 01:00 and 11:31 UTC;
their exact copy, uploaded visuals, sample-report-first destinations, provider
settings, unchanged times, and queue state were confirmed after the update.
The report retains the narrower fit-check action, so the path remains
`public evidence → local fit check → reviewed scope → payment`.

The confidential-PDF guide also has two value-first distribution assets. A
concise X pointer is queued for September 1 at 14:00 UTC. The longer standalone
decision tree was published on September 1 at 02:00 UTC on the connected Reddit
account's own profile—not in a third-party community—so people arriving from
value-only replies can find useful context without a second promotional reply.
Postiz and the public provider page independently confirmed the exact release.
Reddit initially rendered the scheduled protocol-less destination as plain
text; a visible provider-side edit added only the `https://` prefix. The exact
public anchor then resolved to the canonical guide. The live article offered
the project-owned sample report before the commercial action; its real CTA click
preserved the originating Reddit attribution through the complete, empty
fit-check form. The resource retains an explicit maintainer disclosure. The
public Reddit profile itself now has one restrained
bio describing the local-first work and one tracked `Free LKT fit check` social
link pointing directly to the live fit-check page. That owned-profile route is
not permission to add another promotion, follower request, price claim, or link
to a community answer that should remain value-only.

The deployed first-party bridges preserve the originating Reddit, X, or
Instagram attribution when a reader moves from LazyBlog, the LKT offer, or the
sample report into the fit check. They forward only four validated UTM fields
to the exact first-party destination. The reviewed local email draft includes
those fields, while organic readers retain the normal page attribution and no
form is sent automatically.

The downstream payment path can be checked without creating Stripe objects:

```bash
python payment_readiness.py
python payment_readiness.py --check-account --confirm-private-financial-read
```

The report is secret-sanitized and does not expose an account identifier. Even
when live account readiness is true, the per-customer fit check, accepted
written scope, and full fulfillment review remain mandatory; the check never
creates or sends a payment link.

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
