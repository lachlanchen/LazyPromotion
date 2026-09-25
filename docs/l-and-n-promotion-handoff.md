# L & N promotion handoff

Updated: 2026-09-20 (supersedes the 2026-09-19 note; earlier verified facts are kept where still true)

Shared release and promotion reference for [L & N](https://github.com/lachlanchen/L-and-N). This note contains no credentials, tester identities, private email addresses, signing material, or browser cookies. Shipping-reported states are distinguished from independent public checks below; repository paths are relative to L & N unless noted otherwise.

## September 26 Android introduction

One [L & N post on r/AppHunt](https://www.reddit.com/r/AppHunt/comments/1wq4pd5/android_l_n_practise_hearing_and_saying_ln_pairs/)
is recorded in [the campaign receipt](../campaigns/l-and-n-apphunt-introduction.json).
The community's native composer specifies Android links only and no same-app
repost within 30 days. The introduction uses Google Play, clear free-download
with in-app-purchases wording, Android APP flair and the Brand Affiliate tag.
Its exact text, title, author and original link were verified after signed-in
reload. Anonymous visibility is unresolved after Reddit's humanity challenge;
no workaround, second submission or suggested cross-post was attempted. No new
install or purchase is inferred. Review actual feedback, not a repeat launch.

## Promotion verification — September 20, 08:05 UTC

**September 25 follow-up:** A [creator introduction on r/SideProject](https://www.reddit.com/r/SideProject/comments/1wpvosw/l_n_i_mix_up_l_and_n_so_i_built_a_pronunciation/) is published and verified both signed in and logged out. It includes the maintainer's [English walkthrough](https://www.youtube.com/shorts/Nlsx_5U6g6U), the original Apple and Google production links, and GitHub source. The US Apple listing now shows **1.0.6 at USD 0.99**; the anonymous Google listing reports **1.0.9**, free download with in-app purchases. These public checks supersede older review-state notes for this new introduction; historical campaign copy is unchanged. Exact published copy is in [`campaigns/l-and-n-sideproject-introduction.json`](../campaigns/l-and-n-sideproject-introduction.json). See the [product video library](product-video-library.md) for reusable recordings. No beta or PWA call to action, new accuracy claim, app-sale claim or automatic follow-up was added.

- The visible **US App Store page now shows 1.0.2 at USD 0.99**, including the listening-test release notes. This supersedes the earlier waiting-for-review statement below. The public lookup API still returns 1.0.1; do not infer availability on every device or storefront.
- The web app serves `index-zHLbJcBO.js`, SHA-256 `5c0b1ef00a906b57604cf3fe36774e64c21ba6e3d67293389466f0018c65c3a0`. The store-link release in `store/artifacts/pwa-store-links-release.json` is newer than the bundle named in the shipping handoff, not a rollback.
- Six public entry points return HTTP 200: app, lesson, tutor page, fit check, Apple and Google listings. Google still shows a free offer; no production-version value was exposed in the inspected page, so its shipping-reported review state remains unchanged.
- A visible five-word web round reached five result rows. Its predefined operator answers are not learner outcomes. Only the unedited setup screenshot is selected for promotion.
- Existing launch posts are intact. One reviewed X listening update is **queued for September 22, 02:00 UTC / 10:00 HKT**, with the real setup screenshot and clear USD 0.99 iPhone wording. The LinkedIn launch already published today. Do not repeat the Reddit resource comment or post to Hacker News.

Shipping update checked at 08:34 UTC: L & N main `89e4949` records **Android internal build 10** with a one-time USD 0.99 full-curriculum purchase. Its first three pairs per language remain free. This purchase build is internal-only; production build 8 remains in review. Web and iPhone pricing are unchanged. Do not describe the internal purchase as a public launch or change the scheduled web-link post.

Shipping update checked at 10:26 UTC supersedes that Android submission state: commit `0198717` records **production build 10 submitted for review**, replacing queued build 8. Commit `94da8d3` records a separate **L & N Pro** package (`art.lazying.landn.pro`), paid up front at a configured USD 0.99, also submitted for review. The Pro public store URL returned **404**; neither a public Pro release nor a completed Android purchase is verified. Hold Pro-specific posts and purchase links. The original free-download app and its proposed in-app unlock are distinct from Pro. The live homepage still serves `index-DZiUdOSI.js` and its previously verified HTML hash; older PWA fields in `store/release.yaml` do not override the live deployment evidence. Existing web-link campaigns remain unchanged.

Web discovery update at 08:49 UTC: source `75883a4`, evidence `16c162a`, and entry `index-DZiUdOSI.js` supersede the earlier web bundle above. Canonical/social-preview metadata and a no-JavaScript lesson/store fallback are live. The owner passed 86 tests; promotion independently matched all four public file hashes. No indexing or conversion result is claimed. See `store/artifacts/pwa-homepage-discovery-release.json`; dated screenshots from the earlier bundle remain valid historical captures.

The English developer story [I Mix Up L and N, So I Built a Practice App](https://blog.lazying.art/html/computer_internet/3849/l-and-n-pronunciation-listening-practice.html) is now published. It explains the scoring and listening design, includes the real setup screenshot, and has one free-web call to action. One Medium edition on `@lazyingart` is scheduled for **September 21, 02:00 UTC / 10:00 HKT**, with the image, source links, Medium-specific app attribution and a brief AI-assistance label. The saved schedule, disabled paywall and original-blog canonical setting passed a reload check. Anonymous access and the final public canonical are due after publication; no Medium publication or income is claimed yet. Do not reimport or recreate the scheduled story.

## 1. What the product is, in one paragraph

L & N: Speech Practice is a pronunciation coach for one confusable contrast, the consonants **l** and **n**, for learners of English, Mandarin (普通话) and Cantonese (廣東話). It is built by the maintainer because they mix the two sounds up themselves. A learner sees the target letter or character inside a word, hears a studio model, records one word, and gets a score that shows its evidence (what the recognizer heard, whether the onset was nasal or lateral, recording quality, and for Chinese the tone shape). A Listen tab trains the ear: it plays a random run of one minimal pair ("light night light light night") and the learner taps what they heard in order. There is an interactive 3D mouth cutaway for airflow, a live waveform, and no account, ads or tracking. It runs as a free web app, a free-to-download Android app, a paid iPhone/iPad app and a small Apple Watch drill. Feature and purchase availability differ by release; see below.

## 2. Canonical links (all returned HTTP 200 on 2026-09-20)

| Purpose | URL |
| --- | --- |
| Free web app, no sign-up (primary campaign destination) | https://l-and-n.lazying.art/ |
| Free light/night mini-lesson (education-first entry) | https://l-and-n.lazying.art/lessons/light-vs-night/ |
| Tutor offer, USD 250 mini-lesson (separate campaign) | https://l-and-n.lazying.art/for-tutors/ |
| Private fit check for that offer | https://lazying.art/pronunciation-mini-lesson/fit-check/ |
| App Store (US) | https://apps.apple.com/us/app/l-n-speech-practice/id6808872450 |
| Google Play | https://play.google.com/store/apps/details?id=art.lazying.landn |
| TestFlight public beta (tester route only) | https://testflight.apple.com/join/CpkT8m9C |
| Google Play internal test (tester route only) | https://play.google.com/apps/internaltest/4701251861700553150 |
| Signed Android test APK, build 8 | https://l-and-n.lazying.art/downloads/L-and-N-1.0.2-build8-test.apk (SHA-256 `d9e822fb7af4f5a9d5dd7213fef1c69e68319a9e8eecba158fff489b08d2e8b4`) |
| Source | https://github.com/lachlanchen/L-and-N |
| Privacy / Support | https://l-and-n.lazying.art/privacy.html · https://l-and-n.lazying.art/support.html |
| Research notes (credibility, not marketing) | `docs/research/pronunciation-assessment.md`, `docs/research/onset-model.md`, `docs/research/listening-exam.md` in the repo |

Use the store pages and the web app for ordinary visitors. TestFlight, the internal test and the APK are for explicit testing invitations only.

## 3. Pricing (verified through App Store Connect and the Play listing)

| Channel | Price |
| --- | --- |
| Web app | Free |
| Google Play, original app | Public download is free; build 10's USD 0.99 full-curriculum unlock is available internally and submitted for production review, not verified live |
| Google Play, separate Pro app | USD 0.99 configured by shipping; submitted for review, public listing not available in this check. Do not advertise as released |
| App Store | USD 0.99 tier (CNY 8, HKD 8; Apple's tier mapping), available in all 175 territories |

Never describe the iOS app as free. Prefer "Free in the browser, US$0.99 on iPhone" for the current campaign. For a future Android-specific post, distinguish the free download from any paid content after rechecking the release.

## 4. Release state on 2026-09-20 and what may be claimed

| Channel | Public today | In review | Claimable now |
| --- | --- | --- | --- |
| Web | 1.0.2 feature set plus web store links (source `cfe8efe`, release manifest above) | n/a | Observed web features in section 5, with their evidence limits |
| Google Play production, original app | Shipping-reported `4 (1.0.1)`: practice, 3D mouth, scoring, auto-stop; **no Listen tab** | `10 (1.0.2)` with full-curriculum purchase, replacing build 8's submission | Do not claim the new features or purchase are public until independently verified |
| Google Play Pro | Public package URL returned 404 | Separate paid-up-front `10 (1.0.2)` submitted for review | No released-app claim, purchase link or Pro-specific post yet |
| App Store | US page visibly shows 1.0.2 at USD 0.99 | Earlier shipping note said waiting for review; lookup API still shows 1.0.1 | US listing's listening-test release notes verified; no global rollout claim |
| TestFlight public link | Build 7 (1.0.2), beta-approved 2026-09-20 | | Full 1.0.2 feature set, to testers only |
| Play internal test | Shipping-reported `10 (1.0.2)` | | Android purchase testing only: first three pairs per language free, one-time unlock for all 31; not a public purchase claim |

Concrete rule: a post that links the store pages must not promise the Listen tab or the 31 pairs until you have re-read the store page and it shows version 1.0.2. A post that links the web app may describe everything. When the reviews clear, the shipping session updates `store/release.yaml`, `store/apple/submission.md` and `store/google-play/submission.md` in the L & N repo; check those files (or the store pages) rather than assuming.

How to check quickly without any login:

```bash
curl -s https://l-and-n.lazying.art/ | grep -o 'index-[A-Za-z0-9_-]*\.js'   # verified current asset: DZiUdOSI
curl -s https://apps.apple.com/us/app/l-n-speech-practice/id6808872450 | grep -o 'Version [0-9.]*' | head -1
curl -s 'https://play.google.com/store/apps/details?id=art.lazying.landn&hl=en' | grep -o '"[0-9]\.[0-9]\.[0-9]"' | head -1
```

## 5. What the 1.0.2 feature set contains (live on the web now)

- **Listen tab (ear training).** Pick a pair, pick 3, 5 or 7 words, hear a random run of that pair, tap the words in order, submit, see per-position results with replay. Both words always appear; no word repeats more than three times; a repeated word gets a longer pause so "night night" is heard as two. Listening accuracy shows on the Progress tab and counts toward the streak.
- **31 minimal pairs** with coaching cues and glosses in all four interface languages (English, 简体, 繁體, 粵語): 16 English (light/night, low/no, lead/need, lever/never, lock/knock, lame/name, lace/nice, lumber/number, loon/noon, lip/nip, line/nine, let/net, lap/nap, lot/not, life/knife, lit/knit), 8 Mandarin (蓝/南, 老/脑, 里/你, 流/牛, 旅/女, 连/年, 路/怒, 龙/农), 7 Cantonese (你/理, 男/藍, 女/旅, 年/連, 腦/老, 難/蘭, 農/龍).
- **Checked synthetic audio.** The shipping report records one neural voice per language, checked using a recognizer and the app's onset model. 60 of 62 clips passed those checks; 蘭 and 農 remain in practice but are excluded from the exam. These are internal checks, not a guarantee that every clip is error-free. The practice-tab example is the word said twice, nothing else.
- **Auto-stop recording**: the recorder stops itself when the word is over.
- **Recognizer-anchored scoring** with an on-device 1-D CNN onset model (about nine thousand parameters, plain TypeScript, 89 % on held-out speech) that shades the score and explains the cue; if the recognizer heard the paired word, the score is capped and says so.
- Fully localized interface, including the text above the waveform that was English under the Chinese UI before.

For comparison, 1.0.1 has practice, the 3D mouth, the waveform, explainable scoring, local progress and the watch drill, but no Listen tab, 13 pairs, and the older carrier-sentence audio. Do not use this older feature description for the verified US Apple 1.0.2 page.

## 6. Who it is for (audience notes for targeting)

- Mandarin speakers from regions where n/l merge in the local variety (much of Hunan, Hubei, Sichuan, Chongqing, Jiangxi, Fujian, parts of Anhui and Guangxi) who are corrected on 男/蓝, 你/里 in standard Mandarin, and who then carry the same confusion into English (night/light, nine/line).
- Hong Kong and Guangdong Cantonese speakers: the n→l merger is widespread in younger Hong Kong speech; the app deliberately keeps the contrast for clarity training and says so in its cues. Cantonese is a first-class practice language, which is rare.
- English learners of Chinese background in general, plus teachers and tutors who want a quick ear-training tool for one contrast.
- The maintainer's own story is the honest hook: "I mix up L and N, so I built the practice loop I wanted."

## 7. Angles that fit the LazyPromotion contract

Lead with the learner's concrete problem, show the loop, disclose "I built this", invite one specific piece of feedback. Suggested angles, one per post:

1. **The ear before the mouth.** Try hearing the contrast before practising it aloud: five words, tap what you heard, see which positions differed. (Web link.)
2. **A score that shows its work.** The result says what the recognizer heard and whether the onset looked nasal, instead of a bare percentage. Good for Hacker News / r/languagelearning readers who distrust black-box scores. (Web link plus the onset-model research note.)
3. **Cantonese gets the same treatment.** 你/理, 男/藍 with Jyutping and cues written in Cantonese, not translated Mandarin. (r/Cantonese, HK-oriented communities.)
4. **Mandarin n/l for southern speakers.** 蓝 vs 南, 女 vs 旅, with tone kept separate from the consonant. (r/ChineseLanguage, learners' forums.)
5. **Verified audio pipeline** as a builder story: how synthesized minimal pairs were checked with Whisper and a small onset network, and why two words were excluded. (Show HN or a blog article; the research note has the numbers.)

Do not stack angles or links in one post. Do not promise clinical accuracy, diagnosis, therapy outcomes, or guaranteed recognition. Say "coaching feedback", never "assessment".

## 8. Ready-made copy (adjust to the community, keep the disclosure)

English, web link:

> I keep mixing up L and N (night/light, nine/line), so I built a small practice loop for it: hear the pair, record one word, and see what the recognizer actually heard instead of a bare score. The new part is a listening test: it plays "light night light light night" and you tap what you heard in order. Free in the browser, no account. I maintain it; feedback on whether the listening test feels fair is what I am after. https://l-and-n.lazying.art/

简体中文：

> 我自己分不清 l 和 n（蓝/南、你/里，英语里的 light/night 也一样），所以做了一个小练习：听一对词、录一个词、看识别器到底听到了什么，而不是只给一个分数。新增了听辨测试：随机播放「light night light light night」，你按顺序点选听到的词。网页版免费、不用注册。我是作者，想听听听辨测试是否公平。https://l-and-n.lazying.art/

粵語：

> 我自己都成日撈亂 n 同 l（你/理、男/藍），所以整咗個小練習：聽一對字、錄一個字、睇下辨識器真係聽到乜，唔係淨係俾個分。新加咗聽辨測試：隨機播「男 藍 男 男 藍」，你按次序㩒返聽到嘅字。網頁版免費，唔使登記。我係作者，想知聽辨測試公唔公平。https://l-and-n.lazying.art/

Store-page variant (only after checking the relevant release and price): use one store link and that store's current price. Do not copy an unconditional "free on Android" claim into a release that gates paid content.

## 9. Assets you may use

All are project-owned; none show real learners.

| Asset | Path in the L & N repo |
| --- | --- |
| PWA practice screen | `docs/images/pwa-practice.png` |
| 3D mouth model (L and N views) | `docs/images/pwa-mouth-model.png`, `docs/images/pwa-mouth-model-n.png` |
| Android score explanation | `docs/images/android-score-current.png`, `docs/images/android-device-score-current.png` |
| iOS practice, watchOS drill | `docs/images/ios-current.png`, `docs/images/watchos-current.png` |
| Store screenshots (1080×1920 phone set, feature graphic, icon) | `store/assets/google-play-phone-0{1..4}.png`, `store/assets/google-play-feature.png`, `store/assets/google-play-icon.png` |
| App Store captures (iPhone 6.5", iPad 13", Watch) | `store/assets/app-store-iphone-65.png`, `app-store-ipad-13.png`, `app-store-watch-series-11.png` |
| Banner | `docs/images/banner.svg` |

The unedited Listen setup screenshot is now `assets/landn-listen-web-20260920.png` in LazyPromotion. A short screen recording remains optional for a later distinct post; it has not been captured or queued. Use the live web app in the LazyPromotion browser profile and keep synthetic operator answers distinct from learner outcomes.

## 10. Store listing copy (for consistency, not for pasting into posts)

- App name `L & N: Speech Practice`; subtitle "Clearer sounds, one word"; category Education.
- Keywords on the App Store: pronunciation, speech, English, Mandarin, Cantonese, L, N, minimal pairs, language, phonetics.
- The listing descriptions live in `store/apple/metadata.md` and `store/google-play/metadata.md`. They predate the Listen tab; the shipping session will refresh them after the 1.0.2 approvals. Do not quote the "What's new in 1.0" text.

## 11. Boundaries and things not to do

- Keep `l-and-n.lazying.art` as the campaign destination. Tester links only for explicit testing invitations, and never recruit onto old APKs (builds 3 to 7 are historical).
- No claims about downloads, retention, reviews or revenue; a click or a store visit is discovery evidence only.
- The score is coaching feedback from the prompted word and detected speech. Not a medical measurement, not a certified accent judgment. The 3D mouth is a teaching model, not a scan.
- Privacy statements that are safe: no account, no ads, no trackers; progress stays on the device; the native apps use the operating-system recognizer; the web app may send one short clip to the project's own rate-limited transcription gateway when browser recognition fails, and it stores nothing. Do not say "everything is offline".
- The voices are synthetic native neural voices, verified. Do not call them "recorded by native speakers".
- One post per community per angle; follow `docs/voice.md`. Disclose "I maintain / I built".

## 12. Browser and workstation boundaries

Use only LazyPromotion's dedicated noVNC Chrome profile. The L & N store-console browser belongs to the shipping workflow; do not open or stop it. Consult the ignored runtime handoffs for live ownership and ports, never another project's personal or financial tabs.

## 13. Suggested first actions

1. Public entry checks and campaign release-state updates are complete; do not repeat them without a release change, broken route or buyer question.
2. The setup capture and one X preview have been reviewed. The scheduled item is in `campaigns/l-and-n-listening-round.json`; do not recreate it. A short recording can support a later distinct explanation if engagement warrants it.
3. Let the original publication monitor verify the September 22 item. Inspect actual questions before deciding on another post; the five angles above are options, not a posting quota.
4. Read the original scheduled Apple sales-report check before claiming paid downloads or income. A public listing, post or star is not a payment. Native release control remains with the shipping workflow.
5. Keep the tutor offer (`pronunciation-mini-lesson-pilot.json`) separate and use it only for an explicit tutor or school need. No additional operator delivery obligation is accepted by posting the free app.

## 14. Where the detailed records are

- `store/release.yaml`: one-page state of every channel.
- `store/operator-handoff.md`, `store/apple/submission.md`, `store/google-play/submission.md`: dated history of every submission with hashes.
- `store/artifacts/native-release-1.0.2.json`: build hashes, delivery IDs, TestFlight and review states for 1.0.2.
- `docs/research/listening-exam.md`: how the exam and the audio verification work, including the two excluded words.
- `docs/roadmap.md`: what the maintainer wants next (on-device Whisper, sibling apps for R/L and H/F).
