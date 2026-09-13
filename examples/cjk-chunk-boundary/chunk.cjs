'use strict';

// A diagnostic hard cap, not a tokenizer or a semantic retrieval strategy.
function splitWithOffsets(text, maxCodePoints = 200) {
  if (typeof text !== 'string') throw new TypeError('text must be a string');
  if (!Number.isSafeInteger(maxCodePoints) || maxCodePoints < 1) {
    throw new RangeError('maxCodePoints must be a positive safe integer');
  }
  const chunks = [];
  let start = 0;
  let end = 0;
  let count = 0;
  for (const point of text) {
    end += point.length; // JavaScript slice offsets use UTF-16 code units.
    count += 1;
    if (count === maxCodePoints) {
      chunks.push({start, end, codePoints: count, text: text.slice(start, end)});
      start = end;
      count = 0;
    }
  }
  if (count) chunks.push({start, end, codePoints: count, text: text.slice(start, end)});
  return chunks;
}

module.exports = {splitWithOffsets};
