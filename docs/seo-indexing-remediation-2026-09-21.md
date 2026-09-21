# Search Console remediation — September 21, 2026

Technical repairs are deployed. This is not a claim that Google has indexed
every page or that every exclusion should disappear.

## What was actually wrong

1. The blog still had Apache rules for the **inactive GTranslate plugin**.
   English and other language URLs went through that old addon before the
   current LazyBlog Translations router. Removed only the obsolete block,
   preserving WordPress routing and authorization-header forwarding.
2. Blog home and archive pages lacked explicit canonicals. A small MU-plugin
   now adds them, preserves pagination, and redirects existing legacy English/
   Chinese archives to their current URLs. A database dry run identified
   **238 valid destinations among 257 observed archive-path candidates**.
   This count spans several reports; it is not 238 confirmed new indexed pages.
3. The old numbered-post redirect constructed doubled/mistaken paths. It now
   resolves published posts through WordPress, preserving actual translations.
4. The main website's 404 page redirected **every unknown URL to the homepage**.
   Unknown paths now retain an honest 404. Eleven verified historical paths
   have exact redirect pages; seven verified `?p=` IDs have a bounded browser
   redirect. GitHub Pages redirects use immediate HTML refresh or JavaScript,
   not a claimed server-side HTTP 301.
5. One reported pocket-book download had moved. Its new and old source PDFs
   have identical SHA-256 checksums. Added a small redirect page to the current
   download without duplicating the PDF.
6. Ten public landing pages gained self-canonicals: LazyEarn, LinguaLeaf,
   HowYouGotRich, LazySkills, IDEAS, OnlyIdeas, Paper Revision Skill, LalaMedias,
   IdeasGlass, and IdeasRobot. The eInk words-card page also gained one.
7. The coin sitemap and website return 404. Removed the unavailable sitemap
   submission and the coin calls to action from LazyingArt, OnlyIdeas, and
   LazyEarn. No DNS records, source repositories, or customer data were deleted.
8. Added six useful article links to the static product directory: local PDF
   search, multilingual chunking, study-card deduplication, MCP authentication,
   LaTeX redlines, and research-code reproduction. The articles were not padded
   or rewritten to satisfy an indexing counter.

## All eleven reported reasons

The report was last updated **September 18**, before these repairs. Counts are
the baseline, not a measurement of today's results.

| Reason | Baseline URLs | Disposition |
| --- | ---: | --- |
| Alternate with proper canonical | 411 | Expected for genuine duplicates; preserve the canonical article. |
| Not found | 347 | 245 belong to the unavailable coin host, 91 to old blog paths, seven to the main site, and four to other hosts. Recover valid moves; keep nonexistent/private/unrelated paths missing. |
| Duplicate without selected canonical | 91 | Blog archive canonicals and legacy-language routing repaired; main-homepage canonical retained. Provider-managed aliases require separate provider review. |
| Noindex | 80 | 77 are login URLs and stay excluded. Three are provider-managed publishing URLs, not first-party application-code fixes. |
| Redirect | 63 | Normal for moved/canonical URLs; do not remove valid redirects to erase the report. |
| Robots blocked | 2 | Both are administration paths; protection retained. |
| Other 4xx | 1 | An administration AJAX endpoint, not an index target. |
| Soft 404 | 1 | Thin monthly excerpt archive now has a canonical and `noindex`; its underlying article stays eligible. **Google validation started September 21.** |
| Crawled, currently not indexed | 496 | Eligible public articles/landing pages audited; many other examples are feeds, login routes, archives, PDFs, or provider-managed URLs. Indexing remains Google's decision. |
| Discovered, currently not indexed | 190 | Same audit plus stronger internal links to six practical articles; no bulk indexing requests. |
| Google chose another canonical | 2 | One old article slug now redirects to its current slug; the translated example has a same-language canonical. Google's report awaits recrawl. |

## Verification

- Full example lists captured privately for all eleven reasons.
- **383 reported public article/landing URLs checked**: after redirects, every
  one returned HTTP 200, had a canonical, and had no `noindex` directive.
  This includes 357 blog URLs and 26 main-site URLs, not 383 unique articles.
- English, Japanese, and Chinese article routes checked live. Real translations
  keep their own canonicals; source-language aliases identify the source page.
- Live checks confirm archive HTTP 301s, corrected numbered-post destinations,
  self-canonical pagination, the `noindex` monthly archive, and genuine unknown
  404s. The author sitemap provider is omitted because author excerpts are
  intentionally not indexed.
- **47 PHP policy checks** passed; Apache configuration test passed.
- **45 website tests** passed, including generated redirects, unknown-ID safety,
  sitemap consistency, private-URL exclusions, and navigation behavior.
- Mobile product-directory review passed without horizontal overflow. Its six
  guide links are ordinary HTML links, available without JavaScript.
- The five remaining submitted sitemaps showed **Success**. The removed coin
  submission is not a request to remove pages from Google's index.
- Changes committed and pushed in their owning repositories. Live WordPress
  deployment touched only the new MU-plugin and the reviewed `.htaccess` block;
  unrelated live plugin/theme updates were preserved. Generated page cache was
  refreshed, and private rollback copies were retained.

## What remains outside a code fix

- Wait for Google's soft-404 validation and normal recrawl; inspect useful
  canonical pages again after several days. Do not repeatedly submit the same
  requests or mark validation complete ourselves.
- Provider-managed Medium aliases and editorial quality need separate review.
  Do not bypass platform controls or invent content to force indexing.
- This is not an exhaustive metadata rewrite of every portfolio repository.
  Other optional canonical additions remain, including sites with unrelated
  in-progress edits. Missing a canonical alone does not prove an indexing bug.
- Correct 404s, login exclusions, API exclusions, redirects, and duplicate
  alternates are allowed to remain in Search Console.
- No revenue, lead, ranking improvement, or newly indexed page is attributed
  to this work without later evidence.

## References

- [Google: canonical consolidation](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)
- [Google: Page indexing report](https://support.google.com/webmasters/answer/7440203?hl=en)
- [Google: HTTP status codes](https://developers.google.com/crawling/docs/troubleshooting/http-status-codes)
