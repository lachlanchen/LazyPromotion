# Cantonese caption delivery sample

This small delivery packet shows one concrete media workflow:

`project-controlled Cantonese audio → reviewed Traditional Chinese timing → Simplified Chinese SRT → burned H.264 preview`

The source is a 23.52-second excerpt from Musia's Cantonese vocal of *Take Care of Yourself*. The four cue boundaries and both Chinese scripts come from the published `yue-vocal` lyric set. The packet contains:

- `captions-yue-Hant.srt` — Traditional Chinese cue text;
- `captions-zh-Hans.srt` — Simplified Chinese cue text on the same timeline;
- `artifacts/cantonese-caption-sample.mp4` — 1280×720 H.264/AAC preview with the Simplified track burned in;
- three review frames and `artifacts/manifest.json`.

Run `./build.sh` to download the pinned public source, verify its SHA-256, render the sample, extract the review frames, and rebuild the evidence manifest.

## Evidence boundary

This is project-owned workflow evidence built from a generated song vocal. It is not a sermon, customer work, native-editor endorsement, speech-ASR benchmark, translation benchmark, or proof of ±0.2-second alignment on unseen material. The cue text and line boundaries were already reviewed for the selected Musia vocal; token timing remains analysis-grade. A real spoken-word job still needs a terminology guide, manual Cantonese review, speaker/noise inspection, and funded scope before work begins.

Source references:

- <https://fun.lazying.art/#take-care-of-yourself>
- <https://lazyingart.github.io/MusiaSongs/audio/take-care-of-yourself-yue-Hant.mp3>
- <https://github.com/lachlanchen/Musia>
