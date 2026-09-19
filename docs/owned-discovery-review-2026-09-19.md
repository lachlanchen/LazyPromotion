# Owned discovery review — September 19, 2026

Scope: repair current mobile install paths and verifiable discovery metadata,
then return to buyer qualification for the existing paid offers.

## Shipped

LazyingArtWebsite commit `a1376cc89c925ae3e9fcf6876667b2a7c98cdefa`:

- EchoMind's homepage Google Play action now uses the public production listing,
  not a restricted internal-test invitation. All 13 interface languages retain
  the distinction between public Android and iPhone TestFlight access.
- Historical Android tester binaries remain recoverable, including the upstream
  builds 81 and 82. They are not the ordinary homepage install recommendation.
- The L & N work card now links its production Google Play and App Store pages,
  alongside the free browser version and source. The US Apple listing is paid;
  the existing social demonstration describes the free browser version only.
- The homepage now declares one canonical URL and uses an existing social-preview
  image. Its `/index.html` and query-string duplicates should consolidate, not
  compete as separate pages.
- The GlassAgent privacy page has a self-canonical without changes to policy text.
- The sitemap contains 36 local, canonical, indexable source pages; the old
  cross-subdomain chat entry was removed without removing public app links.

GitHub Pages built this exact commit. Website contracts: 35 passed. Visible
browser checks: 13 languages at desktop and mobile widths, 26 passes; reviewed
screenshots remain private. The upstream APK additions were preserved during
rebase and checksum verification. No force push or artifact deletion occurred.

## Indexing decision

Search Console samples distinguish old archives, redirects, duplicate routes,
translated articles, and useful pages awaiting crawl. Both the main and blog
sitemaps are being read successfully. No blanket redirect, archive recreation,
mass indexing request, or removal of intentional noindex was performed.

Canonical URLs and sitemaps are signals, not a promise that Google will index a
page. See [Google's canonical consolidation guidance](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls).
Counts and selected report samples are private operational evidence.

## Distribution and money

The September 19 Postiz read confirms the existing L & N LinkedIn item is still
queued for September 20 at 02:00 UTC. Its reviewed copy is unchanged and no
duplicate was created. Store availability, queue state, code stars, and indexing
repairs are not sales. The next priority is a qualified buyer for an existing
bounded paid offer, with delivery and verified payment recorded separately.
