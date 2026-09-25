import test from 'node:test';
import assert from 'node:assert/strict';
import {validateBrief, starterDraft, createDraft, parseDraft, publicUrl} from '../apps/web/draft-model.mjs';

const brief = {
  name: 'L & N', productUrl: 'https://apps.apple.com/us/app/l-n-speech-practice/id6808872450',
  audience: 'learners who mix up L and N', problem: 'Telling light and night apart',
  feature: 'Short listening rounds and single-word practice.',
  useful: 'Ask a partner to read light and night in a mixed order. Write down what you hear.',
  price: 'iPhone: US$0.99.', limitation: 'Practice feedback, not a diagnosis.',
  evidenceUrl: 'https://apps.apple.com/us/app/l-n-speech-practice/id6808872450',
  destinationUrl: 'https://www.linkedin.com/in/lazyingart/', account: 'LazyingArt',
};
const stamp = '2026-09-25T21:00:00.000Z';

test('starter uses supplied value first and invents no claims', () => {
  const draft = starterDraft(brief);
  assert.equal(draft.title, brief.name);
  assert.ok(draft.body.startsWith(brief.useful));
  for (const field of ['feature', 'limitation', 'price', 'productUrl']) assert.ok(draft.body.includes(brief[field]));
  assert.ok(draft.body.includes('I work on L & N'));
  assert.ok(!draft.body.includes('1000'));
});
test('bounded text and required public facts', () => {
  for (const [key, val] of Object.entries(brief)) {
    if (key === 'limitation') continue;
    assert.throws(() => validateBrief({...brief, [key]: ''}), key);
    assert.throws(() => validateBrief({...brief, [key]: val + '\u0000'}), key);
  }
  assert.equal(validateBrief({...brief, limitation: ''}).limitation, '');
  assert.throws(() => validateBrief({...brief, name: 'n'.repeat(121)}));
});
test('only public HTTPS links are accepted, no URL is fetched', () => {
  assert.equal(publicUrl('https://play.google.com/store/apps/details?id=art.lazying.landn'), 'https://play.google.com/store/apps/details?id=art.lazying.landn');
  for (const url of ['javascript:alert(1)', 'http://example.com', 'https://127.0.0.1/',
    'https://[::1]/', 'https://app.local/', 'https://localhost/', 'https://app.internal/',
    'https://user:password@example.com/', 'https://example.com:9000/', 'https://example.com/#token',
    'https://example.com/\nsecret', 'https://example.com\\private', 'https://2130706433/']) {
    assert.throws(() => publicUrl(url), url);
  }
});
test('local drafts round-trip without claiming verification or send approval', () => {
  const original = createDraft(brief, 'Edited title', 'My edited copy', stamp);
  assert.deepEqual(parseDraft(JSON.stringify(original)), original);
  assert.equal(original.publication, 'not_connected');
  assert.equal(original.sourceVerification, 'user_supplied_unverified');
  assert.equal(original.state, 'draft');
});
test('unknown private fields and fake approvals cannot be retained', () => {
  const original = createDraft({...brief, token: 'not-real'}, 'Title', 'Body', stamp);
  const restored = parseDraft(JSON.stringify({...original, approval: {publish: true}, token: 'not-real'}));
  assert.ok(!('token' in restored.brief));
  assert.ok(!('token' in restored));
  assert.ok(!('approval' in restored));
  for (const change of [{version: 2}, {state: 'approved'}, {publication: 'published'}, {sourceVerification: 'verified'}]) {
    assert.throws(() => parseDraft(JSON.stringify({...original, ...change})));
  }
});
test('invalid, oversized, empty and malformed saved content is rejected', () => {
  for (const raw of [null, 'invalid', '{}', 'x'.repeat(65537), 'null']) assert.throws(() => parseDraft(raw));
  for (const stamp of ['yesterday', null, '2026-13-50T21:00:00Z']) assert.throws(() => createDraft(brief, 'Title', 'Body', stamp));
  assert.throws(() => createDraft(brief, '', 'body', stamp));
  assert.throws(() => createDraft(brief, 'title', ' '.repeat(100), stamp));
  assert.throws(() => createDraft(brief, 'title', 'x'.repeat(12001), stamp));
});
test('HTML is retained as literal draft text, never interpreted by the model', () => {
  const draft = createDraft(brief, '<script>bad()</script>', '<img src=x onerror=bad()>', stamp);
  assert.equal(parseDraft(JSON.stringify(draft)).body, '<img src=x onerror=bad()>');
});
