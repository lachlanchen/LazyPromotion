# Postiz affiliate experiment

Yes, this can be a secondary income channel. It is a better fit than a random
affiliate offer because LazyingArt already uses Postiz and can teach a real,
reviewed workflow. It is not passive or proven income yet: the experiment starts
at zero, and the USD 250 Local Knowledge Terminal sprint remains the primary
first-USD-1,000 path until received commission proves otherwise.

The machine-readable contract is
[`campaigns/postiz-affiliate-pilot.json`](../campaigns/postiz-affiliate-pilot.json).

## What is verified

Checked again on 2026-09-10:

- The Postiz application is accepted. Its authenticated Dub overview states
  **30% per sale for the customer's lifetime** and a **30-day holding period**.
  Neither is a conversion rate, payout guarantee, or income result.
- The [application page](https://partners.dub.co/postiz/apply) requires a name,
  email, website or social channel, promotion plan, and acceptance of terms.
- [Dub's partner terms](https://dub.co/legal/partners) say a partner may need a
  separate client agreement, an active account, identity verification, and a
  valid payout method. Commission becomes payable only after the client pays
  Dub; dashboard states before `Completed` are not proof of cash received.
- The [public Postiz terms](https://postiz.com/terms-of-service) cover use of the
  product but do not supply every program-specific affiliate detail. The
  overview does not state the attribution window, eligible-plan boundary,
  payout threshold, or reversal rules, so those claims must not be invented.
- The current public program page does not state a seven-day trial. Do not use
  that detail in promotion unless the accepted program terms confirm it.

The program may therefore produce recurring commission, but 30% is a reward
rate—not a conversion rate, payout guarantee, or revenue forecast.

The application was submitted once with verified LazyingArt business details
and accepted. Dub issued a referral link, which was opened once without a
purchase and resolved to the official Postiz site with attribution parameters.
The dashboard then showed one click, zero leads, zero sales, zero earnings, and
no payouts. That click is the destination test, not audience demand.

Payout onboarding reached Stripe Connect after the verified partner business
name and user-authorized US checking-account route passed the visible precheck.
Stripe then presented a human anti-bot challenge, which was not bypassed.
Public referral placement remains off until the payout and placement gates
pass.

## Useful-first angle

The audience is narrow: open-source maintainers, solo builders, and small teams
that already need to schedule reviewed content across multiple platforms. Three
assets are enough for the first 30-day cycle:

1. a reproducible Postiz CLI and MCP setup guide using official documentation;
2. a provider-pitfall checklist for uploads, live settings, drafts, public
   release verification, and analytics;
3. an honest managed-versus-self-hosted decision guide based on the [official
   Postiz repository](https://github.com/gitroomhq/postiz-app), including who
   should not buy the managed service.

Each asset must solve the operational problem without the affiliate link. Add
the link only after the answer, show free and self-hosted paths where they fit,
and state real limitations. Do not scatter a bare referral link across social
profiles, repositories, comments, or direct messages.

The first asset is now live: [Postiz CLI and MCP: A Review-First Social
Scheduling Workflow](https://blog.lazying.art/html/computer_internet/unix_linux/command_shell_software/3772/postiz-cli-mcp-review-first-social-scheduling.html).
It was published on 2026-09-02 in English with Chinese and Japanese
translations. The page uses ordinary, untracked Postiz links and contains no
affiliate disclosure or referral call to action. This counts as one useful
owned asset, not a click, referral, commission, or revenue event.

## Disclosure templates

Blog or article:

> Affiliate disclosure: I use Postiz and may earn a commission if you subscribe
> through this link. The guide and its limitations come first.

Short social post:

> Ad/affiliate: I use Postiz and may earn a commission if you subscribe through
> this link.

Video, both spoken and on-screen:

> Affiliate disclosure: I may earn a commission if you subscribe through my
> Postiz link.

Put the disclosure with the recommendation and before or next to the link. It
must remain visible before collapsed text; a profile statement, `affiliate
link`, platform control, or hashtag cluster is not enough by itself. This
follows the FTC's [affiliate guidance](https://www.ftc.gov/business-guidance/resources/ftcs-endorsement-guides-what-people-are-asking)
and [social disclosure guidance](https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers).

## Evidence and tracking

The truthful funnel is:

`useful asset → tracked click → signup/trial if reported → paid referral → pending commission → received commission → possible reversal`

The 2026-09-01 baseline is an administrative zero: no application acceptance,
referral URL, affiliate content, tracked click, referral, or commission has been
verified. It is not an authenticated Dub analytics snapshot.

At the 2026-09-10 checkpoint, one useful owned asset, acceptance, the issued
link, and its destination are verified. The dashboard contains only the single
operator test click; leads, sales, earnings, payouts, and received revenue are
zero.

Keep dated aggregate clicks and signup or trial counts in a private
`signals.py` snapshot. For example, after visibly reading the Dub dashboard,
prepare `.local/private/postiz-affiliate-signals.json` with source
`dub_partners`, a precise period, the observation time, and evidence under
`.local/evidence/`; then run:

```bash
python signals.py import-json .local/private/postiz-affiliate-signals.json \
  --confirm-private-first-party-data
python signals.py report --source dub_partners
```

Clicks and signup/trial counts are demand evidence, not revenue. Record each
verified paid referral with its private Dub conversion reference; only a hash is
stored:

```bash
python metrics.py record \
  --kind affiliate_referral_confirmed \
  --campaign-id postiz-affiliate-pilot \
  --reference PRIVATE_DUB_CONVERSION_REFERENCE \
  --confirm-verified-outcome
```

Record money only when the payout is actually received:

```bash
python metrics.py record \
  --kind affiliate_commission_received \
  --campaign-id postiz-affiliate-pilot \
  --amount RECEIVED_AMOUNT \
  --currency USD \
  --reference PRIVATE_DUB_PAYOUT_REFERENCE \
  --confirm-verified-outcome
```

Use `affiliate_commission_reversed` with a private reversal reference if a
received commission is later clawed back. Never copy customer names, emails,
subscriptions, dashboard exports, bank data, payout credentials, or raw
identifiers into Git.

## Acceptance and stop rules

Activation requires an accepted Postiz application, reviewed exact program
terms, a complete payout route, a Dub-issued referral URL, a non-purchasing
attribution test, and a disclosure review. Acceptance, the link, and the test
are complete; payout and placement remain pending. The URL stays in
`.local/private/affiliate-programs/postiz.json`; no URL is invented in source
control.

After one capped 30-day cycle, continue once if there is either one confirmed
paid referral, or at least 25 verified outbound clicks plus one dashboard-
reported signup or trial. The channel becomes proven income only after the
first `affiliate_commission_received` record.

Stop or pause when any of these occurs:

- terms, payout eligibility, or attribution cannot be verified;
- a disclosure is hidden, the destination changes, a platform forbids the
  placement, or a reader reports deceptive or spam-like promotion;
- three useful assets produce fewer than 25 verified clicks in 30 days;
- 50 verified clicks produce no dashboard-reported signup or trial; or
- two capped cycles and at least 100 verified clicks produce no paid referral.

These limits prevent a promising percentage from consuming the time needed for
LazyingArt's owned products and customer work.

## Remaining activation gate

Keep the issued URL private and do not change the live tutorial while payout is
incomplete. Resume the existing connected-account draft only with a legitimate
account-country business phone and recheck the resulting payout, program, and
placement terms before adding one nearby disclosure and link.
