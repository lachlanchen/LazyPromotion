---
title: "How to Deliver Cantonese Subtitles in Traditional and Simplified Chinese"
slug: "cantonese-subtitles-traditional-simplified-srt"
status: "publish"
source_language: "en"
author: "Lachlan Chen"
categories:
  - "Computer & Internet"
  - "Video"
tags:
  - "Cantonese subtitles"
  - "Traditional Chinese"
  - "Simplified Chinese"
  - "SRT"
  - "FFmpeg"
excerpt: "A practical workflow for producing one checked Cantonese timeline, Traditional and Simplified Chinese SRT files, and a verifiable H.264 preview."
---

For a Cantonese video, “Traditional plus Simplified subtitles” should not mean two unrelated caption files. The safer shape is one reviewed timeline, one Traditional Chinese transcript, a derived and checked Simplified Chinese track, and a preview rendered from the same data.

That keeps later corrections small. Fix one cue, carry the change into both scripts, rebuild the preview, and verify the exact output you plan to deliver.

## Preserve the source before editing

Keep the supplied recording unchanged and make a working copy. Record the original filename, duration, audio language, video dimensions, and SHA-256 hash. Also record who owns the material and where the finished captions may be published.

```bash
sha256sum source.mp4
ffprobe -v error -show_entries format=duration \
  -show_entries stream=codec_type,codec_name,width,height,r_frame_rate \
  -of json source.mp4
```

This small ledger prevents a compressed preview from quietly replacing the source. It also makes it possible to reproduce the result when a client asks for a correction weeks later.

## Correct the Cantonese track first

Automatic speech recognition can provide a draft, but the Traditional Chinese track should be corrected while listening to the actual recording. Mark uncertain words instead of guessing. Names, quotations, numbers, and specialist terms deserve a separate list.

For a lecture or sermon, ask which edition or terminology guide the speaker follows. A familiar phrase can still be wrong if it comes from a different translation. Keep editorial improvements out of the transcript unless they are clearly labeled.

Cue boundaries should follow meaning as well as pauses. A subtitle that cuts a name, number, or short negative across two cues is difficult to read even when every timestamp is technically valid.

## Convert the script, then review the words

[OpenCC](https://github.com/BYVoid/OpenCC) provides deterministic conversion between Simplified, Traditional, Hong Kong, and Taiwan character and phrase conventions. For a Hong Kong Traditional text going to Simplified Chinese, a first pass can be as small as:

```bash
opencc -c hk2s.json -i captions-yue-Hant.srt -o captions-zh-Hans.srt
```

That is script and regional-wording conversion, not Cantonese-to-Mandarin translation. OpenCC’s own documentation says its dictionaries use Mandarin vocabulary as their base and do not translate between Mandarin and Cantonese. Review personal names, biblical or technical terms, Cantonese particles, quotations, and region-specific wording against the recording and the intended audience.

Do not regenerate the Simplified track with new timestamps. Both files should keep the same cue numbers and time ranges so one timing correction remains one correction.

## Keep one timeline for both files

Plain SRT is useful because it is easy to inspect. [YouTube’s current caption documentation](https://support.google.com/youtube/answer/2734698?hl=en) recommends basic SRT or SBV for newcomers and requires plain UTF-8 for basic SRT. A four-cue pair should therefore differ in text, not structure:

```text
4
00:00:18,020 --> 00:00:23,520
小小心仍輕輕顫抖
```

The Simplified file keeps cue `4` and the same time range, changing only the reviewed text to `小小心仍轻轻颤抖`.

Check the first and last cue, every speaker change, long pauses, rapid passages, and every place the recognizer was uncertain. If a contract specifies a timing tolerance, compare the visible cue edges with the actual speech. A file parser cannot prove that a subtitle starts within 0.2 seconds of a spoken word.

## Burn a preview and inspect it

[FFmpeg’s `subtitles` filter](https://ffmpeg.org/ffmpeg-filters.html#subtitles-1) renders subtitle files through libass and supports an additional font directory and explicit style overrides. A simple H.264/AAC review master can be built with:

```bash
ffmpeg -i source.mp4 \
  -vf "subtitles=captions-zh-Hans.srt:fontsdir=/usr/share/fonts/opentype/noto:force_style='FontName=Noto Sans CJK SC,FontSize=24,Outline=2'" \
  -c:v libx264 -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart preview.mp4
```

Watch the result at normal speed. Check line wrapping, punctuation, safe margins, Chinese glyph fallback, cuts, and whether the captions cover faces, slides, or existing on-screen text. Then use `ffprobe` again and hash the finished file. A successful FFmpeg exit proves that the render completed; it does not prove that the words or timing are right.

## Deliver editable files with the video

A small, useful delivery contains:

- the corrected Traditional Chinese SRT;
- the matching Simplified Chinese SRT;
- the H.264 MP4 with the requested track burned in;
- a short issue list for uncertain audio and terminology decisions;
- a manifest with source and output hashes, duration, dimensions, codecs, and tools;
- the agreed correction window.

Do not make the burned video the only deliverable. Separate subtitle files let the owner correct terminology, upload selectable captions, or render a different style without transcribing the recording again. [LazyEdit](https://github.com/lachlanchen/LazyEdit) is the open-source timed-media workflow I use for this kind of source-first handling.

## Inspect a complete small packet

I published a [23.52-second Cantonese caption packet](https://github.com/lachlanchen/LazyPromotion/tree/8db8e1722c85c626296f1306e7dca662439a6a6e/examples/cantonese-caption-delivery) with both SRT files, a burned H.264/AAC preview, review frames, source hashes, and a rebuild script. It uses our own short Cantonese song excerpt, so every input can be shared and checked. It is a workflow example, not a customer video or proof of accuracy on unseen speech.

If you have a rights-cleared Cantonese lecture, interview, or course, send the duration, audio condition, dialect, existing transcript, preferred terminology, target script, and required video format to `contact@lazying.art`. I can check whether the first minute fits this workflow before quoting the full job.
