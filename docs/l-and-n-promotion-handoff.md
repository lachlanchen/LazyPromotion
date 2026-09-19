# L & N promotion handoff

Updated: 2026-09-19

This note is the secret-free bridge between LazyPromotion and the L & N release workflow. It contains no account credentials, tester identities, private email addresses, signing material, or browser cookies.

## Canonical sources

- Product: `L & N: Speech Practice`
- Website and primary campaign destination: https://l-and-n.lazying.art/
- Tutor offer: https://l-and-n.lazying.art/for-tutors/
- Private fit check: https://lazying.art/pronunciation-mini-lesson/fit-check/
- Free light/night lesson: https://l-and-n.lazying.art/lessons/light-vs-night/
- Owned discovery shelf: https://lazying.art/work/
- Source: https://github.com/lachlanchen/L-and-N
- L & N release evidence commit: `201081025c1523f8fbe27f0356098ab548241d5e`
- Deployed lesson source commit: `7b969e618bb870ab2f09fd4390215f092934ce32`
- Detailed durable operator handoff: `store/operator-handoff.md` in the L & N repository
- Campaign record: `campaigns/l-and-n-pronunciation-launch.json`

Use `/home/lachlan/ProjectsLFS/L-And-N`; the user repaired the filesystem and the checkout, build, and tests are healthy again.

## What is safe to say now

- The PWA is live, free, open source, and usable without an account.
- The free **Light or night?** lesson is live with project-owned listening prompts, mouth-placement images, captions, and a short demonstration video.
- Learners can practice English, Mandarin, and Cantonese separately from the interface language.
- The app provides L/N listening practice, mouth and airflow guidance, a 3D mouth view, recording, a visible waveform, recognized text, and explainable coaching feedback.
- The repaired PWA uses one microphone stream on iPhone browsers, leaves the last waveform visible after Stop, and does not show or save a score when it could not recognize speech.
- Both production storefronts are public: [Google Play](https://play.google.com/store/apps/details?id=art.lazying.landn) and [App Store](https://apps.apple.com/app/l-n-speech-practice/id6808872450). Their public pages were independently checked on September 19.
- The US App Store lists version `1.0.1` at USD 0.99. The US Google Play listing shows Install with a zero-price offer. Do not describe both native versions as free; prices and availability can vary by storefront.
- The September 19 release handoff reports Google Play production `1.0.1 (4)`, internal Android `1.0.2 (7)`, internal TestFlight build 6, and public TestFlight build 3.
- The 3/5/7 listening-exam lengths, longer pause between repeated words, and player reload repair are reported live on the web and internal tracks. Do not advertise them as current production-store features until a new public release is verified.

Do not promise clinical accuracy, diagnosis, speech-therapy outcomes, or guaranteed recognition. The score is coaching feedback based on the prompted word and detected speech, not a medical measurement.

## Tester links and historical artifact

- TestFlight public beta: https://testflight.apple.com/join/CpkT8m9C
- Google Play internal test: https://play.google.com/apps/internaltest/4701251861700553150
- Previous verified signed APK: https://l-and-n.lazying.art/downloads/L-and-N-1.0-build3-test.apk
- Previous APK SHA-256: `89867c73d2ae3f3023a1e402e7c7fd21dd4337a409262aff3832f3c30efd1fb7`
- Newer operator-reported Android tester artifact: https://l-and-n.lazying.art/downloads/L-and-N-1.0.2-build7-test.apk. Recheck its signed identity and checksum before sending a new tester invitation.

Use the production Google Play and App Store listings for ordinary mobile visitors. TestFlight, internal-test URLs, and direct APKs are tester routes, not substitutes for the paid iOS storefront.

## Promotion angle

Lead with the concrete learner problem: “I mix up L and N, so I built the practice loop I wanted.” Show the loop in this order: hear the prompted contrast, inspect the mouth/airflow cue, record one word, see the waveform and recognized text, then inspect the coaching result. Invite specific feedback about whether the mouth view and visible evidence make the contrast easier to understand.

The existing LinkedIn item is scheduled for `2026-09-20T02:00:00Z` and remains a scheduled draft until provider delivery is independently verified. Do not record a post, view, tester, lead, or store review as a conversion or publication outcome without separate evidence.

The September 19 Postiz read confirms that exactly one matching LinkedIn item is still QUEUE, with its reviewed free-browser wording and no release URL. No duplicate was created, no schedule changed, and no internal-build features were added to its claims. Earlier X, Instagram, and YouTube items are reported PUBLISHED by Postiz; this check does not establish new engagement or revenue.

The selected-work shelf now links the free no-signup PWA and public source from a pronunciation-shaped card. The standalone lesson is an additional education-first discovery path. Either link is discovery evidence only; a visit is not a lead or sale.

The fixed USD 250 tutor service now leads to a review-first encrypted fit check
instead of relying on email alone. The live test made no endpoint request before
review, required a separate confirmation, accepted exactly one synthetic
request, and left no pending remote envelope after private receipt. The
synthetic payload was removed. This verifies the intake path, not a buyer,
payment, or revenue.

## Release-following actions

1. Before the scheduled promotion, recheck the PWA, tester links, and both store states.
2. Apple production availability is now independently verified. Keep any later internal update separate from the version visible on the public storefront.
3. Recheck the public Google Play listing before store-specific promotion; availability is not evidence of downloads or retention.
4. Route tester feedback to the current release workflow; do not keep recruiting users onto the historical build 3 APK.
5. Keep the campaign destination on `l-and-n.lazying.art`; use the tester URLs only for explicit testing invitations.

## Browser handoff

Consult the ignored L & N runtime handoff for current stack ownership; this public note is not a runtime inventory. Start or reuse only one dedicated project-owned stack when store review is needed and stop it after evidence capture. Never touch the user's personal Firefox or copy browser profiles, cookies, or credentials into Git.
