import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {validateWorkspace, parseSnapshot, safeLink, outcomeText} from '../apps/web/model.mjs';
const fixture = JSON.parse(execFileSync('python3', ['app_workspace.py'], {encoding: 'utf8'}));

test('real public projection renders without inventing outcomes', () => {
  assert.equal(validateWorkspace(fixture), fixture);
  assert.equal(fixture.projects.length, 2);
  assert.equal(outcomeText(fixture.projects[0].outcomes.installs), 'Not connected');
});
test('unsupported versions and actions are not silently accepted', () => {
  for (const key of ['version', 'capabilities']) {
    const data = structuredClone(fixture);
    if (key === 'version') data.version = 2;
    else data.capabilities.publish = true;
    assert.throws(() => validateWorkspace(data));
  }
});
test('empty campaigns are valid, duplicate projects are not', () => {
  assert.deepEqual(validateWorkspace({...fixture, projects: []}).projects, []);
  assert.throws(() => validateWorkspace({...fixture, projects: [fixture.projects[0], fixture.projects[0]]}));
});
test('snapshots require a dated, valid read-only workspace', () => {
  const saved = {fetchedAt: '2026-09-25T18:30:00.000Z', workspace: fixture};
  assert.equal(parseSnapshot(JSON.stringify(saved)).fetchedAt, saved.fetchedAt);
  for (const raw of [null, '{}', '{"fetchedAt":"yesterday"}', 'x'.repeat(524289)]) {
    assert.throws(() => parseSnapshot(raw));
  }
});
test('external links cannot become script or credential destinations', () => {
  assert.equal(safeLink('https://apps.apple.com/us/app/l-n-speech-practice/id6808872450'), true);
  for (const url of ['javascript:alert(1)', 'data:text/html,bad', 'https://evil.example/',
    'http://127.0.0.1/', 'https://password@github.com/', 'https://github.com:9443/', 'https://github.com/#secret']) {
    assert.equal(safeLink(url), false);
  }
});
test('unknown metrics are never formatted as revenue or zero', () => {
  assert.equal(outcomeText({state: 'not_connected', value: null}), 'Not connected');
  assert.equal(outcomeText({state: 'not_connected', value: 0}), 'Unavailable');
  const data = structuredClone(fixture);
  data.projects[0].outcomes.receivedGrossUsd.value = 1000;
  assert.throws(() => validateWorkspace(data));
});
