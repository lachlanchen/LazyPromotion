# L & N promotion handoff

Updated: 2026-09-06

This note is the secret-free bridge between LazyPromotion and the L & N release workflow. It contains no account credentials, tester identities, private email addresses, signing material, or browser cookies.

## Canonical sources

- Product: `L & N: Speech Practice`
- Website and primary campaign destination: https://l-and-n.lazying.art/
- Source: https://github.com/lachlanchen/L-and-N
- L & N release evidence commit: `d389aacf93d5109858ac6d4abd62e7336bb11c49`
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
- Google Play production `1.0 (3)` is Changes in review after the corrected binary replaced build 1 and restarted review. It is not yet confirmed public.
- Android build `1.0 (3)` is available to internal testers and includes the microphone permission, waveform/Stop, and no-empty-score repairs verified on an API-36.1 release emulator.

Do not promise clinical accuracy, diagnosis, speech-therapy outcomes, guaranteed recognition, store approval, or public storefront availability. The score is coaching feedback based on the prompted word and detected speech, not a medical measurement.

## Tester links

- TestFlight public beta: https://testflight.apple.com/join/CpkT8m9C
- Google Play internal test: https://play.google.com/apps/internaltest/4701251861700553150
- First-party signed APK: https://l-and-n.lazying.art/downloads/L-and-N-1.0-build3-test.apk
- APK SHA-256: `89867c73d2ae3f3023a1e402e7c7fd21dd4337a409262aff3832f3c30efd1fb7`

Build 3 is the current repaired Android tester binary. Call the Play link and direct APK test builds—not public Google Play availability—and keep the score framed as coaching feedback rather than an accuracy guarantee.

## Promotion angle

Lead with the concrete learner problem: “I mix up L and N, so I built the practice loop I wanted.” Show the loop in this order: hear the prompted contrast, inspect the mouth/airflow cue, record one word, see the waveform and recognized text, then inspect the coaching result. Invite specific feedback about whether the mouth view and visible evidence make the contrast easier to understand.

The existing LinkedIn item is scheduled for `2026-09-20T02:00:00Z` and remains a scheduled draft until provider delivery is independently verified. Do not record a post, view, tester, lead, or store review as a conversion or publication outcome without separate evidence.

## Release-following actions

1. Before the scheduled promotion, recheck the PWA, tester links, and both store states.
2. If Apple approves the formal version, remember that release is manual; verify the public storefront only after the explicit release action succeeds.
3. If Google approves production, verify the public listing before changing campaign language.
4. Collect physical-device feedback for Android build 3, especially permission, visible waveform, Stop completion, recognition, and abstention when speech is unclear.
5. Keep the campaign destination on `l-and-n.lazying.art`; use the tester URLs only for explicit testing invitations.

## Browser handoff

L & N store work reuses the dedicated local stack at Xvfb `:164`, x11vnc `5964`, noVNC/websockify `6164`, and Chrome CDP `9484`. Open:

`http://127.0.0.1:6164/vnc.html?host=127.0.0.1&port=6164&autoconnect=1&resize=scale&view_only=0&shared=0&reconnect=0`

Do not start another L & N stack while it is running. App Store Connect and Google Play use the existing logged-in Chrome profile; never copy its profile, cookies, or credentials into Git. EchoMind-specific browser details and the distinction between its older display and this L & N stack are documented in the L & N repository handoff.
