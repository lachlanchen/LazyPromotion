#!/usr/bin/env bash
set -euo pipefail

sample_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
artifact_dir="${sample_dir}/artifacts"
latexdiff_bin="${LATEXDIFF_BIN:-$(command -v latexdiff || true)}"

if [[ -z "${latexdiff_bin}" || ! -f "${latexdiff_bin}" ]]; then
  echo "latexdiff is required; set LATEXDIFF_BIN to the executable" >&2
  exit 1
fi

latexdiff_version="$(${latexdiff_bin} --version 2>&1 | head -1)"
if [[ "${latexdiff_version}" != *"1.4.0"* ]]; then
  echo "this sample is pinned to latexdiff 1.4.0; found: ${latexdiff_version}" >&2
  exit 1
fi

for command_name in latexmk pdflatex pdfinfo pdftotext jq sha256sum python3; do
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "missing required command: ${command_name}" >&2
    exit 1
  fi
done

build_dir="$(mktemp -d /tmp/lazypromotion-latex-redline.XXXXXX)"
cleanup() {
  rm -rf -- "${build_dir}"
}
trap cleanup EXIT

export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1788307200}"
export FORCE_SOURCE_DATE=1

mkdir -p "${build_dir}/baseline" "${build_dir}/revision" "${build_dir}/redline" "${artifact_dir}"

latexmk -pdf -interaction=nonstopmode -halt-on-error \
  -outdir="${build_dir}/baseline" "${sample_dir}/baseline/main.tex" \
  >"${build_dir}/baseline/latexmk.stdout" 2>&1

latexmk -pdf -interaction=nonstopmode -halt-on-error \
  -outdir="${build_dir}/revision" "${sample_dir}/revision/main.tex" \
  >"${build_dir}/revision/latexmk.stdout" 2>&1

"${latexdiff_bin}" \
  "${sample_dir}/baseline/main.tex" \
  "${sample_dir}/revision/main.tex" \
  >"${build_dir}/redline/redline.tex"

latexmk -pdf -interaction=nonstopmode -halt-on-error \
  -outdir="${build_dir}/redline" "${build_dir}/redline/redline.tex" \
  >"${build_dir}/redline/latexmk.stdout" 2>&1

if rg -n "LaTeX Error|There were undefined references|Reference .* undefined" \
  "${build_dir}"/*/*.log >/dev/null; then
  echo "a final LaTeX log contains an error or undefined reference" >&2
  exit 1
fi

pdftotext -layout "${build_dir}/baseline/main.pdf" "${build_dir}/baseline/main.txt"
pdftotext -layout "${build_dir}/revision/main.pdf" "${build_dir}/revision/main.txt"
pdftotext -layout "${build_dir}/redline/redline.pdf" "${build_dir}/redline/redline.txt"

rg -q "successful clean build is necessary but not sufficient" "${build_dir}/baseline/main.txt"
rg -q "redline as a third build" "${build_dir}/revision/main.txt"
rg -q "editor-readable redline as a third build" "${build_dir}/redline/redline.txt"

install -m 0644 "${build_dir}/baseline/main.pdf" "${artifact_dir}/baseline.pdf"
install -m 0644 "${build_dir}/revision/main.pdf" "${artifact_dir}/revision.pdf"
install -m 0644 "${build_dir}/redline/redline.pdf" "${artifact_dir}/redline.pdf"
install -m 0644 "${build_dir}/redline/redline.tex" "${artifact_dir}/redline.tex"
install -m 0644 "${build_dir}/baseline/main.log" "${artifact_dir}/baseline-final.log"
install -m 0644 "${build_dir}/revision/main.log" "${artifact_dir}/revision-final.log"
install -m 0644 "${build_dir}/redline/redline.log" "${artifact_dir}/redline-final.log"

baseline_source_sha="$(sha256sum "${sample_dir}/baseline/main.tex" | cut -d' ' -f1)"
revision_source_sha="$(sha256sum "${sample_dir}/revision/main.tex" | cut -d' ' -f1)"
latexdiff_sha="$(sha256sum "${latexdiff_bin}" | cut -d' ' -f1)"
baseline_pdf_sha="$(sha256sum "${artifact_dir}/baseline.pdf" | cut -d' ' -f1)"
revision_pdf_sha="$(sha256sum "${artifact_dir}/revision.pdf" | cut -d' ' -f1)"
redline_pdf_sha="$(sha256sum "${artifact_dir}/redline.pdf" | cut -d' ' -f1)"
pdftex_version="$(pdflatex --version | head -1)"
latexmk_version="$(latexmk -v | rg -o 'Version [0-9.]+' | head -1 | cut -d' ' -f2)"

jq -n \
  --arg sample "project-owned synthetic LaTeX revision" \
  --arg latexdiff_tag "1.4.0" \
  --arg latexdiff_commit "57d0ec532c41eb73645804d7f67667336da8bd01" \
  --arg latexdiff_sha256 "${latexdiff_sha}" \
  --arg pdftex "${pdftex_version}" \
  --arg latexmk "${latexmk_version}" \
  --arg baseline_source_sha256 "${baseline_source_sha}" \
  --arg revision_source_sha256 "${revision_source_sha}" \
  --arg baseline_pdf_sha256 "${baseline_pdf_sha}" \
  --arg revision_pdf_sha256 "${revision_pdf_sha}" \
  --arg redline_pdf_sha256 "${redline_pdf_sha}" \
  '{
    sample: $sample,
    evidence_boundary: "Not a customer result, scientific result, journal submission, or paid delivery.",
    toolchain: {
      latexdiff_tag: $latexdiff_tag,
      latexdiff_commit: $latexdiff_commit,
      latexdiff_sha256: $latexdiff_sha256,
      pdftex: $pdftex,
      latexmk: $latexmk
    },
    source_sha256: {
      baseline: $baseline_source_sha256,
      revision: $revision_source_sha256
    },
    pdf_sha256: {
      baseline: $baseline_pdf_sha256,
      revision: $revision_pdf_sha256,
      redline: $redline_pdf_sha256
    },
    verification: {
      baseline_build: "passed",
      revision_build: "passed",
      redline_build: "passed",
      final_undefined_references: 0,
      final_latex_errors: 0
    }
  }' >"${artifact_dir}/manifest.json"

printf 'Built baseline, revision, and redline PDFs in %s\n' "${artifact_dir}"
python3 "${sample_dir}/package_sample.py"
