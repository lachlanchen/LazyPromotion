#!/usr/bin/env bash
set -euo pipefail

sample_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$sample_dir"
export SOURCE_DATE_EPOCH=1788566400
export FORCE_SOURCE_DATE=1

command -v espeak-ng >/dev/null
command -v ffmpeg >/dev/null
command -v ffprobe >/dev/null
command -v xelatex >/dev/null
command -v jq >/dev/null
command -v zip >/dev/null

mkdir -p artifacts delivery/preview delivery/study-companion source

espeak-ng -v en-us -s 145 -p 38 -a 160 \
  -f source/lecture-script.txt \
  -w source/lecture-source.wav

(cd delivery/study-companion && xelatex -interaction=nonstopmode -halt-on-error study-companion.tex >/dev/null)
(cd delivery/study-companion && xelatex -interaction=nonstopmode -halt-on-error study-companion.tex >/dev/null)

duration="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 source/lecture-source.wav)"

ffmpeg -hide_banner -loglevel error -y \
  -f lavfi -i "color=c=0x17231f:s=1280x720:r=24:d=${duration}" \
  -i source/lecture-source.wav \
  -vf "drawbox=x=64:y=62:w=1152:h=596:color=0x21332d:t=fill,drawbox=x=92:y=92:w=8:h=74:color=0xb9d76b:t=fill,drawtext=font='Noto Sans':text='LAZYINGART · BILINGUAL LECTURE PACK':fontcolor=0xb9d76b:fontsize=24:x=120:y=92,drawtext=font='Noto Serif':text='Why provenance matters':fontcolor=white:fontsize=58:x=120:y=128,drawtext=font='Noto Sans':text='CLAIM':fontcolor=0x17231f:fontsize=25:x=175:y=287:box=1:boxcolor=0xf2eadb:boxborderw=18,drawtext=font='Noto Sans':text='PASSAGE':fontcolor=0x17231f:fontsize=25:x=525:y=287:box=1:boxcolor=0xf2eadb:boxborderw=18,drawtext=font='Noto Sans':text='SOURCE HASH':fontcolor=0x17231f:fontsize=25:x=865:y=287:box=1:boxcolor=0xf2eadb:boxborderw=18,drawtext=font='Noto Sans':text='>':fontcolor=0xb9d76b:fontsize=48:x=420:y=277,drawtext=font='Noto Sans':text='>':fontcolor=0xb9d76b:fontsize=48:x=775:y=277,drawtext=font='Noto Sans':text='Project-owned synthetic English source · zh-TW study track':fontcolor=0xaebdb6:fontsize=22:x=120:y=405,ass=delivery/preview/bilingual.ass,drawbox=x=92:y=704:w='1096*t/${duration}':h=5:color=0xed7b43:t=fill" \
  -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -profile:v high -level 4.0 \
  -c:a aac -b:a 160k -ar 48000 -movflags +faststart -shortest \
  -metadata title="Bilingual Lecture Pack sample" \
  -metadata comment="Project-owned synthetic process evidence; CC BY 4.0" \
  delivery/preview/bilingual-caption-preview.mp4

ffmpeg -hide_banner -loglevel error -y \
  -ss 10 -i delivery/preview/bilingual-caption-preview.mp4 \
  -frames:v 1 delivery/preview/poster.png

source_sha="$(sha256sum source/lecture-source.wav | cut -d' ' -f1)"
preview_sha="$(sha256sum delivery/preview/bilingual-caption-preview.mp4 | cut -d' ' -f1)"
pdf_sha="$(sha256sum delivery/study-companion/study-companion.pdf | cut -d' ' -f1)"

jq -n \
  --arg source_sha "$source_sha" \
  --arg preview_sha "$preview_sha" \
  --arg pdf_sha "$pdf_sha" \
  --arg duration "$duration" \
  '{
    schema: "bilingual-lecture-pack-sample/v1",
    sample_id: "knowledge-graph-provenance-synthetic-2026-09",
    created_utc: "2026-09-05T00:00:00Z",
    status: "project_owned_synthetic_process_evidence",
    source: {
      title: "Why provenance matters in a multilingual knowledge graph",
      language: "en",
      format: "PCM WAV",
      duration_seconds: ($duration | tonumber),
      sha256: $source_sha,
      rights_holder: "LazyingArt LLC",
      license: "CC BY 4.0",
      third_party_content: false,
      generation: "eSpeak NG 1.51, en-us, 145 wpm, pitch 38, amplitude 160"
    },
    target: {
      language: "zh-TW",
      status: "assisted translation; terminology and alignment reviewed; not certified; no independent native-language review"
    },
    asr: {
      first_draft: "working/asr-draft.srt",
      tool: "openai-whisper 20250625",
      model: "tiny.en",
      review: "corrected against the included source script and audio; corrections recorded in delivery/issue-ledger.md"
    },
    preview: {
      duration_seconds: ($duration | tonumber),
      video: "H.264 1280x720 24fps yuv420p",
      audio: "AAC 48kHz",
      burned_captions: ["en", "zh-TW"],
      sha256: $preview_sha
    },
    study_companion: {
      format: "A5 PDF",
      editable_source: "delivery/study-companion/study-companion.tex",
      sha256: $pdf_sha
    },
    exclusions: [
      "customer result",
      "certified translation",
      "independent native-language review",
      "professional narration",
      "audio restoration"
    ],
    inventory_hashes: "delivery/SHA256SUMS"
  }' > delivery/manifest.json

find delivery source working -type f \
  ! -name 'SHA256SUMS' \
  ! -name '*.aux' \
  ! -name '*.log' \
  ! -name '*.out' \
  -print0 | sort -z | xargs -0 sha256sum > delivery/SHA256SUMS
sha256sum README.md LICENSE-SAMPLE.md build.sh >> delivery/SHA256SUMS

find README.md LICENSE-SAMPLE.md build.sh source working delivery -type f \
  ! -name '*.aux' \
  ! -name '*.log' \
  ! -name '*.out' \
  -exec touch -d '2026-09-05 00:00:00 UTC' {} +

find README.md LICENSE-SAMPLE.md build.sh source working delivery -type f \
  ! -name '*.aux' \
  ! -name '*.log' \
  ! -name '*.out' \
  -print | LC_ALL=C sort | zip -X -9 -FS -q artifacts/bilingual-lecture-pack-sample.zip -@
sha256sum artifacts/bilingual-lecture-pack-sample.zip > artifacts/bilingual-lecture-pack-sample.zip.sha256

printf 'Built %s seconds; ZIP %s bytes\n' \
  "$duration" \
  "$(stat -c %s artifacts/bilingual-lecture-pack-sample.zip)"
