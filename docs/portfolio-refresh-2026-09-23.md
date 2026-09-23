# Portfolio and domain refresh — September 23, 2026

Refreshed GitHub repository metadata, Pages settings, project README links,
local checkout mappings, and the LazyingArt/OnlyIdeas DNS inventories. Private
repositories and operational hosts remain in the ignored local inventory only.

## New work

| Project | Visitor destination | Source and status |
| --- | --- | --- |
| Bunko · 文庫 | [Web reader](https://lachlan.lazying.art/Bunko/) | [Bunko](https://github.com/lachlanchen/Bunko); browser bookshelf verified. Mobile-store publication is not claimed. |
| Bunko reader data | Used by the Bunko reader | [bunko-books](https://github.com/lachlanchen/bunko-books); chapter JSON and catalogue, not a separate website. |
| LazyOracle | [Web app](https://oracle.lazying.art/) | [LazyOracle](https://github.com/lachlanchen/LazyOracle); cultural exploration and reflection, with rule-based calculations and optional AI narration. |
| Auspice · 宜时 | [App introduction](https://auspice.lazying.art/) | Native companion maintained inside LazyOracle; mobile builds in testing, not a separate repository. |

Three new public repositories were created since the September 21 inventory.
The public directory now contains **127 repository entries**, including forks
and archived code, with the existing LightMind-named exclusion retained.
The separate promotion source index has **112 non-archived, non-fork public
repositories**. These counts describe different views, not missing projects.

## Domain decisions

- `oracle.lazying.art`: live HTTPS app with a matching canonical.
- `oracle-fast.lazying.art`: live mirror whose canonical points to the main app;
  documented as an alternative, not added as a competing sitemap URL.
- `auspice.lazying.art`: live public introduction; added to discovery.
- `bunko.lazying.art`: DNS exists, but HTTPS fails. Bunko's project brief makes
  this a possible future alias; the working Pages address remains the listed URL.

No DNS configuration was changed. The owner's removed OnlyIdeas records were
not restored. Backend URLs discovered in repository documentation were not
turned into public product links or probed as visitor pages.

## Updated surfaces

- [LazyingArt product directory](https://lazying.art/products/): 41 reviewed
  destinations, including Bunko, LazyOracle and Auspice.
- [Website/source map](https://github.com/lachlanchen/lachlanchen/blob/main/projects/sites.md)
  and [complete public repo list](https://github.com/lachlanchen/lachlanchen/blob/main/projects/repositories.md).
- Matching JSON catalogues in the website and profile repos, structured data,
  the existing cross-site discovery sitemap, and the product-page modified date.
- LazyPromotion's GitHub source index and categorized work inventory.
- Fresh full private domain/repository map in the profile checkout's ignored
  `.private` directory; no private source links enter the public directory.

## Checks and remaining scope

- Fresh account enumeration and Pages reads, not cached deployment settings.
- Both West DNS zones fully paginated; record values and verification strings
  were not collected.
- 17 portfolio tests and 45 website tests pass; catalogue generation is current.
- Desktop and 390-pixel mobile directory previews pass without horizontal
  overflow. Public-source privacy checks and the two JSON catalogues match.
- The profile-style checker still reports pre-existing README/citation gaps.
  The profile README, translations and support files are unchanged in this update.
- Live Bunko bookshelf and LazyOracle interface inspected without model downloads,
  cloud activation, personal inputs or store actions. Auspice introduction checked.
- No duplicate Search Console registration or sitemap resubmission: the existing
  verified domain property covers the new subdomains and project path.
- Bunko and Auspice HTML currently lack canonical tags; Oracle's `robots.txt`
  and `sitemap.xml` paths currently serve its app shell. Recorded as follow-ups
  for the owning app projects; their active worktrees were not changed.

This inventory covers the authenticated account, declared project links, local
Git checkouts and the two in-scope DNS zones. It cannot establish that no other
unlisted deployment exists. Existing indexing validation still awaits Google's
processing; no traffic, indexing or revenue gain is inferred from this refresh.
