# Source-bounded educational prompt specimen

This project-owned specimen turns a learning objective and reference material
into one neutral, checkable lesson. It is topic-neutral and ready to paste into
an editable document. It is evidence of prompt structure, not a customer
delivery or a guarantee about a particular model.

## Prompt

You are preparing a short technical lesson from material supplied by the
editor. Write for the stated learner level and make every factual claim
traceable to that material.

### Inputs

- `learning_goal`: what the learner should be able to explain or do afterward
- `learner_level`: assumed knowledge and any prerequisites
- `source_material`: the only factual reference for the lesson
- `target_length`: desired word count or reading time
- `notation_and_terms`: required symbols, units, vocabulary, or conventions
- `citation_style`: how passages, pages, timestamps, or links should be cited

If an input is missing in a way that would change the lesson, list the missing
item and stop. Do not guess it.

### Work

1. Restate the learning goal as one observable learner outcome.
2. Identify no more than three prerequisites from `learner_level`.
3. Explain the idea in the smallest logical sequence that reaches the outcome.
4. Preserve equations, units, names, and qualifications from the source.
5. Include one worked example only when the source supports it.
6. End with one short check for understanding and a separate answer.

### Output

Use these headings:

1. Learning goal
2. Prerequisites
3. Explanation
4. Worked example, or “Not supported by the supplied material”
5. Check for understanding
6. Answer
7. Sources and limits

Under “Sources and limits,” cite the supporting page, passage, timestamp, or
URL for each main claim. State what the supplied material does not establish.

### Constraints

- Use a neutral, direct voice. Do not advertise, praise, or address the reader
  with motivational filler.
- Define a technical term at first use unless it appears in the stated
  prerequisites.
- Do not introduce a factual claim, quotation, citation, or numerical example
  that cannot be traced to `source_material`.
- Clearly label any necessary inference and the evidence that supports it.
- Prefer a short sentence over unexplained jargon, but do not replace a precise
  technical term with an inaccurate simplification.
- Stay within `target_length`, excluding citations.

### Evaluation

Before returning the lesson, check that:

- every part contributes to the stated learning goal;
- the explanation assumes no knowledge beyond `learner_level`;
- equations, units, names, quotations, and citations match the source;
- the worked example is reproducible from the information given;
- the learner check has one answer justified by the lesson; and
- unsupported or missing information is named rather than invented.

Return only the completed lesson or the short missing-input list.

## Section annotation

- **Inputs** make the audience, evidence, and acceptance boundary explicit.
- **Work** gives the lesson a reproducible order without prescribing a topic.
- **Output** makes the result easy to review and reuse.
- **Constraints** protect neutrality, source fidelity, and accessibility.
- **Evaluation** turns general quality claims into checks an editor can apply.
