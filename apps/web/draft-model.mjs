// Local authoring only. This format is not an operator approval or send request.
export const draftKey = 'lazypromotion.local-draft.v1';
export const briefFields = {
  name: 120, productUrl: 2048, audience: 300, problem: 600, feature: 1000,
  useful: 3000, price: 300, limitation: 600, evidenceUrl: 2048,
  destinationUrl: 2048, account: 120,
};

function bounded(value, limit, optional = false) {
  if (typeof value !== 'string' || value.length > limit ||
      /[\u0000-\u0008\u000b-\u001f\u007f]/u.test(value) || (!optional && !value.trim())) {
    throw new Error('Complete the brief using plain text within the field limits.');
  }
  return value.trim();
}

export function publicUrl(value) {
  // URLs are not fetched. Keep credentials, local services and non-web schemes
  // out of exported campaign references; this is not a general secret scanner.
  const input = bounded(value, 2048);
  let url;
  try { url = new URL(input); } catch { throw new Error('Use a public HTTPS URL.'); }
  if (!input.startsWith('https://') || /\s|\\/.test(input) ||
      url.protocol !== 'https:' || url.username || url.password || url.port || url.hash ||
      !/^(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,63}$/i.test(url.hostname) ||
      /(?:^|\.)(?:localhost|local|internal|test|invalid)$/i.test(url.hostname)) {
    throw new Error('Use a public HTTPS URL without passwords, fragments or custom ports.');
  }
  return input;
}

export function validateBrief(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw new Error('Missing app brief.');
  const brief = {};
  for (const [key, limit] of Object.entries(briefFields)) {
    brief[key] = key.endsWith('Url') ? publicUrl(input[key]) : bounded(input[key], limit, key === 'limitation');
  }
  return brief;
}

export function starterDraft(input) {
  const brief = validateBrief(input);
  return {
    title: brief.name,
    body: [brief.useful, `I work on ${brief.name}, for ${brief.audience}.`,
      brief.feature, brief.limitation, `${brief.price}\n${brief.productUrl}`].filter(Boolean).join('\n\n'),
  };
}

export function createDraft(input, title, body, savedAt = new Date().toISOString()) {
  if (typeof savedAt !== 'string' || !/^\d{4}-\d{2}-\d{2}T.*Z$/.test(savedAt) || !Number.isFinite(Date.parse(savedAt))) {
    throw new Error('Invalid draft time.');
  }
  return {
    version: 1, kind: 'local_campaign_draft', state: 'draft', savedAt,
    brief: validateBrief(input), title: bounded(title, 300), body: bounded(body, 12000),
    sourceVerification: 'user_supplied_unverified', publication: 'not_connected',
  };
}

export function parseDraft(raw) {
  if (typeof raw !== 'string' || raw.length > 65536) throw new Error('Invalid saved draft.');
  const data = JSON.parse(raw);
  if (data?.version !== 1 || data.kind !== 'local_campaign_draft' || data.state !== 'draft' ||
      data.sourceVerification !== 'user_supplied_unverified' || data.publication !== 'not_connected') {
    throw new Error('Unsupported saved draft.');
  }
  // Reconstruct only the supported fields. Never preserve injected approvals,
  // credentials, publication states or actions from a modified storage record.
  return createDraft(data.brief, data.title, data.body, data.savedAt);
}
