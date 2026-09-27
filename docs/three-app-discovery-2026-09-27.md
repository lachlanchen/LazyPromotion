# Three-app homepage discovery — September 27, 2026

[LazyingArt's homepage](https://lazying.art/) now identifies L & N, Bunko and
EchoMind in its page title, description and matching social-preview metadata.
The description names the actual uses: pronunciation practice, annotated
classics, and conversations with language support.

The existing layout, app-store destinations, prices, account routes and all
13 locale dictionaries are unchanged. The homepage sitemap date reflects this
edit; other page dates were not refreshed without changes.

Website source:
[`14750eb`](https://github.com/lachlanchen/LazyingArtWebsite/commit/14750eb9dba24185a5f31072635b40a21aae334b).
All 48 website tests and a local HTTP metadata check passed. GitHub Pages built
that commit, and public HTTP readback at 14:30 UTC returned the new title,
description and sitemap date. This was a metadata-only change, not a visual
redesign or a new app release.

Google may choose different snippets and recrawl later. No new indexing,
ranking, traffic or sales result is claimed, and no duplicate Search Console
submission was made.

## Subsequent store and search checks

The [L & N handoff](l-and-n-promotion-handoff.md) now records the Apple
promotional-text save and Google's separate English description review. The
Google production binary is unchanged; reviewed copy is not yet verified as
approved or public.

Search Console's September 27 review confirms the L & N homepage is indexed,
with its own canonical selected and sitemap detected. No additional indexing
request was made. This is separate from today's company-homepage metadata
edit; it does not establish that the edit caused an indexing or sales result.

Bunko's [reader homepage](https://lachlan.lazying.art/Bunko/) is discovered but
not yet indexed, with no last crawl reported. Public HTML returns 200 but has
no explicit canonical or useful non-JavaScript entry content. Its URL already
appears in the existing discovery sitemap. A bounded web-only improvement has
been handed to Bunko's release owner; it is not deployed evidence and must not
bring unqualified app/account features into a web release. Descriptive metadata,
a consistent canonical and accessible initial content follow
[Google's JavaScript guidance](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics),
but do not guarantee indexing.

The older blog Soft 404 validation did not pass: the remaining example is the
legacy `writing/shoping` category archive. It needs its own content/status
disposition, not repeated validation or an unrelated app pitch. No claim that
every indexing issue is solved is made.

Existing Reddit moderation and scheduled-post states remain governed by their
campaign receipts. Search counts and raw Search Console captures remain private;
none establishes installs, retained users or revenue.
