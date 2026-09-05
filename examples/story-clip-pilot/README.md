# Story Clip Pilot delivery sample

This packet shows the handoff for the fixed [USD 250 Story Clip Pilot](https://lazying.art/story-clip/): two timestamped moments, one selected vertical clip, corrected source-language captions, a caption/source ledger, rights notes, and file hashes.

The source is a 41-second LazyingArt-owned synthetic mini-lecture already published in this repository's Bilingual Lecture Pack sample. Candidate B was selected because its conclusion stands alone: provenance cannot make a claim true, but it can make the claim inspectable.

## Open the sample

- `candidates.json` — two moments with hooks, cut rationale, and rights notes
- `delivery/selected-provenance-clip.mp4` — the selected 12.82-second 9:16 clip
- `delivery/selected-caption.en.srt` — corrected English captions on the clip timeline
- `delivery/caption-source-ledger.md` — source locators, timing shift, and recorded corrections
- `delivery/rights-manifest.json` — source ownership, license, and reuse boundary
- `delivery/manifest.json` and `delivery/SHA256SUMS` — machine-readable inventory and hashes
- `artifacts/story-clip-pilot-sample.zip` — deterministic delivery packet

This is project-owned process evidence, not customer work, a natural-interview edit, a performance result, or proof of 30-minute turnaround. It demonstrates the files and review trail; it does not promise views, retention, conversion, or publishing.

## Rebuild

Run `./build.sh` with FFmpeg 6.1, `jq`, `zip`, and the committed Bilingual Lecture Pack sample present. The source media is referenced rather than duplicated.
