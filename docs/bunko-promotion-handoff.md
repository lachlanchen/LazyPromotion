# Bunko promotion handoff

Store facts checked 2026-09-25 at 22:10 UTC (September 26 Hong Kong). This is a public-facts handoff for [Bunko](https://github.com/lachlanchen/Bunko), separate from the L & N campaign. It contains no tester links, private contacts, store credentials or browser state. Recheck store pages before any public post.

## What is public now

| Channel | Verified state | Visitor destination |
| --- | --- | --- |
| Web reader | Live, with a 183-edition downloadable catalogue | https://lachlan.lazying.art/Bunko/ |
| US App Store | Public storefront now shows **1.0.1**, at **USD 0.99** | https://apps.apple.com/us/app/bunko-classics-with-ruby/id6815137919 |
| Google Play | The public US listing returned **404** at 22:09 UTC; the shipping record still reports production **1.0.0 (1)** in review | Do not use a public Play call to action yet |
| Shipped Apple update | The 1.0.1 storefront release notes describe illustrated covers, Light/Dark/System controls, catalogue refresh and offline-download recovery improvements | These may be described for this iOS release; they do not establish 1.0.2 availability |
| Play updates | The shipping record lists **1.0.1 (2)** and latest **1.0.2 (3)** on the internal track | Internal testing is not a public Android release |

The app is paid up front on iOS, with no subscription or in-app purchase. The web reader is a separate free destination. The public [bunko-books](https://github.com/lachlanchen/bunko-books) repository carries the downloadable book bundles, not an additional app store. Adding approved book bundles can update the catalogue without a new binary.

The public storefront's version history and a multi-app Apple lookup agree on
1.0.1, with release time **September 25 at 18:03:18 UTC** in the lookup. A
single-app lookup still returned 1.0.0 during the same check. The cause of that
disagreement is unverified; do not let the older response or the original
submission artifact overwrite the observed storefront release. This verification
covers the US listing, not installation, every territory or private review state.
The [campaign's subsequent release check](../campaigns/bunko-classics-introduction.json)
keeps this evidence separate from its original 1.0.0 publication snapshot.

## Product and audience

Bunko is a pocket reader for public-domain Chinese, Japanese and English classics, alongside owner-edited study books. Readers can choose displayed languages and layouts, see pinyin or furigana above characters where available, and save chapters for offline reading. The interface has English, Simplified Chinese, Traditional Chinese and Japanese. The catalogue has **183 cleared editions**: 150 classics and 33 owner editions, not necessarily 183 distinct original works. Study renderings are AI-generated and may contain errors; they are not scholarly editions. Public-domain status varies by territory. The app includes mature literary themes and must not be marketed as a children's app.

Useful audiences include readers of Classical Chinese history and philosophy, Japanese literature learners, bilingual readers, and teachers who want readable parallel passages. Lead with a specific reading problem: following a classical passage while keeping the original and its readings visible, or carrying a chapter offline. Avoid claiming that every classic has been acquired or that the companion tutor is already in the shipping app.

## Safe launch angle

An Apple-specific post can link the US App Store page now, with the current **USD 0.99** price and verified 1.0.1 features. A web-reading post may link the live web reader and show the expanded catalogue. Keep later 1.0.2, native Mac and unverified Android claims separate. Suggested draft for review:

> I built Bunko to make Chinese and Japanese classics easier to read without losing the original text. It puts pinyin or furigana above the characters, lets you compare languages, and saves chapters for offline reading. The web reader has a growing public-domain catalogue; Bunko is also available on the US App Store for $0.99. Which classic would you want to read this way?

Use one clear destination per post. Disclose that the maintainer built the app. Do not send or schedule this draft without the normal LazyPromotion destination and exact-content review. Do not reuse L & N's posts, images, target communities or existing campaign queue.

## Assets and evidence

- Creator recording: [Bunko App: Read World Classics with Ruby Annotations](https://www.youtube.com/shorts/pSWnOwzyc-4), on [@lazyingart](https://www.youtube.com/@lazyingart). The native player and multilingual captions including English were checked September 25. The recording shows a TestFlight-installed version; verify demonstrated features against the public release before using it as store-specific proof. More material is indexed in the [product video library](product-video-library.md).
- Reader source, screenshots and product contract: [Bunko repository](https://github.com/lachlanchen/Bunko), especially `store/assets/`, `BRIEF.md` and `store/release.yaml`.
- Book rights audit and publishing workflow: [catalogue](https://github.com/lachlanchen/Bunko/blob/main/docs/catalogue.md) and [library guide](https://github.com/lachlanchen/Bunko/blob/main/docs/library-publishing.md).
- Live catalogue index: [bunko-books/reader-index.json](https://github.com/lachlanchen/bunko-books/blob/main/reader-index.json).
- Historical Apple 1.0.1 submission record: [curated artifact](https://github.com/lachlanchen/Bunko/blob/main/store/artifacts/apple-submission-1.0.1.json). Its original waiting-for-review state predates the public release verified above.

Before an Apple post, reopen the public listing to confirm price, version, artwork and regional availability. Before any Google Play post, require a live public listing and a published production release. Store submission, tester access, public listing visibility, installs and sales are separate states; none implies revenue.

## Owned reading guide — September 25

[Reading Chinese and Japanese Classics Without Constantly Switching Tabs](https://blog.lazying.art/html/books/3853/bunko-chinese-japanese-classics-pinyin-furigana.html) is published on the blog. It uses the shipping reader's *Sanshirō* screenshot, explains a short original/parallel-text reading routine, and links to the US App Store at the verified USD 0.99 price. It identifies the AI-generated study renderings without presenting them as scholarly translations. No Google release, then-pending 1.0.1 feature, distinct-book count, learning result or revenue was claimed in that publication.

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

### LanguageHub directory — September 26 (Hong Kong)

One [Bunko entry](https://www.reddit.com/r/languagehub/comments/1sic66r/comment/pc0legb/)
was submitted to LanguageHub's pinned tools thread, where the moderator explicitly
invites developer introductions. It explains the Sanshirō reading layout and
links to the free reader and paid iPhone/iPad edition. Apple's public lookup still
reported 1.0.0 at US$0.99 immediately before submission. Exact text, author and both
links survived reload; anonymous visibility remains unresolved after a cache miss
and browser timeout. Do not repost. The [campaign receipt](../campaigns/bunko-languagehub-introduction.json)
does not establish an install or purchase and has no automatic follow-up.

## Instagram reading example — queued September 26

One Bunko post is scheduled through Postiz for **September 26, 2026 at 12:00 UTC
(8:00 PM Hong Kong)** on [@lazying.art](https://www.instagram.com/lazying.art/).
It shows an actual 4:5 capture of the browser reader at the start of *Sanshirō*,
with furigana and English together. The caption suggests reading the Japanese,
checking the difficult part, then rereading; it gives the exact App Store name
and verified US$0.99 one-time price. It does not claim that Instagram caption
links are clickable or direct people to an unverified profile link.

The saved caption, loaded image, destination account, local time and provider
settings were reviewed before one scheduling action. A fresh Postiz read
confirmed one matching `QUEUE` item and no release. This is **scheduled, not
published**, and no installation or purchase is inferred. LinkedIn's separate
account hold was left unchanged. The [campaign record](../campaigns/bunko-instagram-reading-demo.json)
and [reviewed image](../assets/bunko-sanshiro-reader-20260926.png) preserve the
exact material; the existing read-only owned monitor recognizes the caption.

## Reader community introduction — queued September 28

A separate text introduction is queued for **September 28 at 12:00 UTC / 8:00 PM
Hong Kong** in [r/Recommend_A_Book](https://www.reddit.com/r/Recommend_A_Book/).
The currently pinned moderator policies explicitly welcome creator promotion
and AI-assisted work. The post leads with a *Sanshirō* reading routine, links to
the free reader and paid Apple edition, and keeps the study-translation
limitation beside that claim. The saved copy, title, account, community and date
were visibly reviewed before one scheduling action. A fresh provider read
confirmed one unchanged `QUEUE` item, not publication. See the
[exact campaign](../campaigns/bunko-book-reading-introduction.json).

The earlier private general developer-community draft remains a reserve, not
another scheduled launch. No automatic repost or follow-up reply is planned.
This placement is a reader-discovery test, not evidence of an install or sale.

## Library expansion — September 25

Bunko's downloadable catalogue now has **162 cleared editions**: the previous 150 classics plus 12 owner editions in separate Physics, Learning, Finance and Travel shelves. The additions include three trilingual travel guides, *How You Got Rich* in English, Japanese and Chinese, six independent Leonard Susskind lecture companion volumes in English, *How to Speak and Write* and *Wealth From First Principles*. The source and rights records are in [bunko-books](https://github.com/lachlanchen/bunko-books). Bunko 1.0.2 adds local equation rendering and mobile figure support; describe these app features publicly only after that binary reaches the relevant public store. The web reader can show them after its deployment passes. Do not call the companion notes Susskind-authored or endorsed, and do not imply every source work has all three languages. The existing Reddit, X, blog and Medium introductions describe the older public version and should remain as historical posts.

Later the same day, the downloadable catalogue grew to **183 editions** at `bunko-books` commit `09644d2`: all nine supplementary Susskind companion courses, four additional core course runs, *Justice with Michael Sandel*, and seven more edited LazyEarn books. Physics now has 19 English companion editions, Learning has two English editions, Finance has nine editions (one trilingual), and Travel has three trilingual guides. The downloadable catalogue update requires no new binary; the existing 1.0.2 internal builds fetch it online. Do not imply the Jim Rohn transcript book or raw Hard Knocks interview corpus is in Bunko, or imply the supplementary notes are Susskind-authored.

## Native Mac submission — September 25, 14:11 UTC

Bunko **macOS 1.0.2 (4)** is **Waiting for Review** on the existing Apple app record, with automatic release after approval. The native Mac build is also available in the internal TestFlight group. This is not yet a public Mac launch. It includes a resizable reading window, native menus and keyboard controls, offline books, local dictionaries, and equations/figures. The universal binary supports Intel and Apple silicon with a macOS 12.0 deployment target. Native tests passed on the 3040 (12.7.6), 7050 iMac (15.7.7) and KVM Mac (15.7.9), all Intel; no physical Apple silicon test was performed.

The existing [App Store URL](https://apps.apple.com/app/id6815137919) will serve the Mac edition after approval; recheck its Mac compatibility and public availability before announcing it. Use the [Mac submission record](https://github.com/lachlanchen/Bunko/blob/main/store/macos/submission.md) and actual Mac screenshots in `store/assets/macos-*.png` when preparing future material. No new promotional post is authorized by this handoff. At that submission checkpoint, iOS 1.0.1 was still in review; the later public iOS release is recorded above and does not establish Mac approval. The Google Play production review was not changed by this promotion work.

## Reader controls update — September 26

Bunko **1.0.3 (5)** is available in Google Play internal testing and in iOS/Mac TestFlight. iOS 1.0.1 is now Ready for Sale according to App Store Connect; iOS 1.0.3 was submitted at 01:58:51 UTC and is Waiting for Review. Mac 1.0.2 is In Review; Mac 1.0.3 remains an internal update. Google production 1.0.0 remains in review. Recheck public listings before store-specific promotion.

The new reader uses long-press selection and explicit Dictionary actions, adjustable native selection handles, a Sentence action, rightward edge-swipe back navigation on phones, separate main-text/ruby size controls, and a compact library header. Android native and WebKit selection tests passed; no physical iPhone test was performed. See the [reading controls guide](https://github.com/lachlanchen/Bunko/blob/main/docs/reading-controls.md) and [release evidence](https://github.com/lachlanchen/Bunko/blob/main/store/artifacts/release-1.0.3.json). Use these as web/internal-build facts until the relevant public release is approved. No promotional post was sent as part of this update.

## Optional update prompts — September 26

Bunko **1.0.4 (6)** is live on the web and available in Android internal testing and iOS/Mac Bunko Internal TestFlight. It checks for app updates, offers a dismissible 24-hour reminder and includes a manual Settings check in English, Simplified Chinese, Traditional Chinese and Japanese. Web readers choose when to reload; native readers are directed to their store only for a newer verified public release. Saved books, notes and settings remain on-device. Android also migrates an old app-shell cache that could mask a newly installed reader update.

Public availability remains separate: iOS 1.0.1 is live, iOS 1.0.3 is Waiting for Review, Mac 1.0.2 is In Review, and Play production 1.0.0 is still in review. Describe update detection as a web/internal-build feature until its native release is public. Existing installations require the new binary to enable future detection. The current public feed intentionally contains only iOS 1.0.1 (2). See the [update guide](https://github.com/lachlanchen/Bunko/blob/main/docs/app-updates.md) and [release evidence](https://github.com/lachlanchen/Bunko/blob/main/store/artifacts/release-1.0.4.json). No promotional post was sent as part of this change.

## Latest build submitted — September 26

The owner requested formal review of **1.0.4 (6)**. Both iOS and Mac are now **Waiting for Review**, submitted at 02:47 and 02:49 UTC respectively, with automatic release after approval. Google Play production build 6 is under **Changes in review**, with automatic pre-review checks running, 100% rollout and all 172 configured eligible countries retained. Earlier submissions were replaced, restarting review timing. Internal testing remains available.

This supersedes the earlier note that build 6 was internal only. It does **not** establish public availability: iOS 1.0.1 remains the verified public release, and Android/Mac store publication is pending. Check the [submission record](https://github.com/lachlanchen/Bunko/blob/main/store/artifacts/submission-1.0.4.json) and live storefronts before announcing a launch. No promotional message was sent.
