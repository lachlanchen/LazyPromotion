---
id: 3849
title: "I Mix Up L and N, So I Built a Practice App"
slug: "l-and-n-pronunciation-listening-practice"
status: "publish"
source_language: "en"
categories:
  - "Computer & Internet"
excerpt: "Building a small English, Mandarin and Cantonese practice loop: explainable pronunciation feedback, short listening rounds, and the audio details that make them work."
---

I mix up L and N. That is why I built L & N: Speech Practice, a small app for practising the contrast in English, Mandarin and Cantonese. I use it myself, and both the pronunciation feedback and the listening exercises have been useful in my own practice.

The loop is short: hear a word, say it, see what the recognizer heard, and try again. There is also a separate listening test. Keeping those two activities separate turned out to be an important design choice.

## A score should tell me what happened

If I am practising *light* and the recognizer hears *night*, a cheerful percentage is not enough. I need to see the word it heard and which contrast to work on.

The app combines word recognition with a small model that examines the beginning of the recording. The recognizer establishes which member of the pair it heard when it can; the onset model contributes acoustic evidence about L versus N. When the recognizer clearly hears the other word, the score is capped and the feedback says so. An empty transcript produces no saved score.

This division matters because an early hand-written acoustic rule disagreed with the recognizer even on the app's own example audio. Replacing it with a trained onset model helped, but hiding the disagreement behind a single number would have left the interface confusing.

The [onset-model development note](https://github.com/lachlanchen/L-and-N/blob/cfe8efe169acd18da13f0c6908eedbaab4496d76/docs/research/onset-model.md) explains the change and its tests. Most of the training speech is English and comes from one speaker, so those test results are not an accuracy claim for everyone speaking into a phone. What I want from the practice screen is useful feedback I can inspect, not a certificate for my pronunciation.

## Hearing the difference is a separate exercise

The Listen tab plays a short sequence from one pair:

> light · night · light · light · night

You tap what you heard in order, then submit. Each result row shows the played word and your answer, with a replay button. Nothing is revealed partway through the round.

![The L & N web app's Listen screen, with English light/night selected and a five-word round ready to play.](https://blog.lazying.art/wp-content/uploads/2026/09/landn-listen-web-20260920.png)

*The web app, ready for a five-word round.*

Rounds have three, five or seven words. Both words appear, repeats are allowed, and a word never repeats more than three times in a row. I kept the sequences short so remembering a long list would not become the main task; this is still a listening-and-memory exercise, not a pure measurement of hearing.

Unlike the pronunciation score, the listening result needs no speech model: it compares each tap with the word that was played. That makes a mistake easy to revisit. Play the missed position again, then hear its partner.

## Small audio decisions matter

The two words in a pair use the same synthetic voice. Otherwise, a listener might learn to distinguish the voices rather than the consonants. There is one voice for each language, with checks on the generated clips before they enter the listening exercise.

Those checks do not settle every case. Two Cantonese clips remained ambiguous under the verification pipeline, so their pairs stay out of the listening test. They are still available in pronunciation practice. An uncertain example should not quietly become the answer key.

Each isolated word is also a separate audio file. An earlier playback approach relied on seeking within a longer recording, which did not work consistently across the web and native asset handlers. Small files made playback easier to reason about.

The normal web path schedules the clips on the Web Audio clock. A fallback uses an audio element. There is an extra pause before a repeated word, so *night, night* is less likely to sound like one long word. The [listening-exam implementation note](https://github.com/lachlanchen/L-and-N/blob/cfe8efe169acd18da13f0c6908eedbaab4496d76/docs/research/listening-exam.md) covers the sequence rules, clip checks and playback paths.

## Try one pair

Start with a three-word round. Replay a missed position, compare the two examples, then switch to speaking practice and record one word. There is no need to turn it into a long study session.

[Try L & N in the browser](https://l-and-n.lazying.art/?utm_source=blog&utm_medium=article&utm_campaign=l_and_n_listening). It is free and needs no account. The app also links to the native versions; the US iPhone listing is US$0.99.
