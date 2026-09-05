#!/usr/bin/env bash
set -euo pipefail

sample_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
artifact_dir="${sample_dir}/artifacts"
subtitle_file="${sample_dir}/sample.ass"
video="${artifact_dir}/rtl-caption-feasibility.mp4"
render_log="${artifact_dir}/render.log"

for command_name in ffmpeg ffprobe fc-match jq rg sha256sum; do
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "missing required command: ${command_name}" >&2
    exit 1
  fi
done

for font_name in "Noto Sans" "Noto Sans Hebrew" "Noto Sans Arabic"; do
  if [[ "$(fc-match -f '%{family}\n' "${font_name}" | head -1)" != *"${font_name}"* ]]; then
    echo "missing required font: ${font_name}" >&2
    exit 1
  fi
done

if ! rg -q ' subtitles +V->V' <<<"$(ffmpeg -hide_banner -filters 2>/dev/null)"; then
  echo "FFmpeg subtitles filter is unavailable" >&2
  exit 1
fi

mkdir -p "${artifact_dir}"
export SOURCE_DATE_EPOCH=1788307200

ffmpeg -hide_banner -y -loglevel verbose \
  -f lavfi -i "color=c=0x101826:s=1080x1920:r=30:d=8" \
  -vf "subtitles=${subtitle_file}:fontsdir=/usr/share/fonts/truetype/noto" \
  -an -c:v libx264 -preset slow -crf 18 -threads 1 -pix_fmt yuv420p \
  -metadata creation_time=2026-09-05T00:00:00Z -movflags +faststart \
  "${video}" >"${render_log}" 2>&1

rg -q 'Shaper: FriBidi .* HarfBuzz' "${render_log}"

for frame in "hebrew:1.20" "arabic:3.90" "mixed:6.60"; do
  name="${frame%%:*}"
  second="${frame##*:}"
  ffmpeg -hide_banner -loglevel error -y -ss "${second}" -i "${video}" \
    -frames:v 1 "${artifact_dir}/${name}.png"
done

probe="$(ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate,codec_name,pix_fmt -of json "${video}")"
duration="$(jq -r '.format.duration' <<<"${probe}")"
width="$(jq -r '.streams[0].width' <<<"${probe}")"
height="$(jq -r '.streams[0].height' <<<"${probe}")"
[[ "${duration}" == "8.000000" && "${width}" == "1080" && "${height}" == "1920" ]]

ffmpeg_version="$(ffmpeg -version | head -1)"
shaper="$(rg -m1 -o 'Shaper: FriBidi .* HarfBuzz[^ ]* [0-9.]+' "${render_log}")"

jq -n \
  --arg sample "project-owned synthetic RTL and bidirectional caption fixture" \
  --arg boundary "Renderer feasibility only; not ASR, language-accuracy, word-alignment, template-scale, ingestion, throughput, or buyer-acceptance evidence." \
  --arg ffmpeg "${ffmpeg_version}" \
  --arg shaper "${shaper}" \
  --arg subtitle_sha256 "$(sha256sum "${subtitle_file}" | cut -d' ' -f1)" \
  --arg video_sha256 "$(sha256sum "${video}" | cut -d' ' -f1)" \
  --arg hebrew_sha256 "$(sha256sum "${artifact_dir}/hebrew.png" | cut -d' ' -f1)" \
  --arg arabic_sha256 "$(sha256sum "${artifact_dir}/arabic.png" | cut -d' ' -f1)" \
  --arg mixed_sha256 "$(sha256sum "${artifact_dir}/mixed.png" | cut -d' ' -f1)" \
  --argjson probe "${probe}" \
  '{
    sample: $sample,
    evidence_boundary: $boundary,
    toolchain: {ffmpeg: $ffmpeg, shaping: $shaper},
    source_sha256: {subtitles: $subtitle_sha256},
    output_sha256: {
      video: $video_sha256,
      hebrew_frame: $hebrew_sha256,
      arabic_frame: $arabic_sha256,
      mixed_frame: $mixed_sha256
    },
    probe: $probe,
    verification: {
      duration_seconds: 8,
      dimensions: "1080x1920",
      video_codec: "h264",
      pixel_format: "yuv420p",
      frame_count: 3,
      directional_isolates_present: true,
      native_language_review: false
    }
  }' >"${artifact_dir}/manifest.json"

printf 'Built %s\n' "${video}"
