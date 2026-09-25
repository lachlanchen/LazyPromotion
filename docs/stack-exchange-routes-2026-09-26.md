# Stack Exchange: app discovery and participation fit

Checked September 26, 2026 (Hong Kong). Research only: no account registration,
answer, comment, profile edit, resource-list edit or advertising submission.

## Where to look

| Site | Decision for L & N and Bunko |
| --- | --- |
| Chinese Language | Worth researching specific pronunciation and reading problems. Its [AI policy](https://chinese.stackexchange.com/help/gen-ai-policy) permits properly attributed assistance, supported by a [moderator policy announcement](https://chinese.meta.stackexchange.com/questions/1974/we-now-have-an-ai-policy). This is conditional participation, not an app-launch invitation. |
| Software Recommendations | The strongest format match for an existing request with explicit app requirements. Its [scope](https://softwarerecs.stackexchange.com/help/on-topic) requires a concrete purpose and feature constraints. Its [AI help page](https://softwarerecs.stackexchange.com/help/gen-ai-policy) requires attribution. Check current local Meta guidance and the full question before considering an answer. |
| English Language Learners | Useful for learning which sound distinctions cause difficulty. [Specific pronunciation questions are on topic, but tool and resource requests are not](https://ell.stackexchange.com/help/on-topic). Its [AI policy](https://ell.stackexchange.com/help/gen-ai-policy) requires attribution; that does not create permission for a promotional answer. |
| Japanese Language | Research only for this agent. The [moderator policy bans AI-generated posts](https://japanese.meta.stackexchange.com/questions/2370/policy-on-banning-ai-generated-content), despite the generic help page describing attribution. Its [scope also excludes learning-resource recommendations](https://japanese.stackexchange.com/help/on-topic). Do not treat the generic help text as an override. |
| Stack Overflow | Research only for this agent: [AI-written content is prohibited](https://stackoverflow.com/help/gen-ai-policy), including drafts. Coding questions concern implementation, not a general audience for the consumer apps. Do not supply AI drafts for a human to paste there. |

## Participation is not a launch channel

The [promotion rules](https://chinese.stackexchange.com/help/promotion) require
affiliation disclosure and useful, complete answers; repeated product mentions
or posting solely to drive sales are inappropriate. Software Recommendations
also expects [an explanation of how each requirement is met](https://softwarerecs.meta.stackexchange.com/questions/356/what-is-required-for-an-answer-to-be-high-quality).
An app name, store link or copied listing is not an answer. Its
[own-software guidance](https://softwarerecs.meta.stackexchange.com/questions/2741/are-there-any-guidelines-for-answering-with-your-own-software)
does not create an exception to those standards.

Where assistance is allowed, identify the specific AI tool and the extent of its
contribution, as well as the maintainer relationship. Keep both disclosures
plain and accurate. Do not fabricate personal use, independent endorsement or
human review. Never publish private prompts or conversation history as proof.
No automated answering, duplicate answers, manufactured questions, comments used
to bypass answer requirements, or private outreach is planned.

Older Stack Exchange questions can remain useful to future readers. Evaluate
their open/locked state, existing answers and unmet requirements; do not apply
Reddit's seven-day reply window mechanically. Age alone neither clears nor
disqualifies an answer, and old questions are not fresh customer leads.

## Concrete needs found

- [Traditional characters and pinyin together in an ebook](https://chinese.stackexchange.com/questions/21024/looking-for-pinyin-traditional-characters-ebooks),
  asked in 2016: a real layout and price concern potentially relevant to Bunko.
  Selected book data and the 1.0.1-era renderer now establish a partial format
  match, but the pronunciation-focused recommendation is held for the content
  issue below. No answer is drafted yet.
- [Chinese, English and pinyin books for intermediate readers](https://chinese.stackexchange.com/questions/14195/chinese-english-pinyin-books-for-young-adult-readers),
  asked in 2015: the display format is relevant, but Bunko's unadapted classics
  must not be advertised as graded intermediate books.
- [Nanjing N/L pronunciation](https://chinese.stackexchange.com/questions/59649/people-in-nanjing-pronounce-n-as-l),
  asked in 2025: seeks prevalence data and regional research, not an exercise
  app. Do not turn an accent-description question into a correction pitch.
- [Recorded English-pronunciation practice](https://softwarerecs.stackexchange.com/questions/4172/learning-english-pronunciation),
  asked in 2014: the author prefers Windows and broader word/sentence practice.
  L & N's mobile L/N drills are not a complete match to those requirements.

These examples establish problem patterns, not qualified users or purchases.
The next useful research target is an open request whose required platform,
language, text collection and practice scope actually match the shipping app.
Account eligibility and current policy review remain unresolved; no registration
is needed merely to research the public questions.

### Bunko content check: traditional text is real; pronunciation fit is held

The [Journey to the West bundle](https://github.com/lachlanchen/bunko-books/blob/09644d26513ad8cd447109f402cf0d0e8db6fe50/books/journey-to-the-west/c0001.json)
contains traditional forms such as 聞, 數, 萬 and 歲, with pinyin tokens beside
them in the data. The [1.0.1-era renderer](https://github.com/lachlanchen/Bunko/blob/286c8a3/src/components/Line.tsx)
places supplied readings in HTML ruby, and that revision's CSS places them above
the characters. This is source/data verification, not a new native-device test
or a catalogue-wide script audit. Interface localization is not the evidence.

However, chapter one's second paragraph supplies `wèi` for 為 in both
`歲為一元` and `分為十二會`. The [Ministry of Education dictionary](https://dict.mini.moe.edu.tw/SearchIndex/word_detail?breadcrumbs=Search_&wordID=D0002104)
assigns `wéi` to the being/becoming senses; applying those senses to these two
sentences indicates a contextual annotation error. This limited check does not
estimate the catalogue's overall error rate. The app displays the supplied
reading, so layout support alone does not make this a reliable pronunciation
exercise for the questioner's stated purpose.

Hold this specific answer pending corrected, published data and a fresh sample
check. Bunko is also an app, not an established Kindle/EPUB export; the reader's
update considering an iPhone app makes that an explicit alternative, not an
exact match to the original device requirement. No book data, sibling project,
existing campaign or queue was changed. The broader reading-discovery route
remains available without claiming pronunciation-reference accuracy.

## Community advertising is not currently an available shortcut

Some help pages still link to free community/open-source ads. The newer
[staff announcement, updated June 2026](https://meta.stackexchange.com/questions/416429/a-proposal-for-bringing-back-community-promotion-open-source-ads),
says the proposed restart was deprioritized for at least a couple of quarters.
No active submission cycle was established in this check. Do not create ad
assets, promise free placement or submit to an old annual thread on that basis.

The existing Reddit and Instagram schedules are unchanged. Stack Exchange is a
selective research and useful-answer route, not a reason to increase posting
volume or divert from the two apps.
