---
id: 3857
title: "The App Demo Is Recorded. Now Come the Subtitles."
slug: "app-demo-subtitles-lazyedit-workflow"
status: "publish"
source_language: "en"
author: "Lachlan Chen"
categories:
  - "Computer & Internet"
excerpt: "How I use LazyEdit to turn my L & N and Bunko recordings into checked multilingual captions and a reviewed publishing handoff."
---

I build tools, and I also need to show what they do. A screen recording gets me part of the way there. After that come the less interesting jobs: correcting the transcript, preparing another language, checking whether the captions cover the screen, and making sure the right video actually reached the right account.

I use my own [LazyEdit](https://github.com/lachlanchen/LazyEdit) workflow for that part. It connects transcription, subtitle correction and translation, rendering, and a publishing handoff. Two recent examples are my L & N pronunciation app and Bunko, a reader for Chinese and Japanese classics.

These are ordinary recordings of me showing the apps. The material already has a subject. The editing job is to make that subject easier to follow.

## Keep the demonstration small

For an app video, one action is usually enough to start with. Show a word being practised, or a passage being read. Let someone see what happens before asking them to care about the architecture.

The [English L & N walkthrough](https://www.youtube.com/shorts/Nlsx_5U6g6U) introduces the app I built because I mix up L and N. The [English Bunko recording](https://www.youtube.com/shorts/CcziX7FoW2M) shows the reader. There is a [Chinese Bunko introduction](https://www.youtube.com/shorts/pSWnOwzyc-4) too. They give me something concrete to work with: speech, an interface, and a few things a viewer should notice.

Before editing your own recording, write down the one thing it needs to explain. Keep that sentence beside the transcript. It helps you decide which repetitions are harmless and which passages take the viewer away from the demonstration.

## Fix the source before translating it

A recognizer does not know your product as well as you do. Give it the app name and a short list of terms, then check those terms against the audio. “Polished” should still sound like the person in the recording.

For the Bunko clips, the correction context came from the product's actual documentation. The subtitle checks also kept the original cue timings. That matters because a good sentence in a text editor can still appear at the wrong moment in a video.

Check uncertain speech before you make more language versions. Otherwise, one mistaken phrase becomes several neatly written mistakes. I would rather leave a doubtful word for review than let fluent translation make it look settled.

Keep the editable subtitle files alongside the finished video, too. Burned-in captions are convenient for viewing, but they should not be your only copy of the text. A name correction should not require starting again from the recording.

## Watch the captions on a phone

More languages take more room. In the Bunko exports, the visible stack included English, Japanese, Traditional Chinese and French, with reading aids where configured. That demonstrates what the renderer can do; it does not mean every video needs four rows.

The important question is whether the viewer can still see the thing being explained. If the captions cover the word you are tapping or the sentence you are reading, the layout needs another pass.

Open the rendered video at roughly phone size. Watch it at normal speed. Check a long subtitle, a short one, the beginning and the ending. Look at the actual export, not just the subtitle editor's preview. For another audience, fewer languages or separate exports may be the better choice.

## Keep editing and publishing separate

LazyEdit prepares the media; [AutoPublish](https://github.com/lachlanchen/AutoPublish) handles the platform-specific publishing work. That separation becomes useful when an upload stalls after other destinations have already succeeded.

My workflow has needed fixes here. One queue bug could start processing the same job twice. Another lost the logo settings chosen for an individual job. The [queue notes](https://github.com/lachlanchen/LazyEdit/blob/main/references/PUBLISH_QUEUE_RELIABILITY_2026_07_14.md) describe the corrections.

The practical lesson is to keep the finished video, its caption and each destination's result together. Before retrying, check whether the original post exists. A failed overall job does not necessarily mean every upload failed.

This still needs review and occasional account login. If you are building something similar, start with one recording and one destination. Get the subtitles and the result right, then add the next step.

If you already have a longer recording and want help finding a short piece worth sharing, my [Story Clip Pilot](https://lazying.art/story-clip/?utm_source=lazyblog&utm_medium=article&utm_campaign=story_clip_pilot&utm_content=app_demo_subtitles#sample) is $250: two timestamped suggestions from one recording up to 30 minutes, then one chosen vertical clip up to 60 seconds with source-language captions and an editable SRT. Translation and publishing are separate. The page has a sample and a free fit check; we agree the scope before payment or sending the recording.
