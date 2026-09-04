---
title: "Before You OCR 1,000 Multilingual Books, Build a Small Test Set"
slug: "evaluate-multilingual-ocr-book-archive-before-rag"
status: "publish"
source_language: "en"
author: "Lachlan Chen"
categories:
  - "Computer & Internet"
  - "Books"
tags:
  - "OCR"
  - "multilingual"
  - "Arabic"
  - "Urdu"
  - "local RAG"
excerpt: "A practical way to compare OCR engines on a large multilingual book archive: sample the real page types, measure text and reading order separately, preserve the source, and route each page to the workflow that actually wins."
---

A thousand-book archive is a bad place to discover that the OCR looked convincing but changed names, joined columns in the wrong order, or quietly lost Urdu lines.

Do not begin with the question “Which OCR engine is best?” Begin with a small test set that represents the books you actually have. The result may be one engine for clean English pages, another for Arabic or Nastaliq, and manual review only for the small group that neither can read safely.

## Sample page types, not just books

Choose about 60 pages before processing the full collection. The exact count is less important than the coverage. A useful first set might contain:

- 10 clean English pages;
- 10 clean Arabic pages;
- 10 Urdu or Nastaliq pages;
- 10 mixed right-to-left and left-to-right pages;
- 10 difficult scans: skew, bleed-through, weak contrast, marginal notes;
- 10 structural pages: two columns, footnotes, tables, poetry, or parallel text.

Take pages from several publishers, decades, fonts, and scan sources. Keep a second, smaller holdout set that you do not use while tuning. Otherwise it is easy to optimize for the first examples and mistake that for general improvement.

Record the sample in a plain manifest:

```csv
page_id,book_id,page_label,script,page_type,image_sha256,ground_truth
p001,b017,23,ara,single_column,8a4f...,truth/p001.txt
p002,b042,118,urd,nastaliq_footnotes,37c1...,truth/p002.txt
p003,b051,ix,mixed,mixed_rtl_ltr,2e90...,truth/p003.txt
```

The page image and its hash are the fixed reference. Engine name, model or language pack, version, settings, runtime, and output paths belong in a separate run record. This lets you reproduce a result instead of remembering that “Paddle looked better last week.”

## Make ground truth small and trustworthy

Transcribe each sampled page exactly enough to answer the question you care about. For search, that usually means body text, headings, names, quotations, and meaningful punctuation. If footnotes matter, include them. If vowel marks or other diacritics matter to the collection, keep them.

Save the transcription as UTF-8. Keep the diplomatic transcription—the text as printed—unchanged. If you need normalized text for comparison, derive it into another file and record the rule. The [W3C string-matching specification](https://www.w3.org/TR/charmod-norm/) recommends normalization for reliable comparison, but compatibility normalization can fold distinctions you may want to preserve. NFC is a reasonable comparison baseline; removing diacritics, changing Urdu characters to Arabic forms, or folding punctuation should be an explicit experiment, never a silent cleanup.

Mixed Arabic/Urdu and English pages need two checks. First, is the underlying Unicode text correct? Second, is its reading order correct? A line can contain the right characters and still be unusable because the English phrase, page number, or footnote was inserted at the wrong point.

## Measure characters and layout separately

Character error rate is a useful first number:

```text
CER = (substitutions + deletions + insertions) / reference characters
```

Compute it per page type and script, not only as one average. A large block of easy English can hide catastrophic Urdu performance. Tools such as [JiWER](https://github.com/jitsi/jiwer) implement character- and word-level error measures, but the normalization policy is part of the result and should be saved beside it.

CER does not measure reading order. The [OCR-D evaluation specification](https://ocr-d.de/en/spec/ocrd_eval.html) treats text, layout, reading order, and runtime as separate quality dimensions. Add a short structural checklist for every sampled page:

- headings before their paragraphs;
- columns in the intended order;
- footnotes attached to the right page and marker;
- tables kept as cells or clearly marked as unreliable;
- mixed-direction phrases in logical reading order;
- page boundaries preserved.

Save a layout-aware output when the engine provides one. Tesseract can emit hOCR or TSV as well as plain text. [ALTO](https://www.loc.gov/standards/alto/) is a maintained XML format for OCR text, page layout, coordinates, and processing metadata. You do not need to standardize the entire archive on day one, but discarding bounding boxes before evaluation makes layout failures much harder to diagnose.

## Test preprocessing as a controlled variable

The [Tesseract quality guide](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html) separates problems such as resolution, binarization, noise, rotation, borders, and page segmentation. Change one family at a time and keep the unmodified source.

For PDFs, [OCRmyPDF](https://ocrmypdf.readthedocs.io/en/latest/advanced.html) can skip pages that already contain text, redo an existing OCR layer, or force rasterization. Those choices are not equivalent. Force mode flattens interactive content and existing text, while skip mode can preserve born-digital pages. Its current renderer supports right-to-left text, but that does not guarantee recognition quality for a particular Urdu font or scan.

A sensible experiment table is small:

```text
run A: original image + engine/model 1
run B: deskew only + engine/model 1
run C: original image + engine/model 2
run D: deskew only + engine/model 2
```

Compare CER, reading order, failed pages, runtime, and storage. Do not run every filter over every book because one damaged sample improved.

## Route pages instead of choosing one universal winner

Once the test is scored, build a simple routing table:

| Page class | Selected route | Review rule |
| --- | --- | --- |
| Born-digital English | Extract existing text | Review only extraction failures |
| Clean Arabic print | Best measured Arabic route | Review below confidence threshold |
| Urdu Nastaliq | Best measured Urdu route | Review names, quotations, and low-confidence spans |
| Mixed RTL/LTR | Layout-aware route | Always check reading order |
| Tables or parallel text | Structure-specific route | Do not index as prose when cells collapse |

Confidence scores from different engines are not directly comparable until you calibrate them against the ground-truth set. A safer rule is based on observed errors: choose a threshold that catches most bad pages in the sample, then manually inspect what falls below it.

## Keep the evidence chain through RAG

For every page, keep four things together:

1. the original page image or source PDF reference;
2. raw OCR and layout output;
3. normalized search text;
4. the exact engine, model, settings, and run time.

Index the normalized text, but make every search result jump back to the source page. If a later correction changes the searchable text, keep the earlier raw output and record the correction instead of overwriting history.

Be particularly careful with language-model cleanup. On religious, legal, historical, or scientific texts, a model can replace an unlikely character with a fluent but false one. Use it to flag suspicious spans or rank pages for review. Do not let it silently rewrite the only stored transcription.

Finally, test retrieval with real questions. Save 20–50 queries, the pages they should find, and the passages a reader must be able to verify. If a query fails because OCR destroyed a name, fix the OCR route. If the text is correct but the vocabulary differs, then lexical plus semantic retrieval may help. The companion [scientific-collection integrity guide](https://blog.lazying.art/html/computer_internet/3788/test-research-pdf-collection-before-local-rag.html) carries that evaluation into versions, citations, retrieval, and graph provenance. This keeps an embedding model from masking a source-quality problem.

## The decision you want after 60 pages

The test should end with a concrete answer:

- which page classes can be processed automatically;
- which route wins for each script and layout;
- which pages require review;
- what error rate and reading-order failures remain;
- how long and how much storage a full run would take;
- whether the collection is ready for indexing.

I maintain [Local Knowledge Terminal](https://github.com/lachlanchen/LocalKnowledgeTerminal), which keeps multilingual collection work tied to inspectable sources. Its [sample report](https://lazying.art/lkt/sample-report/?utm_source=lazyblog&utm_medium=article&utm_campaign=local_knowledge_terminal_pilot&utm_content=multilingual_ocr) shows the provenance and go/no-go shape. If you want the same bounded check on one collection, start with the [free fit check](https://lazying.art/lkt/fit-check/?utm_source=lazyblog&utm_medium=article&utm_campaign=local_knowledge_terminal_pilot&utm_content=multilingual_ocr); the optional USD 250 sprint is scoped only after the metadata and rights fit. It evaluates a representative sample, not custom OCR or a full-library conversion.

The useful order is simple: sample, transcribe, measure, route, preserve, then index.
