# Bunko promotion handoff

Checked 2026-09-25 UTC. This is a public-facts handoff for [Bunko](https://github.com/lachlanchen/Bunko), separate from the L & N campaign. It contains no tester links, private contacts, store credentials or browser state. Recheck store pages before any public post.

## What is public now

| Channel | Verified state | Visitor destination |
| --- | --- | --- |
| Web reader | Live, with a 150-edition downloadable catalogue | https://lachlan.lazying.art/Bunko/ |
| US App Store | Version **1.0.0** is **Ready for Sale**; Apple's public lookup reports **USD 0.99** | https://apps.apple.com/us/app/bunko-classics-with-ruby/id6815137919 |
| Google Play | Production **1.0.0 (1)** is still in review; the public listing returned **404** in this check | Do not use a public Play call to action yet |
| App Store update | Version **1.0.1 (2)**, with covers, visible Light/Dark/System controls and catalogue refresh, is **Waiting for Review** | Do not describe these as features of the approved iOS binary yet |
| Play update | Version **1.0.1 (2)** is available only to internal testers | Do not advertise it as a public Android release |

The app is paid up front on iOS, with no subscription or in-app purchase. The web reader is a separate free destination. The public [bunko-books](https://github.com/lachlanchen/bunko-books) repository carries the downloadable book bundles, not an additional app store. Adding approved book bundles can update the catalogue without a new binary.

## Product and audience

Bunko is a pocket reader for public-domain Chinese, Japanese and English classics. Readers can choose displayed languages and layouts, see pinyin or furigana above characters, and save chapters for offline reading. The interface has English, Simplified Chinese, Traditional Chinese and Japanese. The catalogue has **150 cleared editions**, not necessarily 150 distinct original works. Study renderings are AI-generated and may contain errors; they are not scholarly editions. Public-domain status varies by territory. The app includes mature literary themes and must not be marketed as a children's app.

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
