#!/usr/bin/env bash
set -euo pipefail

sample_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
artifact_dir="${sample_dir}/artifacts"
source_manifest="${sample_dir}/source-manifest.json"
traditional_srt="${sample_dir}/captions-yue-Hant.srt"
simplified_srt="${sample_dir}/captions-zh-Hans.srt"
video="${artifact_dir}/cantonese-caption-sample.mp4"

for command_name in curl ffmpeg ffprobe fc-match jq sha256sum; do
  command -v "${command_name}" >/dev/null 2>&1 || {
    echo "missing required command: ${command_name}" >&2
    exit 1
  }
done

font_file="$(fc-match -f '%{file}\n' 'Noto Sans CJK SC' | head -1)"
[[ -f "${font_file}" ]] || {
  echo "Noto Sans CJK SC is unavailable" >&2
  exit 1
}

temporary="$(mktemp -d)"
trap 'rm -rf "${temporary}"' EXIT
source_audio="${temporary}/source.mp3"
waveform="${temporary}/waveform.png"
render_log="${temporary}/render.log"
source_url="$(jq -r '.source_audio_url' "${source_manifest}")"
source_sha256="$(jq -r '.source_audio_sha256' "${source_manifest}")"

curl --fail --location --silent --show-error --output "${source_audio}" "${source_url}"
printf '%s  %s\n' "${source_sha256}" "${source_audio}" | sha256sum --check --status

mkdir -p "${artifact_dir}"
export SOURCE_DATE_EPOCH=1788566400

ffmpeg -hide_banner -y -loglevel error \
  -i "${source_audio}" -t 23.52 \
  -filter_complex "showwavespic=s=1280x720:colors=0x48BFE3@0.72:scale=sqrt" \
  -frames:v 1 "${waveform}"

ffmpeg -hide_banner -y -loglevel verbose \
  -loop 1 -framerate 24 -i "${waveform}" -i "${source_audio}" \
  -filter_complex "[0:v]format=yuv420p,drawbox=x=0:y=0:w=1280:h=128:color=0x0B1020@0.92:t=fill,drawtext=fontfile=${font_file}:text='CANTONESE CAPTION DELIVERY':fontcolor=white:fontsize=38:x=52:y=28,drawtext=fontfile=${font_file}:text='Traditional + Simplified SRT  |  burned preview uses Simplified':fontcolor=0xA7C7E7:fontsize=24:x=54:y=78,subtitles=${simplified_srt}:fontsdir=/usr/share/fonts/opentype/noto:force_style='FontName=Noto Sans CJK SC,FontSize=34,PrimaryColour=&H00FFFFFF,OutlineColour=&H0020100B,BorderStyle=1,Outline=3,Shadow=0,MarginV=54'[video]" \
  -map '[video]' -map 1:a:0 -t 23.52 \
  -c:v libx264 -preset slow -crf 18 -threads 1 -pix_fmt yuv420p -r 24 \
  -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -metadata creation_time=2026-09-05T00:00:00Z -map_metadata -1 \
  -movflags +faststart "${video}" >"${render_log}" 2>&1

for frame in 'cue-1:3.2' 'cue-2:8.5' 'cue-4:20.5'; do
  name="${frame%%:*}"
  second="${frame##*:}"
  ffmpeg -hide_banner -loglevel error -y -ss "${second}" -i "${video}" \
    -frames:v 1 "${artifact_dir}/${name}.png"
done

probe="$(ffprobe -v error -show_entries format=duration,size:stream=index,codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels -of json "${video}")"
duration="$(jq -r '.format.duration' <<<"${probe}")"
width="$(jq -r '.streams[] | select(.codec_type == "video") | .width' <<<"${probe}")"
height="$(jq -r '.streams[] | select(.codec_type == "video") | .height' <<<"${probe}")"
jq -e '(.format.duration | tonumber) >= 23.52 and (.format.duration | tonumber) <= 23.57' <<<"${probe}" >/dev/null
[[ "${width}" == "1280" && "${height}" == "720" ]]

jq -n \
  --arg source_audio_url "${source_url}" \
  --arg source_audio_sha256 "${source_sha256}" \
  --arg traditional_srt_sha256 "$(sha256sum "${traditional_srt}" | cut -d' ' -f1)" \
  --arg simplified_srt_sha256 "$(sha256sum "${simplified_srt}" | cut -d' ' -f1)" \
  --arg video_sha256 "$(sha256sum "${video}" | cut -d' ' -f1)" \
  --arg cue_1_sha256 "$(sha256sum "${artifact_dir}/cue-1.png" | cut -d' ' -f1)" \
  --arg cue_2_sha256 "$(sha256sum "${artifact_dir}/cue-2.png" | cut -d' ' -f1)" \
  --arg cue_4_sha256 "$(sha256sum "${artifact_dir}/cue-4.png" | cut -d' ' -f1)" \
  --arg boundary "Project-owned generated-song workflow evidence; not a sermon, customer work, native-editor endorsement, ASR or translation benchmark, or proof of plus-or-minus 0.2-second alignment on unseen material." \
  --argjson output_duration_seconds "${duration}" \
  --argjson probe "${probe}" \
  '{
    schema: "lazyingart.cantonese-caption-delivery/v1",
    source: {
      url: $source_audio_url,
      sha256: $source_audio_sha256,
      excerpt_seconds: [0, 23.52],
      type: "project-controlled generated Cantonese song vocal"
    },
    delivery: {
      cue_count: 4,
      tracks: ["yue-Hant", "zh-Hans"],
      burned_track: "zh-Hans",
      traditional_srt_sha256: $traditional_srt_sha256,
      simplified_srt_sha256: $simplified_srt_sha256,
      video_sha256: $video_sha256,
      review_frame_sha256: {
        cue_1: $cue_1_sha256,
        cue_2: $cue_2_sha256,
        cue_4: $cue_4_sha256
      }
    },
    probe: $probe,
    evidence_boundary: $boundary,
    verification: {
      source_excerpt_seconds: 23.52,
      output_duration_seconds: $output_duration_seconds,
      dimensions: "1280x720",
      video_codec: "h264",
      audio_codec: "aac",
      cue_timing_source: "reviewed Musia per-vocal lyric track",
      native_spoken_word_review: false,
      unseen_alignment_tolerance_claimed: false
    }
  }' >"${artifact_dir}/manifest.json"

printf 'Built %s\n' "${video}"
