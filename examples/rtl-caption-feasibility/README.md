# RTL and bidirectional caption-rendering feasibility

This project-owned synthetic clip exercises one narrow part of a short-video
caption pipeline: burning Hebrew, Arabic, English, numbers, and punctuation into
a 1080×1920 H.264 video with FFmpeg, libass, FriBidi, HarfBuzz, and Noto fonts.

The mixed-script lines use Unicode directional isolates so the right-to-left
and left-to-right runs have explicit boundaries. Three still frames make the
render inspectable without playing the video.

## Build

```bash
./build.sh
```

The script checks the required fonts and FFmpeg features, renders the clip,
requires the libass log to report FriBidi and HarfBuzz shaping, extracts three
frames, and writes a hash manifest.

## Current artifacts

| Artifact | Purpose |
| --- | --- |
| `artifacts/rtl-caption-feasibility.mp4` | Eight-second 1080×1920 visual render |
| `artifacts/hebrew.png` | Hebrew/English/number mixed-script frame |
| `artifacts/arabic.png` | Arabic/English/number mixed-script frame |
| `artifacts/mixed.png` | Two-line Hebrew and Arabic mixed-script frame |
| `artifacts/manifest.json` | Source, output, toolchain, and boundary evidence |
| `artifacts/render.log` | libass font and shaping log |

## Boundary

This proves only that the checked local renderer can shape and burn this small,
synthetic mixed-script fixture. It does not prove Hebrew or Arabic
transcription, linguistic accuracy, word alignment, animation templates,
large-file ingestion, production throughput, or a buyer's acceptance test. A
native-language reviewer and representative recordings are still required.
