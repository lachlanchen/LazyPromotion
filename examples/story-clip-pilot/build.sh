#!/usr/bin/env bash
set -euo pipefail

sample_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$sample_dir/../.." && pwd)"
cd "$sample_dir"
export SOURCE_DATE_EPOCH=1788652800
export FORCE_SOURCE_DATE=1

command -v ffmpeg >/dev/null
command -v ffprobe >/dev/null
command -v jq >/dev/null
command -v zip >/dev/null

source_video="$repo_root/examples/bilingual-lecture-pack/delivery/preview/bilingual-caption-preview.mp4"
source_caption="$repo_root/examples/bilingual-lecture-pack/delivery/subtitles/en.srt"
source_ledger="$repo_root/examples/bilingual-lecture-pack/delivery/issue-ledger.md"
source_script="$repo_root/examples/bilingual-lecture-pack/source/lecture-script.txt"

expected_source_sha="79d44204269139d7476d198bf600335bedcfa9db940c07afc3354c962abaa271"
expected_caption_sha="00ce15da344e39620274710b01a5d04380c87a4fca906447082ff51be6f4bb63"
expected_ledger_sha="05feb4baee902f350ec579fd69dc4ed1316ff23c760c13d5f7d3197a111c12d2"
expected_script_sha="e3a3efdb183ee94cdf3770c20c71e4bf17c83f16fedaa2684ecb517a75ce0823"

test "$(sha256sum "$source_video" | cut -d' ' -f1)" = "$expected_source_sha"
test "$(sha256sum "$source_caption" | cut -d' ' -f1)" = "$expected_caption_sha"
test "$(sha256sum "$source_ledger" | cut -d' ' -f1)" = "$expected_ledger_sha"
test "$(sha256sum "$source_script" | cut -d' ' -f1)" = "$expected_script_sha"

mkdir -p artifacts delivery

clip_start="27.600"
clip_duration="12.820"

ffmpeg -hide_banner -loglevel error -y \
  -ss "$clip_start" -i "$source_video" -t "$clip_duration" \
  -filter_complex "[0:v]split=2[base][card];[base]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=18:2,eq=brightness=-0.42[bg];[card]scale=1000:-2[fg];[bg][fg]overlay=x=(W-w)/2:y=(H-h)/2,drawbox=x=40:y=190:w=1000:h=250:color=0x17231f@0.88:t=fill,drawtext=font='Noto Sans':text='LAZYINGART · STORY CLIP SAMPLE':fontcolor=0xb9d76b:fontsize=32:x=(w-text_w)/2:y=245,drawtext=font='Noto Serif':text='Why provenance matters':fontcolor=white:fontsize=58:x=(w-text_w)/2:y=305,subtitles=delivery/selected-caption.en.srt:force_style='FontName=Noto Sans,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H0017231F,BorderStyle=3,BackColour=&HCC17231F,Outline=1,Shadow=0,Alignment=2,MarginL=70,MarginR=70,MarginV=480',drawbox=x=40:y=1490:w=1000:h=190:color=0x17231f@0.88:t=fill,drawtext=font='Noto Sans':text='Project-owned source · selected moment B':fontcolor=0xe7eee9:fontsize=30:x=(w-text_w)/2:y=1550,drawtext=font='Noto Sans':text='12.82 seconds · captions + source ledger included':fontcolor=0xaebdb6:fontsize=24:x=(w-text_w)/2:y=1605[v]" \
  -map "[v]" -map 0:a:0 \
  -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -profile:v high -level 4.1 -r 24 \
  -c:a aac -b:a 160k -ar 48000 -movflags +faststart -shortest \
  -metadata title="Story Clip Pilot sample — Why provenance matters" \
  -metadata comment="Project-owned synthetic process evidence; CC BY 4.0" \
  delivery/selected-provenance-clip.mp4

ffmpeg -hide_banner -loglevel error -y \
  -ss 8 -i delivery/selected-provenance-clip.mp4 \
  -frames:v 1 delivery/poster.png

duration="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 delivery/selected-provenance-clip.mp4)"
clip_sha="$(sha256sum delivery/selected-provenance-clip.mp4 | cut -d' ' -f1)"
poster_sha="$(sha256sum delivery/poster.png | cut -d' ' -f1)"
caption_sha="$(sha256sum delivery/selected-caption.en.srt | cut -d' ' -f1)"
candidates_sha="$(sha256sum candidates.json | cut -d' ' -f1)"
ledger_sha="$(sha256sum delivery/caption-source-ledger.md | cut -d' ' -f1)"
rights_sha="$(sha256sum delivery/rights-manifest.json | cut -d' ' -f1)"

jq -n \
  --arg duration "$duration" \
  --arg clip_sha "$clip_sha" \
  --arg poster_sha "$poster_sha" \
  --arg caption_sha "$caption_sha" \
  --arg candidates_sha "$candidates_sha" \
  --arg ledger_sha "$ledger_sha" \
  --arg rights_sha "$rights_sha" \
  '{
    schema: "story-clip-pilot-sample/v1",
    sample_id: "provenance-inspectability-clip-2026-09",
    created_utc: "2026-09-06T00:00:00Z",
    status: "project_owned_synthetic_process_evidence",
    offer: "USD 250 Story Clip Pilot",
    source: {
      source_id: "knowledge-graph-provenance-synthetic-2026-09",
      repository_path: "examples/bilingual-lecture-pack/delivery/preview/bilingual-caption-preview.mp4",
      sha256: "79d44204269139d7476d198bf600335bedcfa9db940c07afc3354c962abaa271",
      duration_seconds: 41.191,
      language: "en",
      rights_holder: "LazyingArt LLC",
      license: "CC BY 4.0"
    },
    selection: {
      candidate_count: 2,
      selected_id: "candidate-b",
      source_start: "00:00:27.600",
      source_end: "00:00:40.420"
    },
    delivery: {
      video: "delivery/selected-provenance-clip.mp4",
      duration_seconds: ($duration | tonumber),
      dimensions: "1080x1920",
      video_codec: "H.264",
      audio_codec: "AAC",
      captions: "delivery/selected-caption.en.srt",
      caption_source_ledger: "delivery/caption-source-ledger.md",
      rights_manifest: "delivery/rights-manifest.json",
      poster: "delivery/poster.png"
    },
    hashes: {
      video: $clip_sha,
      poster: $poster_sha,
      captions: $caption_sha,
      candidates: $candidates_sha,
      caption_source_ledger: $ledger_sha,
      rights_manifest: $rights_sha
    },
    exclusions: [
      "customer result",
      "natural-interview editing proof",
      "30-minute source turnaround proof",
      "views, retention, or conversion result",
      "publishing"
    ],
    inventory_hashes: "delivery/SHA256SUMS"
  }' > delivery/manifest.json

find README.md LICENSE-SAMPLE.md build.sh source-reference.json candidates.json delivery -type f \
  ! -name 'SHA256SUMS' \
  -print0 | sort -z | xargs -0 sha256sum > delivery/SHA256SUMS

find README.md LICENSE-SAMPLE.md build.sh source-reference.json candidates.json delivery -type f \
  -exec touch -d '2026-09-06 00:00:00 UTC' {} +

find README.md LICENSE-SAMPLE.md build.sh source-reference.json candidates.json delivery -type f \
  -print | LC_ALL=C sort | zip -X -9 -FS -q artifacts/story-clip-pilot-sample.zip -@
sha256sum artifacts/story-clip-pilot-sample.zip > artifacts/story-clip-pilot-sample.zip.sha256

printf 'Built %s-second clip; ZIP %s bytes\n' \
  "$duration" \
  "$(stat -c %s artifacts/story-clip-pilot-sample.zip)"
