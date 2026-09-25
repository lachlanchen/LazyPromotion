import {validateWorkspace, parseSnapshot, snapshotKey, outcomeText} from './model.mjs';

const $ = id => document.getElementById(id);
const root = document.querySelector('[data-testid="workspace"]');
const state = {workspace: null, fetchedAt: null, selected: null, fromSaved: false};
const labels = {apple: 'App Store', google: 'Google Play', video: 'Watch demo', repository: 'Source', reader: 'Browser reader'};
const evidence = {public_verified: 'Public visibility checked', account_verified: 'Signed-in check only', unverified: 'Visibility unverified'};
function node(tag, text, className) {
  const el = document.createElement(tag);
  if (text !== undefined) el.textContent = text;
  if (className) el.className = className;
  return el;
}
function link(label, url) {
  const el = node('a', label);
  el.href = url; el.target = '_blank'; el.rel = 'noopener noreferrer';
  return el;
}
function time(value) { return new Date(value).toLocaleString([], {dateStyle: 'medium', timeStyle: 'short'}); }

function render() {
  $('products').replaceChildren(); $('project').replaceChildren();
  const projects = state.workspace?.projects ?? [];
  if (!projects.length) {
    $('project').append(node('h2', 'No published campaigns to show'), node('p', 'Nothing is sent from this preview.'));
    return;
  }
  if (!projects.some(p => p.id === state.selected)) state.selected = projects[0].id;
  for (const project of projects) {
    const button = node('button', undefined, 'product-button');
    button.type = 'button'; button.dataset.project = project.id;
    button.setAttribute('aria-pressed', String(state.selected === project.id));
    button.append(node('span', project.name), node('small', `${project.publications.length} recorded posts`));
    button.addEventListener('click', () => { state.selected = project.id; render(); });
    $('products').append(button);
  }
  const project = projects.find(p => p.id === state.selected);
  $('project').append(node('p', 'Campaign history', 'eyebrow'), node('h2', project.name));
  const links = node('div', undefined, 'links');
  for (const [key, url] of Object.entries(project.links)) links.append(link(labels[key], url));
  $('project').append(links);
  const outcomes = node('dl', undefined, 'outcomes');
  for (const [key, label] of [['installs', 'Installs'], ['customers', 'Customers'], ['receivedGrossUsd', 'Received revenue · USD']]) {
    const item = node('div'); item.append(node('dt', label), node('dd', outcomeText(project.outcomes[key])));
    outcomes.append(item);
  }
  $('project').append(outcomes, node('p', 'Published posts are not installs or sales.', 'muted'));
  const history = node('section', undefined, 'history'); history.setAttribute('aria-label', 'Published posts');
  if (!project.publications.length) history.append(node('p', 'No published posts recorded for this product.'));
  for (const post of [...project.publications].reverse()) {
    const article = node('article'); article.dataset.testid = 'publication';
    const meta = node('div', undefined, 'post-meta');
    meta.append(node('span', post.community || post.platform), node('span', evidence[post.visibilityEvidence], 'evidence'));
    article.append(meta, node('h3', post.title || 'Community introduction'));
    const detail = node('details'); detail.append(node('summary', 'Read published text'), node('p', post.body, 'post-body'));
    article.append(detail);
    const footer = node('footer');
    footer.append(link('Open published post ↗', post.url), node('span', `${time(post.publishedAt)} · record checked ${post.recordCheckedOn}`));
    article.append(footer); history.append(article);
  }
  $('project').append(history);
}

function savedCopy() {
  try { return parseSnapshot(localStorage.getItem(snapshotKey)); } catch { return null; }
}
async function refresh() {
  $('refresh').disabled = true; $('save').disabled = true;
  root.dataset.status = 'loading'; $('sync-state').textContent = 'Loading campaign history…';
  try {
    const response = await fetch('/api/v1/workspace', {cache: 'no-store', signal: AbortSignal.timeout(8000)});
    if (!response.ok) throw new Error('unavailable');
    const raw = await response.text();
    if (raw.length > 524288) throw new Error('oversized');
    state.workspace = validateWorkspace(JSON.parse(raw));
    state.fetchedAt = new Date().toISOString(); state.fromSaved = false;
    root.dataset.status = 'ready'; $('sync-state').textContent = `Loaded ${time(state.fetchedAt)}`;
    $('save').disabled = false;
  } catch {
    const saved = savedCopy();
    state.workspace = saved?.workspace ?? null; state.fetchedAt = saved?.fetchedAt ?? null;
    state.fromSaved = Boolean(saved);
    root.dataset.status = saved ? 'saved' : 'error';
    $('sync-state').textContent = saved ? `Could not refresh · saved copy from ${time(saved.fetchedAt)}` : 'Could not load campaign history. Try Refresh.';
  } finally {
    $('refresh').disabled = false; render();
    if (root.dataset.status === 'error') {
      $('project').replaceChildren(node('h2', 'Campaign history unavailable'), node('p', 'No saved copy is available in this browser.'));
    }
  }
}
$('refresh').addEventListener('click', refresh);
$('save').addEventListener('click', () => {
  if (!state.workspace || state.fromSaved) return;
  try {
    localStorage.setItem(snapshotKey, JSON.stringify({workspace: state.workspace, fetchedAt: state.fetchedAt}));
    $('storage-state').textContent = `Saved locally · fetched ${time(state.fetchedAt)}`;
  } catch { $('storage-state').textContent = 'Could not save a copy. Browser storage may be unavailable.'; }
});
$('clear').addEventListener('click', () => {
  try {
    localStorage.removeItem(snapshotKey); $('storage-state').textContent = 'Saved campaign copy removed.';
    if (state.fromSaved) {
      state.workspace = null; state.fetchedAt = null; state.fromSaved = false;
      root.dataset.status = 'error'; render();
      $('sync-state').textContent = 'Saved copy removed. Refresh to load campaign history.';
    }
  } catch { $('storage-state').textContent = 'Could not remove the saved copy.'; }
});
refresh();
if ('serviceWorker' in navigator) {
  function checkShell() {
    const worker = navigator.serviceWorker.controller;
    if (!worker) return;
    const channel = new MessageChannel();
    const timer = setTimeout(() => channel.port1.close(), 3000);
    channel.port1.onmessage = event => {
      clearTimeout(timer); channel.port1.close();
      if (event.data === 'lazypromotion-preview-shell-v2') {
        $('offline-shell').textContent = 'Offline app ready · save a history copy or draft separately.';
        root.dataset.offlineShell = 'ready';
      }
    };
    worker.postMessage('shell-version', [channel.port2]);
  }
  navigator.serviceWorker.addEventListener('controllerchange', checkShell);
  navigator.serviceWorker.register('/sw.js').then(checkShell).catch(() => {
    $('offline-shell').textContent = 'Offline page support is unavailable. Online drafting still works.';
  });
} else {
  $('offline-shell').textContent = 'Offline page support is unavailable in this browser.';
}
