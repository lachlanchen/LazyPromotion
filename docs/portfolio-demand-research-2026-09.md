# Current needs matched to the LazyingArt portfolio

Updated: 2026-09-04

The current public inventory contains 104 non-archived source repositories.
The useful question is not how to promote all of them. It is which combinations
already solve a problem someone has described clearly enough to test.

## What should be active now

### 1. Private scientific collection integrity check — USD 250

People building local search over hundreds or thousands of scientific PDFs are
not mainly asking for another chat interface. They are struggling with shallow
cross-document retrieval, multilingual material, silent parsing loss, versions,
tables, equations, provenance, and the absence of a small evaluation set.

That maps well to the existing LKT collection-fit sprint. For a scientific
collection, its representative sample should answer five questions before a
full re-index:

1. What text, structure, tables, or equations disappear during extraction?
2. Which document identity and version fields survive?
3. Can every retrieved passage return to an exact file and page?
4. Which 20–50 real questions expose retrieval misses?
5. Is full-text search, hybrid retrieval, or a knowledge graph actually needed?

This remains a fit report and small browser proof—not ingestion of a 17,000-PDF
library. The clearest current signals are a multilingual 300-PDF owner reporting
shallow retrieval and a scientific-library builder asking how to design for
17,000 PDFs.

The [synthetic scientific-PDF mini-sprint](../examples/lkt-scientific-pdf-fit/)
now supplies the missing executed proof without using customer or third-party
content. It records one duplicate, a v1/v2 family, multilingual extraction, 20
fixed lexical questions, one vocabulary miss, page-resolvable citations, known
table/equation/translation weaknesses, and explicit GO/NO-GO boundaries. This
closes the format-specific proof gap only; it does not validate a real large
collection, OCR, semantic retrieval, or a knowledge graph.

### 2. Manuscript Build & Redline Sprint — USD 250

A current USD 200 marketplace listing asks for claim-preserving academic edits,
figure and table compliance, tracked changes or a redline, and confidentiality.
Other current listings cluster around LaTeX finalization and journal formatting.
The portfolio already has PaperAgent, the paper-revision workflow, a complete
latexdiff guide, and a reproducible three-build sample.

The resulting [fixed offer](https://lazying.art/manuscript-sprint/) covers one
LaTeX manuscript up to 7,500 words, one target template, a clean build, issue
ledger, and redline from a supplied baseline. Its [fit
check](https://lazying.art/manuscript-sprint/fit-check/) keeps the manuscript
private until handling and scope are agreed.

## What should stay in evidence-building

| Need observed now | Portfolio combination | Small next proof | Why it is not the first sales route |
|---|---|---|---|
| Video URL → transcript → important timestamps → searchable knowledge base | Video2Book + MultilingualWhisper + LocalKnowledgeTerminal | One owned lecture with source-linked transcript, concepts, subtitles, and search | The public request is clear, but it is product feedback rather than a buyer; the live pack is still capped at 20 minutes |
| Real-time local translation for mixed-language media | MultilingualWhisper + LazyEdit + FuriganaSubtitles | Measured latency, VRAM, long-audio, and language-pair tests | Current requests need real-time or hour-long performance that the portfolio has not publicly measured |
| Passage-aligned Classical Chinese with readings, glosses, and provenance | PocketPolyglot + LinguaLeaf + zhjpbook + LKT graph | One title-level rights-cleared lesson whose gloss and history edges expose sources and uncertainty | Learner demand is strong, but buying power and title-level reuse rights are unresolved |
| Multilingual etymology collections with trustworthy relationships | WordOrigins + LKT graph + LinguaLeaf + WordsCardEink | A small openly licensed deck with source, locator, relation type, uncertainty, and correction history on every edge | Existing tools are plentiful; accuracy and provenance—not another pretty graph—must be demonstrated first |

## Evidence used

- [A current academic editing job](https://www.upwork.com/freelance-jobs/apply/Academic-Editor-Needed_~022095485257926469387/) asks for three submission-ready manuscripts, a reviewable redline, formatting work, and confidentiality at USD 200 fixed.
- [A 300-PDF local RAG owner](https://www.reddit.com/r/Rag/comments/1tyd87d/local_rag_over_300_pdfs_anythingllm_ollama/) describes multilingual books, limited hardware, shallow retrieval, cross-document connections, and grounded citations.
- [A 17,000-paper local RAG discussion](https://www.reddit.com/r/Rag/comments/1v94yfz/if_you_were_building_a_fully_local_rag_system_for/) repeatedly raises parsing, document versions, tables, formulas, metadata, evaluation, and citation graphs.
- [Hermes Agent issue #12885](https://github.com/NousResearch/hermes-agent/issues/12885) describes the daily friction of extracting subtitles, translating them, finding important timestamps, and storing video knowledge; maintainers currently label it low priority.
- [A current lecture-notes request](https://www.reddit.com/r/NoteTaking/comments/1w31va8/recording_lectures/) validates the transcript → summary → later search requirement, but the learner prefers free software and already accepted another recommendation.
- [An English-only Classical Chinese beginner](https://www.reddit.com/r/classicalchinese/comments/1s3bm63/started_learning_classical_non_mandarin_speaker/) wants affordable guidance and glyph origins, while experienced readers warn that unsupported generated explanations can be confidently wrong.
- [An Analects learning project](https://www.reddit.com/r/ChineseLanguage/comments/1vkx5ss/the_analects_for_learners_15920_definitions/) is evidence that passage-specific glosses, readings, aligned text, and removable annotations are useful; it is another creator's work, not a place to pitch.

## Operating decision

Keep the current Postiz queue. The September 9 LaTeX guide post already leads
to the new manuscript fit check, so another announcement would be repetitive.
Use community discussions as product evidence unless a fresh question can be
answered completely and the local rules permit an affiliated link. Traffic,
stars, replies, applications, and pending balances remain evidence—not revenue.
