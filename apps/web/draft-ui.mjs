import {briefFields, draftKey, validateBrief, starterDraft, createDraft, parseDraft} from './draft-model.mjs';

const $ = id => document.getElementById(id);
const form = $('brief-form');
let generatedFrom = null;
let dirty = false;
let savedRaw = null;
const message = text => { $('draft-status').textContent = text; };
function briefInput() {
  return Object.fromEntries(Object.keys(briefFields).map(key => [key, form.elements[key].value]));
}
function currentDraft() {
  const brief = validateBrief(briefInput());
  if (JSON.stringify(brief) !== generatedFrom) throw new Error('The brief changed. Build a new draft before saving or exporting.');
  return createDraft(brief, $('draft-title').value, $('draft-body').value);
}
function hidePreview() { $('draft-preview').hidden = true; }
function edited() { dirty = true; hidePreview(); message('Unsaved changes. Nothing has been posted.'); }
form.addEventListener('input', edited);
$('draft-title').addEventListener('input', edited);
$('draft-body').addEventListener('input', edited);
form.addEventListener('submit', event => {
  event.preventDefault();
  try {
    const brief = validateBrief(briefInput());
    const draft = starterDraft(brief);
    if (!$('draft-editor').hidden && !window.confirm('Replace the current draft text with a new starter?')) return;
    generatedFrom = JSON.stringify(brief);
    $('draft-title').value = draft.title; $('draft-body').value = draft.body;
    $('draft-editor').hidden = false; dirty = true; hidePreview();
    message('Starter built from your brief. Edit it in your own voice; sources have not been checked.');
    $('draft-title').focus();
  } catch (error) { message(error.message); }
});
$('preview-draft').addEventListener('click', () => {
  try {
    const draft = currentDraft();
    $('preview-destination').textContent = `${draft.brief.account} → ${draft.brief.destinationUrl}`;
    $('preview-source').textContent = `Source to check: ${draft.brief.evidenceUrl}`;
    $('preview-title').textContent = draft.title;
    $('preview-body').textContent = draft.body;
    $('draft-preview').hidden = false;
    message('Preview only. Check the claims, price and destination rules before using this draft.');
    $('draft-preview').focus();
  } catch (error) { hidePreview(); message(error.message); }
});
$('save-draft').addEventListener('click', () => {
  try {
    const raw = JSON.stringify(currentDraft());
    // Do not overwrite a change made in another tab or a different browser run.
    if (localStorage.getItem(draftKey) !== savedRaw) throw new Error('The saved draft changed in another tab. Reload saved draft before replacing it.');
    localStorage.setItem(draftKey, raw); savedRaw = raw; dirty = false;
    message('Draft saved in this browser only. Not encrypted or synced.');
  } catch (error) { message(error.message || 'Could not save the draft.'); }
});
$('load-draft').addEventListener('click', () => {
  try {
    const raw = localStorage.getItem(draftKey);
    if (!raw) { message('No saved draft in this browser.'); return; }
    const draft = parseDraft(raw);
    if (dirty && !window.confirm('Replace your unsaved changes with the saved draft?')) return;
    for (const key of Object.keys(briefFields)) form.elements[key].value = draft.brief[key];
    $('draft-title').value = draft.title; $('draft-body').value = draft.body;
    generatedFrom = JSON.stringify(draft.brief); savedRaw = raw; dirty = false;
    $('draft-editor').hidden = false; hidePreview();
    message(`Loaded saved draft from ${new Date(draft.savedAt).toLocaleString()}. Nothing is scheduled.`);
  } catch { message('The saved draft is unsupported or unreadable. It has not been changed.'); }
});
$('delete-draft').addEventListener('click', () => {
  try {
    const removing = localStorage.getItem(draftKey);
    if (!window.confirm('Remove this browser’s saved draft? The text on screen will remain.')) return;
    if (localStorage.getItem(draftKey) !== removing) throw new Error('The saved draft changed in another tab. Nothing was removed.');
    localStorage.removeItem(draftKey); savedRaw = null; dirty = true;
    message('Saved draft removed. The unsaved text remains on screen.');
  } catch (error) { message(error.message || 'Could not remove the saved draft.'); }
});
$('export-draft').addEventListener('click', () => {
  try {
    const draft = currentDraft();
    if ($('draft-preview').hidden) throw new Error('Preview this exact draft before exporting.');
    const url = URL.createObjectURL(new Blob([JSON.stringify(draft, null, 2) + '\n'], {type: 'application/json'}));
    const anchor = document.createElement('a'); anchor.href = url;
    anchor.download = 'lazypromotion-draft.json'; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    message('Draft exported. Export is not approval, scheduling or publication.');
  } catch (error) { message(error.message); }
});
window.addEventListener('beforeunload', event => {
  if (dirty) { event.preventDefault(); event.returnValue = ''; }
});
try {
  if (localStorage.getItem(draftKey)) message('A saved draft is available. Choose Load saved draft to open it.');
} catch { message('Browser storage is unavailable. Drafting and export still work.'); }
