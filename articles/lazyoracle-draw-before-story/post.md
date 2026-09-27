---
id: 3866
title: "Draw the Cards Before Writing the Story"
slug: "lazyoracle-cards-rules-before-ai-story"
status: "publish"
source_language: "en"
categories:
  - "Computer & Internet"
excerpt: "LazyOracle separates a tarot draw or I Ching cast from the AI prose that explains it. A small design choice makes the result easier to inspect and discuss."
---

Ask a language model for a tarot reading and it can write something convincing immediately. But which cards were actually drawn? If the model chooses the cards while telling the story, there is no clear result to inspect underneath the prose.

LazyOracle, a project I’m building at LazyingArt, separates those two steps. Code draws the cards or casts the hexagram. The explanation comes afterwards, using that result. It is a tool for exploring symbolic traditions and reflecting on a question, not a way to establish what will happen.

## Give the explanation something fixed to explain

A tarot draw records the cards, their positions and their orientation. LazyOracle uses a seeded shuffle, so the same seed and settings reproduce the draw. For the I Ching, the result includes the hexagram and changing lines. BaZi has its own date and chart calculations.

The language model receives those structured results rather than deciding them in prose. That does not make an interpretation true, or guarantee the model will never make a mistake. It makes a narrower question possible: does this explanation actually refer to the result on the screen?

![LazyOracle showing three face-down tarot cards, with their spread positions visible.](https://blog.lazying.art/wp-content/uploads/2026/09/20260927-lazyoracle-draw-before-story-lazyoracle-tarot-before-explanation.png)

*The web tarot view. The draw exists before its explanation.*

This is also useful when you ask a follow-up. “Why did you connect that card with this question?” should discuss the existing spread, not quietly replace it with another one. A new draw should be a deliberate action.

## Try a question that leaves room to think

For a first look, choose a one-card or three-card spread and a low-stakes question. “What am I overlooking in this project?” is more useful for reflection than asking the app to guarantee an outcome.

Look at the card and its position before reading the prose. Write down your own association, then compare it with the explanation. You do not have to agree with it. The exercise is to find a question or a perspective worth considering, not to hand over a decision.

The same distinction applies when exploring the I Ching or the traditional calendar: faithfully implementing a tradition's rules is different from demonstrating predictive power. I would not use a reading to choose a medical treatment, a trade or another consequential decision.

## Know when the explanation uses a service

Cards and charts are computed on the device. Cloud narration is different: your question and relevant reading context are sent through the reading service. That context may include birth details for a chart. Check the current settings before entering personal information; local calculation does not make a cloud conversation private to the device.

[Open LazyOracle](https://oracle.lazying.art/?utm_source=lazyblog&utm_medium=article&utm_campaign=lazyoracle_introduction) to explore the web version. The [source code](https://github.com/lachlanchen/LazyOracle) shows how the engines and explanations are separated. The mobile versions are still in testing.
