# Bunko promotion handoff

Checked 2026-09-25 UTC. This is a public-facts handoff for [Bunko](https://github.com/lachlanchen/Bunko), separate from the L & N campaign. It contains no tester links, private contacts, store credentials or browser state. Recheck store pages before any public post.

## What is public now

| Channel | Verified state | Visitor destination |
| --- | --- | --- |
| Web reader | Live, with a 183-edition downloadable catalogue | https://lachlan.lazying.art/Bunko/ |
| US App Store | Version **1.0.0** is **Ready for Sale**; Apple's public lookup reports **USD 0.99** | https://apps.apple.com/us/app/bunko-classics-with-ruby/id6815137919 |
| Google Play | Production **1.0.0 (1)** is still in review; the public listing returned **404** in this check | Do not use a public Play call to action yet |
| App Store update | Version **1.0.1 (2)**, with covers, visible Light/Dark/System controls and catalogue refresh, is **Waiting for Review** | Do not describe these as features of the approved iOS binary yet |
| Play update | Version **1.0.1 (2)** is available only to internal testers | Do not advertise it as a public Android release |

The app is paid up front on iOS, with no subscription or in-app purchase. The web reader is a separate free destination. The public [bunko-books](https://github.com/lachlanchen/bunko-books) repository carries the downloadable book bundles, not an additional app store. Adding approved book bundles can update the catalogue without a new binary.

## Product and audience

Bunko is a pocket reader for public-domain Chinese, Japanese and English classics, alongside owner-edited study books. Readers can choose displayed languages and layouts, see pinyin or furigana above characters where available, and save chapters for offline reading. The interface has English, Simplified Chinese, Traditional Chinese and Japanese. The catalogue has **183 cleared editions**: 150 classics and 33 owner editions, not necessarily 183 distinct original works. Study renderings are AI-generated and may contain errors; they are not scholarly editions. Public-domain status varies by territory. The app includes mature literary themes and must not be marketed as a children's app.

Useful audiences include readers of Classical Chinese history and philosophy, Japanese literature learners, bilingual readers, and teachers who want readable parallel passages. Lead with a specific reading problem: following a classical passage while keeping the original and its readings visible, or carrying a chapter offline. Avoid claiming that every classic has been acquired or that the companion tutor is already in the shipping app.

## Safe launch angle

An Apple-specific launch post can link the US App Store page now, with the current **USD 0.99** price and 1.0.0 feature set. A web-reading post may link the live web reader and show the expanded catalogue and covers. Keep those claims separate. Suggested draft for review:

> I built Bunko to make Chinese and Japanese classics easier to read without losing the original text. It puts pinyin or furigana above the characters, lets you compare languages, and saves chapters for offline reading. The web reader has a growing public-domain catalogue; Bunko is also available on the US App Store for $0.99. Which classic would you want to read this way?

Use one clear destination per post. Disclose that the maintainer built the app. Do not send or schedule this draft without the normal LazyPromotion destination and exact-content review. Do not reuse L & N's posts, images, target communities or existing campaign queue.

## Assets and evidence

- Reader source, screenshots and product contract: [Bunko repository](https://github.com/lachlanchen/Bunko), especially `store/assets/`, `BRIEF.md` and `store/release.yaml`.
- Book rights audit and publishing workflow: [catalogue](https://github.com/lachlanchen/Bunko/blob/main/docs/catalogue.md) and [library guide](https://github.com/lachlanchen/Bunko/blob/main/docs/library-publishing.md).
- Current 150-edition index: [bunko-books/reader-index.json](https://github.com/lachlanchen/bunko-books/blob/main/reader-index.json).
- Apple 1.0.1 review record: [curated submission artifact](https://github.com/lachlanchen/Bunko/blob/main/store/artifacts/apple-submission-1.0.1.json).

Before an Apple post, reopen the public listing to confirm price, version, artwork and regional availability. Before any Google Play post, require a live public listing and a published production release. Store submission, tester access, public listing visibility, installs and sales are separate states; none implies revenue.

## Owned reading guide — September 25

[Reading Chinese and Japanese Classics Without Constantly Switching Tabs](https://blog.lazying.art/html/books/3853/bunko-chinese-japanese-classics-pinyin-furigana.html) is published on the blog. It uses the shipping reader's *Sanshirō* screenshot, explains a short original/parallel-text reading routine, and links to the US App Store at the verified USD 0.99 price. It identifies the AI-generated study renderings without presenting them as scholarly translations. No Google release, pending 1.0.1 feature, distinct-book count, learning result or revenue is claimed.

The source is `articles/bunko-reading-classics/post.md`; the LazyBlog archive is `content/lazypub/20260925-bunko-reading-classics/`. The live source content, image, canonical and store link were checked on desktop and mobile. This is a source-only English article, separate from the multilingual editorial completion count.

The [free Medium edition](https://lazyingart.medium.com/reading-chinese-and-japanese-classics-without-constantly-switching-tabs-b21c8b1ed6d2) is also published, under Language Learning and Books. Its original-source canonical points to the blog. All 15 expected text blocks, the screenshot and both destination links were verified in the published author view; the paywall was disabled before the one publication action. Medium blocked the separate unauthenticated HTTP check, so that check does not establish anonymous visibility. No duplicate import, additional social post or community reply was sent.

## Creator introductions — September 25

Two separate introductions were subsequently published through Postiz after reviewing the saved copy, links and previews:

- [Reddit: Bunko on r/SideProject](https://www.reddit.com/r/SideProject/comments/1wpsber/bunko_a_reader_for_chinese_and_japanese_classics/). The community welcomes project introductions. The post explains the reading problem, shows how Sanshirō fits, describes the small React/ruby/IndexedDB implementation, and includes both the free reader and USD 0.99 US App Store route. The public post and original links were verified both signed in and logged out.
- [X: the Sanshirō reading layout](https://x.com/lazyingart/status/2103425611532550326). A short introduction uses the real reader screenshot and links to the illustrated blog guide, which continues to the App Store. The published text, link and loaded image were verified in the signed-in view.

Exact published copy and public evidence are in [`campaigns/bunko-classics-introduction.json`](../campaigns/bunko-classics-introduction.json). These records let the existing read-only owned-post monitor recognize the campaign. No community replies, private messages, votes or paid promotion were sent. A relevant incoming question can be reviewed on its own merits; neither post calls for an automatic second pitch. Publication is not a lead or sale.

### Incoming reader feedback

A later [comment](https://www.reddit.com/r/SideProject/comments/1wpsber/comment/pbxz0ky/) suggested hiding translations sentence by sentence and asked which books readers open first. A [short reply](https://www.reddit.com/r/SideProject/comments/1wpsber/comment/pbympai/) acknowledged the idea and explained the current no-analytics behaviour; it was verified after reload and in the logged-out view. No additional promotional link was added. The monitor records one owned reply so it is not mistaken for another reader's response.

Sentence-level reveal and optional aggregate book-open counts are proposals, not shipped features. Reading progress currently stays on the device. Adding collection would require an opt-in design and updated product, privacy and store declarations; an open must not be described as completed reading. No app code or data collection was changed by this feedback follow-up.

## Library expansion — September 25

Bunko's downloadable catalogue now has **162 cleared editions**: the previous 150 classics plus 12 owner editions in separate Physics, Learning, Finance and Travel shelves. The additions include three trilingual travel guides, *How You Got Rich* in English, Japanese and Chinese, six independent Leonard Susskind lecture companion volumes in English, *How to Speak and Write* and *Wealth From First Principles*. The source and rights records are in [bunko-books](https://github.com/lachlanchen/bunko-books). Bunko 1.0.2 adds local equation rendering and mobile figure support; describe these app features publicly only after that binary reaches the relevant public store. The web reader can show them after its deployment passes. Do not call the companion notes Susskind-authored or endorsed, and do not imply every source work has all three languages. The existing Reddit, X, blog and Medium introductions describe the older public version and should remain as historical posts.

Later the same day, the downloadable catalogue grew to **183 editions** at `bunko-books` commit `09644d2`: all nine supplementary Susskind companion courses, four additional core course runs, *Justice with Michael Sandel*, and seven more edited LazyEarn books. Physics now has 19 English companion editions, Learning has two English editions, Finance has nine editions (one trilingual), and Travel has three trilingual guides. The downloadable catalogue update requires no new binary; the existing 1.0.2 internal builds fetch it online. Do not imply the Jim Rohn transcript book or raw Hard Knocks interview corpus is in Bunko, or imply the supplementary notes are Susskind-authored.
