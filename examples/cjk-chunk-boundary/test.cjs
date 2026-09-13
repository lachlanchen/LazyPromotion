'use strict';

const assert = require('node:assert/strict');
const {test} = require('node:test');
const {splitWithOffsets} = require('./chunk.cjs');

function check(text, budget) {
  const chunks = splitWithOffsets(text, budget);
  assert.equal(chunks.map(chunk => chunk.text).join(''), text);
  let previousEnd = 0;
  for (const chunk of chunks) {
    assert.equal(chunk.start, previousEnd);
    assert.equal(text.slice(chunk.start, chunk.end), chunk.text);
    assert.equal(chunk.codePoints, [...chunk.text].length);
    assert.ok(chunk.codePoints > 0 && chunk.codePoints <= budget);
    previousEnd = chunk.end;
  }
  assert.equal(previousEnd, text.length);
  return chunks;
}

test('a whitespace-free Chinese passage needs more than a word budget', () => {
  const text = '春山映水，白云过桥。'.repeat(100);
  assert.equal([...text.matchAll(/\S+/g)].length, 1);
  assert.equal([...text].length, 1000);
  assert.equal(check(text, 200).length, 5);
});

test('UTF-16 locators retain supplementary CJK characters and emoji', () => {
  const chunks = check('甲𠮷乙🧪丙', 2);
  assert.deepEqual(chunks.map(({start, end}) => [start, end]), [[0, 3], [3, 6], [6, 7]]);
  assert.deepEqual(chunks.map(chunk => chunk.text), ['甲𠮷', '乙🧪', '丙']);
});

test('English, Japanese, whitespace and mixed passages preserve exact source', () => {
  for (const text of [
    '', ' ', '\n\t  ', 'An English paragraph.\nNext line.',
    '静かな川のそばで本を読む。'.repeat(30),
    '中文 English 日本語\r\nsecond line 🧪', 'https://example.invalid/' + 'x'.repeat(600),
  ]) {
    for (const budget of [1, 2, 7, 200]) check(text, budget);
  }
});

test('code-point safety is not grapheme-cluster safety or normalization', () => {
  const text = 'e\u0301👩‍🔬';
  const chunks = check(text, 1);
  assert.equal(chunks[0].text, 'e');
  assert.equal(chunks[1].text, '\u0301');
  assert.notEqual(text, text.normalize('NFC'));
});

test('invalid limits and non-string inputs are rejected', () => {
  for (const budget of [0, -1, 1.5, Infinity, NaN, '200', null, true]) {
    assert.throws(() => splitWithOffsets('source', budget), RangeError);
  }
  for (const text of [null, 42, {}, []]) {
    assert.throws(() => splitWithOffsets(text, 200), TypeError);
  }
});
