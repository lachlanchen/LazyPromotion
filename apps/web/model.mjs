export const snapshotKey = 'lazypromotion.public-preview.v1';
const visibility = new Set(['public_verified', 'account_verified', 'unverified']);
const linkHosts = new Set(['apps.apple.com', 'play.google.com', 'www.youtube.com',
  'github.com', 'lachlan.lazying.art', 'www.reddit.com', 'reddit.com', 'x.com', 'twitter.com']);

function require(value) {
  if (!value) throw new Error('Unsupported campaign data');
}
function text(value, max = 20000) {
  require(typeof value === 'string' && value.length > 0 && value.length <= max);
}
export function safeLink(value) {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && linkHosts.has(url.hostname) &&
      !url.username && !url.password && !url.port && !url.hash;
  } catch { return false; }
}
export function validateWorkspace(value) {
  require(value?.version === 1 && value.mode === 'public_campaign_preview');
  require(value.capabilities?.readPublishedCampaigns === true);
  for (const key of ['discover', 'draft', 'approve', 'publish', 'paymentAttribution']) {
    require(value.capabilities[key] === false);
  }
  require(Array.isArray(value.projects) && value.projects.length <= 20);
  const ids = new Set();
  for (const project of value.projects) {
    text(project.id, 120); text(project.name, 300);
    require(!ids.has(project.id)); ids.add(project.id);
    require(project.links && typeof project.links === 'object' && !Array.isArray(project.links));
    require(Object.keys(project.links).every(key => ['apple', 'google', 'video', 'repository', 'reader'].includes(key)));
    require(Object.values(project.links).every(safeLink));
    require(Array.isArray(project.publications) && project.publications.length <= 100);
    const posts = new Set();
    for (const post of project.publications) {
      text(post.id, 300); text(post.body); text(post.platform, 40);
      require(!posts.has(post.id)); posts.add(post.id);
      require(post.title === null || typeof post.title === 'string');
      require(post.community === null || typeof post.community === 'string');
      require(safeLink(post.url) && visibility.has(post.visibilityEvidence));
      require(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(post.publishedAt) && Number.isFinite(Date.parse(post.publishedAt)));
      require(/^\d{4}-\d{2}-\d{2}$/.test(post.recordCheckedOn));
      require(/^[a-f0-9]{64}$/.test(post.bodySha256));
    }
    for (const key of ['installs', 'customers', 'receivedGrossUsd']) {
      require(project.outcomes?.[key]?.state === 'not_connected' && project.outcomes[key].value === null);
    }
  }
  return value;
}
export function parseSnapshot(raw) {
  require(typeof raw === 'string' && raw.length < 524288);
  const saved = JSON.parse(raw);
  require(typeof saved.fetchedAt === 'string' && Number.isFinite(Date.parse(saved.fetchedAt)));
  validateWorkspace(saved.workspace);
  return saved;
}
export function outcomeText(metric) {
  return metric?.state === 'not_connected' && metric.value === null ? 'Not connected' : 'Unavailable';
}
