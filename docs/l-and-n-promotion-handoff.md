# L & N promotion handoff

Updated: 2026-09-06

This note is the secret-free bridge between LazyPromotion and the L & N release workflow. It contains no account credentials, tester identities, private email addresses, signing material, or browser cookies.

## Canonical sources

- Product: `L & N: Speech Practice`
- Website and primary campaign destination: https://l-and-n.lazying.art/
- Source: https://github.com/lachlanchen/L-and-N
- L & N release evidence commit: `d538acb1637618eda9633acd3ec13186fecd73e2`
- Deployed audio-repair source commit: `d837c146eb0ff66b4ea4000a004f582f4c31ef5f`
- Detailed durable operator handoff: `store/operator-handoff.md` in the L & N repository
- Campaign record: `campaigns/l-and-n-pronunciation-launch.json`

The original LazyPromotion checkout under `/home/lachlan/Projects/LazyPromotion` is on a filesystem returning kernel I/O errors. Use the healthy checkout `/home/lachlan/LazyPromotion-landn-handoff` until that storage is repaired.

## What is safe to say now

- The PWA is live, free, open source, and usable without an account.
- Learners can practice English, Mandarin, and Cantonese separately from the interface language.
- The app provides L/N listening practice, mouth and airflow guidance, a 3D mouth view, recording, a visible waveform, recognized text, and explainable coaching feedback.
- The repaired PWA uses one microphone stream on iPhone browsers, leaves the last waveform visible after Stop, and does not show or save a score when it could not recognize speech.
- iOS and embedded watchOS build `1.0 (2)` are Testing in TestFlight.
- The same Apple build is Waiting for formal App Review. It is not yet public on the App Store.
- Google Play production `1.0.0 (1)` is Changes in review. It is not yet confirmed public.

Do not promise clinical accuracy, diagnosis, speech-therapy outcomes, guaranteed recognition, store approval, or public storefront availability. The score is coaching feedback based on the prompted word and detected speech, not a medical measurement.

## Tester links

- TestFlight public beta: https://testflight.apple.com/join/CpkT8m9C
- Google Play internal test: https://play.google.com/apps/internaltest/4701251861700553150
- First-party signed APK: https://l-and-n.lazying.art/downloads/L-and-N-1.0-build2-test.apk
- APK SHA-256: `9b018d62df3c2e0ca1dc3004bd8c0b30fc08459e12b83fe96a395467c4839934`

The Android tester builds predate the 2026-09-06 no-placeholder-score repair. Use them only with that disclosure until a newer Android build is produced and verified.

## Promotion angle

Lead with the concrete learner problem: “I mix up L and N, so I built the practice loop I wanted.” Show the loop in this order: hear the prompted contrast, inspect the mouth/airflow cue, record one word, see the waveform and recognized text, then inspect the coaching result. Invite specific feedback about whether the mouth view and visible evidence make the contrast easier to understand.

The existing LinkedIn item is scheduled for `2026-09-20T02:00:00Z` and remains a scheduled draft until provider delivery is independently verified. Do not record a post, view, tester, lead, or store review as a conversion or publication outcome without separate evidence.

## Release-following actions

1. Before the scheduled promotion, recheck the PWA, tester links, and both store states.
2. If Apple approves the formal version, remember that release is manual; verify the public storefront only after the explicit release action succeeds.
3. If Google approves production, verify the public listing before changing campaign language.
4. Once a repaired Android build is tested and uploaded, replace the Android caveat and record the new version, artifact hash, and track status.
5. Keep the campaign destination on `l-and-n.lazying.art`; use the tester URLs only for explicit testing invitations.

## Browser handoff

L & N store work reuses the dedicated local stack at Xvfb `:164`, x11vnc `5964`, noVNC/websockify `6164`, and Chrome CDP `9484`. Open:

`http://127.0.0.1:6164/vnc.html?host=127.0.0.1&port=6164&autoconnect=1&resize=scale&view_only=0&shared=0&reconnect=0`

Do not start another L & N stack while it is running. App Store Connect and Google Play use the existing logged-in Chrome profile; never copy its profile, cookies, or credentials into Git. EchoMind-specific browser details and the distinction between its older display and this L & N stack are documented in the L & N repository handoff.
