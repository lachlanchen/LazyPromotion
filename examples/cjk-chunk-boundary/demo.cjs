'use strict';

const {splitWithOffsets} = require('./chunk.cjs');
const text = '春山映水，白云过桥。'.repeat(100);
const chunks = splitWithOffsets(text, 200);
process.stdout.write(JSON.stringify({
  source: 'synthetic multilingual regression fixture',
  whitespaceMatches: [...text.matchAll(/\S+/g)].length,
  codePoints: [...text].length,
  chunks: chunks.length,
  maximumChunkCodePoints: Math.max(...chunks.map(chunk => chunk.codePoints)),
  exactSourceRecovered: chunks.map(chunk => chunk.text).join('') === text,
  offsetUnit: 'UTF-16 code units, exclusive end',
  embeddingTokenLimitVerified: false,
}, null, 2) + '\n');
