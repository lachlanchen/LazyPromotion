// Execute the real collector against a synthetic, virtualized metadata-only DOM.
const fs = require('node:fs');
const vm = require('node:vm');
const expression = fs.readFileSync(0, 'utf8');
const scenario = process.argv[2];
let top = 70;
let moved = false;
const total = scenario === 'short' ? 8 : 100;
const scroller = {
  clientHeight: 100,
  isConnected: true,
  get scrollTop() { return top; },
  set scrollTop(value) {
    if (value > 70) moved = true;
    if (scenario !== 'stuck' || value === 0 || value === 70) top = value;
  },
};
const folder = {
  getAttribute(name) {
    if (name !== 'aria-selected') throw new Error('Unexpected folder field');
    return scenario === 'folder-change' && moved ? 'false' : 'true';
  },
};
function row(position) {
  const match = position === (scenario === 'short' ? 7 : 43);
  const participants = match ? 'Hiring Team' : 'Other Person';
  return {
    getAttribute(name) {
      if (name === 'aria-posinset') return String(position);
      if (name === 'aria-setsize') return String(scenario === 'growing' && !moved ? 50 : total);
      throw new Error('Unapproved row attribute');
    },
    querySelector(selector) {
      if (selector === '.thread-participants') return {textContent: participants};
      if (selector === '.thread-subject') {
        if (scenario === 'missing' && position === 9) return null;
        return {textContent: scenario === 'shifted' && moved && position === 0
          ? 'Changed head' : match ? 'Alpha role' : 'Unrelated subject'};
      }
      if (selector === '.thread-timestamp') return {textContent: 'Yesterday'};
      if (selector === '.adornment-unread') return match ? {} : null;
      throw new Error('Unapproved row field');
    },
  };
}
const tree = {
  isConnected: true,
  querySelector(selector) {
    if (selector === '[role="treeitem"][aria-posinset="0"]') return row(0);
    throw new Error('Unexpected tree selector');
  },
};
const document = {
  querySelector(selector) {
    if (selector === '[role="tree"][aria-label="Messages"]') return tree;
    throw new Error('Unexpected document selector');
  },
  querySelectorAll(selector) {
    if (selector.startsWith('[role="option"]')) return [folder];
    if (selector === '.thread-list-actual') return [scroller];
    if (selector === '[role="tree"][aria-label="Messages"] [role="treeitem"]') {
      const start = Math.floor(top / 10);
      return Array.from({length: Math.min(10, Math.max(0, total - start))}, (_, i) => row(start + i));
    }
    throw new Error('Unexpected document selector');
  },
};
(async () => {
  try {
    const result = await vm.runInNewContext(expression, {
      document, CSS: {escape: value => value}, setTimeout: callback => callback(),
    });
    process.stdout.write(JSON.stringify({...result, restoredTop: top}));
  } catch (error) {
    process.stdout.write(JSON.stringify({error: error.message, restoredTop: top}));
  }
})();
