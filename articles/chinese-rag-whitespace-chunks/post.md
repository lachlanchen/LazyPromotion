---
id: 3841
title: "Why Your Chinese Document Becomes One Giant RAG Chunk"
slug: "chinese-rag-whitespace-chunking-source-offsets"
status: "publish"
source_language: "en"
categories:
  - "Computer & Internet"
  - "Artificial Intelligence"
tags:
  - "RAG"
  - "Chinese"
  - "JavaScript"
excerpt: "A small regression test for Chinese and Japanese document ingestion: catch whitespace-based chunking, add a code-point cap, and preserve source offsets without confusing characters with embedding tokens."
---

Before changing an embedding model, print the length of your largest chunk. If a Chinese document has become one enormous record, the problem may be much simpler than retrieval quality: the splitter is counting spaces.

This JavaScript looks like a reasonable way to find words:

```js
const text = '春山映水，白云过桥。'.repeat(100);
const words = [...text.matchAll(/\S+/g)];
console.log(words.length); // 1
console.log([...text].length); // 1000 Unicode code points
```

The regular expression finds runs of non-whitespace. Chinese punctuation does not introduce spaces, so the whole passage is one match. A limit of “200 words” will not split it. Long unbroken URLs and some extracted document text can produce the same surprise.

A [September 11 RunAnywhere Web SDK issue](https://github.com/RunanywhereAI/runanywhere-sdks/issues/922) describes this exact failure in a TypeScript ingestion path, separate from an earlier native-core fix. It is a useful reminder to test the actual path your application calls. Testing the desktop implementation does not establish what the browser implementation does.

## First, make the failure visible

Keep one small, whitespace-free fixture beside an English paragraph. Inspect the chunk count, largest chunk, and whether every chunk still points to the right part of the source. Do this before embedding anything.

I put a [runnable example and tests](https://github.com/lachlanchen/LazyPromotion/tree/main/examples/cjk-chunk-boundary) together. For the 1,000-code-point passage above, the whitespace matcher produces one unit. A hard cap of 200 code points produces five chunks, each with an exact source range. Joining them recovers the original text.

From the repository root:

```bash
node examples/cjk-chunk-boundary/demo.cjs
node --test examples/cjk-chunk-boundary/test.cjs
```

This is a small ingestion check, not a benchmark of an embedding model or a patch for the RunAnywhere SDK.

## Add a hard cap without losing the source

A sentence or paragraph splitter can choose useful boundaries. It still needs a fallback when a paragraph has no suitable break. This minimal fallback counts Unicode code points while retaining JavaScript-compatible source offsets:

```js
function splitWithOffsets(text, maxCodePoints = 200) {
  if (typeof text !== 'string') {
    throw new TypeError('text must be a string');
  }
  if (!Number.isSafeInteger(maxCodePoints) || maxCodePoints < 1) {
    throw new RangeError('maxCodePoints must be a positive safe integer');
  }
  const chunks = [];
  let start = 0, end = 0, count = 0;

  for (const point of text) {
    end += point.length;
    count += 1;
    if (count === maxCodePoints) {
      chunks.push({start, end, text: text.slice(start, end)});
      start = end;
      count = 0;
    }
  }
  if (count) {
    chunks.push({start, end, text: text.slice(start, end)});
  }
  return chunks;
}
```

The [complete version](https://github.com/lachlanchen/LazyPromotion/blob/main/examples/cjk-chunk-boundary/chunk.cjs) also records each chunk's code-point count. The example deliberately has no overlap or sentence scoring, so its source-preservation behavior is easy to inspect.

There are two different units here. JavaScript's string iterator steps through Unicode code points; `slice` uses UTF-16 code-unit offsets. A supplementary character such as `𠮷`, or the emoji `🧪`, occupies two of those code units. Adding `point.length` keeps the locator in the right coordinate system instead of assuming every visible character occupies one position. [MDN explains the iterator's behavior](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/Symbol.iterator).

For `甲𠮷乙🧪丙` and a two-code-point cap, the ranges are `[0, 3)`, `[3, 6)`, and `[6, 7)`. Each range can be reopened with `source.slice(start, end)`. The test checks that exact operation.

Code points are not the same as user-perceived characters. Combining accents and joined emoji can span several code points, so this fallback can cut inside a grapheme cluster. If the chunks also become reader-facing excerpts, use grapheme-aware boundaries or expand the displayed excerpt around its locator. Keep the hard-cap policy explicit when a single grapheme is itself unusually long.

## A character cap is not a token limit

Do not rename this limit `maxTokens`. The five chunks above satisfy a code-point budget; that tells us nothing exact about their size under your embedding model's tokenizer.

After choosing structural boundaries and applying a hard cap, count tokens with the tokenizer for the model you actually use. Check the complete input, including any title, prefix, or metadata you prepend. Split again when necessary. Keep that model-specific check separate from the language-independent regression fixture.

## Keep citations attached through the pipeline

For a multilingual book or knowledge graph, a chunk is only useful if a retrieved passage can lead back to the source. Keep the document revision, chapter or source unit, offset unit, and range alongside the chunk. A content hash can identify the exact extracted text used for those offsets.

Avoid silently normalizing the source before saving a range. Collapsing spaces, converting Unicode normalization forms, correcting OCR, or joining page breaks changes the text the offsets refer to. Keep the original extraction and a separate normalized representation, or retain an explicit mapping between them. A character range in extracted text is not automatically a printed page number or a PDF highlight box.

The practical order is: preserve the source, inspect the chunks, validate the model input size, then evaluate retrieval with questions whose answers you can reopen. That catches an ingestion failure before it gets mistaken for a model-selection problem.

For a collection that needs this kind of source and ingestion check, my [Local Knowledge Terminal sample report](https://lazying.art/lkt/sample-report/?utm_source=lazyblog&utm_medium=article&utm_campaign=cjk_chunk_boundary&utm_content=sample_report) shows the format and the next step for a fixed USD 250 collection-fit sprint.
